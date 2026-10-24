import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from stats import auc, detectable_difference, per_participant


def test_auc_extremes():
    assert auc([5, 6, 7], [1, 2, 3]) == 1.0
    assert auc([1, 2, 3], [5, 6, 7]) == 0.0
    assert auc([1, 2], [1, 2]) == 0.5


def test_per_participant_difference():
    table = pd.DataFrame({
        "pid": ["001"] * 5,
        "kind": ["meal", "meal", "placebo", "placebo", "placebo"],
        "score": [10.0, 12.0, 1.0, 2.0, 3.0],
    })
    per = per_participant(table, "score")
    assert per.loc[0, "difference"] == 11.0 - 2.0
    assert per.loc[0, "auc"] == 1.0


def test_detectable_difference_grows_with_spread_and_shrinks_with_people():
    tight = pd.DataFrame({"difference": [1.0, -1.0] * 8})
    loose = pd.DataFrame({"difference": [4.0, -4.0] * 8})
    bigger = pd.DataFrame({"difference": [1.0, -1.0] * 32})
    assert detectable_difference(loose) > detectable_difference(tight)
    assert detectable_difference(bigger) < detectable_difference(tight)


def test_holm_matches_hand_calculation():
    from stats import holm

    assert list(holm([0.01, 0.04, 0.03, 0.005])) == pytest.approx([0.03, 0.06, 0.06, 0.02])
