from pydantic import BaseModel
from typing import List, Optional
from app.groq_client import get_runbook
from app.slack_client import post_to_slack


class AlertLabel(BaseModel):
    alertname: str
    severity: Optional[str] = "unknown"
    namespace: Optional[str] = "unknown"
    pod: Optional[str] = None
    deployment: Optional[str] = None


class Alert(BaseModel):
    status: str
    labels: AlertLabel
    annotations: Optional[dict] = {}


class AlertPayload(BaseModel):
    alerts: List[Alert]
    groupLabels: Optional[dict] = {}
    commonAnnotations: Optional[dict] = {}


async def handle_alert(payload: AlertPayload) -> dict:
    results = []
    for alert in payload.alerts:
        if alert.status != "firing":
            continue

        alert_name = alert.labels.alertname
        severity = alert.labels.severity
        namespace = alert.labels.namespace
        pod = alert.labels.pod or "unknown"
        summary = alert.annotations.get("summary", "No summary provided")

        context = f"""
Alert: {alert_name}
Severity: {severity}
Namespace: {namespace}
Pod: {pod}
Summary: {summary}
        """.strip()

        runbook = await get_runbook(context)
        await post_to_slack(alert_name, severity, context, runbook)
        results.append({"alert": alert_name, "status": "processed"})

    return {"processed": len(results), "results": results}
