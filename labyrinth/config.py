"""游戏配置。

旧版在 import 阶段就会创建并读取 config.ini（副作用、且依赖当前工作目录）。
重构后这里只提供数据类与显式读写方法，由 labyrinth.game.main 在启动时调用。
配置节与键名保持和旧版完全一致，老的 config.ini 可以直接继续用。
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_FILENAME = "config.ini"
CONFIG_SECTION = "Game Settings"
CONFIG_KEYS = ("show_position", "show_direction", "show_head")


@dataclass(frozen=True)
class GameConfig:
    """三个开关默认都是关闭的，与旧版新建的 config.ini 一致。"""

    show_position: bool = False
    show_direction: bool = False
    show_head: bool = False

    @classmethod
    def load(cls, path: str | Path = DEFAULT_CONFIG_FILENAME) -> "GameConfig":
        """读取配置；文件或字段缺失时回退到默认值，不抛异常。"""
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        parser = configparser.ConfigParser()
        # 旧版用平台默认编码写文件，这里优先按 UTF-8 读，失败再退回默认编码。
        try:
            parser.read(config_path, encoding="utf-8")
        except UnicodeDecodeError:
            parser = configparser.ConfigParser()
            parser.read(config_path)

        if not parser.has_section(CONFIG_SECTION):
            return cls()

        values: dict[str, bool] = {}
        for key in CONFIG_KEYS:
            try:
                values[key] = parser.getboolean(CONFIG_SECTION, key)
            except (configparser.NoOptionError, ValueError):
                values[key] = False
        return cls(**values)

    @classmethod
    def load_or_create(cls, path: str | Path = DEFAULT_CONFIG_FILENAME) -> "GameConfig":
        """旧版在 import 时"没有就创建"，这里把这一步显式化到 main。"""
        config_path = Path(path)
        if not config_path.exists():
            config = cls()
            config.save(config_path)
            return config
        return cls.load(config_path)

    def save(self, path: str | Path = DEFAULT_CONFIG_FILENAME) -> None:
        parser = configparser.ConfigParser()
        parser.add_section(CONFIG_SECTION)
        for key in CONFIG_KEYS:
            parser.set(CONFIG_SECTION, key, str(getattr(self, key)))
        with open(path, "w", encoding="utf-8") as config_file:
            parser.write(config_file)
