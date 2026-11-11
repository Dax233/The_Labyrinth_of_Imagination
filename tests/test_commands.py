"""指令解析与转向几何的测试。"""

from __future__ import annotations

import pytest

from labyrinth.game import (
    _MSG_HEAD_DIMENSION,
    _MSG_INVALID,
    _MSG_MAX_DIMENSION,
    _MSG_TWO_DIMENSIONS,
    Command,
    describe_ahead,
    move_forward,
    parse_command,
    turn,
)
from labyrinth.maze import END, ROAD, WALL, generate_maze
from labyrinth.renderer import describe_cell

DIRECTION = (1, 0, 0)
HEAD = (0, 1, 0)


def parse(raw, dimensions=3, direction=DIRECTION, head=HEAD):
    return parse_command(raw, dimensions, direction, head)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("w", Command("w", amount=1, dim=0)),
        ("w3", Command("w", amount=3, dim=3)),
        ("w0", Command("w", amount=0, dim=0)),
        ("s", Command("s")),
        ("q", Command("q")),
        ("e", Command("e")),
        ("h", Command("h")),
        ("r", Command("r")),
    ],
)
def test_legal_commands(raw, expected):
    result = parse(raw)
    assert result.error is None
    assert result.command == expected


def test_turn_dimension_commands():
    # a3 -> 转向第 3 维（0 基下标 2）
    result = parse("a3")
    assert result.command == Command("a", dim=2)
    result = parse("d3")
    assert result.command == Command("d", dim=2)


def test_a1_resets_to_default_dimension_because_zero_is_sentinel():
    """历史约定：下标 0 同时当"未指定"，所以 a1 等价于 a。"""
    assert parse("a1").command == Command("a", dim=0)


def test_turning_to_head_axis_is_rejected():
    result = parse("a2")  # 第 2 维 = head 所在轴（下标 1）
    assert result.command is None
    assert result.error == _MSG_HEAD_DIMENSION


def test_turning_beyond_max_dimension_is_rejected():
    result = parse("a4")
    assert result.command is None
    assert result.error == _MSG_MAX_DIMENSION


def test_two_dimensional_world_rejects_left_right():
    result = parse("a", dimensions=2, direction=(1, 0), head=(0, 1))
    assert result.command is None
    assert result.error == _MSG_TWO_DIMENSIONS


@pytest.mark.parametrize(
    "raw",
    ["", "W", "q2", "s1", "w-1", "a1x", "wd", " h", "r ", "1", "向前", "w 1"],
)
def test_illegal_commands(raw):
    result = parse(raw)
    assert result.command is None
    assert result.error == _MSG_INVALID


def test_parse_does_not_need_maze_state():
    """解析只依赖维度/朝向/头向，不依赖迷宫本身，方便单测。"""
    for raw in ("w", "s", "q", "e", "h", "r"):
        assert parse(raw).error is None


def test_turn_backwards_negates_direction():
    direction, head = turn(DIRECTION, HEAD, 0, 3, "s")
    assert direction == (-1, 0, 0)
    assert head == HEAD


def test_turn_pitch_up_and_down_swaps_direction_and_head():
    direction, head = turn(DIRECTION, HEAD, 0, 3, "q")
    assert direction == HEAD
    assert head == (-1, 0, 0)

    direction, head = turn(DIRECTION, HEAD, 0, 3, "e")
    assert direction == (0, -1, 0)
    assert head == DIRECTION


def test_turn_left_and_right_use_cross_product():
    direction, head = turn(DIRECTION, HEAD, 2, 3, "a")
    assert direction == (0, 0, -1)
    assert head == HEAD

    direction, head = turn(DIRECTION, HEAD, 2, 3, "d")
    assert direction == (0, 0, 1)
    assert head == HEAD


def test_turn_default_dimension_picks_lowest_available_axis():
    direction, head = turn(DIRECTION, HEAD, 0, 3, "d")
    assert direction == (0, 0, 1)
    assert head == HEAD


def test_unknown_turn_action_raises():
    with pytest.raises(ValueError):
        turn(DIRECTION, HEAD, 0, 3, "x")


def test_describe_ahead_wall_and_out_of_bounds():
    maze = generate_maze(2, 3, rng=__import__("random").Random(0))
    # 原点朝 -x 方向一定越界
    assert describe_ahead(maze, (0, 0), (-1, 0)) == "墙壁"
    # 找一面墙
    wall_positions = maze.positions_of(WALL)
    for position in maze.positions_of(ROAD):
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ahead = tuple(p + d for p, d in zip(position, direction))
            if maze.in_bounds(ahead) and maze.at(ahead) == WALL:
                assert describe_ahead(maze, position, direction) == "墙壁"
                return
    pytest.skip("这个种子生成的迷宫没有相邻墙壁，跳过")


def test_describe_ahead_uses_renderer_names():
    maze = generate_maze(2, 3, rng=__import__("random").Random(0))
    end = maze.positions_of(END)[0]
    # 从终点旁边朝向终点
    for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        position = (end[0] - direction[0], end[1] - direction[1])
        if maze.in_bounds(position):
            assert describe_ahead(maze, position, direction) == describe_cell(END)
            return
    pytest.skip("终点贴着边界，找不到相邻格，跳过")


def test_move_forward_stops_at_wall():
    maze = generate_maze(2, 3, rng=__import__("random").Random(0))
    lines: list[str] = []
    # 从原点朝 -x 走，第一步就撞墙
    position = move_forward(maze, (0, 0), (-1, 0), 3, lines.append)
    assert position == (0, 0)
    assert lines == ["向前移动了0格，撞到了墙壁"]


def test_move_forward_moves_along_road():
    maze = generate_maze(2, 5, rng=__import__("random").Random(0))
    lines: list[str] = []
    position = move_forward(maze, (0, 0), (1, 0), 1, lines.append)
    assert position == (1, 0)
    assert lines[0].startswith("向前移动了1格，前方是")
