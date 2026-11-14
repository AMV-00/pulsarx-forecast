"""Personal baseline: compare each astronaut to their OWN normal, not a general average.
Simple statistics only (mean and spread of the first days)."""
from statistics import mean, pstdev

METRICS = ("sleep_hours", "sleep_midpoint", "resting_hr", "hrv_ms", "skin_temp_c", "active_minutes", "hours_awake", "focus_rt_ms")
BASELINE_DAYS = 7
MIN_SD = {"sleep_hours": 0.2, "sleep_midpoint": 0.2, "resting_hr": 1.0, "hrv_ms": 2.0,
          "skin_temp_c": 0.05, "active_minutes": 3.0, "hours_awake": 0.3, "focus_rt_ms": 5.0}


def baseline(readings: list[dict], days: int = BASELINE_DAYS) -> dict | None:
    """Mean and spread per metric from the first `days` days. None if not enough data."""
    first = sorted(readings, key=lambda r: r["day"])[:days]
    if len(first) < days:
        return None
    out = {}
    for m in METRICS:
        vals = [r[m] for r in first if r.get(m) is not None]
        if not vals:  # older data without this signal (e.g. before the focus test existed)
            continue
        out[m] = {"mean": round(mean(vals), 2), "sd": round(max(pstdev(vals), MIN_SD[m]), 2)}
    return out


def deviation(reading: dict, base: dict) -> dict:
    """How far a day is from the personal normal, in standard deviations (z)."""
    return {m: round((reading[m] - base[m]["mean"]) / base[m]["sd"], 1)
            for m in METRICS if reading.get(m) is not None and m in base}
