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
from app.model.forecast import MAX_POINTS, forecast
from app.model.twin import build_twin
from app.model.whatif import what_if
from app.nova.extract import extract
from app.nova.questions import LOW_CONFIDENCE, MORNING
from app.schedule.rules import suggest_changes
from app import onboard

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


class LinkState(BaseModel):
    online: bool | None = None
    place: str | None = None  # iss | moon | mars


class FocusResult(BaseModel):
    crew: str
    mean_rt_ms: float  # mean reaction time of today's test


class Confirm(BaseModel):
    change_id: str
    confirm: bool
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
    for name in ("suggestions", "decisions", "health_log", "outbox"):
        store.save(name, [] if name != "suggestions" else {})
    onboard.set_link(online=True, place="iss")
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
    return {**f, "label": LABEL, "crew": crew, "mission_day": DAYS, "max_points": MAX_POINTS,
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
    f = forecast(_ring(body.crew), _schedules().get(body.crew, {}), DAYS, self_report=entry)
    worst = min(f["days"], key=lambda d: d["readiness"]) if not f["unknown"] else None
    check = onboard.hidden_fatigue(answers, worst)
    if check["flag"]:
        hedge = answer("hedging")
        onboard.queue("hidden_fatigue", {"crew": body.crew, "text": body.text, "why": check["why"]})
    return {"answers": entry, "nova_note": hedge, "hidden_fatigue": check}


# ---------- forecast + suggestions ----------
@app.get("/forecast/{crew}")
def forecast_crew(crew: str, lang: str = "en", use_claude: bool = True, mars_mode: bool | None = None):
    if mars_mode is None:
        mars_mode = onboard.mars_mode()
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

    old = {c["id"]: c for c in store.load("suggestions", {}).get(crew, [])}
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
        c["mars_mode"] = mars_mode
        prev = old.get(c["id"])
        if prev and prev.get("status") != "pending" and prev.get("type") == c["type"] \
                and prev.get("task_id") == c["task_id"]:
            # Same suggestion as before: keep the decision already taken (and who took it).
            for k in ("status", "note", "provisional", "confirmed", "mars_mode", "approver"):
                if k in prev:
                    c[k] = prev[k]

    all_sug = store.load("suggestions", {})
    all_sug[crew] = changes
    store.save("suggestions", all_sug)
    combined = what_if(readings, me, DAYS, day, changes, rep) if changes else None
    return {"label": LABEL, "forecast": f, "focus_day": day, "mars_mode": mars_mode, "link": onboard.link(),
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
                # Mars mode: the commander's decision counts now, Mission Control confirms later.
                c["provisional"] = bool(c.get("mars_mode")) and body.decision != "reject"
                store.save("suggestions", sug)
                rec = store.append("decisions", {**body.model_dump(), "provisional": c["provisional"],
                                                 "by": "commander" if c.get("mars_mode") else "crew"})
                onboard.queue("decision", {**rec, "task": c.get("task"), "type": c.get("type")})
                onboard.sync()  # goes out now if the link is up, else waits in the outbox
                return rec
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
    q = onboard.outbox()
    return {"label": LABEL, "today": DAYS, "crew": out, "link": onboard.link(), "mars_mode": onboard.mars_mode(),
            "waiting_to_sync": sum(1 for i in q if not i["synced"])}


# ---------- onboard: link, sync, focus test ----------
@app.get("/link")
def get_link():
    q = onboard.outbox()
    return {**onboard.link(), "mars_mode": onboard.mars_mode(), "waiting": sum(1 for i in q if not i["synced"]),
            "sent": sum(1 for i in q if i["synced"]), "places": onboard.PLACES}


@app.post("/link")
def post_link(body: LinkState):
    """Simulate losing/regaining the Earth link or moving the mission (ISS, Moon, Mars)."""
    onboard.set_link(body.online, body.place)
    result = onboard.sync() if onboard.link()["online"] else None
    return {**get_link(), "just_synced": result}


@app.get("/outbox")
def get_outbox():
    """Onboard outbox: what is waiting for Earth and what was already sent."""
    return onboard.outbox()


@app.post("/sync")
def sync_now():
    return onboard.sync()


@app.get("/mission-control/inbox")
def mc_inbox():
    """What Mission Control has received so far (only synced items)."""
    got = [i for i in onboard.outbox() if i["synced"]]
    sug = store.load("suggestions", {})
    arrived = {i["data"].get("change_id") for i in got if i["kind"] == "decision"}
    # Earth can only confirm what has actually reached it.
    to_confirm = [c for ch in sug.values() for c in ch if c.get("provisional") and c["id"] in arrived]
    return {"received": got, "to_confirm": to_confirm, "link": onboard.link()}


@app.post("/mission-control/confirm")
def mc_confirm(body: Confirm):
    """Mission Control confirms or overrules a commander's temporary decision."""
    if not onboard.link()["online"]:
        raise HTTPException(409, "No link to Earth: Mission Control cannot answer yet")
    sug = store.load("suggestions", {})
    for changes in sug.values():
        for c in changes:
            if c.get("id") == body.change_id and c.get("provisional"):
                c["provisional"] = False
                c["confirmed"] = body.confirm
                if not body.confirm:
                    c["status"], c["note"] = "reject", body.note or "Overruled by Mission Control"
                store.save("suggestions", sug)
                return store.append("decisions", {"change_id": body.change_id, "by": "Mission Control",
                                                  "decision": "confirm" if body.confirm else "overrule", "note": body.note})
    raise HTTPException(404, "No temporary decision with this id")


@app.post("/focus")
def focus_test(body: FocusResult):
    """Today's 3-minute focus test (mean reaction time) replaces today's value; the forecast reruns."""
    if not 100 <= body.mean_rt_ms <= 5000:
        raise HTTPException(400, "mean_rt_ms must be 100-5000")
    ring_all = store.load("ring", [])
    for r in ring_all:
        if r["crew"] == body.crew and r["day"] == DAYS:
            r["focus_rt_ms"] = round(body.mean_rt_ms)
            r["focus_source"] = "measured in the app"
    store.save("ring", ring_all)
    f = forecast(_ring(body.crew), _schedules().get(body.crew, {}), DAYS, self_report=_self_report(body.crew))
    base = f.get("baseline", {}).get("focus_rt_ms", {})
    return {"crew": body.crew, "mean_rt_ms": round(body.mean_rt_ms), "normal_ms": base.get("mean"),
            "z": f.get("today", {}).get("deviation", {}).get("focus_rt_ms"),
            "points": f["days"][0]["points"]["focus"] if f.get("days") else None}
