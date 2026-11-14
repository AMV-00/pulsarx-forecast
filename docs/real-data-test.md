# Real-data test

The transparent model was run on **real Fitbit days only** (3 real users, Furberg et al. 2016, Zenodo 53894).
No simulated signal and no task schedule were used. For each day after the 7-day personal baseline,
the model predicted readiness using only the days before it.

| Check | Result |
| --- | --- |
| Real days predicted | 21 (all ran without errors) |
| Average readiness after short sleep (3-night sleep debt of 1.5 h or more vs own normal) | 84.8% (12 days) |
| Average readiness on other days | 93.8% (9 days) |

**Limit:** this dataset has no fatigue labels, so the test checks that the model behaves as designed on real
human data, not how accurate it is. Accuracy needs spaceflight data with fatigue or performance measures
(next step: NASA Open Science Data Repository).

| User | Day | Date | Sleep night before (h) | Own normal (h) | 3-night sleep debt (h) | Readiness | Level | Points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 8 | 2016-04-22 | 6.9 | 7.6 | 0.9 | 93% | low | wake 1 |
| A | 9 | 2016-04-23 | 5.6 | 7.6 | 2.8 | 86% | low | sleep 1, wake 1 |
| A | 10 | 2016-04-24 | 6.4 | 7.6 | 3.9 | 79% | low | sleep 2, wake 1 |
| A | 11 | 2016-04-25 | 9.1 | 7.6 | 3.2 | 86% | low | sleep 2 |
| A | 12 | 2016-04-26 | 7.0 | 7.6 | 1.8 | 86% | low | sleep 1, wake 1 |
| A | 13 | 2016-04-27 | 5.9 | 7.6 | 2.3 | 86% | low | sleep 1, wake 1 |
| A | 14 | 2016-04-28 | 7.1 | 7.6 | 2.8 | 86% | low | sleep 1, wake 1 |
| B | 8 | 2016-05-01 | 7.0 | 7.37 | 0.6 | 93% | low | wake 1 |
| B | 9 | 2016-05-02 | 6.8 | 7.37 | 1.1 | 93% | low | wake 1 |
| B | 10 | 2016-05-03 | 7.8 | 7.37 | 0.9 | 93% | low | body 1 |
| B | 11 | 2016-05-04 | 6.6 | 7.37 | 1.3 | 93% | low | wake 1 |
| B | 12 | 2016-05-05 | 7.4 | 7.37 | 0.8 | 93% | low | wake 1 |
| B | 13 | 2016-05-06 | 7.8 | 7.37 | 0.8 | 100% | low | none |
| B | 14 | 2016-05-07 | 7.4 | 7.37 | 0.0 | 93% | low | wake 1 |
| C | 8 | 2016-04-21 | 11.0 | 8.06 | 2.1 | 93% | low | sleep 1 |
| C | 9 | 2016-04-22 | 6.7 | 8.06 | 3.4 | 79% | low | sleep 2, wake 1 |
| C | 10 | 2016-04-23 | 5.4 | 8.06 | 4.0 | 71% | medium | sleep 2, wake 2 |
| C | 11 | 2016-04-24 | 10.5 | 8.06 | 4.0 | 86% | low | sleep 2 |
| C | 12 | 2016-04-25 | 9.2 | 8.06 | 2.7 | 93% | low | sleep 1 |
| C | 13 | 2016-04-26 | 7.2 | 8.06 | 0.9 | 93% | low | wake 1 |
| C | 14 | 2016-04-27 | 6.9 | 8.06 | 2.0 | 86% | low | sleep 1, wake 1 |
