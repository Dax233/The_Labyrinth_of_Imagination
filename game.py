import os
import re
import time
import random
import numpy as np
import configparser

def create_config():
    config = configparser.ConfigParser()
    config.add_section("Game Settings")
    config.set("Game Settings", "show_position", "False")
    config.set("Game Settings", "show_direction", "False")
    config.set("Game Settings", "show_head", "False")

    with open("config.ini", "w") as config_file:
        config.write(config_file)

def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    show_position = config.getboolean("Game Settings", "show_position")
    show_direction = config.getboolean("Game Settings", "show_direction")
    show_head = config.getboolean("Game Settings", "show_head")
    return show_position, show_direction, show_head

# 在游戏开始时创建配置文件
if not os.path.exists('config.ini'):
    create_config()

# 在游戏过程中读取配置文件
show_position, show_direction, show_head = read_config()

help="\n\n  操作指南：\n   w[n]——向前n步，当n被省略时默认向前一步。\n   q——仰转。\n   e——俯转。\n   a[n]——左转至n维方向上，当n被省略时默认转向可转向的最低维度。\n   d[n]——右转至n维方向上，当n被省略时默认转向可转向的最低维度。\n   s——向后转。\n   h——打开操作指南。\n  r——回到主菜单。\n"


def generate_maze(dimensions, size):
    # 初始化一个空的迷宫网格，所有位置都标记为墙壁
    maze = np.full([size]*dimensions, 'W')

    # 定义一个递归函数来进行深度优先搜索
    def dfs(coords):
        # 标记当前位置为道路
        maze[tuple(coords)] = 'R'

        # 随机打乱所有方向的顺序
        directions = list(np.eye(dimensions, dtype=int))
        random.shuffle(directions)

        for direction in directions:
            new_coords = [coords[i] + 2*direction[i] for i in range(dimensions)]
            if all(0 <= new_coords[i] < size for i in range(dimensions)) and maze[tuple(new_coords)] == 'W':
                # 如果相邻位置是墙壁，打通并继续DFS
                maze[tuple((coords[i] + direction[i]) for i in range(dimensions))] = 'R'
                dfs(new_coords)

    # 从起点开始DFS
    dfs([0]*dimensions)
    # save_maze(maze, "temp")
    maze[tuple([0]*dimensions)] = 'S'
    # 随机选择一个标记为 'R' 的位置作为终点
    road_positions = np.argwhere(maze == 'R')
    end_coords = road_positions[random.randint(0, len(road_positions) - 1)]
    maze[tuple(end_coords)] = 'E'

    # # 打开文件并写入调试信息
    # with open('debug.txt', 'w') as f:
    #     # 遍历迷宫的每一个格子
    #     for index in np.ndindex(maze.shape):
    #         # 将坐标和对应的值写入到文件中
    #         f.write(f'{index}: {maze[index]}\n')

    return maze


def generate_mazes(difficulty):
    clear_maps()
    if difficulty == 1:
        dimensions, size = 2, 3
        for i in range(5):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 2
    elif difficulty == 2:
        dimensions, size = 2, 5
        for i in range(2):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 4
        dimensions, size = 3, 3
        for i in range(2, 5):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 2
    elif difficulty == 3:
        dimensions, size = 3, 5
        for i in range(4):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 1
        dimensions, size = 4, 3
        maze = generate_maze(dimensions, size)
        save_maze(maze, f"maps/stage10")
    elif difficulty == 4:
        size = 5
        for i in range(6):
            dimensions = i + 2
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
    else:
        print("无效的输入，请重新输入")
        game()

def save_maze(maze, filename):
    np.save(filename, maze)
    with open (filename+".txt", 'w', encoding="utf-8") as f:
        f. write(str(maze))

def clear_maps():
    for filename in os.listdir('maps'):
        os.remove(os.path.join('maps', filename))



def play_game(maze, dimensions, size):
    # 初始化玩家位置和朝向
    position = np.array([0]*dimensions, dtype=int)
    direction = np.eye(dimensions, dtype=int)[0]  # 初始朝向为第一个维度的正方向
    head = np.eye(dimensions, dtype=int)[1]
    
    # 定义一个函数来获取前方的情况
    def get_ahead(position, direction):
        ahead = position + direction
        size = np.array(maze.shape)

        if any(p < 0 or p >= s for p, s in zip(ahead, size)) or maze[tuple(ahead.astype(int))] == 'W':
            return '墙壁'
        else:
            if maze[tuple(ahead.astype(int))] == 'W':
                ahead = '墙壁'
            elif maze[tuple(ahead.astype(int))] == 'S':
                ahead = '出口'
            elif maze[tuple(ahead.astype(int))] == 'E':
                ahead = '宝藏'
            elif maze[tuple(ahead.astype(int))] == 'R':
                ahead = '道路'
            return ahead

    # 定义一个函数来处理移动
    def move_forward(move, dim, position, direction):
        for _ in range(move):
            new_position = position + direction
            if any(p < 0 or p >= size for p in new_position) or maze[tuple(new_position.astype(int))] == 'W':
                print(f"向前移动了{_}格，撞到了墙壁")
                break
            else:
                position = new_position
                print(f"向前移动了{min(move, _+1)}格，前方是{get_ahead(position, direction)}")
        return position

    def turn(direction, head, dim, dimensions, command):
        if command == 's':
            direction = -direction  # 向后转，朝向向量反向
        elif command == 'q':
            direction, head = head, -direction  # 仰转90度
        elif command == 'e':
            direction, head = -head, direction  # 俯转90度
        elif command in 'ad':
            # 检测头向量，面向量所在维度轴
            non_zero_indices_d = np.nonzero(direction)
            non_zero_indices_h = np.nonzero(head)
            head_dim = non_zero_indices_h[0][0]
            direction_dim = non_zero_indices_d[0][0]
            # 检测指令输入中是否包含n参数
            n = dim if dim != 0 else min(set(range(dimensions)) - {head_dim, direction_dim})
            # 将数据预处理为三维空间的数据
            mapping = sorted([head_dim, direction_dim, n])
            direction_3d = np.array([direction[i] for i in mapping])
            head_3d = np.array([head[i] for i in mapping])
            # 计算头向量和朝向向量的叉积，得到垂直向量
            cross_product = np.cross(head_3d, direction_3d)
            # 根据命令选择叉积符号
            direction_3d = cross_product if command[0] == 'a' else -cross_product
            # 将结果转换回原来的高维空间
            for i, j in enumerate(mapping):
                direction[j] = direction_3d[i]
        return direction, head

    # 初始化dim变量的值
    dim = 0

    # 初始化一个标志位来检查是否已经到达过终点
    reached_end = False

    while True:
        # 打印当前位置和朝向
        if show_direction:
            print(f"当前朝向：{list(map(int, direction))}")
        if show_position:
            print(f"当前位置：{list(map(int, position))}")
        if show_head:
            print(f"当前头向：{list(map(int, head))}")
        print(f"前方是：{get_ahead(position, direction)}")

        def input_command():
            while True:
                # 获取玩家输入
                command = input("\n请输入指令：")
                if command == 'h':
                    print(help)
                    continue

                if command == 'r':
                    return 'restart', 0

                # 解析玩家输入
                match = re.match(r'^(w[0-9]*|a[0-9]*|s|d[0-9]*|q|e)$', command)

                # 检测头向量，面向量所在维度轴
                non_zero_indices_d = np.nonzero(direction)
                non_zero_indices_h = np.nonzero(head)
                head_dim = non_zero_indices_h[0][0]
                direction_dim = non_zero_indices_d[0][0]

                if match:
                    if command[0] in 'ad' and dimensions == 2:
                        print("二维世界里没有左右哦~请用q\e转向吧！")
                        continue

                    if command[0] in 'w' and len(command) > 1:
                        dim = int(command[1:])
                    else:
                        dim = 0

                    if command[0] in 'ad' and len(command) > 1:
                        dim = int(command[1:]) - 1
                        if dim == head_dim:
                            print("如果要转向到头顶和脚下，请使用q\e指令哦~")
                            continue
                        # print(f"dim：{dim}")
                        # print(f"dimensions：{dimensions}")
                        if dim > dimensions - 1:
                            print("不可转向到当前迷宫所拥有的最大维数哦~")
                            continue
                    else:
                        dim = 0



                    if command[0] in 'ad' and dim == direction_dim :
                        dim = 0
                    return command, dim
                else:
                    print("无效的输入！")
        
        command, dim = input_command()

        if command == 'restart':
            return 'restart'

        if command[0] in 'wasdeq':
            move = int(command[1:]) if len(command) > 1 else 1
            if command[0] == 'w':
                position = move_forward(move, dim, position, direction)
            elif command[0] in 'sdeqa':
                direction, head = turn(direction, head, dim, dimensions, command[0])
                print(f"转向后，前方是{get_ahead(position, direction)}")

        # 检查是否到达终点并返回起点
        if maze[tuple(position)] == 'E':
            print("到达终点")
            maze[tuple(position)] = 'R'
            reached_end = True
        elif (position == [0]*dimensions).all() and reached_end:
            print("成功返回起点，你赢了！")
            return True


def game():
    while True:
        print("[1]开始游戏 [2]自定义模式 [3]退出游戏")
        choice = input("请输入你的选择：")
        if choice == '1':
            print("请选择难度：[1] [2] [3] [4]")
            difficulty = int(input("请输入你的选择："))
            generate_mazes(difficulty)
            break
        elif choice == '2':

            def diy1():
                while True:
                    dimensions = input("请输入迷宫的维度(维度越高，生成迷宫的时间越长，地图文件越大，请注意内存和存储和时间上的安排)：")
                    if not dimensions.isdigit():
                        print("请输入一个有效的数字")
                        continue
                    dimensions = int(dimensions)
                    if dimensions < 2 :
                        print("不支持创建维度小于2的迷宫哦~")
                        continue
                    if dimensions > 29 :
                        print("达X太懒了还没做能够超过29维度的迷宫的功能QAQ~请重新输入你的维度信息吧~")
                        continue
                    return dimensions

            def diy2():
                while True:
                    size = input("请输入迷宫的边长：")
                    if not size.isdigit():
                        print("请输入一个有效的数字")
                        continue
                    size = int(size)
                    if size < 3 :
                        print("不支持创建边长小于3的迷宫哦~")
                        continue
                    if size > 29 :
                        print("达X太懒了还没做能够超过29边长的迷宫的功能QAQ~请重新输入你的边长信息吧~")
                        continue
                    return size

            dimensions = diy1()
            size = diy2()


            clear_maps()
            maze = generate_maze(dimensions, size)
            save_maze(maze, "maps/stage1")
            break
        elif choice == '3':
            print("退出游戏")
            return False
        else:
            print("无效的输入，请重新输入")

    # 在每个关卡开始时，加载迷宫并开始游戏
    start_time = time.time()
    stages = sorted([f for f in os.listdir('maps') if f.startswith('stage') and f.endswith('.npy')])
    for stage in stages:
        maze = np.load(os.path.join('maps', stage))
        dimensions = len(maze.shape)
        size = maze.shape[0]
        print(f"\n\n{stage[:-4]}：{dimensions}维迷宫，边长{size}\n")
        result = play_game(maze, dimensions, size)
        if result == 'restart':  # 检查特殊的值
            return True  # 结束当前的游戏并开始新的游戏
        elif not result:
            print("你输了")
            break
    else:
        end_time = time.time()
        print("恭喜你，你完成了所有的关卡！")
        print(f"你的总游玩时间是：{end_time - start_time}秒")
    return True



if __name__ == "__main__":
    if not os.path.exists('maps'):
        os.makedirs('maps')
    loop = True
    print(help)
    while loop :
        loop = game()
        print('游戏结束，开启新游戏或者右上角直接关闭游戏\n\n')