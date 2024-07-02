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

    with open("config.ini", "w") as config_file:
        config.write(config_file)

def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    show_position = config.getboolean("Game Settings", "show_position")
    show_direction = config.getboolean("Game Settings", "show_direction")
    return show_position, show_direction

# 在游戏开始时创建配置文件
create_config()

# 在游戏过程中读取配置文件
show_position, show_direction = read_config()


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

    # 随机选择一个位置作为终点
    end_coords = [random.randint(0, size - 1) for _ in range(dimensions)]
    maze[tuple(end_coords)] = 'E'
    maze[tuple([0]*dimensions)] = 'S'

    return maze


def generate_mazes(difficulty):
    clear_maps()
    if difficulty == 1:
        dimensions, size = 2, 3
        for i in range(3):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 1
    elif difficulty == 2:
        dimensions, size = 2, 3
        for i in range(3):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 2
    elif difficulty == 3:
        dimensions, size = 2, 3
        for i in range(3):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 3
    elif difficulty == 4:
        dimensions, size = 2, 5
        for i in range(4):
            maze = generate_maze(dimensions, size)
            save_maze(maze, f"maps/stage{i+1}")
            size += 2
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

    # 定义一个函数来获取前方的情况
    def get_ahead(dim, position, direction):
        ahead = position + direction
        if any(p < 0 or p >= size for p in ahead) or maze[tuple(ahead.astype(int))] == 'W':
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
        print(f"向前移动了{min(move, _+1)}格，前方是{get_ahead(dim, position, direction)}")
        return position

    # 定义一个函数来处理转向
    def turn(direction, dim, dimensions, turn_right=True, turn_back=False):
        # 创建旋转矩阵
        rotation_matrix = np.eye(dimensions, dtype=int)
        rotation_matrix[dim, dim] = 0
        rotation_matrix[(dim+1)%dimensions, (dim+1)%dimensions] = 0
        if turn_back:
            direction = -direction  # 向后转，朝向向量反向
        else:
            if turn_right:
                rotation_matrix[dim, (dim+1)%dimensions] = 1
                rotation_matrix[(dim+1)%dimensions, dim] = -1
            else:  # 向左转
                rotation_matrix[dim, (dim+1)%dimensions] = -1
                rotation_matrix[(dim+1)%dimensions, dim] = 1
            # 旋转朝向向量
            direction = np.dot(rotation_matrix, direction)
        return direction

    # 初始化dim变量的值
    dim = 0

    # 初始化一个标志位来检查是否已经到达过终点
    reached_end = False

    while True:
        if show_direction:
            print(f"当前朝向：{list(direction)}")
        if show_position:
            print(f"当前位置：{list(position)}")

        print(f"前方是：{get_ahead(dim, position, direction)}")

        def input_command():
            # 获取玩家输入
            command = input("请输入指令：")

            # 解析玩家输入
            match = re.match(r'^(w[0-9]*|a|s|d)$', command)

            if match:
                if command[0] == 'w' and len(command) > 1:
                    dim = int(command[1:])
                else:
                    dim = 0
                return command, dim
            else:
                print("无效的输入！")
                return input_command()  # 在递归调用时返回结果

        command, dim = input_command()
        if command[0] in 'wasd':
            move = int(command[1:]) if len(command) > 1 else 1
            if command[0] == 'w':
                position = move_forward(move, dim, position, direction)
            elif command[0] == 's':
                direction = turn(direction, dim, dimensions, turn_back=True)
                print(f"向后转，前方是{get_ahead(dim, position, direction)}")
            elif command[0] == 'a':
                direction = turn(direction, dim, dimensions, turn_right=False)
                print(f"向左转，前方是{get_ahead(dim, position, direction)}")
            elif command[0] == 'd':
                direction = turn(direction, dim, dimensions, turn_right=True)
                print(f"向右转，前方是{get_ahead(dim, position, direction)}")
            else:
                print(f"输入无效，请重新输入。")
        else:
            print(f"输入无效，请重新输入。")

        # 检查是否到达终点并返回起点
        if maze[tuple(position)] == 'E':
            print("到达终点")
            maze[tuple(position)] = 'R'
            reached_end = True
        elif (position == [0]*dimensions).all() and reached_end:
            print("成功返回起点，你赢了！")
            return True




def game():
    print("[1]开始游戏 [2]自定义模式 [3]退出游戏")
    choice = input("请输入你的选择：")
    if choice == '1':
        print("请选择难度：[1] [2] [3] [4]")
        difficulty = int(input("请输入你的选择："))
        generate_mazes(difficulty)
    elif choice == '2':

        def diy1():
            dimensions = int(input("请输入迷宫的维度："))
            if dimensions > 2 :
                print("达X太笨了还做不出高维度的迷宫QAQ~请重新输入你的维度信息吧~")
                diy1()
            return dimensions
            
        def diy2():
            size = int(input("请输入迷宫的边长："))
            if size > 29 :
                print("达X太懒了还没做能够超过29边长的迷宫QAQ~请重新输入你的边长信息吧~")
                diy2()
            return size
        
        dimensions = diy1()
        size = diy2()

        clear_maps()
        maze = generate_maze(dimensions, size)
        save_maze(maze, "maps/stage1")
    elif choice == '3':
        print("退出游戏")
        return
    else:
        print("无效的输入，请重新输入")
        game()

    # 在每个关卡开始时，加载迷宫并开始游戏
    start_time = time.time()
    stages = sorted([f for f in os.listdir('maps') if f.startswith('stage') and f.endswith('.npy')])
    print("w移动，ad左右转向，s向后转")
    for stage in stages:
        maze = np.load(os.path.join('maps', stage))
        dimensions = len(maze.shape)
        size = maze.shape[0]
        print(f"{stage[:-4]}：{dimensions}维迷宫，边长{size}")
        if not play_game(maze, dimensions, size):
            print("你输了")
            break
    else:
        end_time = time.time()
        print("恭喜你，你完成了所有的关卡！")
        print(f"你的总游玩时间是：{end_time - start_time}秒")



if __name__ == "__main__":
    if not os.path.exists('maps'):
        os.makedirs('maps')
    while True :
        game()
        print('游戏结束，开启新游戏或者右上角直接关闭游戏\n\n')