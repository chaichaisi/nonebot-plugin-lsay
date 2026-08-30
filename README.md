<div align="center">
  <a href="https://github.com/chaichaisi/nonebot-plugin-lsay"><img src="./logo.svg" width="240" height="240" alt="胡乱说 Logo"></a>
  <br>
  <sub>Logo 版权：Chaichaisi 版权所有，严禁商用</sub>
  <br>
</div>

<div align="center">

# nonebot-plugin-lsay

_✨ 胡乱说 —— 插这件说都不会话了：谐音恶搞 + 语义块乱序的整活机器人 ✨_


<a href="https://github.com/chaichaisi/nonebot-plugin-lsay/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/chaichaisi/nonebot-plugin-lsay?color=%2300BFFF&style=flat-square">
</a>
<a href="https://github.com/chaichaisi/nonebot-plugin-lsay/issues">
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/chaichaisi/nonebot-plugin-lsay?color=Emerald%20green&style=flat-square">
</a>
<a href="https://github.com/chaichaisi/nonebot-plugin-lsay/network">
    <img alt="GitHub forks" src="https://img.shields.io/github/forks/chaichaisi/nonebot-plugin-lsay?color=%2300BFFF&style=flat-square">
</a>
<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/chaichaisi/nonebot-plugin-lsay.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-lsay">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-lsay.svg" alt="pypi">
</a>
<a href="https://www.python.org">
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
</a>

</div>

## 🙏 致谢

- 感谢 [nonebot-plugin-hsy](https://github.com/chaichaisi/nonebot-plugin-hsy) 提供的 README 排版参考
- 感谢 [nonebot-plugin-template](https://github.com/A-kirami/nonebot-plugin-template) 项目模板

## 📖 前言及介绍

通过谐音替换 + 语义块乱序，把群聊 / 私聊里的文本魔改成"说都不会话了"的整活版本。支持被动监听（按概率触发）与主动 `lsay` 命令，命令有没有空格都能识别，是纯整活插件，请勿用于任何正式场合。

魔改示例：

- `今天天气不错` → `不错今天天气` / `今舔天奇部错`
- `我明天去学校上课` → `学校明天去上课` / `我薛校铭天上课娶`
- `催盼云-886vps 日本9.9/月补货` → `日本9.9/月补货 催盼云-886vps`
- `各位富豪，续费了。` → `各位续费，富号了。` / `各位扶豪，叙啡了。`

标点、助词、连词、代词位置保持不动，不会乱飘；含数字 / 字母 / 符号的品牌与价格词（如 `886vps`、`9.9/月`）会整块移动，不会被拆碎。

## 🔧 开发环境

- NoneBot2：2.x
- Python：3.9+
- 操作系统：Linux / Windows / macOS
- 适配器：OneBot V11（NapCat / LLOneBot / Go-CQHTTP 等）

## 💿 安装

### 1. nb-cli 安装（推荐）

在你 bot 工程的文件夹下运行：

```
nb plugin install nonebot-plugin-lsay
```

### 2. pip 安装

```
pip install nonebot-plugin-lsay
```

若是默认 nb-cli 创建的 nonebot2 工程，在 `pyproject.toml` 的 `[tool.nonebot.plugins]` 中添加一行：

```toml
[tool.nonebot.plugins]
nonebot-plugin-lsay = ["nonebot_plugin_lsay"]
```

### 3. 本地安装（不推荐）

下载源码后，将 `nonebot_plugin_lsay` 目录放到 `你的bot/src/plugins/` 下即可。

## ⚙️ 配置

在 nonebot2 项目的 `.env` 文件中添加以下配置项（全部可选，不填用默认值）：

| 配置项 | 默认值 | 说明 |
|:---:|:---:|:---:|
| lsay_global_enabled | True | 全局默认开启状态 |
| lsay_global_prob | 5 | 全局触发概率（1~50，越大越易触发） |
| lsay_user_prob_min | 1 | 普通用户可设置的概率下限 |
| lsay_user_prob_max | 15 | 普通用户可设置的概率上限 |
| lsay_global_prob_min | 1 | 全局概率下限 |
| lsay_global_prob_max | 50 | 全局概率上限 |
| lsay_homo_prob | 0.35 | 谐音替换概率（0~1，内部参数） |
| lsay_default_mode | mix | 魔改模式：shuffle（仅乱序）/ homo（仅谐音）/ mix（混合） |
| lsay_state_file | lsay_state.json | 状态文件保存路径（相对 bot 运行目录） |

示例：

```
lsay_global_prob=5
lsay_default_mode=mix
lsay_state_file=lsay_state.json
```

机器人超管使用 nonebot 内置配置 `SUPERUSERS`，配置后即可使用超管命令。本插件的命令不依赖 `/` 前缀，直接输入 `lsay` 即可（无需设置 `COMMAND_START`）。

## 🎉 功能

1. **被动整活**：监听文本消息，按概率输出魔改文本；概率单用户独立隔离、互不干扰
2. **随机混搭魔改**：每次触发随机在「纯乱序 / 部分谐音 / 全谐音 / 乱序+谐音」间切换，效果不重样
3. **主动命令**：`lsay 文本` 直接魔改输出；命令有没有空格都行（`lsay on`、`lsayon`、`lsay  on` 等价）
4. **命令别名**：`lsay` / `luan说` / `ssay` / `sao说`
5. **超管控制**：全局开关、全局概率、代用户开启 / 关闭（被 `asoff` 关闭的用户无法自行开启，需联系超管）
6. **语义块乱序**：名词、动词、形容词、时间词参与乱序，标点助词固定，数字 / 英文 / 符号品牌词整块移动
7. **谐音字典外部化**：字典存于 `data/homophone.json`，可用生成脚本重新生成或替换

## 👉 命令

PS：本插件命令无需 `/` 前缀，直接输入即可。命令有无空格等价：`lsay gl show`、`lsayglshow`、`lsay  gl  show` 均能识别。

### 用户命令

| 命令 | 说明 |
|:---:|:---:|
| `lsay 文本` | 魔改并输出该文本；非文本类型（图片 / 表情等）直接抛弃 |
| `lsay on` | 开启插件（默认开启） |
| `lsay off` | 关闭插件 |
| `lsay gl show` | 查看你的触发概率（未自定义则显示全局概率） |
| `lsay gl set N` | 自定义触发概率（N: 1~15，0/100 不允许） |
| `lsay gl noset` | 恢复使用全局默认概率 |
| `lsay help` | 功能菜单（超管会附加超管菜单） |
| `lsay info` | 插件信息 |

例如：`lsay 各位富豪，续费了。`、`lsayon`、`lsay gl set 8`。

### 管理员命令（超管可用）

| 命令 | 说明 |
|:---:|:---:|
| `lsay allon` | 全局开启（默认开启） |
| `lsay alloff` | 全局关闭 |
| `lsay showgl` | 查看全局状态与概率 |
| `lsay setgl N` | 设置全局概率（N: 1~50） |
| `lsay nosetgl` | 恢复插件默认概率（5） |
| `lsay ason ID` | 代用户开启插件 |
| `lsay asoff ID` | 代用户关闭插件（被关闭用户无法自行开启，需联系超管） |

## 🚀 高阶玩法：谐音字典

插件从 `nonebot_plugin_lsay/data/homophone.json` 读取谐音字典，该字典可用 `generate_homophone_json.py` 生成或替换，从而自定义恶搞风格（如加入方言谐音、网络黑话）。

### 内置字典（开箱即用）

默认 `homophone.json` 为 GB2312 一级常用字（约 3700 字），覆盖日常高频字。

### 重新生成字典

```bash
python nonebot_plugin_lsay/data/generate_homophone_json.py --level common     # 常用字（默认）
python nonebot_plugin_lsay/data/generate_homophone_json.py --level extended   # 扩展字集
python nonebot_plugin_lsay/data/generate_homophone_json.py --level all        # 全部字
python nonebot_plugin_lsay/data/generate_homophone_json.py --level all --polyphonic   # 含多音字
python nonebot_plugin_lsay/data/generate_homophone_json.py --compact          # 紧凑格式
```

把生成的 `homophone.json` 放回 `nonebot_plugin_lsay/data/` 即可生效。

## 📝 更新日志

<details>
<summary>展开/收起</summary>

### 26.8.1

- 插件初次发布：谐音恶搞 + 语义块乱序整活机器人
- 被动监听（单用户独立概率）+ 主动 `lsay` 命令（有无空格均可）
- 命令别名：`lsay` / `luan说` / `ssay` / `sao说`
- 超管全局开关、全局概率、代用户开启 / 关闭（`asoff` 后无法自行开启）
- 语义块乱序：名词 / 动词 / 形容词 / 时间词参与，标点助词固定，品牌价格词整块移动
- 谐音字典外部化：`data/homophone.json` + 生成脚本，支持 common / extended / all / 多音字

</details>

## 版权声明

Logo 与插件本体版权归 Chaichaisi 所有，基于 LGPL-2.1 协议开源，**严禁商用**。
