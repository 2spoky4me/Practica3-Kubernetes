import requests

DEV_BASE_URL = "http://flask-dev.local:8081"
PRO_BASE_URL = "http://flask-pro.local:8082"


# =========================
# LIVENESS
# =========================

def test_dev_liveness():
    r = requests.get(f"{DEV_BASE_URL}/live")
    assert r.status_code == 200
    assert r.json()["status"] == "up"


def test_pro_liveness():
    r = requests.get(f"{PRO_BASE_URL}/live")
    assert r.status_code == 200
    assert r.json()["status"] == "up"


# =========================
# READINESS
# =========================

def test_dev_readiness():
    r = requests.get(f"{DEV_BASE_URL}/ready")
    assert r.status_code == 200


def test_pro_readiness():
    r = requests.get(f"{PRO_BASE_URL}/ready")
    assert r.status_code == 200


# =========================
# HEALTHCHECK
# =========================

def test_dev_health():
    r = requests.get(f"{DEV_BASE_URL}/health")
    assert r.status_code == 200

    data = r.json()
    assert data["app"] == "up"
    assert data["database"] == "ok"
    assert data["redis"] == "disabled"


def test_pro_health():
    r = requests.get(f"{PRO_BASE_URL}/health")
    assert r.status_code == 200

    data = r.json()
    assert data["app"] == "up"
    assert data["database"] == "ok"
    assert data["redis"] == "ok"
