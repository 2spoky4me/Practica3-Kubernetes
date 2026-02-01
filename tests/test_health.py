import json
import urllib.request
import os

BASE_URL = os.getenv("APP_URL", "http://localhost:8000")


def request(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}") as response:
        body = response.read().decode("utf-8")
        return response.status, body


def test_live_endpoint():
    status, body = request("/live")

    assert status == 200
    data = json.loads(body)
    assert data["status"] == "up"


def test_health_endpoint():
    status, body = request("/health")

    assert status == 200
    data = json.loads(body)

    # app siempre debe estar up
    assert data["app"] == "up"

    # db puede estar up o down (según entorno)
    assert "db" in data
    assert data["db"]["status"] in ["up", "down"]

