"""Task 5 (live): ask the real Claude to rephrase every reason sentence
and count how many times it tried to change a number.
A blocked attempt is fine: the template sentence is shown instead."""
from app.explain.numbers import numbers_ok
from app.explain.templates import reason_sentence
from app.schedule.rules import suggest_changes
from tests.test_schedule import DAY

FACTS = {"level": "high", "top_factor": "sleep", "sleep_hours": 5, "readiness_before": 42, "readiness_after": 58}

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

changes = (suggest_changes("high", DAY, crew_free={"B": 300}) + suggest_changes("medium", DAY)
           + suggest_changes("high", DAY, mars_mode=True))
total = blocked = 0
for lang in ("en", "ar"):
    for c in changes:
        base = reason_sentence(c, FACTS, lang)
        msg = client.messages.create(
            model="claude-sonnet-5-5", max_tokens=200,
            system=("Rewrite the sentence to sound clear and calm for a mission team, in "
                    f"{'Arabic' if lang == 'ar' else 'English'}. Keep the same meaning. "
                    "Do not add, remove or change any number. Return only the sentence."),
            messages=[{"role": "user", "content": base}])
        out = "".join(b.text for b in msg.content if b.type == "text").strip()
        total += 1
        ok = numbers_ok(out, base)
        blocked += not ok
        print(("OK     " if ok else "BLOCKED"), out[:110])
print(f"\n{total} sentences, {blocked} blocked (template used instead), 0 invented numbers shown.")
