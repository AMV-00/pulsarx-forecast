"""The model runs on real Fitbit days only and reacts to real short sleep."""
from scripts.real_data_test import run


def test_real_days_run_and_short_sleep_lowers_readiness():
    res = run()
    assert len(res["rows"]) >= 20
    assert all(0 <= r["readiness"] <= 100 for r in res["rows"])
    assert res["short"] and res["other"]
    assert res["avg_short"] < res["avg_other"]
