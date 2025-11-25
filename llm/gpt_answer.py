from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def gpt_ans(system: str, user: str, model: str = "gpt-4o", temperature: float = 0.0) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        # max_tokens=512, # 토큰 한도
    )
    return (resp.choices[0].message.content or "").strip()
