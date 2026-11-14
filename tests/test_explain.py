from types import SimpleNamespace

from app.explain.numbers import numbers_ok
from app.explain.templates import polish, reason_sentence
from app.schedule.rules import suggest_changes
from tests.test_schedule import DAY

FACTS = {"level": "high", "top_factor": "sleep", "sleep_hours": 5, "risk_before": 0.72, "risk_after": 0.55}


def all_sentences(lang):
    changes = suggest_changes("high", DAY, crew_free={"B": 300}) + suggest_changes("medium", DAY) \
        + suggest_changes("high", DAY)
    return [(reason_sentence(c, FACTS, lang), c) for c in changes]


def test_every_change_type_has_sentence_in_both_languages():
    for lang in ("en", "ar"):
        kinds = {c["type"] for _, c in all_sentences(lang)}
        assert kinds == {"longer_rest", "reorder", "postpone", "reassign"}


def test_template_numbers_only_from_model_and_rules():
    for lang in ("en", "ar"):
        for s, c in all_sentences(lang):
            allowed = {"5", "0.72", "0.55"} | {str(v) for v in c.values()}
            assert numbers_ok(s, allowed), s


def test_no_model_effect_when_model_gives_none():
    s = reason_sentence({"type": "postpone", "task": "EVA", "approver": "ground"},
                        {"level": "high", "top_factor": "workload"})
    assert "estimate" not in s and numbers_ok(s, set())


def fake(reply):
    return SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(content=[SimpleNamespace(text=reply)])))


def test_polish_rejects_invented_number():
    base = "Postpone EVA to the next day. Fatigue risk is high (5 hours of sleep)."
    assert polish(base, client=fake("Postpone EVA; risk is 80% higher after 5 hours of sleep.")) == base


def test_polish_accepts_same_numbers():
    base = "Postpone EVA to the next day. Fatigue risk is high (5 hours of sleep)."
    better = "Let's move EVA to tomorrow: with only 5 hours of sleep, fatigue risk is high."
    assert polish(base, client=fake(better)) == better


def test_polish_offline_returns_template():
    class Broken:
        messages = SimpleNamespace(create=lambda **kw: (_ for _ in ()).throw(OSError()))
    assert polish("Rest 30 minutes.", client=Broken()) == "Rest 30 minutes."


def test_numbers_ok_handles_arabic_digits():
    assert not numbers_ok("نام ٤ ساعات", {"5"})
    assert numbers_ok("نام ٥ ساعات", {"5"})
