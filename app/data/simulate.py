"""Simulated FORECAST Smart Ring + mission schedule. Everything is labeled "Simulated".

The ring stands for a wearable that records sleep, heart rate, HRV, skin
temperature and activity on its own, so the astronaut types nothing.
Same seed -> same data, so the demo and video always look the same.
"""
import csv
import random
from pathlib import Path

LABEL = "Simulated"
REAL_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "real" / "fitbit_daily.csv"
REAL_SOURCE = "Fitbit, 30 real users (Furberg et al. 2016, Zenodo 53894)"
REAL_FIELDS = ("sleep_hours", "hours_awake", "resting_hr", "active_minutes")
CREW = ["A", "B", "C"]
DAYS = 14          # days of ring history ("today" = day 14)
FORECAST_DAYS = 3  # days we look ahead

# Each astronaut has their own normal (personal baseline).
PERSONAL = {
    "A": {"sleep": 7.2, "mid": 3.0, "hr": 58, "hrv": 62, "temp": 33.8, "active": 70},
    "B": {"sleep": 6.8, "mid": 3.5, "hr": 64, "hrv": 48, "temp": 34.1, "active": 55},
    "C": {"sleep": 7.8, "mid": 2.5, "hr": 61, "hrv": 55, "temp": 33.6, "active": 80},
}

TASK_POOL = [
    ("EVA prep", 120, "heavy", False),
    ("Robotic arm ops", 90, "heavy", True),
    ("Science experiment", 90, "heavy", False),
    ("Exercise", 60, "light", False),
    ("Inventory", 60, "light", False),
    ("Maintenance check", 60, "light", True),
    ("Ground call", 30, "light", False),
]


def _hhmm(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def load_real() -> dict:
    """{(crew, day): row} from data/real/fitbit_daily.csv, or {} if the file is missing."""
    if not REAL_FILE.is_file():
        return {}
    with REAL_FILE.open(newline="") as f:
        return {(r["crew"], int(r["day"])): r for r in csv.DictReader(f)}


def generate_ring(days: int = DAYS, seed: int = 1, real: bool = True) -> list[dict]:
    """Daily ring readings. When data/real/fitbit_daily.csv exists, sleep, hours awake,
    resting heart rate and activity are REAL Fitbit values; HRV, skin temperature and
    sleep midpoint stay simulated (that dataset has none)."""
    out = _simulated_ring(days, seed)
    rows = load_real() if real else {}
    for r in out:
        x = rows.get((r["crew"], r["day"]))
        if x:
            for k in REAL_FIELDS:
                r[k] = float(x[k]) if "." in x[k] else int(x[k])
            r["label"] = "Real + simulated"
            r["source"] = REAL_SOURCE
            r["real_fields"] = list(REAL_FIELDS)
            r["real_date"] = x["date"]
    return out


def _simulated_ring(days: int = DAYS, seed: int = 1) -> list[dict]:
    """Daily ring readings. Demo story: crew B slowly loses sleep in the last
    4 days; A and C stay near their own normal."""
    rng = random.Random(seed)
    out = []
    for crew in CREW:
        p = PERSONAL[crew]
        for d in range(1, days + 1):
            drift = (d - (days - 4)) if crew == "B" and d > days - 4 else 0
            sleep = max(3.5, p["sleep"] + rng.gauss(0, 0.3) - 0.3 * drift)
            out.append({
                "crew": crew, "day": d, "label": LABEL, "source": "FORECAST Smart Ring (simulated)",
                "sleep_hours": round(sleep, 1),
                "sleep_midpoint": round(p["mid"] + rng.gauss(0, 0.3) + 0.4 * drift, 1),  # hour of the night
                "resting_hr": round(p["hr"] + rng.gauss(0, 1.2) + 1.8 * drift),
                "hrv_ms": round(p["hrv"] + rng.gauss(0, 3) - 4 * drift),
                "skin_temp_c": round(p["temp"] + rng.gauss(0, 0.1) + 0.12 * drift, 2),
                "active_minutes": round(p["active"] + rng.gauss(0, 6) - 6 * drift),
                "hours_awake": round(24 - sleep - 1.5 + rng.gauss(0, 0.4) + 0.3 * drift, 1),
            })
    return out


def generate_schedule(crew: str, day: int, seed: int = 1, day_start: int = 8 * 60) -> list[dict]:
    """One work day: four tasks with one rest block at midday."""
    rng = random.Random(f"{seed}-{crew}-{day}")
    picks = rng.sample(TASK_POOL, 4)
    if crew == "B" and day == DAYS + 2:  # demo story: critical EVA two days ahead
        picks[0] = ("EVA (critical)", 180, "heavy", True)
    tasks, t = [], day_start
    for i, (name, minutes, load, critical) in enumerate(picks):
        if i == 2:
            tasks.append({"id": f"{crew}-d{day}-rest", "name": "Rest", "start": _hhmm(t), "minutes": 60,
                          "load": "rest", "critical": False, "crew": crew, "day": day, "label": LABEL})
            t += 60
        tasks.append({"id": f"{crew}-d{day}-t{i + 1}", "name": name, "start": _hhmm(t), "minutes": minutes,
                      "load": load, "critical": critical, "crew": crew, "day": day, "label": LABEL})
        t += minutes
    return tasks


def generate_schedules(seed: int = 1) -> dict:
    """{crew: {"day": [tasks]}} for history + forecast days."""
    return {c: {str(d): generate_schedule(c, d, seed) for d in range(1, DAYS + FORECAST_DAYS + 1)} for c in CREW}


def free_minutes(day_tasks: dict[str, list[dict]], day_minutes: int = 10 * 60) -> dict[str, int]:
    """Free time per crew member on one day."""
    return {c: max(0, day_minutes - sum(t["minutes"] for t in tasks)) for c, tasks in day_tasks.items()}
