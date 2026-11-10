"""N 维迷宫生成。

设计要点：

- generate_maze 是纯函数：不碰文件系统、不读全局配置，随机源通过 rng 参数注入，
  方便测试里固定种子复现。
- 仍然沿用旧版的"网格 + 沿坐标轴每次走 2 格"的 DFS，尺寸语义（所有维度边长相同、
  起点在原点、只有奇数坐标才会被完全填满）与旧版一致。
- 旧版用 numpy 多维数组和递归 DFS；这里换成纯 Python 平铺列表 + 显式栈。
  显式栈顺便修掉了旧版在 7 维 5 边长这种规模下会触发 Python 递归深度上限的问题。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator, Sequence

WALL = "W"
ROAD = "R"
START = "S"
END = "E"

#: 难度 -> 依次生成的 (维度, 边长) 列表。数值与旧版 generate_mazes 完全一致。
DIFFICULTY_STAGES: dict[int, tuple[tuple[int, int], ...]] = {
    1: ((2, 3), (2, 5), (2, 7), (2, 9), (2, 11)),
    2: ((2, 5), (2, 9), (3, 3), (3, 5), (3, 7)),
    3: ((3, 5), (3, 6), (3, 7), (3, 8), (4, 3)),
    4: ((2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5)),
}


def difficulty_stages(difficulty: int) -> tuple[tuple[int, int], ...]:
    """返回某难度下的关卡规格；难度非法时抛 ValueError。"""
    try:
        return DIFFICULTY_STAGES[difficulty]
    except KeyError:
        raise ValueError(f"无效的难度：{difficulty}") from None


@dataclass(frozen=True)
class Maze:
    """不可变的 N 维迷宫网格。

    cells 按行主序（C order）平铺，shape 每个维度都是同一个边长。
    需要修改单个格子时用 set()，返回新的 Maze。
    """

    cells: tuple[str, ...]
    shape: tuple[int, ...]

    def __post_init__(self) -> None:
        expected = 1
        for side in self.shape:
            expected *= side
        if expected != len(self.cells):
            raise ValueError(
                f"cells 长度 {len(self.cells)} 与 shape {self.shape} 不匹配"
            )

    @property
    def dimensions(self) -> int:
        return len(self.shape)

    def index_of(self, coords: Sequence[int]) -> int:
        coords = tuple(coords)
        if len(coords) != len(self.shape):
            raise ValueError(f"坐标 {coords} 的维数与迷宫 {self.shape} 不一致")
        index = 0
        for coord, side in zip(coords, self.shape):
            if not 0 <= coord < side:
                raise IndexError(f"坐标 {coords} 超出迷宫范围 {self.shape}")
            index = index * side + coord
        return index

    def at(self, coords: Sequence[int]) -> str:
        return self.cells[self.index_of(coords)]

    def in_bounds(self, coords: Sequence[int]) -> bool:
        return len(coords) == len(self.shape) and all(
            0 <= coord < side for coord, side in zip(coords, self.shape)
        )

    def set(self, coords: Sequence[int], value: str) -> "Maze":
        index = self.index_of(coords)
        cells = list(self.cells)
        cells[index] = value
        return Maze(tuple(cells), self.shape)

    def iter_coords(self) -> Iterator[tuple[int, ...]]:
        """按行主序逐个产出坐标。"""
        for flat_index in range(len(self.cells)):
            remainder = flat_index
            coords = []
            for side in reversed(self.shape):
                coords.append(remainder % side)
                remainder //= side
            yield tuple(reversed(coords))

    def positions_of(self, value: str) -> list[tuple[int, ...]]:
        return [
            coords
            for coords, cell in zip(self.iter_coords(), self.cells)
            if cell == value
        ]


def _shuffled_axes(dimensions: int, rng: random.Random) -> list[int]:
    axes = list(range(dimensions))
    rng.shuffle(axes)
    return axes


def generate_maze(
    dimensions: int, size: int, rng: random.Random | None = None
) -> Maze:
    """用 DFS 生成一个 N 维迷宫，返回带起点 S 与终点 E 的 Maze。

    与旧版相同：只沿坐标轴正方向每次走 2 格，因此偶数边长会留下无法到达的区域；
    为了保持兼容没有加奇偶校验，只是把调用方（DIY 模式）的输入范围原样保留。
    """
    if dimensions < 2:
        raise ValueError("不支持的迷宫维度：至少为 2")
    if size < 3:
        raise ValueError("不支持的迷宫边长：至少为 3")
    if rng is None:
        rng = random.Random()

    shape = (size,) * dimensions
    cells = [WALL] * (size**dimensions)

    def flat_index(coords: Sequence[int]) -> int:
        index = 0
        for coord, side in zip(coords, shape):
            index = index * side + coord
        return index

    def carve(coords: Sequence[int], value: str) -> None:
        cells[flat_index(coords)] = value

    origin = (0,) * dimensions
    carve(origin, ROAD)
    visited = {origin}
    # 和递归版一样：每个格子只在自己第一次被访问时洗一次方向顺序，
    # 之后按该顺序逐个尝试，保证与旧实现的生长顺序一致。
    pending: dict[tuple[int, ...], list[int]] = {
        origin: _shuffled_axes(dimensions, rng)
    }
    stack = [origin]

    while stack:
        current = stack[-1]
        axes = pending[current]
        while axes:
            axis = axes.pop()
            neighbor = list(current)
            neighbor[axis] += 2
            if neighbor[axis] >= size or tuple(neighbor) in visited:
                continue
            between = list(current)
            between[axis] += 1
            carve(tuple(between), ROAD)
            carve(tuple(neighbor), ROAD)
            visited.add(tuple(neighbor))
            pending[tuple(neighbor)] = _shuffled_axes(dimensions, rng)
            stack.append(tuple(neighbor))
            break
        else:
            stack.pop()

    maze = Maze(tuple(cells), shape).set(origin, START)
    roads = maze.positions_of(ROAD)
    end = roads[rng.randrange(len(roads))]
    return maze.set(end, END)
