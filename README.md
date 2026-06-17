# 🚨 Incident Responder

An AI-powered incident response bot that automatically generates runbooks and posts them to Slack when Prometheus alerts fire — fully deployed on Kubernetes via GitOps.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                        │
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │   production ns  │     │   monitoring ns  │                   │
│  │                  │     │                  │                   │
│  │  ┌────────────┐  │     │  ┌───────────┐  │                   │
│  │  │ devops-app │  │     │  │Prometheus │  │                   │
│  │  │  (2 pods)  │◄─┼─────┼──│  scrapes  │  │                   │
│  │  └────────────┘  │     │  └─────┬─────┘  │                   │
│  │                  │     │        │ alert   │                   │
│  │  ┌────────────┐  │     │  ┌─────▼─────┐  │                   │
│  │  │ incident-  │◄─┼─────┼──│AlertMgr   │  │                   │
│  │  │ responder  │  │     │  │ webhook   │  │                   │
│  │  └─────┬──────┘  │     │  └───────────┘  │                   │
│  │        │         │     │                  │                   │
│  └────────┼─────────┘     └─────────────────┘                   │
│           │                                                      │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ├──► Groq API (llama-3.1-8b-instant) → AI Runbook
            │
            └──► Slack #incidents → Runbook posted
```

## How It Works

```
Prometheus alert fires (e.g. AppPodsDown)
          │
          ▼
AlertManager routes POST → incident-responder/webhook
          │
          ▼
alert_handler.py parses AlertPayload
  - alertname, severity, namespace, pod, summary
          │
          ▼
groq_client.py calls llama-3.1-8b-instant
  - generates: likely causes, immediate actions, verification steps
          │
          ▼
slack_client.py posts runbook to #incidents
```

## CI/CD Pipeline

```
git push → GitHub Actions
              │
              ├── test       ruff lint + pytest
              │
              ├── build-push Docker build → Trivy scan → ECR push
              │                (tag = git SHA)
              │
              └── update-gitops  sed tag in devops-gitops/charts/
                                    │
                                    ▼
                                 ArgoCD detects change
                                    │
                                    ▼
                                 Rolling deploy to production ns
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Bot framework | FastAPI + Uvicorn |
| AI model | Groq API — `llama-3.1-8b-instant` |
| Alerting | Prometheus + AlertManager |
| Notifications | Slack SDK |
| Container runtime | Docker |
| Orchestration | Kubernetes (Docker Desktop) |
| GitOps | ArgoCD |
| Packaging | Helm |
| CI/CD | GitHub Actions |
| Image registry | AWS ECR |
| Data validation | Pydantic v2 |

---

## Project Structure

```
incident-responder/
├── app/
│   ├── main.py            # FastAPI app — /health /ready /webhook
│   ├── alert_handler.py   # Parses AlertPayload, orchestrates flow
│   ├── groq_client.py     # Calls Groq API, returns AI runbook
│   └── slack_client.py    # Posts runbook to Slack channel
├── tests/
│   └── test_alert_handler.py
├── .github/
│   └── workflows/
│       └── ci.yml         # test → build → push → gitops update
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/webhook` | Receives AlertManager webhook payload |

### Example Webhook Payload

```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "AppPodsDown",
        "severity": "critical",
        "namespace": "production"
      },
      "annotations": {
        "summary": "devops-app has fewer than 2 pods running"
      }
    }
  ],
  "groupLabels": {},
  "commonAnnotations": {}
}
```

---

## Alerts Handled

| Alert | Condition | Severity |
|---|---|---|
| `AppPodsDown` | `kube_deployment_status_replicas_available < 2` | critical |
| `HighRequestLatency` | p95 latency > 500ms | warning |

---

## Kubernetes Deployment

The bot is deployed via Helm chart managed by ArgoCD in the `production` namespace.

```
devops-gitops/
└── charts/
    └── incident-responder/
        ├── Chart.yaml
        ├── values.yaml        # image tag updated by CI pipeline
        └── templates/
            ├── deployment.yaml
            └── service.yaml
```

Secrets (`GROQ_API_KEY`, `SLACK_BOT_TOKEN`) are stored as Kubernetes Secrets — never in Git.

```bash
kubectl create secret generic incident-responder-secrets \
  -n production \
  --from-literal=GROQ_API_KEY="your-groq-key" \
  --from-literal=SLACK_BOT_TOKEN="your-slack-token" \
  --from-literal=SLACK_CHANNEL_ID="your-channel-id"
```

---

## Local Development

### Prerequisites

- Docker Desktop
- Python 3.11+
- Groq API key — [console.groq.com](https://console.groq.com)
- Slack Bot Token — [api.slack.com/apps](https://api.slack.com/apps)

### Run locally

```bash
# Build image
docker build -t incident-responder:local .

# Run container
docker run -d -p 8001:8000 \
  --name ir-test \
  -e GROQ_API_KEY=your-key \
  -e SLACK_BOT_TOKEN=your-token \
  -e SLACK_CHANNEL_ID=your-channel-id \
  incident-responder:local

# Test health
curl http://localhost:8001/health

# Send test alert
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"AppPodsDown","severity":"critical","namespace":"production"},"annotations":{"summary":"devops-app has fewer than 2 pods running"}}],"groupLabels":{},"commonAnnotations":{}}'
```

### Run tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

---

## Related Repositories

- **[devops-gitops](https://github.com/GY2AN/devops-gitops)** — Helm charts and ArgoCD app manifests
- **[devops-app](https://github.com/GY2AN/devops-app)** — The application being monitored

---

## GitHub Actions Secrets Required

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM credentials for ECR push |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM credentials for ECR push |
| `GITOPS_PAT` | GitHub PAT with repo scope to update devops-gitops |
