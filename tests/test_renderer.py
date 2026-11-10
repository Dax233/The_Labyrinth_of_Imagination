"""渲染文案测试：操作指南必须与旧版逐字一致。"""

from __future__ import annotations

import pytest

from labyrinth.config import GameConfig
from labyrinth.renderer import (
    CELL_NAMES,
    HELP_TEXT,
    describe_cell,
    format_status,
)

# 直接从旧版 game.py 的 help 字符串复制，保证重构没有改文案。
LEGACY_HELP_TEXT = (
    "\n\n  操作指南：\n"
    "   w[n]——向前n步，当n被省略时默认向前一步。\n"
    "   q——仰转。\n"
    "   e——俯转。\n"
    "   a[n]——左转至n维方向上，当n被省略时默认转向可转向的最低维度。\n"
    "   d[n]——右转至n维方向上，当n被省略时默认转向可转向的最低维度。\n"
    "   s——向后转。\n"
    "   h——打开操作指南。\n"
    "  r——回到主菜单。\n"
)


def test_help_text_is_byte_identical_to_legacy():
    assert HELP_TEXT == LEGACY_HELP_TEXT


def test_cell_names():
    assert describe_cell("W") == "墙壁"
    assert describe_cell("S") == "出口"
    assert describe_cell("E") == "宝藏"
    assert describe_cell("R") == "道路"
    assert CELL_NAMES == {"W": "墙壁", "S": "出口", "E": "宝藏", "R": "道路"}


def test_unknown_cell_raises():
    with pytest.raises(ValueError):
        describe_cell("?")


def test_format_status_respects_config_flags():
    config = GameConfig()
    position, direction, head = (0, 0), (1, 0), (0, 1)
    assert format_status(config, position, direction, head) == []

    config = GameConfig(show_position=True)
    assert format_status(config, position, direction, head) == ["当前位置：[0, 0]"]

    config = GameConfig(show_direction=True, show_head=True)
    assert format_status(config, position, direction, head) == [
        "当前朝向：[1, 0]",
        "当前头向：[0, 1]",
    ]


def test_status_line_order_matches_legacy():
    config = GameConfig(show_direction=True, show_position=True, show_head=True)
    lines = format_status(config, (1, 2), (3, 4), (5, 6))
    assert lines == [
        "当前朝向：[3, 4]",
        "当前位置：[1, 2]",
        "当前头向：[5, 6]",
    ]
