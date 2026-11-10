"""让 python -m labyrinth 可以直接启动游戏。"""

from .game import main

if __name__ == "__main__":
    raise SystemExit(main())
