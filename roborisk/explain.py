from __future__ import annotations

import requests

from .config import get_settings


SYSTEM_MSG = {
    "role": "system",
    "content": "You are a financial risk assistant.",
}


def explain_var(var_today: float, var_yesterday: float, drivers: list[str]) -> str:
    settings = get_settings()
    delta = var_today - var_yesterday
    body = {
        "model": "deepseek-r1-0528",
        "messages": [
            SYSTEM_MSG,
            {
                "role": "user",
                "content": (
                    f"Today's VaR: {var_today:.2f}. Yesterday's VaR: {var_yesterday:.2f}. "
                    f"Change: {delta:.2f}. Key drivers: {', '.join(drivers)}. "
                    "Explain the change."
                ),
            },
        ],
        "temperature": 0.7,
        "max_tokens": 400,
    }
    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
