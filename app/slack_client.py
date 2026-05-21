import os
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError


async def post_to_slack(
    alert_name: str,
    severity: str,
    context: str,
    runbook: str
):
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel_id = os.environ.get("SLACK_CHANNEL_ID")

    # Validate env variables
    if not token:
        raise ValueError("SLACK_BOT_TOKEN is missing")

    if not channel_id:
        raise ValueError("SLACK_CHANNEL_ID is missing")

    client = AsyncWebClient(token=token)

    severity_emoji = {
        "critical": ":red_circle:",
        "warning": ":warning:",
        "info": ":information_source:"
    }.get(severity.lower(), ":white_circle:")

    message = f"""
{severity_emoji} *Alert:* `{alert_name}`

*Severity:* `{severity}`

*Context:*
{context}

*AI-Generated Runbook:*
{runbook}
""".strip()

    try:
        response = await client.chat_postMessage(
            channel=channel_id,
            text=message,
            mrkdwn=True
        )

        print(
            f"Slack message sent successfully. "
            f"Timestamp: {response['ts']}"
        )

    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")

    except Exception as e:
        print(f"Unexpected Slack error: {str(e)}")