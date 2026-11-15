# FORECAST by PulsarX

**[NASA Space Apps Challenge 2026](https://www.spaceappschallenge.org/) · Challenge: Create Health Monitoring Software for Astronauts on Space Missions**

FORECAST predicts an astronaut's fatigue and readiness for the next 3 days, before it becomes a problem. A smart ring measures sleep, heart rate, HRV, skin temperature and activity. A Readiness Digital Twin compares each day with the astronaut's own normal, the forecast is checked against the mission schedule, and NOVA explains the result in plain words and suggests schedule changes. The astronaut and Mission Control decide. It runs onboard without a link to Earth and syncs when the link returns.

## How it answers the challenge

Built on the challenge's NASA resources: *Risks of Human Spaceflight* and *5 Hazards of Human Spaceflight* (NASA Human Research Program).

| NASA hazard / risk | What FORECAST does |
| --- | --- |
| HRP risk: performance decrements from **sleep loss, circadian desynchronization and work overload** | The transparent model scores exactly these factors (sleep, body clock, hours awake, workload, focus test) and links them to critical tasks such as EVA |
| **Distance from Earth** | Works fully onboard. Mars mode: when Earth is too far for a quick answer, the commander approves a change and Earth confirms after sync |
| **Isolation and confinement** | Daily NOVA check-in (text or voice). A "hidden fatigue" flag goes to human review when the words sound better than the body signals |
| **Gravity fields** | Each astronaut is compared with a personal baseline learned in space, because normal values change in microgravity |
| **Hostile, closed environment** | Ring data stays on the station; only a summary goes to Mission Control |
| **Radiation** | Not covered yet. Future work: add dosimeter data to the twin |

- Claude (NOVA) only talks and phrases sentences. Every number comes from the transparent model, and a test checks that NOVA never invents numbers.
- Sleep, heart rate and activity are real Fitbit days (Furberg et al. 2016, Zenodo 53894). HRV, skin temperature, focus and the schedule are simulated and labeled.
- **Real-data test** ([docs/real-data-test.md](docs/real-data-test.md)): on 21 real Fitbit days, with no simulated signal, readiness after short sleep averaged 84.8% vs 93.8% on other days. The data has no fatigue labels, so this checks behaviour, not accuracy. Run `python scripts/real_data_test.py`.

## Screens

Open http://127.0.0.1:8000 after starting the server.

| Screen | For | What it shows |
| --- | --- | --- |
| **Overview** | Mission Control big screen, demo | Crew readiness today, 3D smart ring with live signals, astronaut hologram twin, 7-day history + 3-day forecast, NOVA summary |
| **Astronaut** | The astronaut, on a tablet | My readiness today, quick focus test, NOVA chat (text or voice), next 3 days with critical tasks, suggested changes to accept or reject |
| **Mission Control** | Flight surgeon and ground team | Side menu: Overview (crew table, 3-day schedule, approvals with "Try" what-if), Twin (3D ring, 8 signals vs personal normal), Forecast (chart + critical tasks), Earth (ISS / Moon / Mars link, outbox, Earth confirm or overrule) |

## NOVA through the ring

Each morning NOVA asks one question out loud ("How did you sleep?"). The astronaut taps the ring and answers by voice, without opening a screen. NOVA turns the answer into numbers (sleep hours, fatigue level) and adds them to the forecast. In the demo the computer microphone stands in for the ring microphone. NOVA also speaks up on its own when a critical task falls on a low-readiness day.

## Voice tone check

The browser measures speech rate, pauses, pitch variation and loudness, and compares them with the astronaut's own normal voice. Two or more changes raise a note for a human. It never changes the readiness score, and no audio is stored.

## Display design

Alerts follow NASA-STD-3001 Vol. 2: red only for warnings, yellow for caution, plain words, large buttons and an Acknowledge step. See [docs/nasa-design-standard.md](docs/nasa-design-standard.md).

## Tests

48 automated tests (`python -m pytest`), including a check that NOVA's sentences never contain numbers the model did not produce.

## Run

```
pip install -r requirements.txt
copy .env.example .env   # then put your key in .env
python -m uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```
