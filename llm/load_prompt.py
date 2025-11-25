from pathlib import Path
from functools import lru_cache

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

# 프롬프트를 메모리에 저장하여 여러번 llm을 호출하더라도 프롬프트 파일을 한번만 읽음
@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")

def render_prompt(name: str, **kwargs) -> str:
    template = load_prompt(name)
    # {menu_prompt}, {user_text} 자리를 인자로 들어온 실제값으로 치환
    return template.format(**kwargs)
