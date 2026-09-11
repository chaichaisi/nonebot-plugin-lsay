"""
胡乱说 · NoneBot2 插件
插这件说都不会话了 —— 谐音恶搞 + 语义块乱序整活。

被动功能：监听文本消息，按概率（单用户独立）输出魔改文本。
主动功能：lsay 系列命令（用户层 / 超管层 / 全局），命令有无空格均可识别。
"""
import random

from nonebot import get_driver, get_plugin_config, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .config import Config
from .parser import parse
from .state import StateStore
from .transformer import magic_transform
from .version import __version__

__plugin_meta__ = PluginMetadata(
    name="胡乱说",
    description="插这件说都不会话了 —— 谐音恶搞 + 语义块乱序整活",
    usage="lsay 文本 | lsay on/off | lsay gl set N | lsay help",
    config=Config,
    type="application",
    homepage="https://github.com/chaichaisi/nonebot-plugin-lsay",
    supported_adapters={"~onebot.v11"},
)

driver = get_driver()
global_config = driver.config
plugin_config = get_plugin_config(Config)

store = StateStore(plugin_config.lsay_state_file)

lsay_matcher = on_message(priority=1, block=False)

# ---------------- 文案 ----------------

_INTRO = (
    "胡乱说 ~ 插这件说都不会话了\n"
    "用法：lsay 文本 | lsay on/off | lsay gl set N | lsay help"
)

_INFO = (
    "胡乱说插件\n"
    "──────────────\n"
    "插件名：nonebot-plugin-lsay\n"
    "包名：nonebot_plugin_lsay\n"
    "作者：Chaichaisi\n"
    "项目主页：https://github.com/chaichaisi/nonebot-plugin-lsay\n"
    "──────────────\n"
    "版权所有，严禁商用"
)

_USER_MENU = (
    "胡乱说 · 用户菜单\n"
    "────────────────────\n"
    "lsay 文本        魔改文本并输出\n"
    "lsay on          开启插件（默认开启）\n"
    "lsay off         关闭插件\n"
    "lsay gl show     查看你的触发概率\n"
    "lsay gl set N    自定义概率（N: 1~15）\n"
    "lsay gl noset    恢复全局默认概率\n"
    "lsay help        显示本菜单\n"
    "lsay info        插件信息\n"
    "────────────────────\n"
    "概率越大越易触发；群聊/私聊均可用"
)

_SUPER_MENU = (
    "\n\n胡乱说 · 超管菜单\n"
    "────────────────────\n"
    "lsay allon       全局开启（默认开启）\n"
    "lsay alloff      全局关闭\n"
    "lsay showgl      查看全局概率\n"
    "lsay setgl N     设置全局概率（N: 1~50）\n"
    "lsay nosetgl     恢复默认概率（5）\n"
    "lsay ason ID     代用户开启\n"
    "lsay asoff ID    代用户关闭\n"
    "────────────────────\n"
    "被 asoff 关闭的用户需联系超管才能重新开启"
)

_CANT_HANDLE = "（胡乱说）这个我实在魔改不了，换个说法再试试~"


def _is_superuser(uid: str) -> bool:
    supers = getattr(global_config, "superusers", set())
    return str(uid) in {str(s) for s in supers}


def _is_pure_text(message) -> bool:
    return bool(message) and all(getattr(seg, "type", None) == "text" for seg in message)


# ---------------- 被动功能 ----------------

async def _passive_handle(bot: Bot, event: MessageEvent) -> None:
    try:
        uid = event.get_user_id()
        if uid == str(bot.self_id):
            return
        if not store.should_trigger(uid):
            return
        if not _is_pure_text(event.message):
            return
        text = event.message.extract_plain_text().strip()
        if not text:
            return
        result = magic_transform(text, mode=plugin_config.lsay_default_mode,
                                 prob=plugin_config.lsay_homo_prob)
        if not result or result == text:
            return
        await bot.send(event, result)
    except Exception as e:  # noqa: BLE001
        logger.opt(exception=False).warning(f"lsay 被动处理异常: {e}")


# ---------------- 主动命令 ----------------

async def _handle_command(bot: Bot, event: MessageEvent, cmd: dict) -> None:
    uid = event.get_user_id()
    is_super = _is_superuser(uid)
    kind = cmd["kind"]

    async def reply(msg: str):
        await bot.send(event, msg)

    if kind == "intro":
        return await reply(_INTRO)

    if kind == "help":
        menu = _USER_MENU
        if is_super:
            menu += _SUPER_MENU
        return await reply(menu)

    if kind == "info":
        return await reply(_INFO)

    if kind == "text":
        if not _is_pure_text(event.message):
            return  # 非文本类型抛弃
        text = cmd["text"]
        if not text:
            return await reply(_CANT_HANDLE)
        result = None
        for _ in range(5):
            try:
                r = magic_transform(text, mode=plugin_config.lsay_default_mode,
                                    prob=plugin_config.lsay_homo_prob)
            except Exception:
                r = None
            if r and r != text:
                result = r
                break
        if result is None:
            return await reply(_CANT_HANDLE)
        return await reply(result)

    if kind == "user_on":
        u = store.get_user(uid)
        if u.get("forced_off"):
            return await reply("（胡乱说）你已被超管关闭该功能，请联系超管解决。")
        store.set_user_enabled(uid, True)
        return await reply("（胡乱说）已开启，我来给你整活~")

    if kind == "user_off":
        store.set_user_enabled(uid, False)
        return await reply("（胡乱说）已关闭，安静如鸡。")

    if kind == "gl_show":
        u = store.get_user(uid)
        g = store.get_global()
        if u.get("custom_prob"):
            text = f"（胡乱说）你的自定义概率：{u['custom_prob']}（优先于全局）"
        else:
            text = f"（胡乱说）你未自定义，使用全局概率：{g['prob']}"
        return await reply(text)

    if kind == "gl_set":
        val = cmd["value"]
        lo, hi = plugin_config.lsay_user_prob_min, plugin_config.lsay_user_prob_max
        if not (lo <= val <= hi):
            return await reply(
                f"（胡乱说）概率只支持 {lo}~{hi} 的整数，0/100 不允许："
                f"一个是不会触发，一个是每条都触发（会刷屏）。你输入的 {val} 超范围了。")
        store.set_user_custom_prob(uid, val)
        return await reply(f"（胡乱说）已把你的触发概率设为 {val}。")

    if kind == "gl_noset":
        store.set_user_custom_prob(uid, None)
        g = store.get_global()
        return await reply(f"（胡乱说）已恢复全局默认概率（当前全局：{g['prob']}）。")

    if kind == "need_number":
        return await reply(f"（胡乱说）缺少数值参数，用法：{cmd['usage']}")

    if kind == "unknown":
        return await reply(f"（胡乱说）看不懂「{cmd.get('rest', '')}」，试试 lsay help")

    # ---------- 超管命令 ----------
    if not is_super:
        return await reply("（胡乱说）这是超管专属命令，你没有权限哦。")

    if kind == "all_on":
        store.set_global_enabled(True)
        return await reply("（胡乱说）全局已开启，所有会话都能玩！")

    if kind == "all_off":
        store.set_global_enabled(False)
        return await reply("（胡乱说）全局已关闭，所有人都安静了。")

    if kind == "showgl":
        g = store.get_global()
        state_txt = "开启" if g["enabled"] else "关闭"
        return await reply(f"（胡乱说）全局状态：{state_txt}，触发概率：{g['prob']}。")

    if kind == "setgl":
        val = cmd["value"]
        lo, hi = plugin_config.lsay_global_prob_min, plugin_config.lsay_global_prob_max
        if not (lo <= val <= hi):
            return await reply(
                f"（胡乱说）全局概率只支持 {lo}~{hi} 的整数。"
                f"你输入的 {val} 超范围：0 不触发，100 每条都触发（会刷屏）。")
        store.set_global_prob(val)
        return await reply(f"（胡乱说）全局概率已设为 {val}。")

    if kind == "nosetgl":
        store.set_global_prob(5)
        return await reply("（胡乱说）已恢复插件默认概率：5。")

    if kind == "ason":
        store.force_on_user(cmd["uid"])
        return await reply(f"（胡乱说）已代用户 {cmd['uid']} 开启插件。")

    if kind == "asoff":
        store.force_off_user(cmd["uid"])
        return await reply(
            f"（胡乱说）已代用户 {cmd['uid']} 关闭插件。"
            f"该用户之后无法自行 lsay on 开启，需联系超管解决。")

    return await reply("（胡乱说）未知指令，试试 lsay help")


@lsay_matcher.handle()
async def _handler(bot: Bot, event: MessageEvent) -> None:
    try:
        raw = event.message.extract_plain_text()
    except Exception:
        raw = event.get_plaintext()
    cmd = parse(raw)
    if cmd is None:
        await _passive_handle(bot, event)
    else:
        await _handle_command(bot, event, cmd)


@driver.on_startup
async def _startup() -> None:
    logger.info(f"胡乱说 nonebot-plugin-lsay v{__version__} 已加载")
    logger.info(f"全局概率 {store.get_global()['prob']}，插件版本 {__version__}")
