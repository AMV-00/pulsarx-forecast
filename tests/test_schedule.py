from app.schedule.rules import suggest_changes

DAY = [
    {"id": "t1", "name": "EVA prep", "start": "09:00", "minutes": 120, "load": "heavy", "critical": False, "crew": "A"},
    {"id": "t2", "name": "Rest", "start": "12:00", "minutes": 60, "load": "rest", "crew": "A"},
    {"id": "t3", "name": "Robotic arm", "start": "14:00", "minutes": 90, "load": "heavy", "critical": True, "crew": "A"},
    {"id": "t4", "name": "Inventory", "start": "16:00", "minutes": 60, "load": "light", "crew": "A"},
]


def types(changes):
    return [c["type"] for c in changes]


def test_low_risk_no_changes():
    assert suggest_changes("low", DAY) == []


def test_medium_adds_rest_and_reorders_heavy():
    ch = suggest_changes("medium", DAY)
    assert types(ch) == ["longer_rest", "reorder"]
    assert ch[0]["extra_minutes"] == 30
    assert ch[1]["task_id"] == "t1" and ch[1]["to"] == "13:30"


def test_high_postpones_and_keeps_critical_when_nobody_free():
    ch = suggest_changes("high", DAY)
    assert types(ch) == ["longer_rest", "postpone"]
    assert ch[1]["task_id"] == "t1"


def test_high_reassigns_when_crew_free():
    ch = suggest_changes("high", DAY, crew_free={"B": 300})
    assert types(ch) == ["longer_rest", "reassign", "reassign"]
    assert all(c["to_crew"] == "B" for c in ch[1:])


def test_reassign_respects_free_time():
    ch = suggest_changes("high", DAY, crew_free={"B": 100})
    # B can take the 90 min critical task, not the 120 min one.
    assert {"type": "postpone", "task_id": "t1"}.items() <= ch[1].items()
    assert ch[2]["type"] == "reassign" and ch[2]["task_id"] == "t3"


def test_mars_mode_commander_approves():
    ch = suggest_changes("high", DAY, mars_mode=True)
    assert all(c["approver"].startswith("commander") for c in ch)


def test_input_not_modified():
    before = [dict(t) for t in DAY]
    suggest_changes("high", DAY, crew_free={"B": 500})
    assert DAY == before
