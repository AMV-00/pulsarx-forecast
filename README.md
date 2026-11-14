# PulsarX Forecast

NOVA asks the astronaut daily about sleep, fatigue, mood and stress. A transparent model predicts fatigue risk (low / medium / high). The system suggests schedule changes (postpone, reorder, longer rest, reassign) with a reason and expected effect for each, and the ground team approves (accept / edit / reject).

- Claude only talks and phrases sentences. Every number comes from the transparent model.
- All demo data is simulated and labeled "Simulated".
- Model factors are based on NASA HRP evidence on sleep loss, circadian desynchronization and work overload.

## Run

```
pip install -r requirements.txt
copy .env.example .env   # then put your key in .env
uvicorn app.main:app --reload
```
