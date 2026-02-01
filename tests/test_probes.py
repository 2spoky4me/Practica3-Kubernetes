import requests

DEV_BASE_URL = "http://flask-dev.local:8081"
PRO_BASE_URL = "http://flask-pro.local:8082"


def test_dev_live():
    r = requests.get(f"{DEV_BASE_URL}/live")
    assert r.status_code == 200
    assert r.json()["status"] == "up"


def test_pro_live():
    r = requests.get(f"{PRO_BASE_URL}/live")
    assert r.status_code == 200
    assert r.json()["status"] == "up"


def test_dev_ready():
    r = requests.get(f"{DEV_BASE_URL}/ready")
    assert r.status_code == 200


def test_pro_ready():
    r = requests.get(f"{PRO_BASE_URL}/ready")
    assert r.status_code == 200


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
