import numpy as np
import pandas as pd

MEAL_GAP_MIN = 30
CLEAN_BEFORE_MIN = 120
CLEAN_AFTER_MIN = 180
PLACEBOS_PER_MEAL = 5
PLACEBO_CLOCK_WINDOW_MIN = 60


def group_meals(food, gap_min=MEAL_GAP_MIN):
    food = food.sort_values("time")
    meal_id = (food["time"].diff() > pd.Timedelta(minutes=gap_min)).cumsum()
    meals = food.groupby(meal_id).agg(
        time=("time", "first"),
        end=("time", "last"),
        calories=("calories", "sum"),
        carbs=("carbs", "sum"),
        items=("food", list),
    )
    meals["standard_breakfast"] = meals["items"].apply(
        lambda items: any("standard breakfast" in str(item).lower() for item in items)
    )
    return meals.reset_index(drop=True)


def food_free(times, eating_times, before=CLEAN_BEFORE_MIN, after=CLEAN_AFTER_MIN, ignore=None):
    # ignore: one (start, end) pair per time, so a meal isn't blocked by its own items
    eating = np.sort(eating_times.to_numpy())
    result = []
    for i, t in enumerate(times):
        lo, hi = t - pd.Timedelta(minutes=before), t + pd.Timedelta(minutes=after)
        nearby = eating[(eating >= lo) & (eating <= hi)]
        if ignore is not None:
            start, end = ignore[i]
            nearby = nearby[(nearby < start) | (nearby > end)]
        result.append(len(nearby) == 0)
    return np.array(result, dtype=bool)


def clean_meals(meals, food):
    keep = food_free(meals["time"], food["time"], ignore=list(zip(meals["time"], meals["end"])))
    return meals[keep].reset_index(drop=True)


def placebo_times(meal_times, food, start, end, per_meal=PLACEBOS_PER_MEAL,
                  max_clock_diff_min=PLACEBO_CLOCK_WINDOW_MIN, step_min=5, seed=0, covered=None):
    # covered: optional filter keeping only grid times the sensor records in full
    rng = np.random.default_rng(seed)
    grid = pd.Series(pd.date_range(start.ceil(f"{step_min}min"), end, freq=f"{step_min}min"))
    grid = grid[food_free(grid, food["time"])]
    if covered is not None:
        grid = grid[np.asarray(covered(grid), dtype=bool)]
    grid_minutes = grid.dt.hour * 60 + grid.dt.minute

    rows = []
    used = set()
    for meal_index, t in enumerate(meal_times):
        meal_minutes = t.hour * 60 + t.minute
        diff = (grid_minutes - meal_minutes).abs()
        diff = np.minimum(diff, 1440 - diff)
        options = grid[(diff <= max_clock_diff_min) & (grid.dt.date != t.date()) & ~grid.isin(list(used))]
        chosen = options.sample(n=min(per_meal, len(options)), random_state=rng) if len(options) else options
        used.update(chosen)
        rows += [{"meal_index": meal_index, "time": c} for c in chosen]
    return pd.DataFrame(rows, columns=["meal_index", "time"])
