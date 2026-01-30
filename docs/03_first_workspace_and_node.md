# 🧩【ROS2 入门系列 #3】创建第一个 ROS2 工作空间与 Python 节点

> 作者：whatqiu  
> 更新时间：2025-11-12  
> 环境：Ubuntu 22.04 + ROS2 Humble  

---

## 🧭 前言

在上一章中，我们通过 turtlesim 示例了解了 ROS2 的核心概念（节点、话题、服务、参数）。但是，这些示例都是 ROS2 官方提供的，如果要创建自己的机器人应用，我们需要学会如何创建自己的工作空间和节点。

本章将手把手教你：
- 创建 ROS2 工作空间（Workspace）
- 创建功能包（Package）
- 编写第一个 Python 节点
- 使用 colcon 构建工具编译项目
- 运行自定义节点

**预计学习时间**：30-45 分钟

**前置章节**：[02 - ROS2 架构与基础概念全解析](02_ros2_basics.md)

---

## 🧱 一、主要内容

### 1.1 ROS2 工作空间（Workspace）

**什么是工作空间？**

工作空间是存放和管理 ROS2 项目的目录，类似于编程项目中的项目文件夹。

**标准工作空间结构**：
```
ros2_ws/
├── build/          # 编译生成的中间文件
├── install/        # 安装后的可执行文件和库
├── log/            # 日志文件
└── src/            # 源代码目录（我们主要在这里工作）
    └── CMakeLists.txt  # 工作空间根目录的 CMake 文件
```

### 1.2 功能包（Package）

**什么是功能包？**

功能包是 ROS2 的基本组织单元，包含：
- 节点代码（Python/C++）
- 配置文件
- 依赖项声明
- 启动文件
- 消息/服务定义（可选）

### 1.3 功能包类型

ROS2 支持三种类型的包：
1. **ament_python**：Python 功能包
2. **ament_cmake**：C++ 功能包
3. **ament_cmake + Python**：混合语言功能包

本章重点介绍 `ament_python` 类型。

---

## 🧩 二、示例与讲解

### 2.1 创建工作空间

#### 步骤 1：Source ROS 2 环境

首先需要 source 你的 ROS 2 安装环境作为"底层"（underlay）：

```bash
source /opt/ros/humble/setup.bash
```

#### 步骤 2：创建工作空间目录

```bash
# 在家目录创建工作空间
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

**最佳实践**：
- 为每个新工作空间创建一个新目录
- 工作空间名称应该能表明其用途（如 `ros2_ws` 表示开发工作空间）
- 将所有功能包放在 `src` 目录中，保持工作空间顶层整洁

#### 步骤 3：验证工作空间结构

```bash
ls -la
```

应该看到 `src` 目录。此时工作空间是空的，还没有任何功能包。

---

### 2.2 创建 Python 功能包

#### 使用 ros2 pkg create（推荐）

**命令语法**：
```bash
ros2 pkg create --build-type ament_python --license Apache-2.0 <package_name>
```

**创建我们的包**：
```bash
cd ~/ros2_ws/src

# 创建 Python 功能包
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  --dependencies rclpy \
  --node-name my_first_node \
  my_first_package
```

**参数说明**：
- `--build-type ament_python`：指定为 Python 包
- `--license Apache-2.0`：设置许可证为 Apache-2.0
- `--dependencies rclpy`：声明依赖（ROS2 Python 客户端库）
- `--node-name my_first_node`：自动创建一个简单的 Hello World 类型的可执行节点
- `my_first_package`：包名

#### 创建后的目录结构

```
my_first_package/
├── setup.py                  # Python 包配置文件
├── setup.cfg                 # 安装配置（当包有可执行文件时必需）
├── package.xml               # ROS2 包描述文件
├── resource/                 # 资源文件
│   └── my_first_package      # 包标记文件
├── test/                     # 测试文件
│   ├── test_copyright.py
│   ├── test_flake8.py
│   └── test_pep257.py
├── my_first_package/         # Python 源代码目录（与包名相同）
│   ├── __init__.py
│   └── my_first_node.py      # 自动生成的示例节点
└── setup.py                  # 包含如何安装包的说明
```

**注意**：Python 包要求有一个与包名同名的目录，用于 ROS2 工具找到你的包。

---

### 2.3 编写第一个 Python 节点

#### 查看自动生成的节点

```bash
cat ~/ros2_ws/src/my_first_package/my_first_node.py
```

你应该看到类似这样的代码：

```python
import rclpy
from rclpy.node import Node


class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        self.get_logger().info('Hello World!')


def main(args=None):
    rclpy.init(args=args)
    node = MinimalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 代码解析

**1. 导入 ROS2 Python 客户端库**：
```python
import rclpy
from rclpy.node import Node
```

**2. 创建节点类**：
```python
class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')  # 节点名称
        self.get_logger().info('Hello World!')  # 输出日志
```

**3. main 函数**：
```python
def main(args=None):
    rclpy.init(args=args)      # 初始化 ROS2
    node = MinimalNode()       # 创建节点实例
    rclpy.spin(node)           # 保持节点运行
    node.destroy_node()        # 销毁节点
    rclpy.shutdown()           # 关闭 ROS2
```

---

### 2.4 配置 setup.py

为了让 ROS2 能够找到并运行我们的节点，需要查看 `setup.py` 文件。

```bash
cat ~/ros2_ws/src/my_first_package/setup.py
```

**关键配置项 - entry_points**：
```python
entry_points={
    'console_scripts': [
        # 节点入口点注册在这里
        'my_first_node = my_first_package.my_first_node:main'
    ],
}
```

这行代码将节点名称 `my_first_node` 映射到 `my_first_package.my_first_node:main` 函数。

---

### 2.5 编译工作空间

#### 步骤 1：解析依赖

在编译工作空间之前，需要先解决包的依赖关系。即使你可能已经拥有所有依赖，最佳实践是每次克隆后都检查依赖。

**从工作空间的根目录（`ros2_ws`）运行以下命令**：

```bash
cd ~/ros2_ws
rosdep install -i --from-path src --rosdistro humble -y
```

**参数说明**：
- `-i`：忽略已安装的包的主要依赖
- `--from-path src`：从 src 目录解析依赖
- `--rosdistro humble`：指定 ROS2 发行版
- `-y`：自动确认安装

如果已经拥有所有依赖，控制台将返回：
```
#All required rosdeps installed successfully
```

**注意**：如果是第一次使用 `rosdep`，需要先初始化：
```bash
sudo apt install python3-rosdep
sudo rosdep init
rosdep update
```

#### 步骤 2：使用 colcon 编译

从工作空间的根目录（`ros2_ws`），现在可以使用以下命令构建包：

```bash
colcon build --packages-select my_first_package
```

**其他有用的 `colcon build` 参数**：
- `--packages-up-to`：构建你想要的包及其所有依赖，但不构建整个工作空间（节省时间）
- `--symlink-install`：使你不必在每次调整 Python 脚本时都重新构建
- `--event-handlers console_direct+`：在构建时显示控制台输出（否则可以在 `log` 目录中找到）

**编译成功输出示例**：
```
Starting >>> my_first_package
Finished <<< my_first_package [3.42s]

Summary: 1 package finished [3.56s]
```

构建完成后，输入以下命令查看工作空间根目录（`~/ros2_ws`）：
```bash
ls
```

你会看到 colcon 创建了新目录：
```
build  install  log  src
```

`install` 目录是你工作空间的设置文件所在的位置。

#### 步骤 3：Source 覆盖层（Overlay）

**重要**：在 source 覆盖层之前，务必打开一个**新终端**，与构建工作空间所在的终端分开。在同一个终端中 source 覆盖层并在其中构建（或在 source 的覆盖层中构建）可能会产生复杂问题。

**在新终端中**：

1. 首先 source 你的主 ROS 2 环境作为"底层"（underlay）：
```bash
source /opt/ros/humble/setup.bash
```

2. 进入工作空间的根目录：
```bash
cd ~/ros2_ws
```

3. 在根目录中，source 你的覆盖层：
```bash
source install/local_setup.bash
```

**说明**：
- `local_setup` 只会将覆盖层中可用的包添加到你的环境中
- `setup` 会 source 覆盖层以及创建它的底层，允许你同时使用两个工作空间

**建议**：将这行添加到 `~/.bashrc` 文件，这样每次打开终端都会自动加载：
```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

---

### 2.6 运行节点

#### 验证节点是否可用

```bash
ros2 pkg list | grep my_first_package
```

应该看到：`my_first_package`

#### 查看包内节点

```bash
ros2 pkg executables my_first_package
```

输出：
```
my_first_package.my_first_node
```

#### 运行节点

```bash
ros2 run my_first_package my_first_node
```

你应该看到：
```
[INFO] [minimal_node]: Hello World!
```

#### 验证节点正在运行

打开另一个终端，运行：
```bash
ros2 node list
```

应该看到：
```
/minimal_node
```

---

### 2.7 进阶示例：创建发布者节点

让我们创建一个能够周期性发布消息的节点，学习如何向包中添加新的功能。

#### 步骤 1：创建新节点文件

```bash
cd ~/ros2_ws/src/my_first_package/my_first_package
```

创建 `hello_publisher.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class HelloPublisher(Node):
    def __init__(self):
        super().__init__('hello_publisher')

        # 创建发布者
        self.publisher = self.create_publisher(String, 'hello_topic', 10)

        # 创建定时器，每秒调用一次
        timer_period = 1.0
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.counter = 0

        self.get_logger().info('Hello Publisher 已启动！')

    def timer_callback(self):
        # 创建消息
        msg = String()
        msg.data = f'Hello ROS2! 计数: {self.counter}'

        # 发布消息
        self.publisher.publish(msg)

        # 输出日志
        self.get_logger().info(f'发布: "{msg.data}"')

        self.counter += 1


def main(args=None):
    rclpy.init(args=args)
    hello_publisher = HelloPublisher()

    try:
        rclpy.spin(hello_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        hello_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 步骤 2：更新 setup.py

编辑 `~/ros2_ws/src/my_first_package/setup.py`，在 `entry_points` 中添加新节点：

```python
entry_points={
    'console_scripts': [
        'my_first_node = my_first_package.my_first_node:main',
        'hello_publisher = my_first_package.hello_publisher:main',  # 新增
    ],
},
```

**提示**：`entry_points` 告诉 `ros2 run` 如何找到可执行文件。格式为 `节点名 = 包名.模块名:函数名`。

#### 步骤 3：重新编译

**重要**：回到之前构建工作空间的终端（或新开一个终端，不要 source 覆盖层）：

```bash
cd ~/ros2_ws
colcon build --packages-select my_first_package
```

**小技巧**：对于 Python 开发，可以使用 `--symlink-install` 参数，这样每次修改 Python 脚本后不必重新构建：
```bash
colcon build --packages-select my_first_package --symlink-install
```

#### 步骤 4：在运行终端中重新 source 环境

在运行节点的终端中：
```bash
source ~/ros2_ws/install/local_setup.bash
```

#### 步骤 5：运行新节点

```bash
ros2 run my_first_package hello_publisher
```

你会看到每秒输出一条消息：
```
[INFO] [hello_publisher]: Hello Publisher 已启动！
[INFO] [hello_publisher]: 发布: "Hello ROS2! 计数: 0"
[INFO] [hello_publisher]: 发布: "Hello ROS2! 计数: 1"
[INFO] [hello_publisher]: 发布: "Hello ROS2! 计数: 2"
...
```

#### 步骤 6：在另一个终端监听话题

打开新终端，source 环境后运行：
```bash
source ~/ros2_ws/install/local_setup.bash
ros2 topic echo /hello_topic
```

你会看到话题中发布的消息内容。

---

### 2.8 工作空间最佳实践

根据官方文档，使用覆盖层（overlay）有以下要点：

#### 覆盖层（Overlay）vs 底层（Underlay）

- **底层（Underlay）**：你的主 ROS 2 安装（`/opt/ros/humble`）
- **覆盖层（Overlay）**：你在 `ros2_ws` 中创建的工作空间

**重要特性**：
- 覆盖层会优先于底层
- 你可以修改覆盖层中的包，而不会影响底层
- 可以有多层覆盖层和底层

#### 工作空间使用建议

1. **使用覆盖层来处理少量包**：这样你不必将所有内容放在同一个工作空间中，也不必在每次迭代时重建巨大的工作空间。

2. **避免在同一终端中混合操作**：
   - 不要在 source 了覆盖层的终端中构建
   - 不要在构建的终端中运行覆盖层的节点

3. **包的放置位置**：
   - 所有包都应放在 `src` 目录中
   - 保持工作空间顶层整洁

4. **不能有嵌套包**：一个包内不能包含另一个包

---

## ✅ 总结

### 本章关键收获

| 概念 | 说明 |
|------|------|
| **工作空间** | ROS2 项目的容器，包含 src、build、install、log 目录 |
| **功能包** | ROS2 的基本组织单元，包含代码、配置、依赖声明 |
| **节点** | 具体的可执行程序，继承自 `rclpy.node.Node` |
| **colcon** | ROS2 的编译工具，用于构建工作空间 |
| **setup.py** | Python 包的配置文件，定义入口点和依赖 |

### 开发流程回顾

1. **创建工作空间**：`mkdir -p ~/ros2_ws/src`
2. **创建功能包**：`ros2 pkg create --build-type ament_python`
3. **编写节点代码**：创建 `.py` 文件，继承 `Node` 类
4. **配置入口点**：在 `setup.py` 的 `entry_points` 中注册节点
5. **编译**：`colcon build --packages-select <package>`
6. **运行**：`ros2 run <package> <node>`

### 常用命令速查表

| 操作 | 命令 |
|------|------|
| 创建包 | `ros2 pkg create --build-type ament_python <package_name>` |
| 编译工作空间 | `colcon build --packages-select <package_name>` |
| 列出所有包 | `ros2 pkg list` |
| 查看包信息 | `ros2 pkg xml <package_name>` |
| 查看包内可执行文件 | `ros2 pkg executables <package_name>` |
| 运行节点 | `ros2 run <package_name> <node_name>` |

---

📘 下一章：[ROS2 命令行工具详解 - 日常开发必备命令](04_ros2_cli_tools.md)
