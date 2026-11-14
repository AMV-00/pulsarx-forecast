"""Readiness Digital Twin: a lightweight digital copy of one astronaut.

It joins three simple parts (no black box):
  1) baseline.py  -> who this astronaut normally is (personal baseline)
  2) forecast.py  -> how ready they will be in the coming days, given their tasks
  3) whatif.py    -> try schedule changes on the twin before doing them for real
It is NOT a full model of the human body; it models readiness only.
"""
from app.model.baseline import baseline, deviation
from app.model.forecast import forecast


def _status(z: float) -> str:
    if z >= 2:
        return "well above normal"
    if z <= -2:
        return "well below normal"
    if z >= 1:
        return "above normal"
    if z <= -1:
        return "below normal"
    return "normal"


def build_twin(crew: str, readings: list[dict], schedule: dict, today: int, self_report=None) -> dict:
    base = baseline(readings)
    f = forecast(readings, schedule, today, self_report=self_report)
    if base is None or f["unknown"]:
        return {"crew": crew, "unknown": True, "message": "Not enough ring data yet, so I don't know."}
    latest = max(readings, key=lambda r: r["day"])
    dev = deviation(latest, base)
    now = {m: {"value": latest[m], "normal": base[m]["mean"], "z": z, "status": _status(z)}
           for m, z in dev.items()}
    return {
        "crew": crew,
        "unknown": False,
        "type": "Readiness Digital Twin (lightweight)",
        "now": {"day": latest["day"], "signals": now},
        "personal_baseline": base,
        "forecast": [{"day": d["day"], "readiness": d["readiness"], "level": d["level"],
                      "critical_tasks": d["critical_tasks"], "alert": d["alert"]} for d in f["days"]],
        "try_changes": "Use /forecast to get suggestions, then /whatif to test them on the twin.",
    }
