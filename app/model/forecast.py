"""Transparent readiness forecast for the next days (no AI, no black box).

Each factor gives 0-2 points; the total gives the level (low/medium/high).
Factors follow the NASA HRP risk of performance errors from sleep loss,
circadian desynchronization and work overload:
  sleep       sleep debt vs own normal over the last 3 nights
  circadian   shift of sleep timing vs own normal
  body        resting HR up / HRV down / skin temp up vs own normal (ring)
  wake        long time awake
  workload    heavy task minutes on that day (from the schedule)
  self_report what the astronaut told NOVA (optional; the ring can't measure mood/stress)
Readiness = 100 - 100 * points / max points.
"""
from app.model.baseline import baseline, deviation

MAX_POINTS = 12


def _level(total: int) -> str:
    return "low" if total <= 3 else ("medium" if total <= 6 else "high")


def _workload_points(tasks: list[dict]) -> int:
    heavy = sum(t["minutes"] for t in tasks if t["load"] == "heavy")
    return 2 if heavy >= 300 else (1 if heavy >= 150 else 0)


def _body_points(dev: dict) -> int:
    signs = sum([dev.get("resting_hr", 0) >= 2, dev.get("hrv_ms", 0) <= -2, dev.get("skin_temp_c", 0) >= 2])
    return min(2, signs)


def forecast(readings: list[dict], schedule: dict, today: int, days_ahead: int = 3,
             self_report: dict | None = None, extra_rest_minutes: dict | None = None) -> dict:
    """readings: one crew's ring days; schedule: {"day": tasks}.
    extra_rest_minutes: {"day": minutes} added by a what-if (assumed to reduce sleep debt)."""
    base = baseline(readings)
    recent = [r for r in sorted(readings, key=lambda r: r["day"]) if today - 2 <= r["day"] <= today]
    if base is None or len(recent) < 2:
        return {"confidence": "low", "unknown": True,
                "message": "Not enough ring data yet, so I don't know.", "days": []}

    last = recent[-1]
    dev = deviation(last, base)
    debt = sum(max(0.0, base["sleep_hours"]["mean"] - r["sleep_hours"]) for r in recent)
    shift = abs(sum(r["sleep_midpoint"] for r in recent) / len(recent) - base["sleep_midpoint"]["mean"])
    extra_rest_minutes = extra_rest_minutes or {}

    pts_now = {
        "circadian": 0 if shift < 1 else (1 if shift < 2 else 2),
        "body": _body_points(dev),
        "wake": 0 if last["hours_awake"] <= 16 else (1 if last["hours_awake"] <= 18 else 2),
    }
    if self_report:
        f, st = self_report.get("fatigue"), self_report.get("stress")
        pts_now["self_report"] = min(2, (2 if f and f >= 4 else 1 if f == 3 else 0) + (1 if st and st >= 4 else 0))

    days, running_debt = [], debt
    for k in range(1, days_ahead + 1):
        day = today + k
        # Stated assumption: extra rest pays back sleep debt hour for hour.
        running_debt = max(0.0, running_debt - extra_rest_minutes.get(str(day), 0) / 60)
        tasks = schedule.get(str(day), [])
        pts = {"sleep": 0 if running_debt < 1.5 else (1 if running_debt < 3 else 2), **pts_now,
               "workload": _workload_points(tasks)}
        total = sum(pts.values())
        critical = [t["name"] for t in tasks if t.get("critical")]
        days.append({
            "day": day, "level": _level(total), "score": total, "max_score": MAX_POINTS,
            "readiness": round(100 - 100 * total / MAX_POINTS), "points": pts,
            "top_factor": max(pts, key=pts.get), "critical_tasks": critical,
            "alert": _level(total) == "high" and bool(critical),
        })

    confidence = "high" if len(recent) == 3 else "medium"
    return {
        "confidence": confidence, "unknown": False, "label": "Simulated",
        "today": {"day": today, "sleep_hours": last["sleep_hours"], "sleep_debt_hours": round(debt, 1),
                  "timing_shift_hours": round(shift, 1), "deviation": dev},
        "baseline": base, "days": days,
    }
