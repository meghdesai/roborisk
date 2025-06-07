import requests
from .config import get_settings


def explain_var(var_today: float, var_yesterday: float, drivers: list[str]) -> str:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
    prompt = (
        "Explain why today's VAR ({:.2f}) differs from yesterday's ({:.2f}). "
        "Key drivers: {}.".format(var_today, var_yesterday, ", ".join(drivers))
    )
    payload = {
        "model": "deepseek-r1-0528",
        "messages": [
            {"role": "system", "content": "You are a risk analyst."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 400,
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
