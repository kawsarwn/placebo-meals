import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from analyze import all_windows, curves
from figure import DARK, LIGHT, make_figure, make_movement_figure, make_v2_figure
from report import RESULTS, build_metrics, display_values, render_readme, seed_range, write_outputs
import v2

SEED_DRAWS = 10


def main():
    table = all_windows()
    metrics, per = build_metrics(table)
    other_draws = [all_windows(seed) for seed in range(1, SEED_DRAWS)]
    metrics["exploratory"]["seed_range"] = seed_range([table] + other_draws)
    curve_table = curves(table)

    RESULTS.mkdir(exist_ok=True)
    subtitle = (
        f"{metrics['participants']} adults, {metrics['meals']} clean meals vs {metrics['placebos']} "
        "time-matched placebo moments. Lines: mean across people. Bands: ±1 standard error."
    )
    make_figure(curve_table, per, subtitle, LIGHT, RESULTS / "figure-light.png")
    make_figure(curve_table, per, subtitle, DARK, RESULTS / "figure-dark.png")

    move = metrics["movement"]
    movement_subtitle = (
        f"One movement model per person, fit on food-free minutes. Still periods: {move['still_meals']} meals, "
        f"{move['still_placebos']} placebo moments. Lines: mean across people. Bands: ±1 standard error."
    )
    make_movement_figure(curve_table, per, movement_subtitle, LIGHT, RESULTS / "movement-light.png")
    make_movement_figure(curve_table, per, movement_subtitle, DARK, RESULTS / "movement-dark.png")
    write_outputs(metrics, per)
    print(f"done: {metrics['participants']} participants, {metrics['meals']} meals, {metrics['placebos']} placebos")

    v2_metrics, v2_per = v2.main()
    chart = v2.chart_data(v2_per, RESULTS / "per_participant.csv")
    v2_subtitle = (f"One dot per person. v1 and CGMacros: wristband. D1NAMO: chest strap, "
                   f"{v2_metrics['window_counts']['D1NAMO']['included']} people, exploratory.")
    make_v2_figure(chart, v2.CHART_ROWS, v2_subtitle, LIGHT, v2.RESULTS / "figure-light.png")
    make_v2_figure(chart, v2.CHART_ROWS, v2_subtitle, DARK, v2.RESULTS / "figure-dark.png")
    render_readme({**display_values(metrics), **v2.display_values(v2_metrics)})
    print("done: v2 and README")


if __name__ == "__main__":
    main()
