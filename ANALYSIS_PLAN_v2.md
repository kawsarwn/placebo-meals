# Analysis plan, v2

I wrote this plan on 2026-10-24, before downloading any v2 heart rate, breathing or CGMacros data. v1's rules in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) stay as they are. Any change after this commit goes under "Deviations" with a date.

## Questions

1. **Main:** in a chest-strap dataset (D1NAMO), does heart rate after real meals differ from heart rate after placebo moments? Then the same for breathing rate, if enough people have usable breathing data.
2. **Replication:** in a second wrist dataset (CGMacros), does wrist heart rate fail the placebo test again, while glucose passes?

The datasets have different people, devices and study designs, so v2 compares results side by side. It doesn't test wrist against chest within the same people. No public dataset I found has both sensors on the same people with timestamped meals.

## What I looked at before writing this

To check that D1NAMO could support the test, I read its food logs, its archive file lists, finger-prick glucose values for 4 people (while checking the file format) and two rows of one chest-strap summary file. I counted clean meals and placebo moments from meal times and recording lengths. I have not seen any other heart rate, breathing or activity values, or any CGMacros file.

## Data

- **D1NAMO** ([Zenodo, v1.2.0](https://doi.org/10.5281/zenodo.5651217), CC BY-SA 4.0; Dubosson et al. 2018):
  - Healthy group only. I leave out folder `012_diabetes`, which sits in the healthy subset but has glucose readings up to 19.7 mmol/L. That leaves 19 people.
  - I leave out the type 1 diabetes group: insulin changes the meal response, and the meal-time counts left at most 3 people with 3 clean meals.
  - Chest strap (Zephyr BioHarness 3): the per-second summary file for each recording session. The strap was worn from morning to night, about 4 days per person.
  - Food log: every row with a date and time counts as eating, photographed meals and text-only snacks and drinks alike, as in v1.
  - The strap's annotations file marks "problem" periods, like a misplaced harness. I drop all strap data inside them.
- **CGMacros** ([PhysioNet, v1.0.0](https://physionet.org/content/cgmacros/1.0.0/), CC BY-NC-SA 4.0):
  - Main sample: people with HbA1c below 6.5% (no diabetes or prediabetes), the range closest to v1. The type 2 diabetes group joins only in a sensitivity check, because the dataset doesn't record diabetes medication, which can change glucose.
  - Wrist heart rate from the smartwatch, Dexcom glucose and meal times. I'll confirm the column names at download. If the file spreads Dexcom readings over every minute, I take 5-minute means so glucose keeps v1's 5-minute step.
  - Every meal record counts as eating.

## Signals

- **D1NAMO heart rate:** the strap's per-second heart rate. I keep seconds with heart rate confidence of at least 80 and heart rate from 30 to 220 bpm, then take the per-minute mean. A minute needs 40 valid seconds (2/3).
- **D1NAMO breathing rate:** the same, with breathing rate confidence of at least 80 and a rate from 4 to 60 breaths per minute.
- **CGMacros heart rate:** per-minute smartwatch heart rate.
- **CGMacros glucose:** Dexcom, 5-minute step.

## Meals, placebo moments and scores

These match v1 exactly:

- Food items logged within 30 minutes of each other form one meal.
- A moment is clean when nothing was logged from 2 hours before to 3 hours after it. Meals and placebo moments follow the same rule.
- 5 placebo moments per clean meal from a 5-minute grid, each on a different date from its meal and used once, with seed 0.
- The search period runs from the later of the first food log entry and the first sensor reading to the earlier of the last ones.
- Peak: the highest value from 0 to 180 minutes after the moment, minus the mean of the 30 minutes before. Average: the mean from 30 to 120 minutes after, minus the same baseline. Each window needs 2/3 of its expected readings.

Two changes, with reasons:

- **Coverage before drawing.** The chest strap was off every night, so most grid times have no data. A placebo moment is drawn only from times where the dataset's main signals meet the 2/3 coverage rule in both the 30 minutes before and the 3 hours after: heart rate for D1NAMO, heart rate and glucose for CGMacros. v1 dropped uncovered windows after drawing them. Here that would waste most draws.
- **Clock window, chosen from counts.** People in both datasets eat at regular times, so placebo moments within 60 minutes of a meal's clock time can run short. For each dataset, I use the smallest of ±60, ±90 and ±120 minutes that leaves at least 10 included people. The choice uses only counts of meals and placebo moments with valid windows, never signal values, the same way v1 chose its still threshold. If no window reaches 10, I use ±120 minutes and label that dataset's results exploratory.

## Inclusion

- A person needs at least 3 clean meals and 2 placebo moments with valid windows on the dataset's main signals.
- A dataset needs at least 10 included people for its tests to count. With Holm correction over about 11 tests, a Wilcoxon test on 8 people can't get below the strictest threshold even if all 8 respond.
- **Breathing rate** joins the tests only if at least 10 people meet the inclusion rule with valid breathing windows.

## Movement

- Same model as v1: one linear model per person predicts per-minute heart rate from movement now, mean movement over the previous 5 minutes and mean movement over the 10 minutes before that. It is fit on minutes at least 3 hours after any logged food, and the leftover heart rate goes through the same placebo test.
- **Movement input:** the chest strap's activity level, averaged per minute (D1NAMO), and the smartwatch's per-minute METs (CGMacros). These replace v1's wrist acceleration.
- **New minimum:** a person needs at least 300 fitting minutes for the movement-removed tests, since the strap has no night data.
- v1's still-period check is not repeated. It was exploratory and didn't reach its own minimum.

## Positive controls

- **CGMacros:** the glucose peak goes through the placebo test, as in v1.
- **D1NAMO:** no continuous glucose, so no placebo-tested control. A meal-timing check takes its place. For each same-day before/after finger-prick pair (before and after breakfast, lunch and dinner), I record the rise and whether a meal was logged between the two readings. Each person's mean rise is tested across people with a Wilcoxon signed-rank test. This shows that meal times line up with the body's response. It does not show that the placebo test can detect an effect in this dataset.

## Summary, correction and pass

- Per person: mean real-meal score minus mean placebo score, and the chance a real meal outscores a placebo moment (win rate). Across people: the median win rate, the count of positive differences and a two-sided Wilcoxon signed-rank test.
- Detection limit: the smallest average difference a paired t-test would detect at 80% power and alpha 0.05, as in v1.
- **Tests, all corrected together with Holm:**
  1. D1NAMO chest heart rate peak
  2. D1NAMO chest heart rate average
  3. D1NAMO chest heart rate peak, movement removed
  4. D1NAMO chest heart rate average, movement removed
  5. D1NAMO chest breathing rate peak (if usable)
  6. D1NAMO chest breathing rate average (if usable)
  7. CGMacros wrist heart rate peak
  8. CGMacros wrist heart rate average
  9. CGMacros wrist heart rate peak, movement removed
  10. CGMacros wrist heart rate average, movement removed
  11. CGMacros glucose peak (positive control)
- **Pass:** Holm-adjusted p below 0.05. I report the direction with every result. A fail is read against the detection limit: it rules out effects above the limit, not smaller ones.
- The D1NAMO meal-timing check is a data check and stays outside the corrected tests.

## Extra checks (not corrected, labeled in the README)

- 10 placebo draws (seeds 0 to 9): the range of win rates.
- D1NAMO with a ±120-minute clock window, if the main window is smaller.
- CGMacros with all participants, type 2 diabetes included.

## Outputs

- One table: dataset, sensor, signal, score, people, win rate, raw p, Holm p, pass or fail, detection limit.
- One chart: per-person win rates for glucose (v1, CGMacros) and heart rate (v1 wrist, CGMacros wrist, D1NAMO chest), plus breathing rate (D1NAMO chest). v1 appears for reference and isn't retested.
- Results derived from D1NAMO are shared under CC BY-SA 4.0 and results derived from CGMacros under CC BY-NC-SA 4.0, as their licenses require.

## Window counts (2026-10-24, before any outcome)

`src/v2.py --counts` applied the count-only rules. It reads which windows have enough readings, never their values.

- **D1NAMO:** 8 of 19 people meet the inclusion rule at ±60, ±90 and ±120 minutes alike, below the minimum of 10. Following the plan, D1NAMO uses ±120 minutes and its results are exploratory: they're reported but leave the corrected tests. Breathing rate also reaches 8 people, so it isn't tested. The included people have 53 clean meals and 121 placebo moments.
  - The cause is strap contact. The share of strap minutes with a confident heart rate ranges from 2% to 98% per person, and two people are under 5%. Lowering the confidence cutoff to 50 would add one person, so I kept it.
- **CGMacros:** 31 people in the main sample, all 31 included at ±60 minutes, with 759 clean meals and 1,722 placebo moments. 24 qualify for the movement-removed tests.
- **Corrected tests:** the five CGMacros tests (heart rate peak and average, both with movement removed, and glucose).

## Deviations

- **2026-10-24, data notes, no rule changes:**
  - 11 of 45 CGMacros files have a smartwatch intensity level instead of METs. Those people have no movement input, so they have no fitting minutes and skip the movement-removed tests, as the 300-minute rule implies.
  - CGMacros spreads Dexcom readings over every minute, so the 5-minute means from the plan apply.
  - Zenodo and PhysioNet served the full archives slowly, so `src/download_v2.py` reads only the needed files out of them with HTTP range requests. Each file is checked against its CRC-32 instead of the archive-wide checksum.
