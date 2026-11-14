"""What-if: apply one suggested change to a copy of the schedule and rerun the
same transparent forecast, so every 'expected effect' number comes from the model."""
from copy import deepcopy

from app.model.forecast import forecast


def apply_change(schedule: dict, change: dict, day: int) -> tuple[dict, dict]:
    """Return (new_schedule, extra_rest_minutes) after one change. Input is not modified."""
    sch, extra = deepcopy(schedule), {}
    d = str(day)
    if change["type"] == "longer_rest":
        extra[d] = change["extra_minutes"]
        for t in sch.get(d, []):
            if t["id"] == change["task_id"]:
                t["minutes"] += change["extra_minutes"]
    elif change["type"] in ("postpone", "reassign"):
        moved = [t for t in sch.get(d, []) if t["id"] == change["task_id"]]
        sch[d] = [t for t in sch.get(d, []) if t["id"] != change["task_id"]]
        if change["type"] == "postpone" and moved:
            sch.setdefault(str(day + 1), []).append(moved[0])
    # reorder: same tasks that day, so the model gives no change (stated honestly).
    return sch, extra


def readiness_on(readings, schedule, today, day, extra=None, self_report=None) -> int | None:
    f = forecast(readings, schedule, today, self_report=self_report, extra_rest_minutes=extra)
    return next((x["readiness"] for x in f["days"] if x["day"] == day), None)


def what_if(readings, schedule, today, day, changes, self_report=None) -> dict:
    """Readiness on `day` before and after applying all `changes` together."""
    before = readiness_on(readings, schedule, today, day, self_report=self_report)
    sch, extra = schedule, {}
    for c in changes:
        sch, e = apply_change(sch, c, day)
        extra.update({k: extra.get(k, 0) + v for k, v in e.items()})
    after = readiness_on(readings, sch, today, day, extra, self_report)
    return {"day": day, "readiness_before": before, "readiness_after": after}
