from types import SimpleNamespace

from app.nova.extract import extract, extract_offline
from app.nova.questions import QUESTIONS, next_question


def test_offline_reads_clear_answer():
    r = extract_offline("I slept 5 hours, tired 4, mood not good, stress 3")
    assert r["sleep_hours"] == 5.0
    assert r["fatigue"] == 4
    assert r["mood"] == "bad"
    assert r["stress"] == 3


def test_offline_never_guesses():
    r = extract_offline("I slept a bit")
    assert r["sleep_hours"] is None and r["fatigue"] is None and r["stress"] is None


def test_out_of_range_dropped():
    r = extract_offline("slept 30 hours, tired 9")
    assert r["sleep_hours"] is None and r["fatigue"] is None


def test_next_question_asks_missing_then_follow_up():
    assert next_question({}) == QUESTIONS["sleep_hours"]
    assert "number" in next_question({}, asked_once={"sleep_hours"})
    full = {"sleep_hours": 7, "fatigue": 2, "mood": "good", "stress": 1}
    assert next_question(full) is None


class FakeClient:
    """Pretends to be Claude so tests run without internet or cost."""

    def __init__(self, data):
        self.messages = SimpleNamespace(create=lambda **kw: SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input=data)]))


def test_claude_path_cleans_values():
    fake = FakeClient({"sleep_hours": 6, "fatigue": 7, "mood": "great", "stress": 2, "hedging": True})
    r = extract("whatever", client=fake)
    assert r["source"] == "claude"
    assert r["sleep_hours"] == 6.0 and r["fatigue"] is None and r["mood"] is None and r["stress"] == 2
    assert r["hedging"] is True


def test_falls_back_offline_on_error():
    class Broken:
        messages = SimpleNamespace(create=lambda **kw: (_ for _ in ()).throw(RuntimeError("no net")))
    r = extract("slept 7 hours", client=Broken())
    assert r["source"] == "offline" and r["sleep_hours"] == 7.0


def test_offline_words_without_numbers():
    from app.nova.extract import extract_offline
    r = extract_offline("I slept about 5 hours, I feel really tired and a bit stressed")
    assert r["sleep_hours"] == 5 and r["fatigue"] == 5 and r["stress"] == 3
