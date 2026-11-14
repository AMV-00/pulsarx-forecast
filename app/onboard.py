"""Works onboard without Earth: an outbox that syncs to Mission Control when the link returns,
Mars mode when Earth is too far or offline, and a check for hidden fatigue.

Everything is stored as JSON in data/ so it keeps working with no internet.
"""
from datetime import datetime, timezone

from app.data import store

# One-way light delay to Earth (minutes). Moon about 1.3 s; Mars 4 to 24 min.
PLACES = {"iss": 0.0, "moon": 0.02, "mars": 12.0}
MARS_DELAY_MIN = 5.0  # above this, waiting for Earth before acting is too slow


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- link to Earth ----------
def link() -> dict:
    return store.load("link", {"online": True, "place": "iss", "delay_min": 0.0, "last_sync": None})


def set_link(online: bool | None = None, place: str | None = None) -> dict:
    s = link()
    if online is not None:
        s["online"] = online
    if place in PLACES:
        s["place"], s["delay_min"] = place, PLACES[place]
    store.save("link", s)
    return s


def mars_mode() -> bool:
    """Crew must decide onboard: no link, or Earth's answer would come too late."""
    s = link()
    return (not s["online"]) or s["delay_min"] >= MARS_DELAY_MIN


# ---------- outbox -> Mission Control ----------
def queue(kind: str, data: dict) -> dict:
    """Everything Mission Control should see goes here first (works offline)."""
    items = store.load("outbox", [])
    item = {"id": f"m{len(items) + 1}", "kind": kind, "data": data, "made": _now(), "synced": None}
    items.append(item)
    store.save("outbox", items)
    return item


def outbox() -> list[dict]:
    return store.load("outbox", [])


def sync() -> dict:
    """Send every waiting item if the link is up. Returns what was sent."""
    s = link()
    if not s["online"]:
        return {"sent": 0, "waiting": sum(1 for i in outbox() if not i["synced"]), "online": False}
    items, sent = outbox(), 0
    for i in items:
        if not i["synced"]:
            i["synced"] = _now()
            sent += 1
    store.save("outbox", items)
    s["last_sync"] = _now()
    store.save("link", s)
    return {"sent": sent, "waiting": 0, "online": True, "delay_min": s["delay_min"]}


# ---------- hidden fatigue ----------
def hidden_fatigue(answers: dict, day: dict | None) -> dict:
    """Flag when what the astronaut says looks better than what the ring shows.
    Text only; it never changes the score, a human reviews it."""
    if not day:
        return {"flag": False, "why": []}
    says_fine = (answers.get("fatigue") is not None and answers["fatigue"] <= 2) \
        or answers.get("mood") == "good" or answers.get("hedging")
    pts = day.get("points", {})
    ring_worry = [k for k in ("sleep", "body", "wake", "focus") if pts.get(k, 0) >= 2]
    flag = bool(says_fine and (day.get("level") == "high" or len(ring_worry) >= 2))
    why = []
    if flag:
        said = "fine" if answers.get("hedging") else ("not tired" if answers.get("fatigue") else "good mood")
        why = [f"Said: {said}", f"Ring and model: {day['level']} risk, readiness {day['readiness']}%",
               "Signals off normal: " + (", ".join(ring_worry) or "none")]
    return {"flag": flag, "why": why}
