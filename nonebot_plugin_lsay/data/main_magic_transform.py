#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
胡乱说 · 文本魔改主脚本

三种模式:
    shuffle  仅语义块乱序（连续相邻的可打乱词合并为大 chunk 再乱序，标点助词不动）
    homo     仅同音字替换（基于外部 homophone.json）
    mix      先 shuffle 再 homo

用法:
    python main_magic_transform.py --mode mix --prob 0.3 --text "输入要魔改的文本"
    python main_magic_transform.py   # 运行内置测试用例
"""
import argparse
import json
import os
import random

import jieba
import jieba.posseg as pseg

DEFAULT_HOMO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "homophone.json")

# 参与乱序的词性：名词、人名、地名、机构名、数量词、符号、英文词
SHUFFLE_FLAGS = {"n", "nr", "ns", "nt", "m", "x", "eng"}
# 禁止乱序的词性：介词、连词、助词、副词、标点、语气词、叹词、动词、形容词、代词、量词
KEEP_FLAGS = {"p", "c", "u", "d", "w", "y", "e", "v", "vn", "a", "r", "q"}

# 分隔标点（永远固定，位置不动）
_SEP_PUNCT = set("，。！？；：、“”‘’（）《》〈〉【】「」『』…—～,.;:!?'\"()[]{}<>")
# 粘连符号（跟相邻语义块一起走，如 盼盼云-886vps 中的 -、9.9/月 中的 /）
_CONNECTOR = set("-‐‑–_/\\×*&@#%^+~≈|=")

_HOMO_DICT = None


def load_homo_dict(path=None):
    """读取外部谐音字典（进程内缓存）"""
    global _HOMO_DICT
    if _HOMO_DICT is None:
        path = path or DEFAULT_HOMO_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"未找到谐音字典文件: {path}\n请先运行: python generate_homophone_json.py")
        with open(path, "r", encoding="utf-8") as fp:
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


def _token_blocks(text, shuffle_flags, keep_flags):
    """
    jieba 分词后把连续相邻、属于 SHUFFLE_FLAGS 的词语合并为完整语义大 chunk。
    - 纯空白 / 纯分隔标点：强制固定，位置不动
    - 纯粘连符号：并入相邻语义块一起移动
    返回 [(kind, content)]，kind: 'm'=可打乱块 'f'=固定块
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
    cur = []
    for word, flag in pseg.lcut(text):
        if is_separator(word):
            if cur:
                blocks.append(("m", "".join(cur)))
                cur = []
            blocks.append(("f", word))
        elif is_mutable(flag, word):
            cur.append(word)
        else:
            if cur:
                blocks.append(("m", "".join(cur)))
                cur = []
            blocks.append(("f", word))
    if cur:
        blocks.append(("m", "".join(cur)))
    return blocks


def semantic_chunk_shuffle(text, shuffle_flags=SHUFFLE_FLAGS, keep_flags=KEEP_FLAGS):
    """仅语义块乱序：对大 chunk 做 shuffle，固定块保持原位置。"""
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
    :param homo_dict: 谐音字典（None 时自动读取外部 json）
    """
    if not isinstance(text, str):
        return text
    if mode == "shuffle":
        return semantic_chunk_shuffle(text, shuffle_flags, keep_flags)
    if mode == "homo":
        return homophone_replace(text, prob, homo_dict)
    if mode == "mix":
        return homophone_replace(
            semantic_chunk_shuffle(text, shuffle_flags, keep_flags),
            prob, homo_dict)
    raise ValueError(f"未知模式: {mode}")


def _split_flags(s):
    return set(x.strip() for x in s.split(",") if x.strip())


def _run_cli():
    ap = argparse.ArgumentParser(description="胡乱说 · 文本魔改")
    ap.add_argument("--mode", choices=["shuffle", "homo", "mix"], default="mix")
    ap.add_argument("--prob", type=float, default=0.35, help="谐音替换概率 0~1")
    ap.add_argument("--text", default=None, help="要魔改的文本")
    ap.add_argument("--file", default=None, help="从文件读取多行文本")
    ap.add_argument("--homo-file", default=None, help="谐音字典路径")
    ap.add_argument("--shuffle-flags", default=None, help="参与乱序词性，逗号分隔")
    ap.add_argument("--keep-flags", default=None, help="禁止乱序词性，逗号分隔")
    args = ap.parse_args()

    shuffle_flags = _split_flags(args.shuffle_flags) if args.shuffle_flags else SHUFFLE_FLAGS
    keep_flags = _split_flags(args.keep_flags) if args.keep_flags else KEEP_FLAGS
    homo_dict = load_homo_dict(args.homo_file) if args.homo_file else None

    texts = []
    if args.text is not None:
        texts.append(args.text)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            texts += [ln.rstrip("\n") for ln in f if ln.strip()]
    if not texts:
        run_demo(shuffle_flags, keep_flags, homo_dict)
        return

    for s in texts:
        print(f"【原始】{s}")
        print(f"【语义乱序】{magic_transform(s, 'shuffle', shuffle_flags=shuffle_flags, keep_flags=keep_flags, homo_dict=homo_dict)}")
        print(f"【谐音替换】{magic_transform(s, 'homo', args.prob, shuffle_flags, keep_flags, homo_dict)}")
        print(f"【混合魔改】{magic_transform(s, 'mix', args.prob, shuffle_flags, keep_flags, homo_dict)}")
        print("-" * 70)


TEST_CASES = [
    "nmd校园网，我的100mbps呢",
    "xx云-999vps 日本9.9/月补货",
    "各位富豪，续费了。",
    "云机-2核4G 香港29/月 补货",
    "该死的公网IP，我的IPv6呢",
]

BOUNDARY_CASES = [
    "",
    "！！！",
    "hello world 123",
    "   ",
    "。，！？",
]


def run_demo(shuffle_flags=SHUFFLE_FLAGS, keep_flags=KEEP_FLAGS, homo_dict=None):
    """内置测试用例演示"""
    print("========== 常规测试用例 ==========")
    for s in TEST_CASES:
        print(f"【原始】{s}")
        print(f"【语义乱序】{magic_transform(s, 'shuffle', shuffle_flags=shuffle_flags, keep_flags=keep_flags, homo_dict=homo_dict)}")
        print(f"【谐音替换】{magic_transform(s, 'homo', 0.35, shuffle_flags, keep_flags, homo_dict)}")
        print(f"【混合魔改】{magic_transform(s, 'mix', 0.35, shuffle_flags, keep_flags, homo_dict)}")
        print("-" * 70)

    print("========== 边界情况用例 ==========")
    for s in BOUNDARY_CASES:
        r = magic_transform(s, "mix", 0.35, shuffle_flags, keep_flags, homo_dict)
        print(f"【原始】{s!r}  ->  【混合魔改】{r!r}")
    print("-" * 70)


if __name__ == "__main__":
    jieba.setLogLevel(20)
    _run_cli()
