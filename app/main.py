from fastapi import FastAPI, Request
from app.alert_handler import AlertPayload, handle_alert

app = FastAPI(title="incident-responder")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.post("/webhook")
async def webhook(payload: AlertPayload):
    result = await handle_alert(payload)
    return result
