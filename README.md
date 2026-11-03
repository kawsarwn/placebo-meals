# Placebo meals

**A placebo test for heart rate meal responses, run on public wearable data.**

Wearables that report meal responses need a way to check that the response comes from the meal. To check heart rate, I scored real meals and *placebo moments* the same way. A placebo moment is a time when the same person ate nothing, at the same time of day as a real meal but on a different day. If heart rate responds to food, real meals should score higher.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/figure-dark.png">
  <img alt="Glucose rises after real meals but not after placebo moments. Heart rate looks the same after both, and real meals outscore placebos about half the time." src="results/figure-light.png">
</picture>

## Result

**Glucose rises far more after real meals than after placebo moments. Heart rate shows no difference.**

> **v2 update:** [repeated on 31 people from a second wrist dataset](#v2-a-second-wrist-dataset-and-a-first-look-at-a-chest-strap), heart rate is a median of +2.8 bpm higher from 30 to 120 minutes after real meals than after placebo moments. That's below what v1 could detect, and too small to read from a single meal.

| Score | After real meals | After placebo moments | Difference | Real meal scores higher |
|---|---|---|---|---|
| Glucose peak: highest in the 3 h after, minus the 30 min before | +44 mg/dL | +11 mg/dL | +35.0 mg/dL | 85% of the time |
| Heart rate peak: same definition | +48 bpm | +50 bpm | -0.5 bpm | 49% of the time |
| Heart rate average: 30 to 120 min after, minus the 30 min before | +1.5 bpm | -0.8 bpm | -1.4 bpm | 49% of the time |

How to read the table:

- **Every value is a median across 15 people**, taken after summarizing each person.
- **"Difference"** is a person's average after real meals minus their average after placebo moments.
- **"Real meal scores higher"** is the chance that one of a person's real meals beats one of their placebo moments. 50% is a coin flip.

Across people:

- **Glucose** is higher after real meals for 14 of 15 people (p < 0.001, Wilcoxon signed-rank test).
- **Heart rate peak** is higher for 6 of 15 (p = 0.23).
- **Heart rate average** is higher for 6 of 15 (p = 0.80).

**What it means.** In everyday wrist data, the heart rate peak after a meal reaches about +48 bpm, which looks like a strong response. Placebo moments reach +50 bpm. A 3-hour peak catches movement, like walking or standing up, along with sensor noise. The movement check below tests that.

Without a placebo comparison, you would read that +48 bpm as a meal response. Glucose, scored the same way, separates meals from placebo moments, so the test can detect a real effect.

These results rule out a large heart rate response to meals in this data. A smaller one could still hide below the detection limits listed under Limitations.

## Movement check

The wristband also records motion, so I repeated the test in two ways that take movement out of the picture. I wrote both down in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) before running them.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/movement-dark.png">
  <img alt="With movement removed, heart rate after real meals and after placebo moments still looks similar, and real meals outscore placebos a little more often than a coin flip." src="results/movement-light.png">
</picture>

1. **Movement removed.**
   - For each person, I fit a model that predicts heart rate from wrist movement over the current and previous 15 minutes.
   - I fit it on minutes at least 3 hours after eating, so a meal effect can't leak in.
   - Movement explains a median 35% of minute-to-minute heart rate variation (range 0% to 60%). The lowest is participant 013, whose heart rate has frequent sensor spikes.
   - I then ran the placebo test on the heart rate that movement doesn't explain:
     - Heart rate peak: a real meal scores higher 48% of the time (7 of 15 people higher, p = 0.89).
     - Heart rate average: 61% of the time (11 of 15 people higher, median difference +1.9 bpm, p = 0.28).
2. **Still periods** (exploratory).
   - I planned to keep meals and placebo moments where at least 80% of minutes were still, both in the 30 min before and from 30 to 120 min after.
   - **People kept moving after most meals.** With the loosest planned threshold (0.1 g), 27 of 167 meals (16%) passed, against 193 of 504 placebo moments (38%).
   - That left 7 people with enough data, under the planned minimum of 8, so I report this comparison as exploratory:
     - Heart rate average: a real meal scores higher 51% of the time.
     - Glucose in the same windows, as a check: 88%.

**What it means.** With movement removed, the peak still can't tell meals from placebo moments, so the large peak comes from something other than the meal.

The average leans toward real meals. With movement removed, heart rate after real meals was higher for 11 of 15 people, by a median of +1.9 bpm, and a real meal wins 61% of the time.

The evidence is weak (p = 0.28). The lean also shrinks to 54% when you restrict the test to lunch and dinner, so early-morning and late-night timing around sleep may explain it better than food does. Either way, an effect this small can't tell you anything about a single meal.

## What I'd do next

- **Look for a small heart rate effect under controlled conditions.** Give people the same standardized meal on several days, keep them seated for 2 hours afterward and compare against matched no-meal sessions. That would confirm or rule out the small lean seen above.
- **Score each meal response against a personal placebo baseline.** Use food-free moments from the same person at the same time of day. The comparison costs little and catches responses that have nothing to do with food.
- **Run the same test on other signals.** Skin temperature and EDA sit in this dataset already, and sensors closer to digestion are the obvious next candidates.

## How it works

1. **Data.** From the dataset description:
   - 16 adults aged 35 to 65, with HbA1c in the high-normal to prediabetic range, recorded for 8 to 10 days each.
   - Heart rate from an Empatica E4 wristband, which I averaged per minute.
   - Glucose from a Dexcom G6, every 5 minutes.
   - Timestamped food logs.
2. **Meals.** Food items logged within 30 minutes of each other form one meal. A meal counts as *clean* when the person ate nothing else from 2 hours before to 3 hours after it started. That leaves 167 clean meals.
3. **Placebo moments.** For each clean meal, I picked 5 moments that pass the same food-free rule, on other days, within 60 minutes of the meal's clock time. That gives 504 placebo moments.
4. **Scores.** I compared each moment with the 30 minutes before it in two ways:
   - Peak: the highest value in the next 3 hours.
   - Average: the mean from 30 to 120 minutes after.
5. **Statistics.** I compared each person's real meals with their own placebo moments, then summarized across people.
6. **Checks.**
   - Every included participant's heart rate bottoms out between 3 and 7 am, so the device clocks run on local time.
   - Glucose peaks a median of 63 minutes after logged meals, so the meal times line up with the sensors.

I included 15 of 16 people, the ones with at least 3 clean meals with usable heart rate and glucose. I left out participant 015, whose food log and glucose recording overlap for 0 hours.

I wrote the analysis rules down before looking at any heart rate result. They are in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md), with links to the commits that added them.

## Robustness

- **Leaving out the 1 person whose glucose check failed** (012): real meals outscore placebos 85% of the time for glucose, 49% for heart rate peak and 47% for heart rate average.
- **Exploratory checks**, outside the fixed rules:
  - Different random draws of placebo moments (10 draws): real meals outscore placebos 80% to 85% of the time for glucose, 47% to 52% for heart rate peak, 48% to 56% for heart rate average and 54% to 63% for the movement-removed average.
  - Lunch and dinner (moments starting between 11:00 and 21:00, 12 people): 77% for glucose, 42% for heart rate peak, 46% for heart rate average and 54% for the movement-removed average.
  - Smoothing heart rate over 5 minutes before taking the peak: 51%.
  - Large meals (the top third, at least 617 kcal, 12 people): 97% for glucose, 46% for heart rate peak and 32% for heart rate average.

## Limitations

- **One dataset, built for another question.** The BIG IDEAs study collected these recordings to estimate glucose from wearables, so the meals were free-living and uncontrolled. The participants, adults aged 35 to 65 with HbA1c in the high-normal to prediabetic range, don't represent everyone. I haven't repeated this test on a second dataset yet.
  - *v2 update:* [v2](#v2-a-second-wrist-dataset-and-a-first-look-at-a-chest-strap) repeats the test on a second wrist dataset of 31 people.
- **Detection limits.**
  - The test has 15 people with a median of 11 clean meals each (range 4 to 17).
  - At 80% power, it can reliably detect average differences of about 13 mg/dL for glucose, 7 bpm for heart rate peak, 4 bpm for heart rate average and 5 bpm for the movement-removed average.
  - Glucose cleared its limit by a wide margin. A heart rate effect from digestion of a few beats per minute would fall below these limits, so measuring one takes a bigger or controlled study.
- **Wrist sensor.** The E4 measures heart rate optically at the wrist, and the signal gets noisy during movement.
- **Approximate movement control.** A linear model of wrist motion leaves in other things that change heart rate, like posture, stress or caffeine. It also misses movement that doesn't involve the wrist.
- **Self-reported food logs.** An unlogged snack would make a placebo moment look more like a meal. Snacks like that would blur the glucose result too, and glucose still separates meals from placebo moments, so the logs hold up well enough for this test.
- **Sleep around placebo moments.** 18% of placebo moments started while the person lay still, probably asleep, against 8% of meals. Leaving those moments out gives 48% for heart rate peak and 44% for heart rate average.
- **No repeatability measure.** I couldn't use the dataset's repeated standard breakfast for this, because 3 of them passed the clean-window rule, from 2 people.
- **Not medical advice.** This is an analysis of a public research dataset for general wellness interest. It makes no claim about any specific product.

## v2: a second wrist dataset and a first look at a chest strap

v1 left two questions open. A small heart rate response could hide below its detection limits, and a better sensor might pick up what the wrist missed. v2 runs the same placebo test on two more public datasets. I wrote the rules in [ANALYSIS_PLAN_v2.md](ANALYSIS_PLAN_v2.md) and committed them before downloading any v2 heart rate data.

- **CGMacros, a second wrist dataset:** 31 adults with HbA1c below 6.5%, about 10 days each, wearing a smartwatch and a Dexcom glucose monitor and photographing their meals. It tests whether v1's wrist result holds in different people, with glucose again as the positive control.
- **D1NAMO, a chest strap:** 19 healthy adults, about 4 days each. The strap reads heart rate from the heart's electrical signal, while a wristband reads it optically and picks up more noise from movement. If v1's wrist failed because of a noisy sensor, the strap should do better.

No public dataset I found has both sensors on the same people with timestamped meals, so v2 compares different people and different studies side by side.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/v2/figure-dark.png">
  <img alt="Glucose separates real meals from placebo moments in both wrist datasets. Heart rate moves from a coin flip in v1 to a small lean toward real meals in CGMacros, stronger with movement removed. The chest strap rows lean the same way but have only 8 people." src="results/v2/figure-light.png">
</picture>

### Result

| Dataset | Sensor | Score | People | Real meal scores higher | Difference | p | Holm p | Pass | Detectable at 80% power |
|---|---|---|---|---|---|---|---|---|---|
| CGMacros | wrist | Heart rate peak | 31 | 58% | +4.7 bpm | 0.09 | 0.09 | no | 4 bpm |
| CGMacros | wrist | Heart rate average | 31 | 59% | +2.8 bpm | 0.01 | 0.01 | yes | 3 bpm |
| CGMacros | wrist | Heart rate peak, movement removed | 23 | 65% | +3.5 bpm | < 0.001 | < 0.001 | yes | 2 bpm |
| CGMacros | wrist | Heart rate average, movement removed | 23 | 67% | +3.3 bpm | < 0.001 | < 0.001 | yes | 2 bpm |
| CGMacros | arm (CGM) | Glucose peak | 31 | 82% | +29.9 mg/dL | < 0.001 | < 0.001 | yes | 10 mg/dL |
| D1NAMO | chest | Heart rate peak | 8 | 46% | -1.2 bpm | 0.31 |  | exploratory | 16 bpm |
| D1NAMO | chest | Heart rate average | 8 | 63% | +5.6 bpm | 0.74 |  | exploratory | 10 bpm |
| D1NAMO | chest | Heart rate peak, movement removed | 8 | 60% | +2.4 bpm | 0.95 |  | exploratory | 12 bpm |
| D1NAMO | chest | Heart rate average, movement removed | 8 | 87% | +7.3 bpm | 0.04 |  | exploratory | 9 bpm |

How to read the table:

- **Real meal scores higher** and **Difference** work as in v1: medians across people, after summarizing each person.
- **Holm p** corrects for running 5 CGMacros tests at once. A test passes when Holm p is below 0.05.
- **D1NAMO rows are exploratory.** Only 8 of 19 people had enough reliable strap data, under the planned minimum of 10, so they stay out of the corrected tests.

**What it means.**

- **Glucose passes again.** A real meal outscores a placebo moment 82% of the time, and glucose rises more after real meals for 31 of 31 people, so meal times line up with the sensors.
- **A small heart rate response shows up.** From 30 to 120 minutes after eating, heart rate was higher after real meals for 23 of 31 people, by a median of +2.8 bpm. With movement removed, it was higher for 20 of 23 people (+3.3 bpm), and a real meal wins 67% of the time.
- **The peak needs movement removed.** On raw heart rate, the 3-hour peak fails (58%, p = 0.09). With movement removed it passes (65%). As in v1, the peak mostly tracks movement.
- **This fits v1 instead of contradicting it.** v1's 15 people could only detect an average difference of about 4 bpm. CGMacros has 31 people and can detect about 3 bpm, and the response it finds sits below v1's limit. v1's movement-removed average already leaned the same way (61%).
- **Too small to read one meal.** A real meal winning 59% of comparisons is a pattern across many meals. One meal's heart rate can't tell you whether you ate.
- **The chest strap leans the same way, without proof.** Heart rate average: 63% (+5.6 bpm). With movement removed: 87%, higher for 6 of 8 people. Peak: 46%. With 8 people, this is a hint for a bigger chest strap study, not a result.

### How v2 differs from v1

- **Same rules where possible:** meal grouping, clean windows, placebo moments, scores and statistics all match v1.
- **Placebo moments only where the sensor recorded the whole window.** The chest strap was off every night, so v2 draws placebo moments only from times with enough readings.
- **Clock window chosen from counts:** the smallest of ±60, ±90 and ±120 minutes that keeps 10 people. CGMacros uses ±60 minutes (759 clean meals, 1,722 placebo moments). D1NAMO never reached 10 people, so it uses ±120 minutes (53 clean meals, 121 placebo moments).
- **Movement:** the strap's activity level (D1NAMO) and the smartwatch's METs (CGMacros) replace wrist acceleration. 24 of 31 CGMacros people have movement data, since some files record activity intensity instead of METs.
- **Checks:**
  - CGMacros clocks run on local time: 28 of 31 people have their lowest heart rate between 1 and 7 am.
  - D1NAMO has no continuous glucose, so it gets a meal-timing check instead of a positive control. Finger-prick glucose rose after meals for 18 of 19 people (median +0.5 mmol/L, p < 0.001), and 80% of before/after pairs have a logged meal between them.

### Robustness (v2)

- **Different random draws of placebo moments** (10 draws), CGMacros: 80% to 85% for glucose, 55% to 58% for heart rate peak, 57% to 61% for heart rate average and 67% to 69% for the movement-removed average.
- **All 45 CGMacros participants**, type 2 diabetes included: 82% for glucose, 55% for heart rate peak, 56% for heart rate average and 65% for the movement-removed average.

### Limitations (v2)

- **Different people, devices and studies.** v1, CGMacros and D1NAMO used different sensors on different groups, so the chart compares results side by side, not sensors head-to-head.
- **Protocol meals.** CGMacros breakfasts were shakes and lunches were set meals, each at least 3 hours after the last, with only water or unsweetened coffee in between. Cleaner meals than v1's free-living ones may make a small response easier to see.
- **Small, patchy chest data.** The strap often lost skin contact, and it flags those readings as unreliable. For some people, most readings were flagged, which is why D1NAMO fell short of 10 people.
- **No glucose control for the chest strap.** Finger pricks show that meal times line up, but not that this test could detect a known effect in D1NAMO.
- **Not medical advice.** The same general wellness framing as v1 applies.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/download.py
.venv/bin/python src/motion.py
.venv/bin/python src/download_v2.py
.venv/bin/python run_all.py
```

`src/motion.py` streams the 13 GB of raw accelerometer files once, checks each against its published checksum and keeps a per-minute movement summary of about 7 MB.

`src/download_v2.py` reads only the needed files out of the D1NAMO and CGMacros archives with HTTP range requests and checks each file's CRC-32.

`run_all.py` writes `results/metrics.json`, `results/per_participant.csv`, `results/v2/`, the figures and this README. Every result above comes from that run. To run the tests: `.venv/bin/python -m pytest -q`.

## Data and credit

- Cho P, Kim J, Bent B, Dunn J. *BIG IDEAs Lab Glycemic Variability and Wearable Device Data* (version 1.1.3). PhysioNet, 2026. https://doi.org/10.13026/aw6y-fc44
- Bent B, Cho PJ, Henriquez M, et al. Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine* 4, 89 (2021).
- Goldberger A, et al. PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 101(23): e215-e220 (2000).
- Dubosson F, Ranvier JE, Bromuri S, Calbimonte JP, Ruiz J, Schumacher M. *The open D1NAMO dataset* (version 1.2.0). Zenodo, 2018. https://doi.org/10.5281/zenodo.5651217
- Dubosson F, et al. The open D1NAMO dataset: A multi-modal dataset for research on non-invasive type 1 diabetes management. *Informatics in Medicine Unlocked* 13, 92-100 (2018). https://doi.org/10.1016/j.imu.2018.09.003
- Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring* (version 1.0.0). PhysioNet, 2025. https://doi.org/10.13026/3z8q-x658
- Das A, Kerr D, Glanz N, Bevier W, Santiago R, Gutierrez-Osuna R, Mortazavi B. CGMacros: a scientific dataset for personalized nutrition and diet monitoring. *Scientific Data* (under review).

BIG IDEAs is under the Open Data Commons Attribution License v1.0, D1NAMO under CC BY-SA 4.0 and CGMacros under CC BY-NC-SA 4.0. None of the raw data is included in this repository. Results derived from D1NAMO (`results/v2/`, D1NAMO rows) are shared under CC BY-SA 4.0, and results derived from CGMacros under CC BY-NC-SA 4.0. The code is MIT licensed.

Built by [Kawsar Nabawi](https://kawsarnabawi.com).
