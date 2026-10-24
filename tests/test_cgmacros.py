import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from cgmacros import load, participants


def make_files(tmp_path):
    (tmp_path / "bio.csv").write_text("subject,Age,A1c PDL (Lab)\n1,30,5.4\n2,50,7.1\n3,40,5.0\n")
    rows = ["Unnamed: 0,Timestamp,Libre GL,Dexcom GL,HR,Calories (Activity),Intensity,Meal Type,Calories,Carbs,"
            "Amount Consumed ,Image path"]
    for i in range(10):
        meal = "Lunch,600,70" if i == 2 else ",,"
        rows.append(f"{i},2020-05-01 10:0{i}:00,90,{100 + i},{60 + i},1.2,0,{meal},,")
    for pid in ("001", "002"):  # 003 is in bio.csv but has no folder
        (tmp_path / f"CGMacros-{pid}").mkdir()
        (tmp_path / f"CGMacros-{pid}" / f"CGMacros-{pid}.csv").write_text("\n".join(rows))


def test_main_sample_keeps_hba1c_below_6_5_with_data(tmp_path):
    make_files(tmp_path)
    assert participants(root=tmp_path) == ["001"]
    assert participants(everyone=True, root=tmp_path) == ["001", "002"]


def test_glucose_becomes_5_minute_means_and_missing_mets_is_empty(tmp_path):
    make_files(tmp_path)
    hr, mets, glucose, food = load("001", root=tmp_path)
    assert len(hr) == 10 and mets.empty
    assert list(glucose) == [102.0, 107.0]
    assert list(glucose.index) == [pd.Timestamp("2020-05-01 10:00"), pd.Timestamp("2020-05-01 10:05")]
    assert list(food["time"]) == [pd.Timestamp("2020-05-01 10:02")] and food["calories"].iloc[0] == 600
