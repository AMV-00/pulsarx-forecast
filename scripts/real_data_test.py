"""Run the transparent model on REAL Fitbit days only (no simulated signals, no schedule).

For each real user and each day after the 7-day personal baseline, the model predicts
readiness for that day using only the days before it (no peeking). Then we check:
  1) it runs on every real day without errors,
  2) after nights well below the person's own sleep normal, predicted readiness is lower,
  3) every point can be traced to a real measured value.
Limit: the Fitbit data has no fatigue labels, so this checks behaviour, not accuracy.
True accuracy needs spaceflight data (next step: NASA OSDR).
Writes docs/real-data-test.md.  Run:  python scripts/real_data_test.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.model.baseline import baseline  # noqa: E402
from app.model.forecast import forecast  # noqa: E402

REAL = ROOT / "data" / "real" / "fitbit_daily.csv"
FIELDS = ("sleep_hours", "hours_awake", "resting_hr", "active_minutes")


def load() -> dict:
    out = {}
    with REAL.open(newline="") as f:
        for r in csv.DictReader(f):
            row = {"day": int(r["day"]), "date": r["date"], "sleep_midpoint": 3.0}  # timing not in dataset: held fixed
            for k in FIELDS:
                row[k] = float(r[k])
            out.setdefault(r["crew"], []).append(row)
    return out


def run() -> dict:
    users, rows = load(), []
    for crew, days in users.items():
        for d in range(8, max(r["day"] for r in days) + 1):
            past = [r for r in days if r["day"] <= d - 1]
            f = forecast(past, {}, d - 1, days_ahead=1)
            base = baseline(past)
            x = f["days"][0]
            debt = f["today"]["sleep_debt_hours"]
            rows.append({"crew": crew, "day": d, "date": next(r["date"] for r in days if r["day"] == d),
                         "sleep_prev": past[-1]["sleep_hours"], "normal": base["sleep_hours"]["mean"],
                         "debt": debt, "readiness": x["readiness"], "level": x["level"],
                         "points": x["points"]})
    short = [r["readiness"] for r in rows if r["debt"] >= 1.5]
    other = [r["readiness"] for r in rows if r["debt"] < 1.5]
    avg = lambda v: round(sum(v) / len(v), 1) if v else None  # noqa: E731
    return {"rows": rows, "short": short, "other": other, "avg_short": avg(short), "avg_other": avg(other)}


def report(res: dict) -> str:
    L = ["# Real-data test", "",
         "The transparent model was run on **real Fitbit days only** (3 real users, Furberg et al. 2016, Zenodo 53894).",
         "No simulated signal and no task schedule were used. For each day after the 7-day personal baseline,",
         "the model predicted readiness using only the days before it.", "",
         "| Check | Result |", "| --- | --- |",
         f"| Real days predicted | {len(res['rows'])} (all ran without errors) |",
         f"| Average readiness after short sleep (3-night sleep debt of 1.5 h or more vs own normal) | {res['avg_short']}% ({len(res['short'])} days) |",
         f"| Average readiness on other days | {res['avg_other']}% ({len(res['other'])} days) |", "",
         "**Limit:** this dataset has no fatigue labels, so the test checks that the model behaves as designed on real",
         "human data, not how accurate it is. Accuracy needs spaceflight data with fatigue or performance measures",
         "(next step: NASA Open Science Data Repository).", "",
         "| User | Day | Date | Sleep night before (h) | Own normal (h) | 3-night sleep debt (h) | Readiness | Level | Points |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res["rows"]:
        pts = ", ".join(f"{k} {v}" for k, v in r["points"].items() if v)
        L.append(f"| {r['crew']} | {r['day']} | {r['date']} | {r['sleep_prev']} | {r['normal']} | {r['debt']} | {r['readiness']}% | {r['level']} | {pts or 'none'} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    res = run()
    (ROOT / "docs" / "real-data-test.md").write_text(report(res), encoding="utf-8")
    print(f"{len(res['rows'])} real days | short sleep avg {res['avg_short']}% ({len(res['short'])}) | other avg {res['avg_other']}% ({len(res['other'])})")
