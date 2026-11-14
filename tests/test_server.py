import pytest
from fastapi.testclient import TestClient

from app.data import store
from app.data.simulate import generate_ring, generate_schedules
from app.main import app
from app.model.baseline import baseline
from app.model.forecast import forecast


@pytest.fixture(autouse=True)
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)


client = TestClient(app)


def crew(c):
    return [r for r in generate_ring() if r["crew"] == c]


def test_ring_data_labeled_and_repeatable():
    assert generate_ring() == generate_ring()
    assert all(r["label"] in ("Simulated", "Real + simulated") for r in generate_ring())
    assert all(r["label"] == "Simulated" for r in generate_ring(real=False))


def test_real_fitbit_values_used():
    b14 = [r for r in generate_ring() if r["crew"] == "B" and r["day"] == 14][0]
    assert b14["label"] == "Real + simulated" and "Fitbit" in b14["source"]
    assert b14["sleep_hours"] == 5.0 and b14["resting_hr"] == 62  # from data/real/fitbit_daily.csv


def test_baseline_is_personal():
    a, b = baseline(crew("A")), baseline(crew("B"))
    assert a["resting_hr"]["mean"] != b["resting_hr"]["mean"]


def test_not_enough_data_says_unknown():
    f = forecast(crew("A")[:3], {}, 3)
    assert f["unknown"] and "don't know" in f["message"]


def test_demo_story_alert_on_critical_day():
    f = forecast(crew("B"), generate_schedules()["B"], 14)
    alerts = [d for d in f["days"] if d["alert"]]
    assert alerts and alerts[0]["day"] == 16 and "EVA (critical)" in alerts[0]["critical_tasks"]
    assert all(not d["alert"] for d in forecast(crew("A"), generate_schedules()["A"], 14)["days"])


def test_full_offline_flow():
    assert client.post("/simulate").status_code == 200
    q = client.get("/nova/morning/B", params={"lang": "ar"}).json()["question"]
    assert q
    r = client.get("/forecast/B", params={"use_claude": False, "lang": "ar"}).json()
    assert r["label"] in ("Simulated", "Real + simulated") and r["focus_day"] == 16 and r["changes"]
    eff = r["all_changes_effect"]
    assert eff["readiness_after"] >= eff["readiness_before"]
    ids = [c["id"] for c in r["changes"]]
    w = client.post("/whatif/B", json={"day": 16, "change_ids": ids}).json()
    assert w == eff
    assert client.post("/decision", json={"change_id": ids[0], "decision": "accept"}).status_code == 200
    s = client.get("/mission-control/summary").json()
    b = next(x for x in s["crew"] if x["crew"] == "B")
    assert b["alert"] and ids[0] not in b["pending_changes"]


def test_bad_decision_rejected():
    client.post("/simulate")
    assert client.post("/decision", json={"change_id": "x", "decision": "maybe"}).status_code == 400


def test_reassign_only_to_ready_crew():
    client.post("/simulate")
    r = client.get("/forecast/B?use_claude=false").json()
    day = r["focus_day"]
    for c in r["changes"]:
        if c["type"] == "reassign":
            other = client.get(f"/forecast/{c['to_crew']}?use_claude=false").json()
            lvl = next(d["level"] for d in other["forecast"]["days"] if d["day"] == day)
            assert lvl == "low"


def test_digital_twin():
    client.post("/simulate")
    t = client.get("/twin/B").json()
    assert t["label"] in ("Simulated", "Real + simulated") and not t["unknown"]
    assert len(t["forecast"]) == 3
    assert any(d["alert"] for d in t["forecast"])
    assert t["now"]["signals"]["sleep_hours"]["status"].endswith("below normal")
    assert not client.get("/twin/A").json()["forecast"][1]["alert"]


def test_model_view_is_checkable():
    client.post("/simulate")
    m = client.get("/model/B").json()
    assert len(m["ring"]) == 14 and m["max_points"] == 14
    for d in m["days"]:
        assert d["score"] == sum(d["points"].values())
        assert d["readiness"] == round(100 - 100 * d["score"] / m["max_points"])
