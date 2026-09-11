from pydantic import BaseModel, Field

from .version import __version__


class Config(BaseModel):
    """胡乱说插件配置项（可在 .env 中覆盖）"""

    # 全局默认开启状态
    lsay_global_enabled: bool = True
    # 全局默认触发概率（1~50，越大越容易触发；默认 5）
    lsay_global_prob: int = 5
    # 普通用户可设置的概率范围（1~15）
    lsay_user_prob_min: int = 1
    lsay_user_prob_max: int = 15
    # 超管可设置的全局概率范围（1~50）
    lsay_global_prob_min: int = 1
    lsay_global_prob_max: int = 50
    # 谐音替换概率（0~1，魔改内部参数）
    lsay_homo_prob: float = 0.35
    # 魔改模式: shuffle | homo | mix
    lsay_default_mode: str = "mix"
    # 状态文件保存路径（相对 NoneBot 运行目录）
    lsay_state_file: str = "lsay_state.json"
    # 插件版本号
    lsay_version: str = Field(default=__version__)
