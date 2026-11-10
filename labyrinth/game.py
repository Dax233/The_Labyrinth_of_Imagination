"""指令解析、单关卡循环、主菜单与程序入口。

玩法与文案都沿用旧版：w[n] / q / e / a[n] / d[n] / s / h / r，
只把原来挤在 game.py 一个命名空间里的东西拆开并加上可测试的纯函数。
"""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from typing import Callable, Sequence

from .config import DEFAULT_CONFIG_FILENAME, GameConfig
from .maze import END, ROAD, WALL, Maze, difficulty_stages, generate_maze
from .renderer import HELP_TEXT, describe_cell, format_status

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]

_COMMAND_PATTERN = re.compile(r"^(w[0-9]*|a[0-9]*|s|d[0-9]*|q|e)$")

_MSG_TWO_DIMENSIONS = r"二维世界里没有左右哦~请用q\e转向吧！"
_MSG_HEAD_DIMENSION = r"如果要转向到头顶和脚下，请使用q\e指令哦~"
_MSG_MAX_DIMENSION = "不可转向到当前迷宫所拥有的最大维数哦~"
_MSG_INVALID = "无效的输入！"

_MENU_TEXT = "[1]开始游戏 [2]自定义模式 [3]退出游戏"
_PROMPT_CHOICE = "请输入你的选择："
_PROMPT_COMMAND = "\n请输入指令："


@dataclass(frozen=True)
class Command:
    """解析后的指令。action 取值：w/a/d/s/q/e/h/r。"""

    action: str
    amount: int = 1
    dim: int = 0

    @property
    def is_turn(self) -> bool:
        return self.action in "sadqe"


@dataclass(frozen=True)
class ParseResult:
    command: Command | None = None
    error: str | None = None


def _axis_of(vector: Sequence[int]) -> int:
    for axis, value in enumerate(vector):
        if value:
            return axis
    raise ValueError("方向向量不能是零向量")


def parse_command(
    raw: str,
    dimensions: int,
    direction: Sequence[int],
    head: Sequence[int],
) -> ParseResult:
    """把一行玩家输入解析成 Command，非法输入返回错误文案。

    校验顺序和提示语都照抄旧版实现，包括"二维世界不能用 a/d"这类特殊提示。
    """
    if raw == "h":
        return ParseResult(Command("h"))
    if raw == "r":
        return ParseResult(Command("r"))
    if not _COMMAND_PATTERN.fullmatch(raw):
        return ParseResult(error=_MSG_INVALID)

    action = raw[0]
    if action in "ad" and dimensions == 2:
        return ParseResult(error=_MSG_TWO_DIMENSIONS)

    head_axis = _axis_of(head)
    direction_axis = _axis_of(direction)

    dim = 0
    if action == "w" and len(raw) > 1:
        dim = int(raw[1:])
    elif action in "ad":
        if len(raw) > 1:
            dim = int(raw[1:]) - 1
            if dim == head_axis:
                return ParseResult(error=_MSG_HEAD_DIMENSION)
            if dim > dimensions - 1:
                return ParseResult(error=_MSG_MAX_DIMENSION)
        if dim == direction_axis:
            dim = 0

    if action == "w":
        amount = int(raw[1:]) if len(raw) > 1 else 1
        return ParseResult(Command("w", amount=amount, dim=dim))
    return ParseResult(Command(action, dim=dim))


def _negate(vector: Sequence[int]) -> tuple[int, ...]:
    return tuple(-value for value in vector)


def _cross3(left: Sequence[int], right: Sequence[int]) -> tuple[int, int, int]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def turn(
    direction: Sequence[int],
    head: Sequence[int],
    dim: int,
    dimensions: int,
    action: str,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """执行转向，返回新的 (direction, head)。几何规则与旧版一致。"""
    direction = tuple(int(value) for value in direction)
    head = tuple(int(value) for value in head)

    if action == "s":
        return _negate(direction), head
    if action == "q":
        return head, _negate(direction)
    if action == "e":
        return _negate(head), direction
    if action not in "ad":
        raise ValueError(f"未知的转向指令：{action}")

    head_axis = _axis_of(head)
    direction_axis = _axis_of(direction)
    # dim 用 0 当作"未指定"的哨兵值，这是旧版的历史约定，原样保留。
    if dim != 0:
        target_axis = dim
    else:
        candidates = [
            axis
            for axis in range(dimensions)
            if axis not in (head_axis, direction_axis)
        ]
        target_axis = min(candidates)

    mapping = sorted([head_axis, direction_axis, target_axis])
    direction_3d = [direction[axis] for axis in mapping]
    head_3d = [head[axis] for axis in mapping]
    cross = _cross3(head_3d, direction_3d)
    result = cross if action == "a" else _negate(cross)

    new_direction = list(direction)
    for offset, axis in enumerate(mapping):
        new_direction[axis] = result[offset]
    return tuple(new_direction), head


def describe_ahead(
    maze: Maze, position: Sequence[int], direction: Sequence[int]
) -> str:
    """返回"前方是……"里的描述；越界和墙都算墙壁。"""
    ahead = tuple(p + d for p, d in zip(position, direction))
    if not maze.in_bounds(ahead):
        return "墙壁"
    return describe_cell(maze.at(ahead))


def move_forward(
    maze: Maze,
    position: Sequence[int],
    direction: Sequence[int],
    steps: int,
    output_fn: OutputFn = print,
) -> tuple[int, ...]:
    """沿当前朝向走 steps 步，撞墙就停在原地并输出提示。"""
    position = tuple(position)
    for step in range(steps):
        new_position = tuple(p + d for p, d in zip(position, direction))
        if not maze.in_bounds(new_position) or maze.at(new_position) == WALL:
            output_fn(f"向前移动了{step}格，撞到了墙壁")
            break
        position = new_position
        output_fn(
            f"向前移动了{min(steps, step + 1)}格，前方是"
            f"{describe_ahead(maze, position, direction)}"
        )
    return position


def _read_command(
    dimensions: int,
    direction: Sequence[int],
    head: Sequence[int],
    input_fn: InputFn,
    output_fn: OutputFn,
) -> Command:
    while True:
        raw = input_fn(_PROMPT_COMMAND)
        result = parse_command(raw, dimensions, direction, head)
        if result.error is not None:
            output_fn(result.error)
            continue
        assert result.command is not None
        if result.command.action == "h":
            output_fn(HELP_TEXT)
            continue
        return result.command


def play_stage(
    maze: Maze,
    config: GameConfig,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> bool | str:
    """玩一个关卡。返回 True 表示通关，"restart" 表示玩家选择回主菜单。"""
    dimensions = maze.dimensions
    position = (0,) * dimensions
    direction = tuple(1 if axis == 0 else 0 for axis in range(dimensions))
    head = tuple(1 if axis == 1 else 0 for axis in range(dimensions))
    reached_end = False

    while True:
        for line in format_status(config, position, direction, head):
            output_fn(line)
        output_fn(f"前方是：{describe_ahead(maze, position, direction)}")

        command = _read_command(dimensions, direction, head, input_fn, output_fn)
        if command.action == "r":
            return "restart"
        if command.action == "w":
            position = move_forward(
                maze, position, direction, command.amount, output_fn
            )
        else:
            direction, head = turn(
                direction, head, command.dim, dimensions, command.action
            )
            output_fn(
                f"转向后，前方是{describe_ahead(maze, position, direction)}"
            )

        if maze.at(position) == END:
            output_fn("到达终点")
            maze = maze.set(position, ROAD)
            reached_end = True
        elif position == (0,) * dimensions and reached_end:
            output_fn("成功返回起点，你赢了！")
            return True


def _build_stages(
    difficulty: int, rng: random.Random | None = None
) -> list[tuple[str, Maze]]:
    return [
        (f"stage{index}", generate_maze(dimensions, size, rng))
        for index, (dimensions, size) in enumerate(
            difficulty_stages(difficulty), start=1
        )
    ]


def _ask_difficulty(input_fn: InputFn, output_fn: OutputFn) -> int:
    while True:
        raw = input_fn(_PROMPT_CHOICE)
        if raw.isdigit() and int(raw) in (1, 2, 3, 4):
            return int(raw)
        output_fn("无效的输入，请重新输入")


def _ask_dimensions(input_fn: InputFn, output_fn: OutputFn) -> int:
    while True:
        raw = input_fn(
            "请输入迷宫的维度(维度越高，生成迷宫的时间越长，地图文件越大，"
            "请注意内存和存储和时间上的安排)："
        )
        if not raw.isdigit():
            output_fn("请输入一个有效的数字")
            continue
        dimensions = int(raw)
        if dimensions < 2:
            output_fn("不支持创建维度小于2的迷宫哦~")
            continue
        if dimensions > 29:
            output_fn(
                "达X太懒了还没做能够超过29维度的迷宫的功能QAQ~"
                "请重新输入你的维度信息吧~"
            )
            continue
        return dimensions


def _ask_size(input_fn: InputFn, output_fn: OutputFn) -> int:
    while True:
        raw = input_fn("请输入迷宫的边长：")
        if not raw.isdigit():
            output_fn("请输入一个有效的数字")
            continue
        size = int(raw)
        if size < 3:
            output_fn("不支持创建边长小于3的迷宫哦~")
            continue
        if size > 29:
            output_fn(
                "达X太懒了还没做能够超过29边长的迷宫的功能QAQ~"
                "请重新输入你的边长信息吧~"
            )
            continue
        return size


def game(
    config: GameConfig,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
    rng: random.Random | None = None,
) -> bool:
    """主菜单 + 依次游玩所有关卡。返回 False 表示玩家选择退出游戏。"""
    while True:
        output_fn(_MENU_TEXT)
        choice = input_fn(_PROMPT_CHOICE)
        if choice == "1":
            output_fn("请选择难度：[1] [2] [3] [4]")
            difficulty = _ask_difficulty(input_fn, output_fn)
            stages = _build_stages(difficulty, rng)
            break
        if choice == "2":
            dimensions = _ask_dimensions(input_fn, output_fn)
            size = _ask_size(input_fn, output_fn)
            stages = [("stage1", generate_maze(dimensions, size, rng))]
            break
        if choice == "3":
            output_fn("退出游戏")
            return False
        output_fn("无效的输入，请重新输入")

    start_time = time.time()
    for name, maze in stages:
        output_fn(
            f"\n\n{name}：{maze.dimensions}维迷宫，边长{maze.shape[0]}\n"
        )
        result = play_stage(maze, config, input_fn, output_fn)
        if result == "restart":
            return True
        if not result:
            output_fn("你输了")
            break
    else:
        output_fn("恭喜你，你完成了所有的关卡！")
        output_fn(f"你的总游玩时间是：{time.time() - start_time}秒")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """python -m labyrinth 的入口：启动时才读写 config.ini。"""
    config = GameConfig.load_or_create(DEFAULT_CONFIG_FILENAME)
    output_fn = print
    output_fn(HELP_TEXT)
    running = True
    while running:
        running = game(config)
        output_fn("游戏结束，开启新游戏或者右上角直接关闭游戏\n\n")
    return 0
