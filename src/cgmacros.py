"""Readers for CGMacros (PhysioNet v1.0.0), from the CSVs src/download_v2.py extracts.

Column names vary between participants: some files have METs, others Intensity, some an unnamed index
column, and some names carry trailing spaces. Glucose readings are spread over every minute.
"""

import pandas as pd

from load import DATA_DIR

ROOT = DATA_DIR / "cgmacros" / "CGMacros"
MAX_A1C = 6.5  # main sample: no diabetes or prediabetes (see ANALYSIS_PLAN_v2.md)


def participants(everyone=False, root=ROOT):
    bio = pd.read_csv(root / "bio.csv")
    keep = bio if everyone else bio[bio["A1c PDL (Lab)"] < MAX_A1C]
    return [f"{s:03d}" for s in keep["subject"] if (root / f"CGMacros-{s:03d}").exists()]


def load(pid, root=ROOT):
    """Per-minute heart rate and METs (empty if the file has none), 5-minute Dexcom glucose, and meal records."""
    d = pd.read_csv(root / f"CGMacros-{pid}" / f"CGMacros-{pid}.csv")
    d.columns = d.columns.str.strip()
    d.index = pd.DatetimeIndex(pd.to_datetime(d["Timestamp"]), name="time")
    hr = d["HR"].dropna().rename("hr")
    mets = (d["METs"] / 10 if "METs" in d else pd.Series(dtype=float)).dropna().rename("mets")
    glucose = d["Dexcom GL"].dropna().resample("5min").mean().dropna().rename("glucose")
    meals = d[d["Meal Type"].notna()]
    food = pd.DataFrame({
        "time": meals.index,
        "food": meals["Meal Type"].to_numpy(),
        "calories": pd.to_numeric(meals["Calories"], errors="coerce").to_numpy(),
        "carbs": pd.to_numeric(meals["Carbs"], errors="coerce").to_numpy(),
    })
    return hr, mets, glucose, food
