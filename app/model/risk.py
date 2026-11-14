"""PLACEHOLDER transparent risk model, so the demo runs end to end.
The model owner can replace `predict` with the real one: keep the same output keys.

Five factors from NASA HRP (sleep loss, circadian, workload, time awake, cognition).
Each factor (plus NOVA self-report) gives 0-2 points; the total decides the level. No AI here.
"""

def _points(state: dict) -> dict:
    p = {}
    s = state.get("sleep_hours")
    p["sleep"] = 0 if s is None or s >= 7 else (1 if s >= 6 else 2)
    c = state.get("circadian_regularity")
    p["circadian"] = 0 if c is None or c >= 85 else (1 if c >= 70 else 2)
    w = state.get("workload_tasks")
    p["workload"] = 0 if w is None or w <= 4 else (1 if w <= 6 else 2)
    a = state.get("hours_awake")
    p["wake"] = 0 if a is None or a <= 16 else (1 if a <= 18 else 2)
    g = state.get("cognitive")
    p["cognitive"] = 0 if g is None or g >= 80 else (1 if g >= 65 else 2)
    # what the astronaut told NOVA (fatigue 1-5, stress 1-5)
    f, st = state.get("fatigue"), state.get("stress")
    self_pts = (2 if f is not None and f >= 4 else 1 if f == 3 else 0) + (1 if st is not None and st >= 4 else 0)
    p["self_report"] = min(2, self_pts)
    return p


def predict(state: dict) -> dict:
    pts = _points(state)
    total = sum(pts.values())
    level = "low" if total <= 2 else ("medium" if total <= 5 else "high")
    top = max(pts, key=pts.get) if total else "workload"
    return {"level": level, "score": total, "max_score": 12, "points": pts,
            "top_factor": top, "sleep_hours": state.get("sleep_hours")}
