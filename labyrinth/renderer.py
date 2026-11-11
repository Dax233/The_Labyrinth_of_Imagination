"""纯文字渲染：操作指南、格子名称、状态行。

这里不做任何输入输出，只负责把游戏状态翻译成字符串，方便单元测试。
"""

from __future__ import annotations

from typing import Sequence

from .config import GameConfig

#: 操作指南文案与旧版逐字一致（包括 r 前少一个空格的历史缩进）。
HELP_TEXT = (
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

CELL_NAMES = {
    "W": "墙壁",
    "S": "出口",
    "E": "宝藏",
    "R": "道路",
}


def describe_cell(cell: str) -> str:
    """把迷宫格子字符翻译成给玩家看的名字。"""
    try:
        return CELL_NAMES[cell]
    except KeyError:
        raise ValueError(f"未知的迷宫格子：{cell!r}") from None


def format_status(
    config: GameConfig,
    position: Sequence[int],
    direction: Sequence[int],
    head: Sequence[int],
) -> list[str]:
    """按配置开关生成状态行，顺序与旧版一致：朝向、位置、头向。"""
    lines: list[str] = []
    if config.show_direction:
        lines.append(f"当前朝向：{list(direction)}")
    if config.show_position:
        lines.append(f"当前位置：{list(position)}")
    if config.show_head:
        lines.append(f"当前头向：{list(head)}")
    return lines
