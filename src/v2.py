"""v2: the placebo test on a chest strap (D1NAMO) and on a second wrist dataset (CGMacros).

Rules: ANALYSIS_PLAN_v2.md.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

import cgmacros
import d1namo
from movement import FIT_MIN_SINCE_FOOD, adjust_hr, minutes_since_food, movement_features
from placebo_test import covered_by, participant_windows, report
from stats import holm, per_participant

RESULTS = Path(__file__).resolve().parent.parent / "results" / "v2"
CLOCK_WINDOWS = [60, 90, 120]
MIN_PEOPLE = 10
MIN_MEALS = 3
MIN_PLACEBOS = 2
MIN_FIT_MINUTES = 300
SEEDS = range(10)

# (key, dataset, sensor, signal, score, window column, who takes part)
TESTS = [
    ("d1_hr_peak", "D1NAMO", "chest", "heart rate", "peak", "hr_peak", "main"),
    ("d1_hr_sustained", "D1NAMO", "chest", "heart rate", "average", "hr_sustained", "main"),
    ("d1_adj_hr_peak", "D1NAMO", "chest", "heart rate, movement removed", "peak", "hr_adj_peak", "movement"),
    ("d1_adj_hr_sustained", "D1NAMO", "chest", "heart rate, movement removed", "average", "hr_adj_sustained", "movement"),
    ("d1_br_peak", "D1NAMO", "chest", "breathing rate", "peak", "br_peak", "breathing"),
    ("d1_br_sustained", "D1NAMO", "chest", "breathing rate", "average", "br_sustained", "breathing"),
    ("cgm_hr_peak", "CGMacros", "wrist", "heart rate", "peak", "hr_peak", "main"),
    ("cgm_hr_sustained", "CGMacros", "wrist", "heart rate", "average", "hr_sustained", "main"),
    ("cgm_adj_hr_peak", "CGMacros", "wrist", "heart rate, movement removed", "peak", "hr_adj_peak", "movement"),
    ("cgm_adj_hr_sustained", "CGMacros", "wrist", "heart rate, movement removed", "average", "hr_adj_sustained",
     "movement"),
    ("cgm_glucose", "CGMacros", "arm (CGM)", "glucose", "peak", "glucose_peak", "main"),
]


def fit_minutes(hr, movement, food_times):
    # same fitting set as movement.adjust_hr
    data = movement_features(movement).join(hr.rename("hr"), how="inner").dropna()
    return int((minutes_since_food(data.index, food_times) >= FIT_MIN_SINCE_FOOD).sum())


def prepare(pid, signals, main, food, movement):
    hr = signals["hr"][0]
    fit = fit_minutes(hr, movement, food["time"]) if len(movement) else 0
    adjusted = adjust_hr(hr, movement, food["time"])[0] if fit >= MIN_FIT_MINUTES else hr.iloc[:0]
    starts = [s.index.min() for s, _ in main.values()] + [food["time"].min()]
    ends = [s.index.max() for s, _ in main.values()] + [food["time"].max()]
    return {"pid": pid, "signals": {**signals, "hr_adj": (adjusted, 1)}, "main": main, "food": food,
            "start": max(starts), "end": min(ends), "fit_minutes": fit}


def prepare_d1namo():
    out = []
    for pid in d1namo.PARTICIPANTS:
        hr, br, activity = d1namo.load_signals(pid)
        out.append(prepare(pid, {"hr": (hr, 1), "br": (br, 1)}, {"hr": (hr, 1)}, d1namo.load_food(pid), activity))
    return out


def prepare_cgmacros(everyone=False):
    out = []
    for pid in cgmacros.participants(everyone):
        hr, mets, glucose, food = cgmacros.load(pid)
        main = {"hr": (hr, 1), "glucose": (glucose, 5)}
        out.append(prepare(pid, main, main, food, mets))
    return out


def windows(prepared, clock_window, seed=0):
    tables = []
    for p in prepared:
        if p["start"] >= p["end"]:
            continue
        table = participant_windows(p["signals"], p["food"], p["start"], p["end"], seed=seed,
                                    covered=covered_by(p["main"]), max_clock_diff_min=clock_window)
        tables.append(table.assign(pid=p["pid"], fit_minutes=p["fit_minutes"]))
    table = pd.concat(tables, ignore_index=True)
    return table.dropna(subset=[f"{name}_peak" for name in prepared[0]["main"]]).reset_index(drop=True)


def included(table, column):
    valid = table.dropna(subset=[column])
    counts = valid.groupby(["pid", "kind"]).size().unstack(fill_value=0).reindex(columns=["meal", "placebo"],
                                                                                   fill_value=0)
    return sorted(counts[(counts["meal"] >= MIN_MEALS) & (counts["placebo"] >= MIN_PLACEBOS)].index)


def choose_clock_window(prepared):
    """Smallest clock window leaving MIN_PEOPLE included people. Uses window counts only."""
    counts = {}
    for minutes in CLOCK_WINDOWS:
        table = windows(prepared, minutes)
        counts[minutes] = len(included(table, "hr_peak"))
        if counts[minutes] >= MIN_PEOPLE:
            return minutes, counts, table
    return CLOCK_WINDOWS[-1], counts, table


def groups(table):
    main = included(table, "hr_peak")
    return {
        "main": main,
        "movement": sorted(set(main) & set(table.loc[table["fit_minutes"] >= MIN_FIT_MINUTES, "pid"])),
        "breathing": included(table, "br_peak") if "br_peak" in table else [],
    }


def window_counts(d1, cgm):
    """Everything the count-only rules need, without touching any signal value."""
    out = {}
    for name, prepared in [("D1NAMO", d1), ("CGMacros", cgm)]:
        minutes, counts, table = choose_clock_window(prepared)
        g = groups(table)
        main = table[table["pid"].isin(g["main"])]
        out[name] = {
            "participants": len(prepared),
            "people_by_clock_window": counts,
            "clock_window_min": minutes,
            "exploratory": counts[minutes] < MIN_PEOPLE,
            "included": len(g["main"]),
            "movement_included": len(g["movement"]),
            "meals": int((main["kind"] == "meal").sum()),
            "placebos": int((main["kind"] == "placebo").sum()),
        }
        if name == "D1NAMO":
            out[name]["breathing_included"] = len(g["breathing"])
            out[name]["breathing_usable"] = len(g["breathing"]) >= MIN_PEOPLE
    return out


def run_tests(tables, counts):
    rows, per = [], {}
    for key, dataset, sensor, signal, score, column, who in TESTS:
        if who == "breathing" and not counts["D1NAMO"]["breathing_usable"]:
            continue
        table = tables[dataset]
        p = per_participant(table[table["pid"].isin(groups(table)[who])], column)
        per[key] = p
        summary = report(table[table["pid"].isin(groups(table)[who])], {key: column})[key]
        rows.append({"key": key, "dataset": dataset, "sensor": sensor, "signal": signal, "score": score,
                     "exploratory": counts[dataset]["exploratory"], **summary})
    result = pd.DataFrame(rows)
    family = ~result["exploratory"]
    result["holm_p"] = np.nan
    result.loc[family, "holm_p"] = holm(result.loc[family, "wilcoxon_p"])
    result["passed"] = family & (result["holm_p"] < 0.05)
    return result, per


def meal_timing_check():
    """D1NAMO: rise from each before-meal finger prick to the after-meal one on the same day."""
    people, rises_logged = {}, []
    for pid in d1namo.PARTICIPANTS:
        pricks, food = d1namo.load_fingerpricks(pid), d1namo.load_food(pid)
        rises = []
        for meal in "BLD":
            before, after = pricks[pricks["type"] == "B" + meal], pricks[pricks["type"] == "A" + meal]
            for _, b in before.iterrows():
                same_day = after[after["time"].dt.date == b["time"].date()]
                if len(same_day):
                    a = same_day.iloc[0]
                    rises.append(a["glucose"] - b["glucose"])
                    rises_logged.append(bool(((food["time"] > b["time"]) & (food["time"] <= a["time"])).any()))
        if rises:
            people[pid] = float(np.mean(rises))
    values = list(people.values())
    return {"participants": len(values), "pairs": len(rises_logged), "median_rise_mmol": float(np.median(values)),
            "participants_positive": int(sum(v > 0 for v in values)), "wilcoxon_p": float(wilcoxon(values).pvalue),
            "pairs_with_meal_logged_between": float(np.mean(rises_logged))}


def seed_range(d1, cgm, counts):
    aucs = {}
    for seed in SEEDS:
        tables = {"D1NAMO": windows(d1, counts["D1NAMO"]["clock_window_min"], seed),
                  "CGMacros": windows(cgm, counts["CGMacros"]["clock_window_min"], seed)}
        for _, row in run_tests(tables, counts)[0].iterrows():
            aucs.setdefault(row["key"], []).append(row["median_auc"])
    return {key: [float(min(v)), float(max(v))] for key, v in aucs.items()}


def main():
    d1, cgm = prepare_d1namo(), prepare_cgmacros()
    counts = window_counts(d1, cgm)
    tables = {"D1NAMO": windows(d1, counts["D1NAMO"]["clock_window_min"]),
              "CGMacros": windows(cgm, counts["CGMacros"]["clock_window_min"])}
    result, per = run_tests(tables, counts)

    extra = {"seed_range": seed_range(d1, cgm, counts), "meal_timing": meal_timing_check()}
    wide = {**tables, "D1NAMO": windows(d1, CLOCK_WINDOWS[-1])}
    extra["d1namo_120_min"] = run_tests(wide, counts)[0].query("dataset == 'D1NAMO'").set_index("key")[
        "median_auc"].to_dict()
    everyone = {**tables, "CGMacros": windows(prepare_cgmacros(everyone=True), counts["CGMacros"]["clock_window_min"])}
    extra["cgmacros_everyone"] = run_tests(everyone, counts)[0].query("dataset == 'CGMacros'").set_index("key")[
        "median_auc"].to_dict()

    RESULTS.mkdir(parents=True, exist_ok=True)
    result.to_csv(RESULTS / "table.csv", index=False)
    metrics = {"window_counts": counts, "tests": result.to_dict(orient="records"), "extra": extra}
    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2, default=float) + "\n")
    return metrics, per


if __name__ == "__main__":
    import sys

    if "--counts" in sys.argv:
        print(json.dumps(window_counts(prepare_d1namo(), prepare_cgmacros()), indent=2))
    else:
        main()
