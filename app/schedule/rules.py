"""Task 2: suggest schedule changes from the fatigue risk level.

Plain, transparent rules (no AI here). Every change is only a suggestion:
the ground team (or the commander in Mars mode) accepts, edits or rejects it.

Input task example:
  {"id": "t1", "name": "EVA prep", "start": "09:00", "minutes": 120,
   "load": "heavy" | "light" | "rest", "critical": False, "crew": "A"}
"""
from copy import deepcopy

EXTRA_REST = {"medium": 30, "high": 60}   # minutes added to the next rest block


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _hhmm(total: int) -> str:
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def _free_crew(task, crew_free: dict) -> str | None:
    """Another crew member with a free slot long enough for this task."""
    for crew, free_minutes in crew_free.items():
        if crew != task.get("crew") and free_minutes >= task["minutes"]:
            return crew
    return None


def suggest_changes(level: str, tasks: list[dict], crew_free: dict | None = None,
                    mars_mode: bool = False) -> list[dict]:
    """Return a list of suggested changes. Never edits the input list."""
    crew_free = dict(crew_free or {})
    tasks = sorted(deepcopy(tasks), key=lambda t: _minutes(t["start"]))
    changes: list[dict] = []
    if level not in ("medium", "high"):
        return changes

    approver = "commander (temporary, until Mission Control confirms)" if mars_mode else "Mission Control"

    # 1) Longer rest: extend the first rest block.
    rest = next((t for t in tasks if t["load"] == "rest"), None)
    if rest:
        changes.append({"type": "longer_rest", "task_id": rest["id"], "task": rest["name"],
                        "extra_minutes": EXTRA_REST[level], "approver": approver})

    heavy = [t for t in tasks if t["load"] == "heavy"]

    if level == "medium":
        # 2) Reorder: move heavy tasks that come before the rest to just after it.
        if rest:
            after_rest = _minutes(rest["start"]) + rest["minutes"] + EXTRA_REST[level]
            for t in heavy:
                if _minutes(t["start"]) < _minutes(rest["start"]) and not t.get("critical"):
                    changes.append({"type": "reorder", "task_id": t["id"], "task": t["name"],
                                    "from": t["start"], "to": _hhmm(after_rest), "approver": approver})
                    after_rest += t["minutes"]
        return changes

    # level == "high"
    for t in heavy:
        other = _free_crew(t, crew_free)
        if t.get("critical"):
            if other:
                changes.append({"type": "reassign", "task_id": t["id"], "task": t["name"],
                                "from_crew": t.get("crew"), "to_crew": other, "approver": approver})
                crew_free[other] -= t["minutes"]
            # critical with nobody free: keep it, the ground team decides.
            continue
        if other:
            changes.append({"type": "reassign", "task_id": t["id"], "task": t["name"],
                            "from_crew": t.get("crew"), "to_crew": other, "approver": approver})
            crew_free[other] -= t["minutes"]
        else:
            changes.append({"type": "postpone", "task_id": t["id"], "task": t["name"],
                            "from": t["start"], "to": "next day", "approver": approver})
    return changes
