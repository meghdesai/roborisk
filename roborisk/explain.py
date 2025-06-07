import openai
from .config import get_settings


def explain_var(var_today: float, var_yesterday: float, drivers: list[str]) -> str:
    settings = get_settings()

    openai.api_key = settings.OPENROUTER_API_KEY
    openai.api_base = "https://openrouter.ai/api/v1"

    prompt = (
        "Explain why today's VAR ({:.2f}) differs from yesterday's ({:.2f}). "
        "Key drivers: {}.".format(var_today, var_yesterday, ", ".join(drivers))
    )

    completion = openai.chat.completions.create(
        model="deepseek/deepseek-r1-0528-qwen3-8b:free",
        messages=[
            {"role": "system", "content": "You are a risk analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=400,
    )

    return completion.choices[0].message.content
