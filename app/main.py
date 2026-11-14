"""PulsarX FORECAST server: simulated Smart Ring -> personal baseline ->
readiness forecast linked to tasks -> NOVA explains -> what-if -> Mission Control."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.data import store
from app.data.simulate import CREW, DAYS, LABEL as SIM_LABEL, REAL_SOURCE, free_minutes, generate_ring, generate_schedules, load_real

# Real Fitbit values when data/real/fitbit_daily.csv exists; HRV, temperature and schedule stay simulated.
LABEL = "Real + simulated" if load_real() else SIM_LABEL
from app.explain.templates import polish, reason_sentence
from app.fallback.answers import answer
from app.model.forecast import forecast
from app.model.twin import build_twin
from app.model.whatif import what_if
from app.nova.extract import extract
from app.nova.questions import LOW_CONFIDENCE, MORNING
from app.schedule.rules import suggest_changes

app = FastAPI(title="PulsarX FORECAST")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class CheckinText(BaseModel):
    crew: str
    text: str


class WhatIfRequest(BaseModel):
    day: int
    change_ids: list[str]


class Decision(BaseModel):
    change_id: str
    decision: str  # accept | edit | reject
    note: str = ""


# ---------- helpers ----------
def _ring(crew: str) -> list[dict]:
    ring = [r for r in store.load("ring", []) if r["crew"] == crew]
    if not ring:
        raise HTTPException(404, "Run /simulate first")
    return ring


def _schedules() -> dict:
    return store.load("schedule_original", {})


def _self_report(crew: str) -> dict | None:
    log = [c for c in store.load("health_log", []) if c["crew"] == crew]
    return log[-1] if log else None


WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.is_dir():
    app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/web/dashboard/")


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- data ----------
@app.post("/simulate")
def simulate(seed: int = 1):
    """Fresh simulated ring data (14 days) + schedules; resets suggestions and decisions."""
    store.save("ring", generate_ring(seed=seed))
    store.save("schedule_original", generate_schedules(seed))
    for name in ("suggestions", "decisions", "health_log"):
        store.save(name, [] if name != "suggestions" else {})
    return {"label": LABEL, "crew": CREW, "today": DAYS}


@app.get("/ring/{crew}")
def ring(crew: str):
    return {"label": LABEL, "source": REAL_SOURCE if load_real() else "FORECAST Smart Ring (simulated)", "days": _ring(crew)}


@app.get("/model/{crew}")
def model_view(crew: str):
    """Everything the transparent model used for one crew: ring days, personal baseline,
    today's inputs and the points of every factor per forecast day."""
    readings = _ring(crew)
    f = forecast(readings, _schedules().get(crew, {}), DAYS, self_report=_self_report(crew))
    return {**f, "label": LABEL, "crew": crew, "mission_day": DAYS, "max_points": 12,
            "ring": sorted(readings, key=lambda r: r["day"])}


@app.get("/twin/{crew}")
def twin(crew: str):
    """Readiness Digital Twin: personal baseline + today's signals + 3-day readiness forecast."""
    return {"label": LABEL, **build_twin(crew, _ring(crew), _schedules().get(crew, {}), DAYS, _self_report(crew))}


@app.get("/schedule/{crew}/{day}")
def schedule(crew: str, day: int):
    return {"label": LABEL, "tasks": _schedules().get(crew, {}).get(str(day), [])}


# ---------- NOVA ----------
@app.get("/nova/morning/{crew}")
def nova_morning(crew: str, lang: str = "en"):
    """One spoken question at breakfast; a fatigue number only if the ring data is unclear."""
    f = forecast(_ring(crew), _schedules().get(crew, {}), DAYS)
    unsure = f["unknown"] or f["confidence"] != "high"
    return {"question": LOW_CONFIDENCE[lang] if unsure else MORNING[lang], "confidence": f["confidence"]}


@app.post("/nova/answer")
def nova_answer(body: CheckinText):
    """Astronaut's spoken answer (as text) -> mood / stress / fatigue, saved to the health log."""
    answers = extract(body.text)
    entry = store.append("health_log", {"crew": body.crew, **answers})
    hedge = answer("hedging") if answers.get("hedging") else None
    return {"answers": entry, "nova_note": hedge}


# ---------- forecast + suggestions ----------
@app.get("/forecast/{crew}")
def forecast_crew(crew: str, lang: str = "en", use_claude: bool = True, mars_mode: bool = False):
    readings, sch = _ring(crew), _schedules()
    me = sch.get(crew, {})
    rep = _self_report(crew)
    f = forecast(readings, me, DAYS, self_report=rep)
    if f["unknown"]:
        return {"label": LABEL, **f}

    # Act on the worst upcoming day (an alert day first).
    worst = sorted(f["days"], key=lambda d: (not d["alert"], -d["score"]))[0]
    day = worst["day"]
    others = {c: sch[c].get(str(day), []) for c in CREW}
    # Only hand tasks to crew members who are free AND forecast as ready (low risk) that day.
    ready = set()
    for c in CREW:
        if c == crew:
            continue
        fc = forecast(_ring(c), sch.get(c, {}), DAYS, self_report=_self_report(c))
        d = next((x for x in fc.get("days", []) if x["day"] == day), None)
        if d and d["level"] == "low":
            ready.add(c)
    free = {c: m for c, m in free_minutes(others).items() if c in ready}
    changes = suggest_changes(worst["level"], me.get(str(day), []), free, mars_mode)

    for i, c in enumerate(changes):
        c["id"] = f"{crew}-d{day}-c{i + 1}"
        effect = what_if(readings, me, DAYS, day, [c], rep)
        facts = {"level": worst["level"], "top_factor": worst["top_factor"],
                 "sleep_hours": f["today"]["sleep_hours"],
                 "readiness_before": effect["readiness_before"], "readiness_after": effect["readiness_after"]}
        sentence = reason_sentence(c, facts, lang)
        c["reason"] = polish(sentence, lang=lang) if use_claude else sentence
        c["effect"] = effect
        c["status"] = "pending"

    all_sug = store.load("suggestions", {})
    all_sug[crew] = changes
    store.save("suggestions", all_sug)
    combined = what_if(readings, me, DAYS, day, changes, rep) if changes else None
    return {"label": LABEL, "forecast": f, "focus_day": day,
            "summary": answer(f"risk_{worst['level']}", lang), "changes": changes, "all_changes_effect": combined}


@app.post("/whatif/{crew}")
def whatif(crew: str, body: WhatIfRequest):
    """Try some suggested changes together and see readiness before/after (nothing is saved)."""
    chosen = [c for c in store.load("suggestions", {}).get(crew, []) if c["id"] in body.change_ids]
    if not chosen:
        raise HTTPException(404, "No such changes; call /forecast first")
    return what_if(_ring(crew), _schedules().get(crew, {}), DAYS, body.day, chosen, _self_report(crew))


# ---------- decisions + Mission Control ----------
@app.post("/decision")
def decision(body: Decision):
    if body.decision not in ("accept", "edit", "reject"):
        raise HTTPException(400, "decision must be accept, edit or reject")
    sug = store.load("suggestions", {})
    for changes in sug.values():
        for c in changes:
            if c.get("id") == body.change_id:
                c["status"], c["note"] = body.decision, body.note
                store.save("suggestions", sug)
                return store.append("decisions", body.model_dump())
    raise HTTPException(404, "change not found")


@app.get("/mission-control/summary")
def mission_summary():
    """Periodic report for Mission Control. The system does not wait for it to act on board."""
    sch, sug, out = _schedules(), store.load("suggestions", {}), []
    for crew in CREW:
        f = forecast(_ring(crew), sch.get(crew, {}), DAYS, self_report=_self_report(crew))
        if f["unknown"]:
            out.append({"crew": crew, "status": "unknown"})
            continue
        low = min(f["days"], key=lambda d: d["readiness"])
        out.append({"crew": crew, "lowest_readiness": low["readiness"], "on_day": low["day"],
                    "level": low["level"], "alert": any(d["alert"] for d in f["days"]),
                    "critical_tasks": low["critical_tasks"],
                    "pending_changes": [c["id"] for c in sug.get(crew, []) if c["status"] == "pending"]})
    return {"label": LABEL, "today": DAYS, "crew": out}
