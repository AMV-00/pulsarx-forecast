from fastapi.testclient import TestClient

from app.main import app
from app.onboard import hidden_fatigue

client = TestClient(app)


def _first_change(crew="B"):
    r = client.get(f"/forecast/{crew}?use_claude=false").json()
    return r, r["changes"][0]["id"]


def test_offline_decisions_wait_then_sync():
    client.post("/simulate")
    client.post("/link", json={"online": False})
    _, cid = _first_change()
    client.post("/decision", json={"change_id": cid, "decision": "accept"})
    link = client.get("/link").json()
    assert link["waiting"] >= 1 and link["mars_mode"]          # stored onboard, not lost
    assert client.get("/mission-control/inbox").json()["received"] == []
    back = client.post("/link", json={"online": True}).json()
    assert back["just_synced"]["sent"] >= 1 and back["waiting"] == 0
    assert client.get("/mission-control/inbox").json()["received"]


def test_mars_mode_commander_then_earth_confirms():
    client.post("/simulate")
    client.post("/link", json={"place": "mars"})
    r, cid = _first_change()
    assert r["mars_mode"] and "commander" in r["changes"][0]["approver"]
    d = client.post("/decision", json={"change_id": cid, "decision": "accept"}).json()
    assert d["provisional"] and d["by"] == "commander"
    todo = client.get("/mission-control/inbox").json()["to_confirm"]
    assert [c["id"] for c in todo] == [cid]
    client.post("/mission-control/confirm", json={"change_id": cid, "confirm": True})
    assert client.get("/mission-control/inbox").json()["to_confirm"] == []


def test_earth_cannot_confirm_without_link():
    client.post("/simulate")
    client.post("/link", json={"online": False})
    _, cid = _first_change()
    client.post("/decision", json={"change_id": cid, "decision": "accept"})
    assert client.post("/mission-control/confirm", json={"change_id": cid, "confirm": True}).status_code == 409


def test_focus_test_changes_factor():
    client.post("/simulate")
    slow = client.post("/focus", json={"crew": "A", "mean_rt_ms": 400}).json()
    assert slow["points"] == 2
    ok = client.post("/focus", json={"crew": "A", "mean_rt_ms": slow["normal_ms"]}).json()
    assert ok["points"] == 0


def test_hidden_fatigue_flag():
    bad_day = {"level": "high", "readiness": 29, "points": {"sleep": 1, "body": 2, "wake": 2, "focus": 2}}
    good_day = {"level": "low", "readiness": 86, "points": {"sleep": 0, "body": 0, "wake": 0, "focus": 0}}
    assert hidden_fatigue({"fatigue": 1, "mood": "good"}, bad_day)["flag"]
    assert not hidden_fatigue({"fatigue": 1, "mood": "good"}, good_day)["flag"]
    assert not hidden_fatigue({"fatigue": 5, "mood": "bad"}, bad_day)["flag"]


def test_nova_flags_fine_when_ring_disagrees():
    client.post("/simulate")
    r = client.post("/nova/answer", json={"crew": "B", "text": "Fine I guess"}).json()
    assert r["hidden_fatigue"]["flag"] and r["nova_note"]


def test_decisions_survive_a_new_forecast():
    client.post("/simulate")
    client.post("/link", json={"place": "mars"})
    _, cid = _first_change()
    client.post("/decision", json={"change_id": cid, "decision": "accept"})
    again = client.get("/forecast/B?use_claude=false").json()
    c = next(x for x in again["changes"] if x["id"] == cid)
    assert c["status"] == "accept" and c["provisional"]


def test_pending_changes_follow_new_mode():
    client.post("/simulate")
    client.get("/forecast/B?use_claude=false")             # ISS: Mission Control approves
    r = client.post("/link", json={"place": "mars"}) and client.get("/forecast/B?use_claude=false").json()
    assert all("commander" in c["approver"] for c in r["changes"])
