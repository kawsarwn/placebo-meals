# placebo-meals

A placebo test for wearable meal responses on public data. The question: does heart rate after a real meal differ from heart rate after a food-free "placebo" moment in the same person's day?

Analysis rules: @ANALYSIS_PLAN.md (v1) and @ANALYSIS_PLAN_v2.md (v2)

## Data

- **Source:** BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3, Open Data Commons Attribution 1.0. Cite Cho et al. 2026 (doi:10.13026/aw6y-fc44) and Bent et al. 2021 (npj Digital Medicine 4:89).
- **Contents:** 16 adults aged 35 to 65, 8 to 10 days each, wearing an Empatica E4 wristband and a Dexcom G6 glucose monitor and keeping a food log. They ate a standardized breakfast every other day.
- **Storage:** raw files stay in `data/`, which git ignores. Don't commit raw data.
- **Downloading:**
  - `src/download.py` fetches HR, Dexcom and Food_Log, about 250 MB.
  - `--extra` adds TEMP and EDA, about 2.5 GB.
  - `src/motion.py` streams the 13 GB of ACC files and stores per-minute summaries in `data/motion/`.
  - Skip BVP and IBI.
- **Quirks:**
  - HR timestamps have minute resolution, with about 60 rows per minute.
  - Dexcom files start with metadata rows.
  - The food log has one row per food item.
- **v2 data** (`src/download_v2.py`, into `data/d1namo/` and `data/cgmacros/`):
  - D1NAMO v1.2.0 (Zenodo, doi:10.5281/zenodo.5651217, CC BY-SA 4.0; Dubosson et al. 2018). Healthy group, chest strap per-second summaries, photo food logs, finger-prick glucose. Strap off at night. Summary timestamps are day-first.
  - CGMacros v1.0.0 (PhysioNet, CC BY-NC-SA 4.0). Per-minute smartwatch heart rate and METs (×10), Dexcom and Libre glucose, meal rows. Dates are shifted for privacy; clock times are real.
  - Results derived from these keep their licenses: CC BY-SA 4.0 and CC BY-NC-SA 4.0.

## Rules

- **Numbers in README.md come from the pipeline.** `src/report.py` renders `README.md` from `README.template.md` and `results/metrics.json`. Edit the template, not README.md.
- **Wellness framing:** no diagnostic language, no medical or dosing advice and no claims about a specific device.
- Don't name or evaluate any company's product or code.
- Label anything simulated as simulated.
- **The participant is the unit of analysis.** Summarize within each person, then across people.
- **Models:** if you train one, start with a classical baseline and split by participant, not by meal or window.
- **Writing:** US English, no em dashes. Avoid "excited to," "passionate about," "leverage" and "dive into."
- **Code:** plain Python with pandas, numpy, scipy and matplotlib. Add comments where something needs explaining.

## Commands

- Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Data: `.venv/bin/python src/download.py`, then `.venv/bin/python src/motion.py`; v2: `.venv/bin/python src/download_v2.py`
- Tests: `.venv/bin/python -m pytest -q`
- Full run: `.venv/bin/python run_all.py`

## Git

- Use `/usr/bin/git`. The binary in `/usr/local/bin` is broken on this machine.
- Commit small working steps and push often. The repo is public.
