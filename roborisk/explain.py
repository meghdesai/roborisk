# roborisk/explain.py
from openai import OpenAI
from .config import get_settings

def explain_var(
    var_today: float,
    var_yesterday: float,
    drivers: list[str],
    date: str | None = None,
) -> str:
    settings = get_settings()

    client = OpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    date = date or "today"
    prompt = (
        "You are a risk analyst. Produce exactly three bullets using the format "
        "🔹 <concise reason> (no extra text).\n"
        f"The first line must start with a bullet. Explain why the portfolio VAR on "
        f"{date} (${'{:.2f}'.format(var_today)}) differs from the previous day "
        f"(${'{:.2f}'.format(var_yesterday)}). "
        f"Key drivers: {', '.join(drivers)}."
    )
    

    completion = client.chat.completions.create(
        model="deepseek/deepseek-r1-0528:free",
        stream=False, 
        messages=[
            {"role": "system", "content": "You are a risk analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    content = (completion.choices[0].message.content or "").strip()
    return content or "[Model returned an empty response]"
