from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.data import store
from app.data.simulate import CREW, LABEL, free_minutes, generate_schedule, generate_states
from app.explain.templates import polish, reason_sentence
from app.fallback.answers import answer
from app.model.risk import predict
from app.nova.extract import extract
from app.nova.questions import next_question
from app.schedule.rules import suggest_changes

app = FastAPI(title="PulsarX Forecast")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class CheckinText(BaseModel):
    text: str


class Checkin(BaseModel):
    crew: str
    sleep_hours: float | None = None
    fatigue: int | None = None
    mood: str | None = None
    stress: int | None = None
    hedging: bool = False


class SuggestRequest(BaseModel):
    facts: dict
    tasks: list[dict]
    crew_free: dict = {}
    mars_mode: bool = False
    lang: str = "en"
    use_claude: bool = True


class Decision(BaseModel):
    change_id: str
    decision: str          # accept | edit | reject
    note: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- data ----------
@app.post("/simulate")
def simulate(seed: int = 1):
    """Make fresh simulated schedules + states and save them as the 'original'."""
    schedules = {c: generate_schedule(c, seed) for c in CREW}
    store.save("schedule_original", schedules)
    store.save("states", generate_states(seed=seed))
    store.save("schedule_proposed", {})
    store.save("decisions", [])
    return {"label": LABEL, "crew": CREW, "schedules": schedules}


@app.get("/schedule/{crew}")
def schedule(crew: str):
    original = store.load("schedule_original", {})
    if crew not in original:
        raise HTTPException(404, "Run /simulate first")
    return {"label": LABEL, "original": original[crew],
            "proposed": store.load("schedule_proposed", {}).get(crew, [])}


# ---------- NOVA ----------
@app.get("/nova/first-question")
def first_question(lang: str = "en"):
    return {"greeting": answer("greeting", lang), "question": next_question({})}


@app.post("/nova/extract")
def nova_extract(body: CheckinText):
    answers = extract(body.text)
    return {"answers": answers, "next_question": next_question(answers)}


@app.post("/checkin")
def checkin(body: Checkin):
    """Log today's state (NOVA answers) into the health log."""
    return store.append("health_log", body.model_dump())


# ---------- prediction + suggestion ----------
@app.post("/predict/{crew}")
def predict_crew(crew: str, day: int = 1, mars_mode: bool = False, lang: str = "en", use_claude: bool = True):
    states = [s for s in store.load("states", []) if s["crew"] == crew and s["day"] == day]
    if not states:
        raise HTTPException(404, "Run /simulate first")
    state = dict(states[0])
    log = [c for c in store.load("health_log", []) if c["crew"] == crew]
    if log:  # latest NOVA answers override simulated self-report
        state.update({k: v for k, v in log[-1].items() if v is not None and k in ("sleep_hours", "fatigue", "mood", "stress")})
    facts = predict(state)

    original = store.load("schedule_original", {})
    changes = suggest_changes(facts["level"], original.get(crew, []), {k: v for k, v in free_minutes(original).items()}, mars_mode)
    for i, c in enumerate(changes):
        c["id"] = f"{crew}-d{day}-c{i + 1}"
        sentence = reason_sentence(c, facts, lang)
        c["reason"] = polish(sentence, lang=lang) if use_claude else sentence
        c["status"] = "pending"
    proposed = store.load("schedule_proposed", {})
    proposed[crew] = changes
    store.save("schedule_proposed", proposed)
    return {"label": LABEL, "state": state, "prediction": facts,
            "summary": answer(f"risk_{facts['level']}", lang), "changes": changes}


@app.post("/suggest")
def suggest(body: SuggestRequest):
    level = body.facts["level"]
    changes = suggest_changes(level, body.tasks, body.crew_free, body.mars_mode)
    for c in changes:
        sentence = reason_sentence(c, body.facts, body.lang)
        c["reason"] = polish(sentence, lang=body.lang) if body.use_claude else sentence
        c["status"] = "pending"
    return {"summary": answer(f"risk_{level}", body.lang), "changes": changes}


# ---------- ground team ----------
@app.post("/decision")
def decision(body: Decision):
    if body.decision not in ("accept", "edit", "reject"):
        raise HTTPException(400, "decision must be accept, edit or reject")
    proposed = store.load("schedule_proposed", {})
    for changes in proposed.values():
        for c in changes:
            if c.get("id") == body.change_id:
                c["status"] = body.decision
                c["note"] = body.note
                store.save("schedule_proposed", proposed)
                return store.append("decisions", body.model_dump())
    raise HTTPException(404, "change not found")
