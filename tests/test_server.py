import pytest
from fastapi.testclient import TestClient

from app.data import store
from app.data.simulate import generate_schedule, generate_states
from app.main import app
from app.model.risk import predict


@pytest.fixture(autouse=True)
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)


client = TestClient(app)


def test_simulated_data_is_labeled_and_repeatable():
    assert generate_schedule("A", 1) == generate_schedule("A", 1)
    assert all(t["label"] == "Simulated" for t in generate_schedule("B", 2))
    assert all(s["label"] == "Simulated" for s in generate_states(2))


def test_model_levels():
    assert predict({"sleep_hours": 8, "circadian_regularity": 95, "workload_tasks": 3,
                    "hours_awake": 14, "cognitive": 90})["level"] == "low"
    hi = predict({"sleep_hours": 4.5, "circadian_regularity": 55, "workload_tasks": 7,
                  "hours_awake": 19, "cognitive": 60, "fatigue": 5})
    assert hi["level"] == "high" and hi["score"] == 12


def test_full_offline_flow():
    assert client.post("/simulate").status_code == 200
    client.post("/checkin", json={"crew": "A", "sleep_hours": 4.5, "fatigue": 5, "mood": "bad", "stress": 4})
    r = client.post("/predict/A", params={"use_claude": False, "lang": "ar"}).json()
    assert r["label"] == "Simulated" and r["prediction"]["level"] in ("low", "medium", "high")
    if r["changes"]:
        cid = r["changes"][0]["id"]
        assert client.post("/decision", json={"change_id": cid, "decision": "accept"}).status_code == 200
        assert client.get("/schedule/A").json()["proposed"][0]["status"] == "accept"
    assert store.load("health_log")[0]["sleep_hours"] == 4.5


def test_bad_decision_rejected():
    client.post("/simulate")
    assert client.post("/decision", json={"change_id": "x", "decision": "maybe"}).status_code == 400
