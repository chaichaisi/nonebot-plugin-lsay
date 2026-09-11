"""
胡乱说 · 文本魔改核心引擎
封装语义块乱序 / 同音字替换 / 混合模式。
谐音字典从包内 data/homophone.json 读取，不硬编码在业务代码里。
"""
import json
import random
from pathlib import Path

import jieba
import jieba.posseg as pseg

jieba.setLogLevel(20)

_HOMO_PATH = Path(__file__).resolve().parent / "data" / "homophone.json"

# 参与乱序的词性：名词、人名、地名、机构名、数量词、符号、英文词、
# 动词、动名词、形容词、时间词、习语/成语
SHUFFLE_FLAGS = {"n", "nr", "ns", "nt", "m", "x", "eng", "v", "vn", "a", "t", "i"}
# 禁止乱序的词性：介词、连词、助词、副词、标点、语气词、叹词、代词、量词
KEEP_FLAGS = {"p", "c", "u", "d", "w", "y", "e", "r", "q"}

# 分隔标点（永远固定，位置不动）
_SEP_PUNCT = set("，。！？；：、“”‘’（）《》〈〉【】「」『』…—～,.;:!?'\"()[]{}<>")
# 粘连符号（跟相邻语义块一起走，如 盼盼云-886vps 中的 -、9.9/月 中的 /）
_CONNECTOR = set("-‐‑–_/\\×*&@#%^+~≈|=")

_HOMO_DICT = None


def load_homo_dict(path=None):
    """读取谐音字典（进程内缓存，避免重复读文件）"""
    global _HOMO_DICT
    if _HOMO_DICT is None:
        p = Path(path) if path else _HOMO_PATH
        if not p.exists():
            raise FileNotFoundError(
                f"未找到谐音字典文件: {p}\n请先运行 generate_homophone_json.py 生成")
        with open(p, "r", encoding="utf-8") as fp:
            _HOMO_DICT = json.load(fp)
    return _HOMO_DICT


def homophone_replace(text, prob=0.35, homo_dict=None):
    """逐字符同音替换，prob 为替换概率（0~1）"""
    if not text:
        return text
    homo_dict = homo_dict or load_homo_dict()
    buf = []
    for ch in text:
        if ch in homo_dict and random.random() < prob:
            buf.append(random.choice(homo_dict[ch]))
        else:
            buf.append(ch)
    return "".join(buf)


def _is_pure_cn(word):
    """是否纯中文（用于决定相邻可乱序词是否合并）"""
    return bool(word) and all(
        "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf"
        for ch in word)


def _token_blocks(text, shuffle_flags, keep_flags):
    """
    jieba 分词后生成语义块列表，返回 [(kind, content)]，kind: 'm'=可打乱块 'f'=固定块。
    合并规则：
    - 纯空白 / 纯分隔标点：强制固定，位置不动
    - 含数字 / 字母 / 粘连符号的连续可乱序 token 合并为整块移动（保留语义，如 催盼云-886vps、日本9.9/月）
    - 相邻的纯中文可乱序词各自独立成块（保证 今天天气 这类句子能明显乱序）
    - 固定词性（助词/连词/代词等）位置不动
    """

    def is_connector(word):
        return bool(word) and set(word) <= _CONNECTOR

    def is_separator(word):
        return (not word.strip()) or set(word) <= _SEP_PUNCT

    def is_mutable(flag, word):
        if is_connector(word):
            return True
        return flag in shuffle_flags and flag not in keep_flags

    blocks = []
    tokens = list(pseg.lcut(text))
    n = len(tokens)
    i = 0
    while i < n:
        word, flag = tokens[i]
        if is_separator(word):
            blocks.append(("f", word))
            i += 1
            continue
        if not is_mutable(flag, word):
            blocks.append(("f", word))
            i += 1
            continue
        j = i
        while j < n:
            w, f = tokens[j]
            if is_separator(w) or not is_mutable(f, w):
                break
            j += 1
        seg = [w for w, _ in tokens[i:j]]
        if any(not _is_pure_cn(w) for w in seg):
            blocks.append(("m", "".join(seg)))
        else:
            for w in seg:
                blocks.append(("m", w))
        i = j
    return blocks


def semantic_chunk_shuffle(text, shuffle_flags=SHUFFLE_FLAGS, keep_flags=KEEP_FLAGS):
    """仅语义块乱序：对大 chunk 做 shuffle，固定块（标点/助词/连词等）保持原位置。"""
    if not text or not text.strip():
        return text
    blocks = _token_blocks(text, shuffle_flags, keep_flags)
    mut = [c for k, c in blocks if k == "m"]
    if len(mut) <= 1:
        return text
    random.shuffle(mut)
    out = []
    mi = 0
    for k, c in blocks:
        if k == "m":
            out.append(mut[mi])
            mi += 1
        else:
            out.append(c)
    return "".join(out)


def magic_transform(text, mode="mix", prob=0.35,
                    shuffle_flags=SHUFFLE_FLAGS, keep_flags=KEEP_FLAGS,
                    homo_dict=None):
    """
    :param text: 输入句子
    :param mode: shuffle | homo | mix
    :param prob: 谐音替换概率 0~1
    :param shuffle_flags: 参与乱序词性集合
    :param keep_flags: 禁止乱序词性集合
    :param homo_dict: 谐音字典（None 时自动读取包内 json）
    """
    if not isinstance(text, str):
        return text
    if mode == "shuffle":
        return semantic_chunk_shuffle(text, shuffle_flags, keep_flags)
    if mode == "homo":
        return homophone_replace(text, prob, homo_dict)
    if mode == "mix":
        # 每次随机一种玩法：
        #   - 50% 先乱序，之后 30% 不换音 / 50% 部分换音 / 20% 全换音
        #   - 50% 不乱序，仅 60% 部分换音 / 40% 全换音
        # 效果在「纯乱序 / 部分谐音 / 全谐音 / 乱序+谐音」间随机切换。
        if random.random() < 0.5:
            r = random.random()
            p = 0.0 if r < 0.3 else (1.0 if r >= 0.8 else prob)
            out = semantic_chunk_shuffle(text, shuffle_flags, keep_flags)
            return homophone_replace(out, p, homo_dict) if p > 0 else out
        r = random.random()
        p = prob if r < 0.6 else 1.0
        return homophone_replace(text, p, homo_dict)
    raise ValueError(f"未知模式: {mode}")
