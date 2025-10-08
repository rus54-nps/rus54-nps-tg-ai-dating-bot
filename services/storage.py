# services/storage.py
from collections import defaultdict
from typing import List, Dict
import time

_dialogs: Dict[int, List[dict]] = defaultdict(list)
_last_active: Dict[int, float] = defaultdict(lambda: time.time())

def add_message(user_id: int, role: str, content: str):
    _dialogs[user_id].append({"role": role, "content": content})
    _last_active[user_id] = time.time()
    if len(_dialogs[user_id]) > 10:
        _dialogs[user_id] = _dialogs[user_id][-10:]

def get_dialog(user_id: int) -> List[dict]:
    return _dialogs[user_id]

def clear_dialog(user_id: int):
    if user_id in _dialogs:
        del _dialogs[user_id]

def get_last_active(user_id: int) -> float:
    return _last_active.get(user_id, 0.0)

def get_all_active_users() -> List[int]:
    return list(_last_active.keys())
