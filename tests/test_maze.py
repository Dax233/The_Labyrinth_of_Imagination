"""迷宫生成的连通性、边界、尺寸语义与难度映射测试。"""

from __future__ import annotations

import random
from collections import deque

import pytest

from labyrinth.maze import (
    DIFFICULTY_STAGES,
    END,
    ROAD,
    START,
    WALL,
    difficulty_stages,
    generate_maze,
)


def reachable_cells(maze, start):
    """从 start 出发，沿非墙格子做 BFS，返回可达坐标集合。"""
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for axis in range(maze.dimensions):
            for delta in (1, -1):
                neighbor = list(current)
                neighbor[axis] += delta
                neighbor = tuple(neighbor)
                if not maze.in_bounds(neighbor):
                    continue
                if neighbor in seen or maze.at(neighbor) == WALL:
                    continue
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


@pytest.mark.parametrize("dimensions,size", [(2, 3), (2, 5), (3, 3), (4, 3)])
def test_shape_and_size_semantics(dimensions, size):
    maze = generate_maze(dimensions, size, random.Random(1))
    assert maze.shape == (size,) * dimensions
    assert maze.dimensions == dimensions
    assert len(maze.cells) == size**dimensions
    # 所有坐标都在范围内，且格子是四种合法字符之一
    for coords in maze.iter_coords():
        cell = maze.at(coords)
        assert cell in {WALL, ROAD, START, END}
        assert maze.in_bounds(coords)


@pytest.mark.parametrize("dimensions,size", [(2, 3), (2, 5), (3, 3), (4, 3), (3, 5)])
def test_start_can_reach_end(dimensions, size):
    maze = generate_maze(dimensions, size, random.Random(42))
    starts = maze.positions_of(START)
    ends = maze.positions_of(END)
    assert len(starts) == 1
    assert len(ends) == 1
    assert starts[0] == (0,) * dimensions
    assert ends[0] in reachable_cells(maze, starts[0])


def test_every_road_belongs_to_the_same_component():
    """DFS 生成的是连通图：所有道路格子都从起点可达（奇数边长时）。"""
    maze = generate_maze(3, 3, random.Random(2026))
    start = maze.positions_of(START)[0]
    reachable = reachable_cells(maze, start)
    for coords in maze.positions_of(ROAD):
        assert coords in reachable


def test_generation_is_deterministic_with_injected_rng():
    left = generate_maze(2, 5, random.Random(1234))
    right = generate_maze(2, 5, random.Random(1234))
    assert left == right

    other = generate_maze(2, 5, random.Random(4321))
    assert other != left


def test_maze_is_immutable():
    maze = generate_maze(2, 3, random.Random(0))
    changed = maze.set((0, 0), WALL)
    assert maze.at((0, 0)) == START
    assert changed.at((0, 0)) == WALL
    assert changed.shape == maze.shape


def test_difficulty_table_matches_legacy_mapping():
    """数值必须和旧版 generate_mazes 完全一致。"""
    assert difficulty_stages(1) == (
        (2, 3),
        (2, 5),
        (2, 7),
        (2, 9),
        (2, 11),
    )
    assert difficulty_stages(2) == ((2, 5), (2, 9), (3, 3), (3, 5), (3, 7))
    assert difficulty_stages(3) == ((3, 5), (3, 6), (3, 7), (3, 8), (4, 3))
    assert difficulty_stages(4) == (
        (2, 5),
        (3, 5),
        (4, 5),
        (5, 5),
        (6, 5),
        (7, 5),
    )
    assert set(DIFFICULTY_STAGES) == {1, 2, 3, 4}


def test_invalid_difficulty_raises():
    with pytest.raises(ValueError):
        difficulty_stages(0)
    with pytest.raises(ValueError):
        difficulty_stages(5)


@pytest.mark.parametrize("dimensions,size", [(1, 3), (2, 2), (0, 3), (2, 0)])
def test_invalid_generation_arguments(dimensions, size):
    with pytest.raises(ValueError):
        generate_maze(dimensions, size, random.Random(0))


def test_index_and_bounds_helpers():
    maze = generate_maze(2, 3, random.Random(0))
    with pytest.raises(IndexError):
        maze.at((3, 0))
    with pytest.raises(ValueError):
        maze.at((0, 0, 0))
    assert maze.in_bounds((2, 2))
    assert not maze.in_bounds((3, 2))
    assert not maze.in_bounds((-1, 0))
