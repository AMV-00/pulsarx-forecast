"""Build data/real/fitbit_daily.csv from the public Fitbit dataset.

Source: Furberg, Brinton, Keating, Ortiz (2016). Crowd-sourced Fitbit datasets
03.12.2016-05.12.2016. Zenodo, record 53894 (also on Kaggle as "FitBit Fitness Tracker Data").
30 consenting Fitbit users shared minute-level sleep, activity and heart rate.

Put sleepDay_merged.csv, dailyActivity_merged.csv and heartrate_seconds_merged.csv
in one folder and run:  python scripts/build_real_data.py <folder>

We keep 14 real days for 3 users and call them crew A, B, C (ids are dropped).
Resting heart rate = 5th percentile of that day's heart rate readings.
Active minutes = very active + fairly active minutes.
Hours awake = 24 - time in bed.
"""
import sys
from pathlib import Path

import pandas as pd

# user id -> (crew, first row of the 14-day window, rows sorted by date)
PICK = {5577150313: ("A", 2), 6962181067: ("B", 12), 5553957443: ("C", 1)}


def main(folder: str) -> None:
    f = Path(folder)
    s = pd.read_csv(f / "sleepDay_merged.csv")
    a = pd.read_csv(f / "dailyActivity_merged.csv")
    hr = pd.read_csv(f / "heartrate_seconds_merged.csv")
    s["date"] = pd.to_datetime(s.SleepDay, format="%m/%d/%Y %I:%M:%S %p").dt.date
    a["date"] = pd.to_datetime(a.ActivityDate, format="%m/%d/%Y").dt.date
    hr["date"] = pd.to_datetime(hr.Time, format="%m/%d/%Y %I:%M:%S %p").dt.date
    g = hr.groupby(["Id", "date"]).Value
    h = pd.DataFrame({"rhr": g.quantile(0.05), "n": g.size()}).reset_index()
    m = s.merge(a, on=["Id", "date"]).merge(h, on=["Id", "date"])
    m = m[m.n > 5000].sort_values(["Id", "date"])
    rows = []
    for uid, (crew, start) in PICK.items():
        u = m[m.Id == uid].iloc[start:start + 14]
        for day, (_, r) in enumerate(u.iterrows(), 1):
            rows.append({"crew": crew, "day": day, "date": r.date,
                         "sleep_hours": round(r.TotalMinutesAsleep / 60, 1),
                         "hours_awake": round(24 - r.TotalTimeInBed / 60, 1),
                         "resting_hr": round(r.rhr),
                         "active_minutes": int(r.VeryActiveMinutes + r.FairlyActiveMinutes)})
    out = Path(__file__).resolve().parent.parent / "data" / "real" / "fitbit_daily.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out, len(rows), "rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
