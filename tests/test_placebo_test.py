import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from placebo_test import participant_windows, report
from stats import auc


def synthetic_day(effect_bpm, seed=0):
    # 10 days, one meal a day, alternating 08:00 and 14:00 so other days have food-free matches
    rng = np.random.default_rng(seed)
    minutes = pd.date_range("2024-01-01", "2024-01-11", freq="1min", inclusive="left")
    hr = pd.Series(70 + rng.normal(0, 2, len(minutes)), index=minutes)
    meal_times = [pd.Timestamp("2024-01-01") + pd.Timedelta(days=d, hours=8 if d % 2 == 0 else 14) for d in range(10)]
    for t in meal_times:
        hr[t + pd.Timedelta(minutes=10): t + pd.Timedelta(minutes=120)] += effect_bpm
    food = pd.DataFrame({"time": meal_times, "food": "meal", "calories": 500.0, "carbs": 50.0})
    return hr, food


def test_planted_meal_effect_is_found():
    hr, food = synthetic_day(effect_bpm=10)
    table = participant_windows({"hr": (hr, 1)}, food, hr.index.min(), hr.index.max())
    meals, placebos = table[table["kind"] == "meal"], table[table["kind"] == "placebo"]
    assert len(meals) == 10 and len(placebos) >= 20
    assert auc(meals["hr_sustained"], placebos["hr_sustained"]) > 0.95


def test_placebos_stay_inside_covered_times():
    hr, food = synthetic_day(effect_bpm=0)
    table = participant_windows({"hr": (hr, 1)}, food, hr.index.min(), hr.index.max(),
                                covered=lambda times: times.dt.hour < 12)
    placebos = table[table["kind"] == "placebo"]
    assert len(placebos) > 0 and (placebos["time"].dt.hour < 12).all()


def test_report_gives_win_rate_p_and_detectable_difference():
    tables = []
    for i in range(6):
        hr, food = synthetic_day(effect_bpm=10, seed=i)
        tables.append(participant_windows({"hr": (hr, 1)}, food, hr.index.min(), hr.index.max()).assign(pid=f"{i}"))
    result = report(pd.concat(tables, ignore_index=True), {"hr_average": "hr_sustained"})["hr_average"]
    assert result["participants"] == 6 and result["median_auc"] > 0.95
    assert result["wilcoxon_p"] < 0.05 and result["detectable_difference"] > 0


@pytest.mark.skipif(not (ROOT / "data" / "motion").exists(), reason="v1 data not downloaded")
def test_v1_metrics_reproduce_exactly():
    from analyze import all_windows
    from report import build_metrics

    metrics, _ = build_metrics(all_windows())
    saved = json.loads((ROOT / "results" / "metrics.json").read_text())
    saved["exploratory"].pop("seed_range")  # added by run_all.py from extra draws
    assert json.dumps(json.loads(json.dumps(metrics)), sort_keys=True) == json.dumps(saved, sort_keys=True)
