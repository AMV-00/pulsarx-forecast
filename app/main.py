from fastapi import FastAPI
from pydantic import BaseModel

from app.nova.extract import extract
from app.nova.questions import next_question

app = FastAPI(title="PulsarX Forecast")


class CheckinText(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/nova/first-question")
def first_question():
    return {"question": next_question({})}


@app.post("/nova/extract")
def nova_extract(body: CheckinText):
    answers = extract(body.text)
    return {"answers": answers, "next_question": next_question(answers)}
