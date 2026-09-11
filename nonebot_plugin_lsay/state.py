"""
胡乱说 · 状态存储
- 全局状态：插件总开关、全局触发概率
- 用户状态：单个用户独立计算，互不干扰（enabled / custom_prob / forced_off）
- 线程安全，原子写入 json 持久化
"""
import json
import random
import threading
from pathlib import Path

DEFAULT_GLOBAL_PROB = 5


def _default_user():
    return {"enabled": True, "custom_prob": None, "forced_off": False}


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self._lock = threading.RLock()
        self._data = {"global": {"enabled": True, "prob": DEFAULT_GLOBAL_PROB}, "users": {}}
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
        except Exception:
            self._data = {"global": {"enabled": True, "prob": DEFAULT_GLOBAL_PROB}, "users": {}}
        g = self._data.setdefault("global", {})
        g.setdefault("enabled", True)
        g.setdefault("prob", DEFAULT_GLOBAL_PROB)
        self._data.setdefault("users", {})

    def _save(self):
        with self._lock:
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)

    # ---------- 全局 ----------
    def get_global(self):
        with self._lock:
            g = self._data["global"]
            return {"enabled": bool(g.get("enabled", True)), "prob": int(g.get("prob", DEFAULT_GLOBAL_PROB))}

    def set_global_enabled(self, enabled):
        with self._lock:
            self._data["global"]["enabled"] = bool(enabled)
            self._save()

    def set_global_prob(self, prob):
        with self._lock:
            self._data["global"]["prob"] = int(prob)
            self._save()

    # ---------- 用户 ----------
    def _user(self, uid):
        uid = str(uid)
        return self._data["users"].setdefault(uid, _default_user())

    def get_user(self, uid):
        with self._lock:
            u = dict(self._user(uid))
            u.setdefault("enabled", True)
            u.setdefault("custom_prob", None)
            u.setdefault("forced_off", False)
            return u

    def set_user_enabled(self, uid, enabled):
        with self._lock:
            self._user(uid)["enabled"] = bool(enabled)
            self._save()

    def set_user_custom_prob(self, uid, prob):
        """prob 为 None 时恢复使用全局概率"""
        with self._lock:
            self._user(uid)["custom_prob"] = None if prob is None else int(prob)
            self._save()

    def force_off_user(self, uid):
        """超管代关：标记 forced_off，用户无法自行 on 开启"""
        with self._lock:
            u = self._user(uid)
            u["forced_off"] = True
            u["enabled"] = False
            self._save()

    def force_on_user(self, uid):
        """超管代开：解除 forced_off"""
        with self._lock:
            u = self._user(uid)
            u["forced_off"] = False
            u["enabled"] = True
            self._save()

    def effective_prob(self, uid):
        """当前用户生效的触发概率（自定义优先，否则用全局）"""
        u = self.get_user(uid)
        g = self.get_global()
        if u.get("custom_prob"):
            return int(u["custom_prob"])
        return g["prob"]

    def should_trigger(self, uid, rnd=None):
        """按用户独立概率判定是否触发被动处理"""
        u = self.get_user(uid)
        g = self.get_global()
        if not g["enabled"]:
            return False
        if not u.get("enabled", True) or u.get("forced_off"):
            return False
        prob = self.effective_prob(uid)
        rnd = random.random() if rnd is None else rnd
        return rnd * 100 < prob
