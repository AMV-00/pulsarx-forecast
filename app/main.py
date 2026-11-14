from fastapi import FastAPI
from pydantic import BaseModel

from app.explain.templates import polish, reason_sentence
from app.fallback.answers import answer
from app.nova.extract import extract
from app.nova.questions import next_question
from app.schedule.rules import suggest_changes

app = FastAPI(title="PulsarX Forecast")


class CheckinText(BaseModel):
    text: str


class SuggestRequest(BaseModel):
    facts: dict            # from the transparent model: level, top_factor, sleep_hours, risk_before/after
    tasks: list[dict]      # today's schedule
    crew_free: dict = {}   # free minutes per other crew member
    mars_mode: bool = False
    lang: str = "en"
    use_claude: bool = True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/nova/first-question")
def first_question(lang: str = "en"):
    return {"greeting": answer("greeting", lang), "question": next_question({})}


@app.post("/nova/extract")
def nova_extract(body: CheckinText):
    answers = extract(body.text)
    return {"answers": answers, "next_question": next_question(answers)}


@app.post("/suggest")
def suggest(body: SuggestRequest):
    level = body.facts["level"]
    changes = suggest_changes(level, body.tasks, body.crew_free, body.mars_mode)
    for c in changes:
        sentence = reason_sentence(c, body.facts, body.lang)
        c["reason"] = polish(sentence, lang=body.lang) if body.use_claude else sentence
        c["status"] = "pending"  # ground team: accept / edit / reject
    return {"summary": answer(f"risk_{level}", body.lang), "changes": changes}
