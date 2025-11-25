# cache/session.py
from cachetools import TTLCache
import os, json
from typing import Tuple, Dict, Any

# (store_id, menu_ver) -> snapshot dict
L1_MENU = TTLCache(maxsize=256, ttl=600)
# (store_id, menu_ver) -> compressed string for prompt
L1_MENU_PROMPT = TTLCache(maxsize=256, ttl=600)

def seed_path(store_id: str, menu_ver: int) -> str:
    return f"./seeds/menu_snapshot_{store_id}_v{menu_ver}.json"

def default_snapshot(store_id: str, menu_ver: int) -> Dict[str, Any]:
    return {
        "store_id": store_id,
        "menu_version": menu_ver,
        "menus": [
            {"id":"M001","name":"아메리카노","price":4500,"tags":["아아","기본","카페인"]},
            {"id":"M002","name":"카페라떼","price":5000,"tags":["라떼","우유"]}
        ],
        "aliases": {"아아":"M001"}
    }

def l1_snapshot_load(store_id: str, menu_ver: int) -> Dict[str, Any]:
    # L1에 해당하는 store_id-menu_ver의 snapshot이 있으면 그대로 반환
    key: Tuple[str, int] = (store_id, menu_ver)
    if key in L1_MENU:
        return L1_MENU[key]

    # seeds(DB)에서 해당하는 store_id-menu_ver의 snapshot를 찾아 로드
    # sedds(DB)에도 없으면 default 반환
    path = seed_path(store_id, menu_ver)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            snap = json.load(f)
    else:
        snap = default_snapshot(store_id, menu_ver)

    # 새로 로드한 snapshot은 L1에 적재
    L1_MENU[key] = snap
    # 프롬프트용 요약 문자열도 같이 빌드 & 캐시
    L1_MENU_PROMPT[key] = build_menu_prompt(snap)
    return snap

# L1에서 snapshot을 읽기 / 없으면 None 반환
def get_menu(store_id: str, menu_ver: int) -> Dict[str, Any]:
    return L1_MENU.get((store_id, menu_ver))

def get_menu_prompt(store_id: str, menu_ver: int) -> str:
    return L1_MENU_PROMPT.get((store_id, menu_ver), "")

# LLM 토큰 낭비 대비 응답 메뉴 정보 최소화
def build_menu_prompt(snapshot: Dict[str, Any]) -> str:
    lines = []
    for m in snapshot.get("menus", []):
        tags = ", ".join(m.get("tags", []))
        lines.append(
            f"- {m['id']} {m['name']} ({m['price']}원)"
            + (f" / 특징: {tags}" if tags else "")
        )
    return "\n".join(lines)

