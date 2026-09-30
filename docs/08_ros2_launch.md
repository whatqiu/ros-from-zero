# 🚦【ROS2 入门系列 #8】Launch 文件使用与多节点启动管理

> 作者：whatqiu
> 更新时间：2026-09-30
> 环境：Ubuntu 22.04 + ROS2 Humble（Jazzy 差异见文末对照）

---

## 🧭 前言

到上一章为止，我们的工作流还是「一个终端一个节点」：

```bash
# 终端 1
ros2 run param_demo configurable_publisher --ros-args --params-file params.yaml

# 终端 2
ros2 run param_demo dynamic_tuner

# 终端 3
ros2 run turtlesim turtlesim_node

# 终端 4
ros2 run turtlesim turtle_teleop_key

# ……终端不够用了
```

一个真实的机器人系统动辄几十个节点。这样手动开终端有四个问题：

1. **终端开不下**——20 个节点要 20 个终端
2. **顺序有讲究**——有些节点必须先启动（如 TF 广播器），否则下游全报错
3. **参数要重复输入**——每次都得手打 `--ros-args`
4. **没法一键复现**——换台机器就要重新配一遍

**Launch 文件就是解决这个问题的**。它把「启动什么、传什么参数、什么顺序、什么条件」写成声明式配置，一条命令拉起整个系统。

**本章是入门系列的收口章节**——它把前面七章的东西整合成一个可复用的启动单元。

本章目标：

- 掌握 Python Launch 的完整语法（**重点，实际项目首选**）
- 会启动多个节点、传参、重映射话题
- 会用条件判断、参数替换实现「一套 launch，多场景」
- 了解 XML / YAML Launch 的写法与取舍
- 掌握 Launch 调试技巧（这是最容易卡住的地方）

**预计学习时间**：60-75 分钟

**前置章节**：

- [03 - 创建第一个 ROS2 工作空间与 Python 节点](03_first_workspace_and_node.md)
- [06 - 服务与动作机制](06_services_and_actions.md)
- [07 - 参数服务器与动态参数管理](07_parameters_and_config.md)

---

## 🧱 一、主要内容

### 1.1 三种 Launch 格式的取舍

ROS2 支持三种格式，很多人一开始就选错。

| 格式 | 文件扩展名 | 表达能力 | 上手难度 | 推荐度 |
| -------- | ------------- | ---------- | ------ | ---------- |
| **Python** | `.launch.py` | **最强** | 中 | ⭐⭐⭐ 首选 |
| XML | `.launch.xml` | 中 | 低 | ⭐⭐ 简单场景 |
| YAML | `.launch.yaml` | 弱 | 低 | ⭐ 较少用 |

**为什么推荐 Python？**

因为 Launch 文件里经常需要写逻辑：

```python
# 根据仿真/真机切换不同的参数文件
params_file = 'sim.yaml' if use_sim else 'real.yaml'
```

XML 做条件判断要靠一堆属性拼接，很难受。Python 可以直接用 `if/else`、列表推导、甚至读环境变量，**本质上你是在写程序**。

**唯一的代价**：Python Launch 需要 `execute_process` 之类的 API，初学时会觉得有点绕。但掌握了之后，写复杂启动逻辑会轻松很多。

**本教程策略**：主线用 Python，XML/YAML 只做了解。实际项目里你 90% 的时间都在写 Python Launch。

### 1.2 Launch 系统的核心概念

先建立一张概念地图，后面所有 API 都是在操作这几个实体：

| 概念 | 对应 API | 作用 |
| ---------------- | ------------------------------------ | ------------------ |
| **节点 (Node)** | `Node(package=, executable=)` | 启动一个可执行程序 |
| **参数 (Parameter)** | `parameters=[{...}]` 或 `[yaml_file]` | 传给节点的参数 |
| **参数文件** | `--params-file` 的 Launch 等价物 | 批量传参 |
| **重映射** | `remappings=[('from','to')]` | 改话题/服务名 |
| **命名空间** | `namespace=` | 加名字前缀 |
| **替换 (Substitution)** | `LaunchConfiguration('x')` | 运行时才能确定的值 |
| **动作 (Action)** | `IncludeLaunchDescription` 等 | 执行一个操作 |
| **条件 (Condition)** | `IfCondition` / `UnlessCondition` | 选择性执行 |
| **事件 (Event)** | `OnProcessExit` 等 | 响应运行状态 |

**最关键的两个概念**：

1. **替换（Substitution）**——Launch 文件是**两层**执行的。第一层在「解析文件时」，第二层在「运行时」。`LaunchConfiguration` 属于第二层，所以不能直接和字符串比较：

```python
# ❌ 错误：这是解析时求值，此时还不知道 use_sim 的值
if use_sim == 'true':
    ...

# ✅ 正确：用 LaunchArgument 的默认值，或注册条件
LaunchConfiguration('use_sim')  # 一个占位符，运行时才求值
```

**这个「两层求值」是 Launch 最大的理解门槛**，2.7 节会专门用一个例子讲透。

2. **动作编排**——`generate_launch_description()` 必须返回一个 `LaunchDescription`，里面是一个**动作列表**。列表顺序影响执行顺序（但节点是并行的，见 2.8 节的坑）。

### 1.3 Python Launch 的最小骨架

先记住这个模板，一切从它开始：

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='my_talker',
            output='screen',
        ),
    ])
```

四个要点：

- 文件名**必须**以 `.launch.py` 结尾（ROS2 靠这个后缀识别）
- **必须**有 `generate_launch_description()` 函数，返回值必须是 `LaunchDescription`
- `package` + `executable` 是必填，对应 `ros2 run <package> <executable>`
- `output='screen'` 让节点日志打印到当前终端（**不加的话看不到节点输出**，新手最容易困惑的点）

---

## 🧩 二、示例与讲解

### 2.1 第一个 Launch 文件

#### 步骤 1：创建功能包

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python \
  --dependencies rclpy launch launch_ros \
  launch_demo
```

**关键**：依赖里必须有 `launch` 和 `launch_ros`，否则 `import` 会失败。

#### 步骤 2：建 launch 目录

```bash
mkdir -p ~/ros2_ws/src/launch_demo/launch
```

#### 步骤 3：写第一个 Launch 文件

创建 `~/ros2_ws/src/launch_demo/launch/hello.launch.py`：

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """最小 Launch 示例：启动 talker 和 listener，观察话题通信"""

    talker = Node(
        package='demo_nodes_cpp',
        executable='talker',
        name='my_talker',
        output='screen',
    )

    listener = Node(
        package='demo_nodes_py',
        executable='listener',
        name='my_listener',
        output='screen',
    )

    return LaunchDescription([
        talker,
        listener,
    ])
```

#### 步骤 4：配置 setup.py 安装 launch 目录

launch 文件不会自动打包，必须声明：

```python
import os
from glob import glob

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 关键：安装 launch 目录下的所有 py 文件
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='whatqiu',
    maintainer_email='whatqiu@example.com',
    description='ROS2 Launch 示例',
    license='MIT',
    entry_points={
        'console_scripts': [],
    },
)
```

**注意 glob 的匹配模式**：`'launch/*.launch.py'` 只匹配 `.launch.py` 结尾的文件。如果你的 launch 文件命名成 `hello.py`（少了 `.launch`），**不会被安装**，运行时报 `file not found`。

#### 步骤 5：编译并运行

```bash
cd ~/ros2_ws
colcon build --packages-select launch_demo
source install/setup.bash
```

```bash
ros2 launch launch_demo hello.launch.py
```

输出：

```text
[INFO] [launch]: All log files can be found below /home/user/.ros/log/2026-09-30-10-00-00-123456
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [talker-1]: process started with pid [12345]
[INFO] [listener-2]: process started with pid [12346]
[my_talker-1] [INFO] [talker]: Publishing: 'Hello World: 1'
[my_listener-2] [INFO] [listener]: I heard: [Hello World: 1]
```

**两个节点在一个终端里跑起来了**。注意日志前缀 `[my_talker-1]` 和 `[my_listener-2]`——这是 Launch 自动加上的**节点名 + 序号**，方便区分。

按 `Ctrl+C` 会**自动关闭所有子进程**，这是 Launch 的另一个好处。

#### 步骤 6：验证 launch 文件被正确安装

```bash
ros2 launch launch_demo --show-args hello.launch.py
```

这个命令可以查看 launch 文件支持的参数（现在还没有，输出会是空的）。

```bash
# 查看所有可用的 launch 文件
ros2 launch launch_demo --show-all
```

如果输出里没有你的文件，说明 `setup.py` 的 `data_files` 配错了。

---

### 2.2 传参数：三种方式

Launch 里传参数比命令行灵活得多。

#### 方式一：直接写字典（最简单）

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """演示：直接传参"""

    publisher = Node(
        package='param_demo',
        executable='configurable_publisher',
        name='configurable_publisher',
        output='screen',
        parameters=[{
            'topic_name': 'launch_sensor',
            'publish_rate': 2.0,
            'initial_value': 42.0,
            'drift_step': 0.5,
            'enable_drift': True,
        }],
    )

    return LaunchDescription([publisher])
```

**注意 `name=` 参数**：这里显式设了节点名。如果不设，节点名由代码里 `super().__init__()` 决定。

**为什么要显式设？** 因为**参数按节点名匹配**。显式设名能让 YAML 文件和 Launch 文件对得上，避免「参数不生效」的诡异问题。

#### 方式二：加载 YAML 文件（推荐）

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """演示：从 YAML 文件加载参数"""

    # 关键：用 get_package_share_directory 定位包目录
    pkg_dir = get_package_share_directory('param_demo')
    params_file = os.path.join(pkg_dir, 'config', 'params.yaml')

    publisher = Node(
        package='param_demo',
        executable='configurable_publisher',
        name='configurable_publisher',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([publisher])
```

**`get_package_share_directory` 是必须掌握的**。它自动定位到 `install/<pkg>/share/<pkg>/`，**不要手写绝对路径**，否则换机器就崩。

**也可以同时传多个 YAML**（后面的覆盖前面的）：

```python
parameters=[base_params, override_params]   # override 里的值生效
```

#### 方式三：YAML + 命令行覆盖

```python
publisher = Node(
    package='param_demo',
    executable='configurable_publisher',
    name='configurable_publisher',
    output='screen',
    parameters=[
        params_file,              # 先加载文件
        {'publish_rate': 20.0},   # 再用字典覆盖
    ],
)
```

**顺序很重要**：列表后面的覆盖前面的。这个特性让你可以「加载一套标准配置，再局部微调」。

#### 完整可运行示例

创建 `~/ros2_ws/src/launch_demo/launch/params_demo.launch.py`：

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """演示：参数文件 + 命令行覆盖"""

    # 声明一个可从命令行传入的参数
    rate_arg = DeclareLaunchArgument(
        'rate',
        default_value='5.0',
        description='发布频率 (Hz)'
    )

    pkg_dir = get_package_share_directory('param_demo')
    params_file = os.path.join(pkg_dir, 'config', 'params.yaml')

    publisher = Node(
        package='param_demo',
        executable='configurable_publisher',
        name='configurable_publisher',
        output='screen',
        parameters=[
            params_file,
            # 用 LaunchConfiguration 引用命令行传入的值
            {'publish_rate': LaunchConfiguration('rate')},
        ],
    )

    return LaunchDescription([
        rate_arg,
        publisher,
    ])
```

运行：

```bash
# 用默认值（5.0 Hz）
ros2 launch launch_demo params_demo.launch.py

# 命令行覆盖（20.0 Hz）
ros2 launch launch_demo params_demo.launch.py rate:=20.0

# 查看支持哪些参数
ros2 launch launch_demo params_demo.launch.py --show-args
```

`--show-args` 输出：

```text
Arguments (pass arguments as '<name>:=<value>'):

    'rate':
        发布频率 (Hz)
        (default: '5.0')
```

**这是 Launch 最实用的功能之一**——把可变的部分暴露成参数，把稳定的部分固化。

---

### 2.3 重映射话题与服务

重映射让你在**不改代码**的前提下改变话题名。这是复用的关键。

#### 基础重映射

```python
talker = Node(
    package='demo_nodes_cpp',
    executable='talker',
    name='talker',
    output='screen',
    # 把节点内部的 'chatter' 重映射为 'my_chatter'
    remappings=[('chatter', 'my_chatter')],
)
```

**等价于命令行的**：

```bash
ros2 run demo_nodes_cpp talker --ros-args -r chatter:=my_chatter
```

#### 实战场景：两个 talker 发到不同话题

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """两个 talker，通过重映射发到不同话题，避免冲突"""

    talker_a = Node(
        package='demo_nodes_cpp',
        executable='talker',
        name='talker_a',
        output='screen',
        remappings=[('chatter', 'chatter_a')],
    )

    talker_b = Node(
        package='demo_nodes_cpp',
        executable='talker',
        name='talker_b',
        output='screen',
        remappings=[('chatter', 'chatter_b')],
    )

    listener_a = Node(
        package='demo_nodes_py',
        executable='listener',
        name='listener_a',
        output='screen',
        remappings=[('chatter', 'chatter_a')],
    )

    return LaunchDescription([talker_a, talker_b, listener_a])
```

**如果不重映射会怎样？** 两个 talker 都发到 `/chatter`，listener 会同时收到两路交错的消息，日志会混乱。**重映射解决了「同一个可执行文件跑多份」的冲突问题**。

#### 配合命名空间

多机器人场景的标准做法是**命名空间 + 相对话题名**：

```python
def make_robot(robot_name):
    """工厂函数：生成一套机器人节点"""
    return [
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='talker',
            namespace=robot_name,          # 命名空间
            output='screen',
        ),
    ]


def generate_launch_description():
    actions = []
    # 生成两台机器人的节点
    for name in ['robot1', 'robot2']:
        actions.extend(make_robot(name))

    return LaunchDescription(actions)
```

结果：`robot1` 的话题是 `/robot1/chatter`，`robot2` 是 `/robot2/chatter`，**天然隔离**。

> **用工厂函数批量生成节点**是 Python Launch 相对 XML 的最大优势。20 台机器人？一个循环就搞定。

---

### 2.4 条件启动：if / unless

真实场景经常需要「这个节点只在仿真时启动」。

#### IfCondition / UnlessCondition

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """演示：根据 use_sim 决定启动哪些节点"""

    use_sim_arg = DeclareLaunchArgument(
        'use_sim',
        default_value='true',
        description='是否使用仿真环境 (true/false)'
    )

    use_sim = LaunchConfiguration('use_sim')

    # 只在仿真时启动
    sim_node = Node(
        package='demo_nodes_cpp',
        executable='talker',
        name='sim_talker',
        output='screen',
        condition=IfCondition(use_sim),
    )

    # 只在真机时启动
    real_node = Node(
        package='demo_nodes_cpp',
        executable='talker',
        name='real_talker',
        output='screen',
        condition=UnlessCondition(use_sim),
    )

    return LaunchDescription([
        use_sim_arg,
        sim_node,
        real_node,
    ])
```

运行验证：

```bash
# 仿真模式：只有 sim_talker
ros2 launch launch_demo conditional.launch.py use_sim:=true

# 真机模式：只有 real_talker
ros2 launch launch_demo conditional.launch.py use_sim:=false
```

#### 条件也可以用 Python 逻辑（解析时判断）

如果条件在**写 launch 文件时**就能确定，直接用 Python：

```python
import os

def generate_launch_description():
    # 从环境变量读，解析时就确定
    is_debug = os.environ.get('ROS_DEBUG_MODE') == '1'

    actions = []
    if is_debug:
        actions.append(Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='debug_helper',
            output='screen',
        ))

    return LaunchDescription(actions)
```

**两种方式的区别**：

| 方式 | 求值时机 | 适用场景 |
| ---------------- | -------- | ---------------- |
| `IfCondition` | 运行时 | 需要命令行控制 |
| Python `if` | 解析时 | 依赖环境变量/文件存在性 |

---

### 2.5 参数替换（Substitution）详解

这是 Launch 里最抽象、也最容易出错的部分。

#### 什么是替换？

**替换是一个「占位符」**，在运行时才被求值成真实字符串。

```python
from launch.substitutions import LaunchConfiguration

# 这不是字符串 'rate'，而是一个"等会儿再求值"的占位符
LaunchConfiguration('rate')
```

#### 常用替换类型

| 替换 | 作用 | 示例 |
| ---------------------- | -------------- | ------------------------------- |
| `LaunchConfiguration` | 引用 launch 参数 | `LaunchConfiguration('rate')` |
| `EnvironmentVariable` | 读环境变量 | `EnvironmentVariable('HOME')` |
| `PathJoinSubstitution` | 拼接路径 | `PathJoinSubstitution([a, b])` |
| `Command` | 执行命令取输出 | `Command(['ls', '-l'])` |
| `FindPackageShare` | 定位包目录 | `FindPackageShare('my_pkg')` |
| `TextSubstitution` | 包装普通字符串 | `TextSubstitution(text='abc')` |

#### 为什么不能直接拼接字符串

这是新手必踩的坑：

```python
from launch.substitutions import LaunchConfiguration

rate = LaunchConfiguration('rate')

# ❌ 错误：这会抛 TypeError
text = 'publish_rate:=' + rate

# ✅ 正确：用列表形式，会被自动拼接
text = ['publish_rate:=', rate]
```

**原因**：`LaunchConfiguration` 不是 `str` 类型，不能用 `+` 拼接。但很多 Launch API 接受**列表**，列表里的元素会被依次求值并拼接。

#### 实战：用替换构造路径

**老写法（不推荐，硬编码）**：

```python
params_file = '/home/user/ros2_ws/install/param_demo/share/param_demo/config/params.yaml'
```

换台机器就崩。

**推荐写法（用替换）**：

```python
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

params_file = PathJoinSubstitution([
    FindPackageShare('param_demo'),
    'config',
    'params.yaml',
])
```

**对比 `get_package_share_directory` 的写法**：

```python
# 解析时求值（文件必须已安装）
pkg_dir = get_package_share_directory('param_demo')
params_file = os.path.join(pkg_dir, 'config', 'params.yaml')
```

**两者都能用，怎么选？**

| 方式 | 求值时机 | 优点 | 缺点 |
| ------------------- | -------- | ------------ | -------------------- |
| `get_package_share_directory` | 解析时 | 直观、能断点调试 | 文件缺失时直接抛异常 |
| `PathJoinSubstitution` | 运行时 | 更"正确" | 调试不便 |

**实践建议**：**调试阶段用前者**（报错信息更明确），**发布时用后者**（行为更标准）。两者混用没问题。

#### 实战：把多个替换拼成参数值

```python
from launch.substitutions import LaunchConfiguration

robot_id = LaunchConfiguration('robot_id')

# 话题名 = 'robot' + id + '_cmd_vel'
# 用列表拼接
topic_name = ['robot', robot_id, '_cmd_vel']

node = Node(
    package='my_pkg',
    executable='controller',
    name=['controller_', robot_id],
    parameters=[{
        'cmd_topic': topic_name,
    }],
)
```

运行时 `robot_id:=3`，节点名变成 `controller_3`，参数 `cmd_topic` 变成 `robot3_cmd_vel`。

---

### 2.6 复用：IncludeLaunchDescription

大型项目会把 launch 文件**分层组织**。

#### 场景

```text
launch/
├── robot.launch.py          # 顶层：启动整个机器人
├── sensors.launch.py        # 子层：所有传感器
├── navigation.launch.py     # 子层：导航栈
└── visualization.launch.py  # 子层：RViz
```

顶层文件把子层组合起来。

#### 子文件：sensors.launch.py

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    lidar_port_arg = DeclareLaunchArgument(
        'lidar_port',
        default_value='/dev/ttyUSB0',
        description='激光雷达串口设备'
    )

    lidar = Node(
        package='my_lidar_driver',
        executable='lidar_node',
        name='lidar',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('lidar_port'),
        }],
    )

    return LaunchDescription([
        lidar_port_arg,
        lidar,
    ])
```

#### 顶层文件：robot.launch.py

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('launch_demo')
    launch_dir = os.path.join(pkg_dir, 'launch')

    # 声明顶层参数
    use_sim_arg = DeclareLaunchArgument(
        'use_sim', default_value='false',
        description='是否使用仿真'
    )

    # 包含子 launch 文件，并传递参数
    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'sensors.launch.py')
        ),
        launch_arguments={
            'lidar_port': '/dev/ttyUSB1',   # 覆盖子文件的默认值
        }.items(),                          # 注意要 .items()
    )

    # 顶层自己的节点
    controller = Node(
        package='my_robot',
        executable='controller',
        name='controller',
        output='screen',
    )

    return LaunchDescription([
        use_sim_arg,
        sensors,
        controller,
    ])
```

**三个必须注意的点**：

**① `launch_arguments` 必须带 `.items()`**

```python
launch_arguments={'key': 'value'}.items()    # ✅
launch_arguments={'key': 'value'}            # ❌ 报错
```

这是 API 设计上的一个坑，非常容易忘。

**② 源文件的导入路径**

```python
from launch.launch_description_sources import PythonLaunchDescriptionSource
```

对应 XML 的是 `FrontendLaunchDescriptionSource`。**别搞混**，写错会报导入错误。

**③ 传参是「覆盖」而非「替换」**

`launch_arguments` 里的值会覆盖子文件的 `DeclareLaunchArgument` 默认值，但子文件里没声明的参数改不了。

---

### 2.7 理解「两层求值」（重点难点）

这是 Launch 最反直觉的地方。用一个例子讲透。

#### 问题复现

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    mode_arg = DeclareLaunchArgument('mode', default_value='sim')
    mode = LaunchConfiguration('mode')

    # ❌ 想根据 mode 选参数文件，但这样写不行
    if mode == 'sim':
        params = 'sim.yaml'
    else:
        params = 'real.yaml'

    return LaunchDescription([mode_arg])
```

**为什么不行？** 因为 `mode` 是个替换对象，不是字符串。`mode == 'sim'` 永远是 `False`。

#### 理解两层

```text
第一层：解析时（Python 代码在这里执行）
   ├─ 执行 generate_launch_description()
   ├─ 此时 LaunchConfiguration 只是个占位符对象
   └─ 无法知道用户会传什么值

第二层：运行时（launch 系统执行动作）
   ├─ 拿到用户传入的 mode:=real
   ├─ 把 LaunchConfiguration('mode') 求值成 'real'
   └─ 用求值结果去配置节点
```

**核心结论**：**依赖运行时信息的逻辑，不能写成解析时的 Python `if`。**

#### 正确做法：用 OpaqueFunction

当逻辑确实需要**运行时**的替换值时，用 `OpaqueFunction`：

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    """这个函数在运行时才被调用，可以拿到替换的真实值"""
    # context 提供了解析替换的能力
    mode = LaunchConfiguration('mode').perform(context)

    if mode == 'sim':
        params = 'sim.yaml'
    else:
        params = 'real.yaml'

    node = Node(
        package='param_demo',
        executable='configurable_publisher',
        name='configurable_publisher',
        output='screen',
        parameters=[params],
    )

    return [node]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='sim'),
        OpaqueFunction(function=launch_setup),
    ])
```

**关键点**：

```python
mode = LaunchConfiguration('mode').perform(context)
```

`.perform(context)` 是**把替换求值成真实值**的方法。`OpaqueFunction` 传进来一个 `context`，用它就能解开替换。

**`OpaqueFunction` 的返回值必须是「动作列表」**，不是 `LaunchDescription`。写成 `return [node]` 而不是 `return LaunchDescription([node])`。

#### 什么时候需要 OpaqueFunction？

| 需求 | 是否需要 |
| -------------------------------- | -------- |
| 固定路径拼接 | 不需要 |
| 简单的 `IfCondition` | 不需要 |
| **基于运行时参数做分支选择** | **需要** |
| **循环创建数量不定的节点** | **需要** |
| **读取 LaunchConfiguration 参与计算** | **需要** |

**经验**：当你发现自己在写 `if LaunchConfiguration(...) == ...` 时，就该用 `OpaqueFunction` 了。

---

### 2.8 Launch 调试技巧

Launch 的报错信息**普遍不友好**，掌握这些技巧能省很多时间。

#### 技巧 1：提高日志级别

```bash
ros2 launch launch_demo hello.launch.py --debug
```

`--debug` 会打印 Launch 内部的解析和执行细节，定位问题非常有用。

#### 技巧 2：查看实际执行的动作

```bash
ros2 launch launch_demo hello.launch.py --print-description
```

输出整个 Launch 描述树，能看到哪些动作被创建了。**如果某个节点没启动，先看这里它在不在**。

#### 技巧 3：检查 launch 文件语法

```bash
# 单独验证文件能否被加载
python3 -c "
from launch import LaunchDescription
import importlib.util
spec = importlib.util.spec_from_file_location('m', 'launch/hello.launch.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
desc = m.generate_launch_description()
print('OK, entities:', len(desc.entities))
"
```

**编译期就能发现语法错误**，不用等运行时。

#### 技巧 4：查看已安装的 launch 文件

```bash
ls install/launch_demo/share/launch_demo/launch/
```

**如果这里是空的，说明 `setup.py` 的 `data_files` 配错了**——这是「launch file not found」的头号原因。

#### 技巧 5：确认包是否被正确找到

```bash
ros2 pkg prefix launch_demo
```

如果报 `Package not found`，说明没 source 环境：

```bash
source install/setup.bash
```

#### 常见错误速查

| 报错 | 原因 | 解决 |
| ------------------------------------------------- | ---------------------------- | -------------------------------------------- |
| `file 'xxx.launch.py' not found` | 文件没被安装 / 文件名后缀不对 | 检查 `setup.py` 的 glob，确认是 `.launch.py` |
| `Package 'xxx' not found` | 没 source | `source install/setup.bash` |
| `Executable 'xxx' not found` | executable 名与 entry_points 不符 | 对照 `setup.py` 的 `console_scripts` |
| 节点启动了但看不到日志 | 没加 `output='screen'` | 加上这个参数 |
| `TypeError: can only concatenate str` | 用 `+` 拼接替换 | 改用列表形式 |
| `'dict' object has no attribute 'items'` | 忘了 `.items()` | `launch_arguments={...}.items()` |
| `launch_arguments` 传参无效 | 子文件没声明该参数 | 子文件加 `DeclareLaunchArgument` |
| `if LaunchConfiguration(...)` 永远不生效 | 两层求值问题 | 改用 `OpaqueFunction` |
| 参数传了但节点没用上 | 节点名不匹配 | 用 `name=` 显式指定，与 YAML 对齐 |
| 节点随机启动顺序导致报错 | 节点默认并行启动 | 见下方「启动顺序」 |

#### 深挖：启动顺序问题

**Launch 里所有节点默认是并行启动的**，列表顺序**不保证**执行顺序。

这会导致一个经典问题：

```python
# 期望：先启动 TF 广播器，再启动依赖 TF 的节点
return LaunchDescription([
    robot_state_publisher,   # 提供 TF
    navigation_node,         # 依赖 TF
])
```

但实际上 `navigation_node` 可能先启动，一上来就报 `No transform from base_link`。

**解决方案**：

**方案 A：用 `TimerAction` 延迟启动**（简单粗暴）

```python
from launch.actions import TimerAction

delayed_nav = TimerAction(
    period=3.0,      # 延迟 3 秒
    actions=[navigation_node],
)

return LaunchDescription([
    robot_state_publisher,
    delayed_nav,
])
```

**方案 B：让节点自己能容错**（推荐）

在节点代码里处理「TF 还没准备好」的情况，例如用 `wait_for_transform`：

```python
# 在节点里等待 TF 可用，而不是靠 launch 延迟
self.tf_buffer.can_transform('base_link', 'laser', rclpy.time.Time(),
                             timeout=rclpy.duration.Duration(seconds=5.0))
```

**真实项目的做法**：两者结合。Launch 里做适度的延迟（2-3 秒），节点内部也做容错。**不要单纯依赖 launch 的顺序**。

---

### 2.9 实战案例：一键启动完整系统

把本章所有知识点串起来，模拟一个真实的机器人启动文件。

#### 目录结构

```text
launch_demo/
├── config/
│   ├── sim_params.yaml
│   └── real_params.yaml
├── launch/
│   ├── robot.launch.py         # 顶层
│   ├── sensors.launch.py       # 传感器层
│   └── visualization.launch.py # 可视化层
└── setup.py
```

#### sensors.launch.py

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """传感器层：激光雷达 + 相机"""

    use_sim_arg = DeclareLaunchArgument(
        'use_sim', default_value='true',
        description='是否使用仿真')

    lidar_port_arg = DeclareLaunchArgument(
        'lidar_port', default_value='/dev/ttyUSB0',
        description='激光雷达串口')

    lidar = Node(
        package='my_lidar_driver',
        executable='lidar_node',
        name='lidar',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('lidar_port'),
            'frame_id': 'laser_link',
            'use_sim': LaunchConfiguration('use_sim'),
        }],
    )

    camera = Node(
        package='my_camera_driver',
        executable='camera_node',
        name='camera',
        output='screen',
        parameters=[{
            'frame_id': 'camera_link',
            'fps': 30,
        }],
    )

    return LaunchDescription([
        use_sim_arg,
        lidar_port_arg,
        lidar,
        camera,
    ])
```

#### visualization.launch.py

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """可视化层：RViz2"""

    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='是否启动 RViz2')

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        rviz_arg,
        rviz,
    ])
```

#### robot.launch.py（顶层）

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """顶层：一键启动整套机器人系统"""

    pkg_dir = get_package_share_directory('launch_demo')
    launch_dir = os.path.join(pkg_dir, 'launch')
    config_dir = os.path.join(pkg_dir, 'config')

    # ========== 声明所有顶层参数 ==========
    use_sim_arg = DeclareLaunchArgument(
        'use_sim', default_value='true',
        description='true=仿真, false=真机')

    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='是否启动 RViz2')

    use_sim = LaunchConfiguration('use_sim')

    # ========== 根据 use_sim 选参数文件（OpaqueFunction 场景） ==========
    # 这里简化处理：两个文件都加载，后者覆盖前者
    sim_params = os.path.join(config_dir, 'sim_params.yaml')
    real_params = os.path.join(config_dir, 'real_params.yaml')

    # ========== 包含子 launch ==========
    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'sensors.launch.py')
        ),
        launch_arguments={
            'use_sim': use_sim,
        }.items(),
    )

    visualization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'visualization.launch.py')
        ),
        launch_arguments={
            'rviz': LaunchConfiguration('rviz'),
        }.items(),
    )

    # ========== 核心控制节点 ==========
    controller = Node(
        package='param_demo',
        executable='configurable_publisher',
        name='configurable_publisher',
        output='screen',
        parameters=[
            sim_params,
            {'publish_rate': 10.0},     # 局部覆盖
        ],
    )

    # ========== 延迟启动依赖 TF 的节点 ==========
    delayed_nav = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='demo_nodes_cpp',
                executable='talker',
                name='nav_node',
                output='screen',
            ),
        ],
    )

    return LaunchDescription([
        use_sim_arg,
        rviz_arg,
        sensors,
        visualization,
        controller,
        delayed_nav,
    ])
```

#### 运行方式

```bash
colcon build --packages-select launch_demo
source install/setup.bash

# 仿真模式 + RViz
ros2 launch launch_demo robot.launch.py

# 真机模式，不开 RViz
ros2 launch launch_demo robot.launch.py use_sim:=false rviz:=false

# 查看所有可配置参数
ros2 launch launch_demo robot.launch.py --show-args
```

**这就是 Launch 的终极价值**：一条命令，切换整套系统配置。

---

## 🔄 Humble 与 Jazzy 差异对照

| 项目 | Humble (22.04) | Jazzy (24.04) |
| ---------------------------- | ------------------ | ------------------ |
| `generate_launch_description` | 一致 | 一致 |
| `Node` 动作 | `launch_ros.actions.Node` | 一致 |
| `IfCondition` / `UnlessCondition` | 一致 | 一致 |
| `OpaqueFunction` | 支持 | 支持 |
| `PathJoinSubstitution` | 支持 | 支持 |
| `--print-description` | 支持 | 支持 |
| `FindPackageShare` | `launch_ros.substitutions` | 一致 |
| Python 版本 | 3.10 | 3.12 |

**结论**：Launch API 在 Humble 与 Jazzy 之间**高度兼容**，本教程代码可直接互用。

**两个小差异**：

1. **Jazzy 的参数求值更严格**。某些在 Humble 里能隐式转换的类型，在 Jazzy 会报错，需要显式包装（如 `TextSubstitution`）。
2. **Jazzy 的 `--print-description` 输出更详细**，调试体验更好。

**实践建议**：如果你在 Humble 里写了能跑的 Launch 文件，迁移到 Jazzy 时**优先检查参数类型**，这是最可能出问题的地方。

---

## ✅ 总结

### 核心知识点回顾

| 概念 | 说明 | 关键代码 |
| ------------------------ | ------------------------------ | ---------------------------------------------------- |
| **Launch 文件命名** | 必须以 `.launch.py` 结尾 | `hello.launch.py` |
| **必需函数** | 返回 `LaunchDescription` | `generate_launch_description()` |
| **启动节点** | 指定包和可执行文件 | `Node(package=, executable=)` |
| **日志输出** | 不加就看不到节点输出 | `output='screen'` |
| **传参** | 三种方式 | `parameters=[{...}]` / `[yaml]` / `[yaml, {...}]` |
| **重映射** | 改话题/服务名 | `remappings=[('a','b')]` |
| **命名空间** | 加名前缀 | `namespace='robot1'` |
| **条件** | 选择性启动 | `condition=IfCondition(...)` |
| **替换** | 运行时占位符 | `LaunchConfiguration('x')` |
| **包含子文件** | 分层复用 | `IncludeLaunchDescription` |
| **运行时逻辑** | 处理两层求值 | `OpaqueFunction` |
| **路径定位** | 别硬编码 | `get_package_share_directory()` |
| **延迟启动** | 解决顺序问题 | `TimerAction(period=3.0)` |

### 代码模板速查

#### 最小模板

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_pkg',
            executable='my_node',
            name='my_node',
            output='screen',
        ),
    ])
```

#### 带参数的模板

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    arg = DeclareLaunchArgument('rate', default_value='10.0')

    params = os.path.join(
        get_package_share_directory('my_pkg'), 'config', 'params.yaml')

    node = Node(
        package='my_pkg',
        executable='my_node',
        name='my_node',
        output='screen',
        parameters=[params, {'rate': LaunchConfiguration('rate')}],
    )

    return LaunchDescription([arg, node])
```

#### 包含子 launch 的模板

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_dir = get_package_share_directory('my_pkg')

    sub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'sub.launch.py')
        ),
        launch_arguments={'key': 'value'}.items(),
    )

    return LaunchDescription([sub])
```

#### OpaqueFunction 模板

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration

def launch_setup(context, *args, **kwargs):
    # 运行时才能拿到真实值
    mode = LaunchConfiguration('mode').perform(context)

    nodes = []
    if mode == 'sim':
        nodes.append(make_sim_node())
    else:
        nodes.append(make_real_node())

    return nodes    # 返回动作列表

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='sim'),
        OpaqueFunction(function=launch_setup),
    ])
```

### 调试命令速查

| 目的 | 命令 |
| ------------------------ | ------------------------------------------- |
| 查看可配置参数 | `ros2 launch <pkg> <file> --show-args` |
| 提高日志级别 | `ros2 launch <pkg> <file> --debug` |
| 打印描述树 | `ros2 launch <pkg> <file> --print-description` |
| 列出所有 launch 文件 | `ros2 launch <pkg> --show-all` |
| 检查安装的 launch 文件 | `ls install/<pkg>/share/<pkg>/launch/` |
| 定位包路径 | `ros2 pkg prefix <pkg>` |

### Launch 与其他章节的关系

```text
03 节点  ────┐
04 CLI   ────┤
05 话题  ────┤
06 服务/动作 ─┼──> 08 Launch（统一编排）
07 参数  ────┘
              │
              ▼
        09 colcon（构建）
              │
              ▼
        12-15 仿真与实战
```

**Launch 是把前面所有知识「工程化」的那一环**。学完它，你就有能力组织一个真实项目了。

### 下一步学习方向

- 📘 [09 - colcon 构建系统与依赖管理详解](09_colcon_build.md)
- 📘 [10 - C++ 与 Python 节点混合开发](10_cpp_python_nodes.md)
- 📘 [19 - ROS2 常见错误与踩坑记录](19_ros2_debug_notes.md)

---

📘 下一章：[09 - colcon 构建系统与依赖管理详解](09_colcon_build.md)
