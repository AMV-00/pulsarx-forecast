from fastapi import FastAPI

app = FastAPI(title="PulsarX Forecast")


@app.get("/health")
def health():
    return {"status": "ok"}
