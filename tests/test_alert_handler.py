import pytest
from unittest.mock import AsyncMock, patch
from app.alert_handler import handle_alert, AlertPayload

@pytest.mark.asyncio
async def test_handle_firing_alert():
    payload = AlertPayload(**{
        "alerts": [{
            "status": "firing",
            "labels": {
                "alertname": "AppPodsDown",
                "severity": "critical",
                "namespace": "production"
            },
            "annotations": {
                "summary": "devops-app has fewer than 2 pods running"
            }
        }],
        "groupLabels": {},
        "commonAnnotations": {}
    })
    with patch(
        "app.alert_handler.get_runbook", new_callable=AsyncMock
    ) as mock_runbook, patch(
        "app.alert_handler.post_to_slack", new_callable=AsyncMock
    ) as mock_slack:
        mock_runbook.return_value = "Check pod logs with kubectl logs"
        result = await handle_alert(payload)
        assert result["processed"] == 1
        assert result["results"][0]["alert"] == "AppPodsDown"
        mock_runbook.assert_called_once()
        mock_slack.assert_called_once()

@pytest.mark.asyncio
async def test_skip_resolved_alert():
    payload = AlertPayload(**{
        "alerts": [{
            "status": "resolved",
            "labels": {
                "alertname": "AppPodsDown",
                "severity": "critical",
                "namespace": "production"
            },
            "annotations": {}
        }],
        "groupLabels": {},
        "commonAnnotations": {}
    })
    with patch(
        "app.alert_handler.get_runbook", new_callable=AsyncMock
    ) as mock_runbook, patch(
        "app.alert_handler.post_to_slack", new_callable=AsyncMock
    ) as mock_slack:
        result = await handle_alert(payload)
        assert result["processed"] == 0
        mock_runbook.assert_not_called()
        mock_slack.assert_not_called()
