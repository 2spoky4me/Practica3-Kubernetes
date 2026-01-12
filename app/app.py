from flask import Flask, request, render_template_string, redirect
import os
import psycopg2
import redis
import json

app = Flask(__name__)

# =====================================================
# VARIABLES DE ENTORNO (inyectadas por Terraform)
# =====================================================
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

INSTANCE_ID = os.getenv("APP_INSTANCE_ID", "0")
APP_ENV = os.getenv("APP_ENV", "dev")
LOGO_URL = os.getenv("LOGO_URL", "")

# -----------------------------
# Redis (cache) - SOLO EN PROD
# -----------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = os.getenv("REDIS_PORT", "")

USE_REDIS = APP_ENV == "prod" and REDIS_HOST != "" and REDIS_PORT != ""

if USE_REDIS:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        decode_responses=True
    )
else:
    redis_client = None
    print("⚠ Redis desactivado en este entorno.")


# =====================================================
# CONEXIÓN A POSTGRES
# =====================================================
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


# =====================================================
# HOME
# =====================================================
@app.route("/")
def index():
    return render_template_string("""
    <html>
      <body style="font-family: sans-serif; max-width: 420px; margin: 40px auto;">

        {% if logo_url %}
        <div style="text-align:center;">
          <img src="{{ logo_url }}" alt="Logo" style="max-width:150px; margin-bottom:20px;">
        </div>
        {% endif %}

        <h2>Hola! La aplicación Flask está funcionando 😊</h2>

        <p>Entorno: <b>{{ env }}</b></p>
        <p>Instancia atendida: <b>{{ instance }}</b></p>

        <a href="/form">
          <button style="padding: 10px 20px; font-size: 16px; cursor: pointer;">
            Ir al formulario
          </button>
        </a>

      </body>
    </html>
    """, instance=INSTANCE_ID, env=APP_ENV, logo_url=LOGO_URL)


# =====================================================
# FORMULARIO
# =====================================================
@app.route("/form")
def form():
    return render_template_string("""
    <html>
      <body style="font-family: sans-serif; max-width: 420px; margin: 40px auto;">

        {% if logo_url %}
        <div style="text-align:center;">
          <img src="{{ logo_url }}" alt="Logo" style="max-width:150px; margin-bottom:20px;">
        </div>
        {% endif %}

        <h2>Registro (Instancia {{ instance }})</h2>

        <form method="POST" action="/submit">
          Nombre:<br><input name="name"><br><br>
          Apellido:<br><input name="surname"><br><br>
          Edad:<br><input name="age"><br><br>

          <button type="submit">Enviar</button>
        </form>

        <br><a href="/">Volver</a>

      </body>
    </html>
    """, instance=INSTANCE_ID, logo_url=LOGO_URL)


# =====================================================
# INSERTAR EN DB
# =====================================================
@app.route("/submit", methods=["POST"])
def submit():

    name = request.form["name"]
    surname = request.form["surname"]
    age = request.form["age"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            surname TEXT,
            age INTEGER
        );
    """)

    cur.execute(
        "INSERT INTO users (name, surname, age) VALUES (%s, %s, %s)",
        (name, surname, age)
    )

    conn.commit()
    cur.close()
    conn.close()

    # invalidar cache SOLO si Redis está activo
    if USE_REDIS:
        redis_client.delete("cached_users")

    return redirect("/list")


# =====================================================
# LISTA DE USUARIOS
# =====================================================
@app.route("/list")
def list_users():

    # ---------- DEV: siempre DB, sin caché ----------
    if not USE_REDIS:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, surname, age FROM users ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return render_template_string(TEMPLATE_LIST,
            rows=rows,
            instance=INSTANCE_ID,
            logo_url=LOGO_URL,
            data_source="DB (sin caché en dev)"
        )

    # ---------- PROD: con Redis ----------
    cached = redis_client.get("cached_users")

    if cached:
        rows = json.loads(cached)
        data_source = "CACHE"

    else:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, surname, age FROM users ORDER BY id DESC LIMIT 10")
        rows_raw = cur.fetchall()
        cur.close()
        conn.close()

        # Ya NO hay datetime → no problemas JSON
        rows = []
        for r in rows_raw:
            rows.append([r[0], r[1], r[2], r[3]])

        redis_client.set("cached_users", json.dumps(rows), ex=30)
        data_source = "DB"

    return render_template_string(TEMPLATE_LIST,
        rows=rows,
        instance=INSTANCE_ID,
        logo_url=LOGO_URL,
        data_source=data_source
    )


# =====================================================
# TEMPLATE HTML (Fecha eliminada)
# =====================================================
TEMPLATE_LIST = """
<html>
<body style="font-family: sans-serif; max-width: 700px; margin: 40px auto;">

    {% if logo_url %}
    <div style="text-align:center;">
      <img src="{{ logo_url }}" alt="Logo" style="max-width:150px; margin-bottom:20px;">
    </div>
    {% endif %}

    <h2>Últimos registros (Instancia {{ instance }})</h2>

    <p style="font-size:20px;">
      <b>Fuente de datos:</b>
      {% if data_source.startswith("DB") %}
        <span style="color: red;"><b>{{ data_source }}</b></span>
      {% else %}
        <span style="color: green;"><b>{{ data_source }}</b></span>
      {% endif %}
    </p>

    <table border="1" cellpadding="6">
      <tr><th>ID</th><th>Nombre</th><th>Apellido</th><th>Edad</th></tr>
      {% for r in rows %}
        <tr>
          <td>{{ r[0] }}</td>
          <td>{{ r[1] }}</td>
          <td>{{ r[2] }}</td>
          <td>{{ r[3] }}</td>
        </tr>
      {% endfor %}
    </table>

    <br><a href="/">Volver</a>

</body>
</html>
"""


# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
