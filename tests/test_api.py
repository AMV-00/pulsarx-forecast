from fastapi.testclient import TestClient

from app.main import app
from tests.test_schedule import DAY

client = TestClient(app)


def test_suggest_offline_sentences():
    r = client.post("/suggest", json={
        "facts": {"level": "high", "top_factor": "sleep", "sleep_hours": 5},
        "tasks": DAY, "lang": "ar", "use_claude": False})
    body = r.json()
    assert r.status_code == 200
    assert body["changes"] and all(c["status"] == "pending" and c["reason"] for c in body["changes"])
