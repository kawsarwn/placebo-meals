import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, t, wilcoxon


def auc(meal_values, placebo_values):
    # chance a random meal outscores a random placebo, ties counting half
    return mannwhitneyu(meal_values, placebo_values).statistic / (len(meal_values) * len(placebo_values))


def per_participant(table, metric, meal_filter=None):
    rows = []
    for pid, d in table.groupby("pid"):
        meals = d[d["kind"] == "meal"]
        if meal_filter is not None:
            meals = meals[meal_filter(meals)]
        meal_values = meals[metric].dropna()
        placebo_values = d.loc[d["kind"] == "placebo", metric].dropna()
        if len(meal_values) < 2 or len(placebo_values) < 2:
            continue
        rows.append({
            "pid": pid,
            "meals": len(meal_values),
            "placebos": len(placebo_values),
            "meal_mean": meal_values.mean(),
            "placebo_mean": placebo_values.mean(),
            "difference": meal_values.mean() - placebo_values.mean(),
            "auc": auc(meal_values, placebo_values),
        })
    return pd.DataFrame(rows)


def detectable_difference(per, power=0.8, alpha=0.05):
    # smallest average difference a paired t-test would detect at this spread and sample size
    n = len(per)
    sd = per["difference"].std(ddof=1)
    return float((t.ppf(1 - alpha / 2, n - 1) + t.ppf(power, n - 1)) * sd / np.sqrt(n))


def holm(pvalues):
    # Holm step-down adjusted p-values, returned in the input order
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order])
    out = np.empty_like(p)
    out[order] = np.minimum(adjusted, 1)
    return out


def summarize(per):
    if len(per) == 0:
        return {"participants": 0}
    return {
        "participants": len(per),
        "median_meal": float(per["meal_mean"].median()),
        "median_placebo": float(per["placebo_mean"].median()),
        "median_difference": float(per["difference"].median()),
        "participants_positive": int((per["difference"] > 0).sum()),
        "wilcoxon_p": float(wilcoxon(per["difference"]).pvalue) if len(per) >= 2 else float("nan"),
        "median_auc": float(per["auc"].median()),
        "mean_auc": float(per["auc"].mean()),
    }
