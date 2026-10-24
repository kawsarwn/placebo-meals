import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from d1namo import load_fingerpricks, load_food, load_signals


def summary_csv():
    # minute 1: 45 confident seconds (kept); minute 2: 30 (dropped); minute 3: inside a flagged problem period
    rows = ["Time,HR,BR,SkinTemp,Activity,HRConfidence,BRConfidence"]
    start = pd.Timestamp("2014-10-02 07:00:00")
    for s in range(180):
        t = (start + pd.Timedelta(seconds=s)).strftime("%d/%m/%Y %H:%M:%S.000")
        confident = s < 45 or 60 <= s < 90 or s >= 120
        rows.append(f"{t},70,12,30,0.1,{100 if confident else 0},{100 if confident else 0}")
    return "\n".join(rows)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_files(tmp_path):
    sensor, logs = tmp_path / "sensor", tmp_path / "logs"
    write(sensor / "001/sensor_data/s1/s1_Summary.csv", summary_csv())
    write(logs / "001/annotations.csv", "start_date,start_time,end_date,end_time,type,description\n"
          "2014-10-02,07:02,2014-10-02,07:03,problem,Harness put wrongly\n")
    write(logs / "001/food.csv", "date,time,picture,description,calories,balance,quality\n"
          '2014-10-02,12:25,"007.jpg","Tuna", 446,"8 "Balance"","Good quality"\n'
          "2014-10-02,08:00,breakfast,,Bread\n"
          "2014-10-02,,,Broken row\n")
    write(logs / "001/glucose.csv", "date,time,glucose,type,comments\n"
          "2014-10-02,07:15,5.7,BB,\n2014-10-02,09:32,7:0,AB,\n")
    return sensor, logs


def test_minutes_need_40_confident_seconds_and_skip_problem_periods(tmp_path):
    sensor, logs = make_files(tmp_path)
    hr, br, activity = load_signals("001", sensor, logs)
    assert list(hr.index) == [pd.Timestamp("2014-10-02 07:00")]
    assert hr.iloc[0] == 70 and br.iloc[0] == 12
    assert list(activity.index) == [pd.Timestamp("2014-10-02 07:00"), pd.Timestamp("2014-10-02 07:01")]


def test_food_log_keeps_rows_with_broken_quoting(tmp_path):
    _, logs = make_files(tmp_path)
    food = load_food("001", logs)
    assert list(food["time"]) == [pd.Timestamp("2014-10-02 08:00"), pd.Timestamp("2014-10-02 12:25")]


def test_fingerpricks_drop_unreadable_values(tmp_path):
    _, logs = make_files(tmp_path)
    pricks = load_fingerpricks("001", logs)
    assert list(pricks["type"]) == ["BB"] and pricks["glucose"].iloc[0] == 5.7
