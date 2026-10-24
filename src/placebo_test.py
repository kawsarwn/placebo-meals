"""The placebo test for any signal: real meals vs food-free moments at the same time of day on other days."""

import numpy as np
import pandas as pd

from meals import clean_meals, group_meals, placebo_times
from response import responses
from stats import detectable_difference, per_participant, summarize


def participant_windows(signals, food, start, end, seed=0, covered=None, **placebo_options):
    """Score one person's clean meals and placebo moments on every signal.

    signals: {name: (series, step_min)}, each series indexed by time.
    food: one row per logged item, with time, food, calories and carbs columns.
    start, end: the period where food was logged and the sensors recorded.
    Returns one row per moment with {name}_peak, {name}_sustained, {name}_baseline and {name}_time_to_peak.
    """
    meals = clean_meals(group_meals(food), food)
    placebos = placebo_times(meals["time"], food, start, end, seed=seed, covered=covered, **placebo_options)
    real = meals.drop(columns=["end", "items"]).assign(kind="meal", meal_index=range(len(meals)))
    windows = pd.concat([real, placebos.assign(kind="placebo")], ignore_index=True)
    windows["time"] = pd.to_datetime(windows["time"])
    scored = [responses(series, windows["time"], step_min).add_prefix(f"{name}_")
              for name, (series, step_min) in signals.items()]
    return pd.concat([windows, *scored], axis=1)


def report(table, columns):
    """Summarize across people, as in v1. columns: {label: window column}."""
    out = {}
    for label, column in columns.items():
        per = per_participant(table, column)
        out[label] = {**summarize(per), "detectable_difference": detectable_difference(per) if len(per) > 1 else np.nan}
    return out
