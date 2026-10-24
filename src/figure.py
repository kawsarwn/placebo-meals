import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LIGHT = {
    "surface": "#fcfcfb", "ink": "#0b0b0b", "secondary": "#52514e", "muted": "#898781",
    "grid": "#e1e0d9", "axis": "#c3c2b7", "meal": "#2a78d6", "placebo": "#eb6834",
}
DARK = {
    "surface": "#1a1a19", "ink": "#ffffff", "secondary": "#c3c2b7", "muted": "#898781",
    "grid": "#2c2c2a", "axis": "#383835", "meal": "#3987e5", "placebo": "#d95926",
}

KIND_LABELS = {"meal": "Real meals", "placebo": "Placebo moments"}
AUC_ROWS = [
    ("glucose", "Glucose rise"),
    ("hr_peak", "Heart rate peak"),
    ("hr_sustained", "Heart rate, 30 to 120 min"),
]


def style_axes(ax, theme, ygrid=True):
    ax.set_facecolor(theme["surface"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme["axis"])
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=theme["muted"], labelcolor=theme["secondary"], labelsize=10, length=0, pad=6)
    if ygrid:
        ax.yaxis.grid(True, color=theme["grid"], linewidth=0.8)
        ax.set_axisbelow(True)


def time_course(ax, curves, signal, title, theme):
    style_axes(ax, theme)
    data = curves[curves["signal"] == signal]
    ax.axvline(0, color=theme["axis"], linewidth=1)
    ax.axhline(0, color=theme["axis"], linewidth=1)
    for kind in ("placebo", "meal"):
        by_minute = data[data["kind"] == kind].groupby("minute")["change"]
        mean = by_minute.mean()
        se = by_minute.std(ddof=1) / np.sqrt(by_minute.count())
        x = mean.index + 2.5  # plot each 5-min bin at its center
        ax.fill_between(x, mean - se, mean + se, color=theme[kind], alpha=0.12, linewidth=0)
        ax.plot(x, mean, color=theme[kind], linewidth=2, solid_capstyle="round", label=KIND_LABELS[kind])
    ax.set_title(title, loc="left", color=theme["ink"], fontsize=12, pad=10)
    ax.set_xlim(-30, 180)
    ax.set_xticks([-30, 0, 30, 60, 90, 120, 150, 180])
    ax.set_xlabel("Minutes from the meal or placebo moment", color=theme["secondary"], fontsize=10)


MOVEMENT_ROWS = [
    ("adj_hr_peak", "Heart rate peak, movement removed"),
    ("adj_hr_sustained", "Heart rate average, movement removed"),
    ("still_hr_sustained", "Heart rate average, still periods only"),
    ("still_glucose", "Glucose rise, still periods only (check)"),
]


def auc_strip(ax, per_metric, theme, rows=AUC_ROWS, title="How often a real meal outscores a placebo"):
    style_axes(ax, theme, ygrid=False)
    ax.xaxis.grid(True, color=theme["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    ax.axvline(0.5, color=theme["axis"], linewidth=1)
    rng = np.random.default_rng(1)
    for row, (key, label) in enumerate(reversed(rows)):
        if len(per_metric[key]) == 0:
            ax.text(0.01, row + 0.27, f"{label}: too few people", color=theme["muted"], fontsize=10)
            continue
        values = per_metric[key]["auc"].to_numpy()
        jitter = rng.uniform(-0.12, 0.12, len(values))
        ax.scatter(values, row + jitter, s=64, color=theme["meal"], edgecolor=theme["surface"],
                   linewidth=1.5, zorder=3)
        median = np.median(values)
        ax.plot([median, median], [row - 0.25, row + 0.25], color=theme["ink"], linewidth=2,
                solid_capstyle="round", zorder=4)
        ax.text(1.0, row + 0.27, f"median {median:.0%}", color=theme["secondary"], fontsize=9,
                ha="right", va="bottom")
        ax.text(0.01, row + 0.27, label, color=theme["ink"], fontsize=10, ha="left", va="bottom")
    ax.text(0.5, len(rows) - 0.32, "coin flip", color=theme["muted"], fontsize=9, ha="center", va="bottom")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(-0.45, len(rows) - 0.15)
    ax.set_xlim(-0.02, 1.03)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_title(title, loc="left", color=theme["ink"], fontsize=12, pad=10)
    ax.set_xlabel("One dot per participant", color=theme["secondary"], fontsize=10)


def make_figure(curves, per_metric, subtitle, theme, path):
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), gridspec_kw={"width_ratios": [1, 1, 1.1], "wspace": 0.22})
    fig.patch.set_facecolor(theme["surface"])
    time_course(axes[0], curves, "glucose", "Glucose change (mg/dL)", theme)
    time_course(axes[1], curves, "hr", "Heart rate change (bpm)", theme)
    auc_strip(axes[2], per_metric, theme)

    fig.text(0.07, 1.04, "Real meals vs placebo moments", color=theme["ink"], fontsize=16, fontweight="bold")
    fig.text(0.07, 0.975, subtitle, color=theme["secondary"], fontsize=10.5)
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles[::-1], labels[::-1], loc="upper right", bbox_to_anchor=(0.91, 1.07), ncol=2,
                        frameon=False, fontsize=10, handlelength=1.6)
    for text in legend.get_texts():
        text.set_color(theme["ink"])
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=theme["surface"])
    plt.close(fig)


def make_movement_figure(curves, per_metric, subtitle, theme, path):
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9), gridspec_kw={"width_ratios": [1, 1.2], "wspace": 0.18})
    fig.patch.set_facecolor(theme["surface"])
    time_course(axes[0], curves, "hr_adjusted", "Heart rate change, movement removed (bpm)", theme)
    auc_strip(axes[1], per_metric, theme, rows=MOVEMENT_ROWS)

    fig.text(0.09, 1.05, "Controlling for movement", color=theme["ink"], fontsize=16, fontweight="bold")
    fig.text(0.09, 0.985, subtitle, color=theme["secondary"], fontsize=10.5)
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles[::-1], labels[::-1], loc="upper right", bbox_to_anchor=(0.91, 1.08), ncol=2,
                        frameon=False, fontsize=10, handlelength=1.6)
    for text in legend.get_texts():
        text.set_color(theme["ink"])
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=theme["surface"])
    plt.close(fig)


def make_v2_figure(per_metric, rows, subtitle, theme, path):
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=(8.5, 0.62 * len(rows) + 1.4))
    fig.patch.set_facecolor(theme["surface"])
    auc_strip(ax, per_metric, theme, rows=rows)
    fig.text(0.125, 1.0 + 0.9 / (0.62 * len(rows) + 1.4), "Wrist vs chest, same placebo test", color=theme["ink"],
             fontsize=16, fontweight="bold")
    fig.text(0.125, 1.0 + 0.45 / (0.62 * len(rows) + 1.4), subtitle, color=theme["secondary"], fontsize=10.5)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=theme["surface"])
    plt.close(fig)
