import os
from groq import Groq

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer.
When given a Prometheus alert, respond with:
1. Likely causes (2-3 bullet points)
2. Immediate actions to take (step by step commands)
3. How to verify the fix
Be concise. Use kubectl commands where relevant.
Format your response clearly with headers."""


def _get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key)


async def get_runbook(alert_context: str) -> str:
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Alert received:\n{alert_context}"},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to generate runbook: {str(e)}"
