"""Readers for D1NAMO's healthy group (Dubosson et al. 2018), from the files src/download_v2.py extracts.

The chest strap's summary file has one row per second, with day-first timestamps ("02/10/2014 07:11:17.445").
Food logs mix photographed meals and text-only snacks, and some rows have broken quoting,
so only the date and time fields are trusted.
"""

import csv
import io

import pandas as pd

from load import DATA_DIR

SENSOR_DIR = DATA_DIR / "d1namo" / "healthy_subset_sensor_data"
LOG_DIR = DATA_DIR / "d1namo" / "healthy_subset_pictures-glucose-food"
# folder 012 is labeled "012_diabetes" and reaches 19.7 mmol/L (see ANALYSIS_PLAN_v2.md)
PARTICIPANTS = [f"{i:03d}" for i in range(1, 21) if i != 12]
MIN_CONFIDENCE = 80
MIN_SECONDS = 40  # 2/3 of a minute
SUMMARY_COLUMNS = ["Time", "HR", "BR", "Activity", "HRConfidence", "BRConfidence"]


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def load_summary(pid, sensor_dir=SENSOR_DIR):
    paths = sorted((sensor_dir / pid).glob("sensor_data/*/*_Summary.csv"))
    summary = pd.concat([pd.read_csv(p, usecols=SUMMARY_COLUMNS) for p in paths], ignore_index=True)
    summary["Time"] = pd.to_datetime(summary["Time"], format="%d/%m/%Y %H:%M:%S.%f")
    return summary.set_index("Time").sort_index()


def per_minute(values, valid, min_seconds=MIN_SECONDS):
    kept = values[valid]
    groups = kept.groupby(kept.index.floor("min"))
    means = groups.mean()
    return means[groups.size() >= min_seconds].rename_axis("time")


def problem_periods(pid, log_dir=LOG_DIR):
    text = read_text(log_dir / pid / "annotations.csv")
    rows = [r for r in csv.DictReader(io.StringIO(text)) if r["type"] == "problem"]
    return [(pd.Timestamp(f"{r['start_date']} {r['start_time']}"), pd.Timestamp(f"{r['end_date']} {r['end_time']}"))
            for r in rows]


def load_signals(pid, sensor_dir=SENSOR_DIR, log_dir=LOG_DIR):
    """Per-minute heart rate, breathing rate and activity, with flagged strap problems removed."""
    s = load_summary(pid, sensor_dir)
    for start, end in problem_periods(pid, log_dir):
        s = s[(s.index < start) | (s.index > end)]
    hr = per_minute(s["HR"], (s["HRConfidence"] >= MIN_CONFIDENCE) & s["HR"].between(30, 220))
    br = per_minute(s["BR"], (s["BRConfidence"] >= MIN_CONFIDENCE) & s["BR"].between(4, 60))
    activity = per_minute(s["Activity"], s["Activity"].notna())
    return hr.rename("hr"), br.rename("br"), activity.rename("activity")


def load_food(pid, log_dir=LOG_DIR):
    text = read_text(log_dir / pid / "food.csv")
    rows = list(csv.reader(io.StringIO(text)))[1:]
    times = pd.to_datetime([f"{r[0]} {r[1]}" if len(r) > 1 else "" for r in rows], errors="coerce")
    food = pd.DataFrame({
        "time": times,
        "food": [r[3] if len(r) > 3 else "" for r in rows],
        "calories": float("nan"),
        "carbs": float("nan"),
    })
    return food.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)


def load_fingerpricks(pid, log_dir=LOG_DIR):
    """Finger-prick glucose (mmol/L) labeled BB/AB, BL/AL, BD/AD: before and after breakfast, lunch and dinner."""
    text = read_text(log_dir / pid / "glucose.csv")
    df = pd.read_csv(io.StringIO(text), dtype=str)
    return pd.DataFrame({
        "time": pd.to_datetime(df["date"] + " " + df["time"], errors="coerce"),
        "glucose": pd.to_numeric(df["glucose"], errors="coerce"),
        "type": df["type"].str.strip(),
    }).dropna(subset=["time", "glucose"])
