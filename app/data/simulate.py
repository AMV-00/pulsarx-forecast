"""Simulated crew data for the demo. Everything here is labeled "Simulated".

Same seed -> same data, so the demo and the video always look the same.
"""
import random

LABEL = "Simulated"
CREW = ["A", "B", "C"]

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


def generate_schedule(crew: str, seed: int = 1, day_start: int = 8 * 60) -> list[dict]:
    """One work day: tasks in a row with one rest block at midday."""
    rng = random.Random(f"{seed}-{crew}")
    picks = rng.sample(TASK_POOL, 4)
    tasks, t = [], day_start
    for i, (name, minutes, load, critical) in enumerate(picks):
        if i == 2:
            tasks.append({"id": f"{crew}-rest", "name": "Rest", "start": _hhmm(t), "minutes": 60,
                          "load": "rest", "critical": False, "crew": crew, "label": LABEL})
            t += 60
        tasks.append({"id": f"{crew}-t{i + 1}", "name": name, "start": _hhmm(t), "minutes": minutes,
                      "load": load, "critical": critical, "crew": crew, "label": LABEL})
        t += minutes
    return tasks


def generate_states(days: int = 7, seed: int = 1) -> list[dict]:
    """Daily astronaut states with ranges taken from the NASA sleep report idea
    (average ~6 h sleep on orbit vs 8 h recommended). Values are simulated."""
    rng = random.Random(seed)
    out = []
    for crew in CREW:
        for d in range(1, days + 1):
            out.append({
                "crew": crew, "day": d, "label": LABEL,
                "sleep_hours": round(rng.uniform(4.5, 8.0), 1),
                "circadian_regularity": rng.randint(50, 100),   # % regular sleep/wake
                "workload_tasks": rng.randint(3, 7),
                "hours_awake": round(rng.uniform(12, 20), 1),
                "cognitive": rng.randint(55, 100),              # % focus test
            })
    return out


def free_minutes(schedules: dict[str, list[dict]], day_minutes: int = 10 * 60) -> dict[str, int]:
    """How much free time each crew member has in a work day."""
    return {c: max(0, day_minutes - sum(t["minutes"] for t in tasks)) for c, tasks in schedules.items()}
