import os, hashlib
import json
from typing import Dict, Any, Optional
import redis
from difflib import SequenceMatcher

from cache.session import l1_snapshot_load, get_menu_prompt
from llm.generate_ans import gen_ans

# --- Redis 접속 ---
_r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True,
)

REDIS_TTL = int(os.getenv("REDIS_FAQ_TTL", "86400"))  # 1일

# 같은 질문에는 같은 키를 생성 (sha256, Redis key)
def make_redis_key(store_id: str, menu_ver: int, user_text: str) -> str:
    raw = f"{store_id}:{menu_ver}:{user_text.strip()}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"faq:{h}"

def get_index_key(store_id: str, menu_ver: int) -> str:
    # 이 매장/버전에서 등장했던 질문 텍스트 모아두는 set
    return f"faq:index:{store_id}:{menu_ver}"

def fuzzy_matching(
        store_id: str,
        menu_ver: int,
        user_text: str,
        threshold: float = 0.8
) -> Optional[str]:
    # redis 과거 질문 중에서 user_text와 유사도가 0.8 이상일 때 cache hit
    index_key=get_index_key(store_id, menu_ver)
    candis=_r.smembers(index_key)

    if not candis:
        return None
    
    best_ques=None
    best_score=0.0

    for q in candis:
        score=SequenceMatcher(None, user_text, q).ratio()
        if score>best_score:
            best_score=score
            best_ques=q
    
    if (best_ques is not None) and (best_score >= threshold):
        return best_ques
    
    return None
    

def agent_answer(store_id: str, menu_ver: int, user_text: str) -> Dict:
    # 1) L1 조회
    l1_snapshot_load(store_id, menu_ver)
    menu_prompt = get_menu_prompt(store_id, menu_ver)

    cache_hit = False  # 기본값: miss

    # 2) L2 캐시 조회
    fuzzy_answer=fuzzy_matching(store_id, menu_ver, user_text)
    if fuzzy_answer:
        cache_key=make_redis_key(store_id,menu_ver,fuzzy_answer)
        cached= _r.get(cache_key)

        if cached is not None:
            try:
                cached_obj = json.loads(cached)
                cached_obj["cache_hit"] = True # Cache Hit
                return cached_obj
            except Exception:
                pass


    # 3) 캐시 미스 → LLM 호출
    answer = gen_ans(menu_prompt=menu_prompt, user_text=user_text)

    response_obj = {
        "reply": answer,
        "store_id": store_id,
        "menu_version": menu_ver,
        "cache_hit": False,
    }

    if "ERROR" in answer:
        return response_obj   # 캐시 저장 금지

    # 4) L2 캐시에 저장 (임베딩 고려 필요)

    # redis key 생성
    if fuzzy_answer:
        # fuzzy hit지만 cache값이 존재하지 않는 경우 → fuzzy key로 저장
        cache_key = make_redis_key(store_id, menu_ver, fuzzy_answer)
    else:
        # fuzzy miss
        cache_key = make_redis_key(store_id, menu_ver, user_text)

    # key-value 쌍 저장
    try:
        _r.setex(cache_key, REDIS_TTL, json.dumps(response_obj, ensure_ascii=False))
        
        # 질문 텍스트를 index set에도 추가해줘야 fuzzy matching이 가능
        index_key = get_index_key(store_id, menu_ver)
        _r.sadd(index_key, user_text.strip())

    except Exception:
        pass


    return response_obj