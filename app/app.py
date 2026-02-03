from flask import Flask, request, redirect, render_template_string
import os
import psycopg2
import redis
import json
import time


app = Flask(__name__)

# =====================================================
# ENV
# =====================================================
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

APP_ENV = os.getenv("APP_ENV", "dev")
INSTANCE_ID = os.getenv("APP_INSTANCE_ID", "0")

REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = os.getenv("REDIS_PORT", "")

LOGO_URL = os.getenv("LOGO_URL", "")

USE_REDIS = (
    APP_ENV == "prod"
    and REDIS_HOST != ""
    and REDIS_PORT != ""
)

redis_client = None
if USE_REDIS:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        decode_responses=True
    )

# =====================================================
# DB
# =====================================================
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def ensure_table_exists(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            surname TEXT,
            age INTEGER
        );
    """)

# =====================================================
# PROBES
# =====================================================
@app.route("/live")
def live():
    return {"status": "up"}, 200

@app.route("/ready")
def ready():
    try:
        conn = get_connection()
        conn.close()
    except Exception:
        return {"status": "db down"}, 503

    if USE_REDIS:
        try:
            redis_client.ping()
        except Exception:
            return {"status": "redis down"}, 503

    return {"status": "ready"}, 200

import time

@app.route("/health")
def health():
    start_app = time.time()

    result = {
        "app": "up",
        "database": {
            "status": "ok",
            "latency_ms": None
        },
        "redis": {
            "status": "disabled",
            "latency_ms": None
        }
    }

    # Database check
    try:
        start_db = time.time()
        conn = get_connection()
        conn.close()
        result["database"]["latency_ms"] = round((time.time() - start_db) * 1000, 2)
    except Exception:
        result["database"]["status"] = "down"

    # Redis check
    if USE_REDIS:
        result["redis"]["status"] = "ok"
        try:
            start_redis = time.time()
            redis_client.ping()
            result["redis"]["latency_ms"] = round((time.time() - start_redis) * 1000, 2)
        except Exception:
            result["redis"]["status"] = "down"

    result["latency_ms"] = round((time.time() - start_app) * 1000, 2)

    return result, 200


# =====================================================
# UI
# =====================================================
@app.route("/")
def index():
    return render_template_string("""
    <div style="display:flex; align-items:center;">
      {% if logo_url %}
        <img src="{{ logo_url }}" width="60" style="margin-right:15px;">
      {% endif %}
      <h2>Flask App</h2>
    </div>

    <p>Env: {{ env }}</p>
    <p>Instance: {{ instance }}</p>

    <ul>
      <li><a href="/form">Formulario</a></li>
      <li><a href="/list">Listado usuarios</a></li>
    </ul>
    """, env=APP_ENV, instance=INSTANCE_ID, logo_url=LOGO_URL)

@app.route("/form")
def form():
    return render_template_string("""
    <h2>Nuevo usuario</h2>
    <form method="POST" action="/submit">
      Nombre: <input name="name"><br>
      Apellido: <input name="surname"><br>
      Edad: <input name="age"><br>
      <button type="submit">Enviar</button>
    </form>
    <a href="/">Volver</a>
    """)

# =====================================================
# INSERT
# =====================================================
@app.route("/submit", methods=["POST"])
def submit():
    conn = get_connection()
    cur = conn.cursor()

    ensure_table_exists(cur)

    cur.execute(
        "INSERT INTO users (name, surname, age) VALUES (%s, %s, %s)",
        (request.form["name"], request.form["surname"], request.form["age"])
    )

    conn.commit()
    cur.close()
    conn.close()

    if USE_REDIS:
        redis_client.delete("cached_users")

    return redirect("/list")

# =====================================================
# LIST
# =====================================================
@app.route("/list")
def list_users():
    conn = get_connection()
    cur = conn.cursor()
    ensure_table_exists(cur)

    if USE_REDIS:
        cached = redis_client.get("cached_users")
        if cached:
            rows = json.loads(cached)
            data_source = "CACHE"
        else:
            cur.execute(
                "SELECT id, name, surname, age FROM users ORDER BY id DESC LIMIT 10"
            )
            rows = cur.fetchall()
            redis_client.set("cached_users", json.dumps(rows), ex=30)
            data_source = "DB"
    else:
        cur.execute(
            "SELECT id, name, surname, age FROM users ORDER BY id DESC LIMIT 10"
        )
        rows = cur.fetchall()
        data_source = "DB"

    cur.close()
    conn.close()

    return render_template_string(
        TEMPLATE_LIST,
        rows=rows,
        instance=INSTANCE_ID,
        data_source=data_source
    )

# =====================================================
# TEMPLATE
# =====================================================
TEMPLATE_LIST = """
<h2>Usuarios (Instancia {{ instance }})</h2>
<p>Fuente: {{ data_source }}</p>
<table border="1">
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
<a href="/">Volver</a>
"""

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
