from llm.load_prompt import load_prompt, render_prompt
from llm.gpt_answer import gpt_ans

SYSTEM_PROMPT_NAME = "system_prompt.txt"
USER_PROMPT_NAME   = "ans_prompt.txt"

# gpt-4o
def gen_ans(menu_prompt: str, user_text: str) -> str:
    system_str = load_prompt(SYSTEM_PROMPT_NAME)
    user_str   = render_prompt(USER_PROMPT_NAME, menu_prompt=menu_prompt, user_text=user_text)
    return gpt_ans(system=system_str, user=user_str, model="gpt-4o", temperature=0)