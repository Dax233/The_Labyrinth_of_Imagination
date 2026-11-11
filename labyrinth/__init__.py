"""The Labyrinth of Imagination —— N 维迷宫探索游戏。

重构后的包结构（0.2.0）：

- labyrinth.config   游戏配置（只在 main 里读写 config.ini）
- labyrinth.maze     N 维 DFS 迷宫生成（纯函数，可注入随机源）
- labyrinth.renderer 纯文字渲染与操作指南
- labyrinth.game     指令解析、主循环与主菜单
"""

__version__ = "0.2.0"
__all__ = ["__version__"]
