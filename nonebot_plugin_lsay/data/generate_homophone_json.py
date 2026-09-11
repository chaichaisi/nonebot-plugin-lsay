#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
胡乱说 · 谐音字典生成器
独立生成外部 json 谐音字典文件 homophone.json，供主业务脚本读取。

用法:
    python generate_homophone_json.py
    python generate_homophone_json.py --level common --output homophone.json
    python generate_homophone_json.py --level all --polyphonic --compact
"""
import argparse
import json
from pypinyin import pinyin, Style


def level1_chars():
    """GB2312 一级汉字（约 3755 个，按拼音排序的常用字）"""
    chars = []
    for hi in range(0xB0, 0xD8):
        for lo in range(0xA1, 0xFE):
            try:
                c = bytes([hi, lo]).decode("gb2312")
            except UnicodeDecodeError:
                continue
            if c and "\u4e00" <= c <= "\u9fa6":
                chars.append(c)
    return chars


def level12_chars():
    """GB2312 一级 + 二级汉字（约 6763 个）"""
    chars = []
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFE):
            try:
                c = bytes([hi, lo]).decode("gb2312")
            except UnicodeDecodeError:
                continue
            if c and "\u4e00" <= c <= "\u9fa6":
                chars.append(c)
    return chars


def all_chars():
    """Unicode 基本区全部汉字（约 2 万，含大量生僻字）"""
    return [chr(c) for c in range(0x4e00, 0x9fa6)]


CHAR_LOADERS = {
    "common": level1_chars,
    "extended": level12_chars,
    "all": all_chars,
}


def build_homophone_dict(chars, polyphonic=False):
    """
    遍历汉字，用 pypinyin 取读音，构建:
    {原汉字: [同音字列表, ...]}
    过滤：如果没有其他同音字，则此 key 不写入。
    """
    char_pys = {}
    py_chars = {}
    for char in chars:
        res = pinyin(char, style=Style.NORMAL, heteronym=polyphonic, errors="ignore")
        if not res or not res[0]:
            continue
        pys = set(p for p in res[0] if p)
        if not pys:
            continue
        char_pys[char] = pys
        for py in pys:
            py_chars.setdefault(py, set()).add(char)

    char2homos = {}
    for char, pys in char_pys.items():
        others = []
        seen = set()
        for py in pys:
            for x in py_chars.get(py, ()):
                if x != char and x not in seen:
                    seen.add(x)
                    others.append(x)
        if others:
            char2homos[char] = others
    return char2homos


def main():
    ap = argparse.ArgumentParser(description="生成谐音字典 homophone.json")
    ap.add_argument("-o", "--output", default="homophone.json",
                    help="输出文件路径（默认 homophone.json）")
    ap.add_argument("--level", choices=list(CHAR_LOADERS.keys()), default="common",
                    help="字库级别: common=GB2312一级常用字(约3755), "
                         "extended=一级+二级(约6763), all=全部汉字(约2万,含生僻字)")
    ap.add_argument("--polyphonic", action="store_true",
                    help="按多音字展开（一个字按全部读音收集同音字）")
    ap.add_argument("--compact", action="store_true",
                    help="压缩输出（不缩进），减小 json 体积")
    args = ap.parse_args()

    chars = CHAR_LOADERS[args.level]()
    print(f"字库级别 [{args.level}]，共 {len(chars)} 个汉字，开始注音构建...")
    d = build_homophone_dict(chars, polyphonic=args.polyphonic)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=None if args.compact else 2)

    total = sum(len(v) for v in d.values())
    avg = total / len(d) if d else 0
    size = len(json.dumps(d, ensure_ascii=False))
    print(f"已生成 {args.output}：有效可替换汉字 {len(d)} 个，"
          f"平均每个字 {avg:.1f} 个同音字，文件约 {size/1024:.1f} KB。")


if __name__ == "__main__":
    main()
