# 🧰【ROS2 入门系列 #4】ROS2 常用命令行工具与调试技巧（ros2 node / topic / run）

> 作者：whatqiu  
> 更新时间：2025-11-12  
> 环境：Ubuntu 22.04 + ROS2 Humble  

---

## 🧭 前言

在前面几章中，我们已经学习了 ROS2 的基础概念、创建了工作空间和节点。但是，在实际开发中，我们经常需要调试、监控和检查节点、话题、服务等的运行状态。

ROS2 提供了一套强大的命令行工具（CLI tools），使我们能够：
- 查看和管理正在运行的节点
- 监控话题通信
- 调用服务和查看参数
- 记录和回放数据
- 调试和诊断问题

本章将系统介绍 ROS2 常用的命令行工具，并通过实际示例帮助你掌握这些调试利器。

**预计学习时间**：40-50 分钟

**前置章节**：
- [02 - ROS2 架构与基础概念全解析](02_ros2_basics.md)
- [03 - 创建第一个 ROS2 工作空间与 Python 节点](03_first_workspace_and_node.md)

---

## 🧱 一、主要内容

### 1.1 ROS2 命令行工具概述

ROS2 提供了丰富的命令行工具，主要分为以下几类：

| 类别 | 命令 | 功能 |
|------|------|------|
| **节点管理** | `ros2 node` | 查看节点信息、列出节点 |
| **话题通信** | `ros2 topic` | 查看话题、发布/订阅消息 |
| **服务调用** | `ros2 service` | 查看服务、调用服务 |
| **参数管理** | `ros2 param` | 查看、设置参数 |
| **动作接口** | `ros2 action` | 查看和调用动作 |
| **包管理** | `ros2 pkg` | 管理功能包 |
| **守护进程** | `ros2 daemon` | 管理 ROS2 守护进程 |
| **数据记录** | `ros2 bag` | 记录和回放数据 |

### 1.2 准备工作

为了演示这些命令行工具，我们需要先启动一些示例节点。

#### 启动 turtlesim

**终端 1** - 启动 turtlesim 节点：
```bash
source /opt/ros/humble/setup.bash
ros2 run turtlesim turtlesim_node
```

**终端 2** - 启动键盘控制节点：
```bash
source /opt/ros/humble/setup.bash
ros2 run turtlesim turtle_teleop_key
```

**终端 3** - 用于执行各种调试命令

---

## 🧩 二、示例与讲解

### 2.1 节点管理工具（ros2 node）

#### 2.1.1 列出所有节点

```bash
ros2 node list
```

**输出示例**：
```
/teleop_turtle
/turtlesim
```

**说明**：
- `/teleop_turtle`：键盘控制节点
- `/turtlesim`：小乌龟仿真节点

#### 2.1.2 查看节点详细信息

```bash
ros2 node info /turtlesim
```

**输出示例**：
```
/turtlesim
  Subscribers:
    /turtle1/cmd_vel: geometry_msgs/msg/Twist
  Publishers:
    /turtle1/color_sensor: turtlesim/msg/Color
    /turtle1/pose: turtlesim/msg/Pose
  Service Servers:
    /clear: std_srvs/srv/Empty
    /kill: turtlesim/srv/Kill
    /reset: std_srvs/srv/Empty
    /spawn: turtlesim/srv/Spawn
    /turtle1/set_pen: turtlesim/srv/SetPen
    /turtle1/teleport_absolute: turtlesim/srv/TeleportAbsolute
    /turtle1/teleport_relative: turtlesim/srv/TeleportRelative
  Service Clients:
  Action Servers:
  Action Clients:
```

**说明**：
- **Subscribers**：该节点订阅的话题
- **Publishers**：该节点发布的话题
- **Service Servers**：该节点提供的服务
- **Service Clients**：该节点调用的服务

#### 2.1.3 实用技巧

**查看所有节点的名称空间**：
```bash
ros2 node list -t
```

**只列出唯一节点名称**（避免重复）：
```bash
ros2 node list --skip-ghost-nodes
```

---

### 2.2 话题管理工具（ros2 topic）

#### 2.2.1 列出所有话题

```bash
ros2 topic list
```

**输出示例**：
```
/parameter_events
/rosout
/turtle1/cmd_vel
/turtle1/color_sensor
/turtle1/pose
```

#### 2.2.2 查看话题详细信息

```bash
ros2 topic info /turtle1/cmd_vel
```

**输出示例**：
```
Type: geometry_msgs/msg/Twist
Publisher count: 1
Subscription count: 1
```

**说明**：
- **Type**：消息类型
- **Publisher count**：发布者数量
- **Subscription count**：订阅者数量

#### 2.2.3 实时监控话题数据

**基本用法**：
```bash
ros2 topic echo /turtle1/cmd_vel
```

现在用方向键控制小乌龟，你会看到实时的速度数据输出：
```
linear:
  x: 2.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 1.0
---
linear:
  x: 0.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0
---
```

**高级选项**：

**只显示 N 条消息后退出**：
```bash
ros2 topic echo --once /turtle1/cmd_vel
```

**显示消息头信息**：
```bash
ros2 topic echo --no-arr /turtle1/cmd_vel
```

**过滤输出**（只显示特定字段）：
```bash
ros2 topic echo /turtle1/cmd_vel --field linear.x
```

#### 2.2.4 查看话题发布频率

```bash
ros2 topic hz /turtle1/cmd_vel
```

**输出示例**：
```
average rate: 1.000
min: 1.000s max: 1.001s std dev: 0.00023s window: 10
```

**说明**：显示话题的平均发布频率

#### 2.2.5 查看消息带宽

```bash
ros2 topic bw /turtle1/cmd_vel
```

**输出示例**：
```
Subscribed to [/turtle1/cmd_vel]
average: 250 B/s
mean min: 250 B/s max: 250 B/s window: 10
```

#### 2.2.6 直接发布消息到话题

**单次发布**：
```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.0}}"
```

**持续发布（让小乌龟画圈）**：
```bash
ros2 topic pub --rate 1 /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}"
```

**参数说明**：
- `--rate 1`：每秒发布 1 次
- `--once`：只发布一次

#### 2.2.7 查看话题类型定义

```bash
ros2 topic type /turtle1/cmd_vel
```

**输出**：
```
geometry_msgs/msg/Twist
```

**查看消息结构**：
```bash
ros2 interface show geometry_msgs/msg/Twist
```

**输出**：
```
# This message expresses a velocity in free space broken into its linear and angular parts.
Vector3  linear
Vector3  angular
```

---

### 2.3 服务管理工具（ros2 service）

#### 2.3.1 列出所有服务

```bash
ros2 service list
```

**输出示例**：
```
/clear
/kill
/reset
/spawn
/teleop_turtle/describe_parameters
/teleop_turtle/get_parameter_types
/teleop_turtle/get_parameters
/turtlesim/describe_parameters
/turtlesim/get_parameter_types
/turtlesim/get_parameters
...
```

#### 2.3.2 查看服务类型

```bash
ros2 service type /spawn
```

**输出**：
```
turtlesim/srv/Spawn
```

#### 2.3.3 查看服务类型定义

```bash
ros2 interface show turtlesim/srv/Spawn
```

**输出**：
```
float32 x
float32 y
float32 theta
string name
---
string name
```

**说明**：
- `---` 上方是请求字段
- `---` 下方是响应字段

#### 2.3.4 调用服务

**生成新的小乌龟**：
```bash
ros2 service call /spawn turtlesim/srv/Spawn "{x: 2.0, y: 2.0, theta: 0.0, name: 'turtle2'}"
```

**响应**：
```
requester: making request: turtlesim.srv.Spawn_Request(x=2.0, y=2.0, theta=0.0, name='turtle2')

response:
turtlesim.srv.Spawn_Response(name='turtle2')
```

你会看到窗口中出现了第二只小乌龟！

**清空画布**：
```bash
ros2 service call /clear std_srvs/srv/Empty
```

---

### 2.4 参数管理工具（ros2 param）

#### 2.4.1 列出节点参数

```bash
ros2 param list /turtlesim
```

**输出示例**：
```
background_b
background_g
background_r
use_sim_time
```

#### 2.4.2 获取参数值

```bash
ros2 param get /turtlesim background_b
```

**输出**：
```
Integer value is: 255
```

**获取所有参数**：
```bash
ros2 param dump /turtlesim
```

**输出示例**：
```yaml
/turtlesim:
  ros__parameters:
    background_b: 255
    background_g: 86
    background_r: 150
    use_sim_time: false
```

#### 2.4.3 设置参数值

**修改背景颜色为紫色**：
```bash
ros2 param set /turtlesim background_r 150
ros2 param set /turtlesim background_g 50
ros2 param set /turtlesim background_b 150
```

你会发现小乌龟窗口的背景色变成了紫色！

#### 2.4.4 从文件加载参数

**保存参数到文件**：
```bash
ros2 param dump /turtlesim > turtlesim_params.yaml
```

**从文件加载参数**：
```bash
ros2 param load /turtlesim turtlesim_params.yaml
```

---

### 2.5 包管理工具（ros2 pkg）

#### 2.5.1 列出所有包

```bash
ros2 pkg list
```

**过滤输出**（查找特定包）：
```bash
ros2 pkg list | grep turtlesim
```

#### 2.5.2 查看包信息

**查看包描述**：
```bash
ros2 pkg xml turtlesim
```

**查看包前缀（安装路径）**：
```bash
ros2 pkg prefix turtlesim
```

#### 2.5.3 列出包的可执行文件

```bash
ros2 pkg executables turtlesim
```

**输出**：
```
turtlesim turtlesim_node
turtlesim turtle_teleop_key
turtlesim draw_square
```

#### 2.5.4 查看包依赖

```bash
ros2 pkg dependencies turtlesim
```

**只查看直接依赖**：
```bash
ros2 pkg dependencies --from turtlesim --depth 1
```

---

### 2.6 动作管理工具（ros2 action）

#### 2.6.1 列出所有动作

```bash
ros2 action list
```

**注意**：turtlesim 没有动作服务器，可能输出为空。

#### 2.6.2 查看动作信息

```bash
ros2 action info <action_name>
```

#### 2.6.3 发送动作目标

```bash
ros2 action send_goal <action_name> <action_type> "<action_data>"
```

---

### 2.7 数据记录与回放（ros2 bag）

#### 2.7.1 记录数据

**记录所有话题**：
```bash
ros2 bag record -a -o my_bag
```

**记录特定话题**：
```bash
ros2 bag record /turtle1/cmd_vel /turtle1/pose -o cmd_vel_bag
```

**参数说明**：
- `-a`：记录所有话题
- `-o`：指定输出文件名

#### 2.7.2 查看包信息

```bash
ros2 bag info my_bag
```

**输出示例**：
```
Files:             my_bag.db3
Bag size:          200.0 KiB
Storage id:        sqlite3
Duration:          35.32s
Start:             Jan  2 12:00:00 2026
End:               Jan  2 12:00:35 2026
Messages:          150
Topic information: Topic /turtle1/cmd_vel | Type: geometry_msgs/msg/Twist | Count: 50 |
Topic /turtle1/pose | Type: turtlesim/msg/Pose | Count: 100 |
```

#### 2.7.3 回放数据

```bash
ros2 bag play my_bag
```

**循环播放**：
```bash
ros2 bag play -l my_bag
```

**以特定速率播放**（2倍速）：
```bash
ros2 bag play -r 2.0 my_bag
```

---

### 2.8 实用调试技巧

#### 2.8.1 组合命令管道

**查找所有发布者数量大于1的话题**：
```bash
ros2 topic list | xargs -I {} sh -c 'ros2 topic info {} | grep -q "Publisher count: [2-9]" && echo {}'
```

**监控所有话题的发布频率**：
```bash
for topic in $(ros2 topic list); do echo "Topic: $topic"; ros2 topic hz $topic & done
```

#### 2.8.2 使用 tab 自动补全

ROS2 命令行工具支持强大的 tab 自动补全功能：

```bash
ros2 topic <TAB>              # 列出所有子命令
ros2 topic echo <TAB>         # 列出所有话题
ros2 topic echo /tu<TAB>      # 自动补全为 /turtle1/
```

#### 2.8.3 设置日志级别

**查看节点日志级别**：
```bash
ros2 node list                  # 找到节点名
ros2 param get /node_name log_level
```

**设置日志级别**：
```bash
ros2 run <package> <node> --ros-args --log-level debug
```

日志级别（从低到高）：
- `debug`
- `info`
- `warn`
- `error`
- `fatal`

---

### 2.9 综合示例：完整的调试流程

让我们通过一个完整的示例来演示如何使用命令行工具调试 ROS2 节点。

#### 场景：调试小乌龟无法移动的问题

**步骤 1：检查节点是否运行**

```bash
ros2 node list
```

预期输出应该包含：
```
/teleop_turtle
/turtlesim
```

**步骤 2：检查话题连接**

```bash
ros2 topic info /turtle1/cmd_vel
```

预期输出应该显示：
```
Publisher count: 1
Subscription count: 1
```

**步骤 3：监控话题数据**

```bash
ros2 topic echo /turtle1/cmd_vel
```

按方向键，应该看到速度数据输出。

**步骤 4：检查话题类型**

```bash
ros2 topic type /turtle1/cmd_vel
```

应该输出：
```
geometry_msgs/msg/Twist
```

**步骤 5：手动测试发布**

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

小乌龟应该移动。

**步骤 6：记录和分析数据**

```bash
ros2 bag record /turtle1/cmd_vel /turtle1/pose -o debug_bag
# 执行一些操作
# Ctrl+C 停止记录
ros2 bag info debug_bag
```

通过这个完整的调试流程，你可以系统地定位和解决问题。

---

## ✅ 总结

### 命令速查表

| 类别 | 命令 | 功能 |
|------|------|------|
| **节点** | `ros2 node list` | 列出所有节点 |
| | `ros2 node info <node>` | 查看节点详细信息 |
| **话题** | `ros2 topic list` | 列出所有话题 |
| | `ros2 topic info <topic>` | 查看话题信息 |
| | `ros2 topic echo <topic>` | 实时显示话题数据 |
| | `ros2 topic pub <topic> <type> <data>` | 发布消息到话题 |
| | `ros2 topic hz <topic>` | 查看话题发布频率 |
| | `ros2 topic bw <topic>` | 查看话题带宽 |
| **服务** | `ros2 service list` | 列出所有服务 |
| | `ros2 service type <service>` | 查看服务类型 |
| | `ros2 service call <srv> <type> <data>` | 调用服务 |
| **参数** | `ros2 param list <node>` | 列出节点参数 |
| | `ros2 param get <node> <param>` | 获取参数值 |
| | `ros2 param set <node> <param> <value>` | 设置参数值 |
| | `ros2 param dump <node>` | 导出参数到 YAML |
| **包** | `ros2 pkg list` | 列出所有包 |
| | `ros2 pkg executables <pkg>` | 列出包的可执行文件 |
| **数据** | `ros2 bag record -a` | 记录所有话题 |
| | `ros2 bag play <bag>` | 回放数据 |

### 关键要点

1. **系统化调试**：使用 `node` → `topic` → `echo` 的流程系统地检查问题
2. **实时监控**：`echo`、`hz`、`bw` 命令是实时监控的利器
3. **手动测试**：`topic pub` 和 `service call` 可以手动测试功能
4. **数据记录**：`ros2 bag` 用于记录和回放，方便离线分析
5. **Tab 补全**：充分利用 tab 自动补全提高效率

### 下一步学习

- 📘 [05 - 话题通信详解（Publisher / Subscriber / QoS）](05_topics_pub_sub.md)
- 📘 [06 - 服务与动作通信（Service / Action）](06_services_and_actions.md)
- 📘 [07 - 参数服务器与动态参数管理](07_parameters_and_config.md)
- 📘 [08 - ROS2 Launch 文件](08_ros2_launch.md)

---

**Sources:**
- [Beginner: CLI tools - Humble documentation](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools.html)
- [Understanding nodes — ROS 2 Documentation](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Nodes/Understanding-ROS2-Nodes.html)
- [Understanding topics — ROS 2 Documentation](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
- [Tutorials - Humble documentation](https://docs.ros.org/en/humble/Tutorials.html)
