"""
胡乱说 · 命令解析器
- 命令头：lsay / luan说 / ssay / sao说
- 兼容「有没有空格都不影响使用」：命令与子命令之间有无空格均可识别
  （如 lsay on、lsay  on、lsayon、lsay  gl  show 等都能识别）
- 文本模式保留原始文本内容（含空格）
"""
import re

# 命令头别名，按长度降序匹配（中文别名不区分大小写无意义，英文别名忽略大小写）
ALIASES = ("sao说", "luan说", "lsay", "ssay")

# 明确命令（去空白小写后精确匹配）
_EXACT_COMMANDS = {
    "on": "user_on",
    "off": "user_off",
    "help": "help",
    "info": "info",
    "allon": "all_on",
    "alloff": "all_off",
    "showgl": "showgl",
    "nosetgl": "nosetgl",
}


def match_alias(text):
    """返回命中的命令头；未命中返回 None"""
    low = text.lower()
    for a in ALIASES:
        if low.startswith(a.lower()):
            return a
    return None


def extract_number(s):
    m = re.search(r"\d+", s or "")
    return m.group(0) if m else None


def parse(raw):
    """
    解析一条消息。
    返回 None：不是 lsay 命令（可能是普通聊天，交给被动逻辑）。
    返回 dict：命令解析结果。
    """
    text = (raw or "").strip()
    if not text:
        return None

    alias = match_alias(text)
    if not alias:
        return None

    rest_raw = text[len(alias):]
    # 去全部空白再小写，用于命令匹配（空格存在与否不影响）
    compact = re.sub(r"\s+", "", rest_raw).lower()

    if not compact:
        return {"kind": "intro"}

    if compact in _EXACT_COMMANDS:
        return {"kind": _EXACT_COMMANDS[compact]}

    # gl 系列（用户概率）
    if compact.startswith("gl"):
        sub = compact[2:]
        if sub == "show":
            return {"kind": "gl_show"}
        if sub == "noset":
            return {"kind": "gl_noset"}
        if sub.startswith("set"):
            num = extract_number(sub)
            if num is None:
                return {"kind": "need_number", "cmd": "gl set", "usage": "lsay gl set N (N: 1~15)"}
            return {"kind": "gl_set", "value": int(num)}
        return {"kind": "unknown", "rest": compact}

    # 超管命令
    if compact.startswith("setgl"):
        num = extract_number(compact)
        if num is None:
            return {"kind": "need_number", "cmd": "setgl", "usage": "lsay setgl N (N: 1~50)"}
        return {"kind": "setgl", "value": int(num)}

    if compact.startswith("ason"):
        num = extract_number(compact)
        if num is None:
            return {"kind": "need_number", "cmd": "ason", "usage": "lsay ason 用户ID"}
        return {"kind": "ason", "uid": num}

    if compact.startswith("asoff"):
        num = extract_number(compact)
        if num is None:
            return {"kind": "need_number", "cmd": "asoff", "usage": "lsay asoff 用户ID"}
        return {"kind": "asoff", "uid": num}

    # 文本模式：保留原始内容（含空格）
    return {"kind": "text", "text": rest_raw.strip()}
