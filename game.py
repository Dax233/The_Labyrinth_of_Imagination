"""兼容旧入口：python game.py。

真正的实现已经拆到 labyrinth 包里，新用法是 python -m labyrinth。
保留这个文件只是为了让老的启动方式继续能跑。
"""

from labyrinth.game import main

if __name__ == "__main__":
    raise SystemExit(main())
