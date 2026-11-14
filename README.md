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

## Run

```
pip install -r requirements.txt
copy .env.example .env   # then put your key in .env
python -m uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```
