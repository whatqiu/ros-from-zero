# ⚙️【ROS2 入门系列 #2】ROS2 架构与基础概念全解析（节点 / 话题 / 服务 / 参数）

> 作者：whatqiu  
> 更新时间：2025-11-12  
> 环境：Ubuntu 22.04 + ROS2 Humble  

---

## 🧭 前言

上一章我们成功安装了 ROS2 环境，现在来学习 ROS2 的核心概念！

刚开始接触 ROS2 时，我被节点、话题、服务这些概念搞得头大。但通过运行经典的 turtlesim 小乌龟示例，一步步调试操作后，终于理解了这些概念的含义和使用方法。

这篇文章会记录我从零开始学习 ROS2 基础概念的完整过程，包括遇到的各种问题和解决方案。

---

## 🐢 一、初识 turtlesim 小乌龟

turtlesim 是 ROS2 的入门必备教程，就像编程语言的 "Hello World" 一样。

通过控制小乌龟移动，我们能直观地理解 ROS2 的通信机制。

### 启动 turtlesim

首先确保 ROS2 环境已加载：

```bash
source /opt/ros/humble/setup.bash
```

然后运行：

```bash
ros2 run turtlesim turtlesim_node
```

如果一切正常，你会看到一个蓝色背景的窗口，里面有一只小乌龟 🐢

### 控制小乌龟移动

打开另一个终端，运行：

```bash
ros2 run turtlesim turtle_teleop_key
```

现在你可以用方向键控制小乌龟移动了！

**注意**：确保 `turtle_teleop_key` 终端窗口处于激活状态（点击该终端）

- **↑** 向前移动
- **↓** 向后移动
- **←** 逆时针旋转
- **→** 顺时针旋转

---

## 🧩 二、理解节点（Node）概念

### 什么是节点？

在 ROS2 中，**节点**是最小的可执行单元。

你可以把它想象成一个程序，每个节点负责特定的功能。

在我们的例子中：
- `turtlesim_node`：负责显示小乌龟和处理移动逻辑
- `turtle_teleop_key`：负责接收键盘输入并发送移动指令

### 查看正在运行的节点

打开新终端，执行：

```bash
ros2 node list
```

输出类似：
```
/teleop_turtle
/turtlesim
```

### 查看节点信息

```bash
ros2 node info /turtlesim
```

你会看到这个节点订阅了什么话题、发布了什么话题、提供了什么服务等详细信息。

### 节点的生命周期

节点可以：

1. **启动**：通过 `ros2 run` 命令启动
2. **通信**：与其他节点通过话题、服务等进行数据交换
3. **停止**：Ctrl+C 终止运行

---

## 📊 三、话题（Topic）通信机制

### 什么是话题？

**话题**是节点之间通信的主要方式，采用**发布-订阅**模式：

- 发布者（Publisher）向话题发送数据
- 订阅者（Subscriber）从话题接收数据
- 多个发布者和订阅者可以连接到同一个话题

### 查看当前话题

```bash
ros2 topic list
```

你会看到类似输出：
```
/parameter_events
/rosout
/turtle1/cmd_vel
/turtle1/color_sensor
/turtle1/pose
```

### 实时监控话题数据

让我们看看小乌龟的速度指令：

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
```

### 查看话题详情

```bash
ros2 topic info /turtle1/cmd_vel
```

输出：
```
Type: geometry_msgs/msg/Twist
Publisher count: 1
Subscription count: 1
```

### 直接发布话题数据

我们也可以直接通过命令行发送移动指令：

**单次发送**：
```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.0}}"
```

小乌龟会移动一小段距离然后停止。

**持续发送**（让小乌龟画圈）：
```bash
ros2 topic pub --rate 1 /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}"
```

按 `Ctrl+C` 停止发送。

---

## 🤝 四、服务（Service）通信

### 什么是服务？

**服务**是同步的请求-响应通信机制：

- 客户端（Client）发送请求
- 服务端（Server）处理请求并返回响应
- 一对一的通信模式

### 查看可用服务

```bash
ros2 service list
```

输出包含：
```
/spawn
/teleop_turtle/describe_parameters
/teleop_turtle/get_parameter_types
/teleop_turtle/get_parameters
/turtlesim/describe_parameters
/turtlesim/get_parameter_types
/turtlesim/get_parameters
...
```

### 生成新的小乌龟

`/spawn` 服务可以创建新的小乌龟：

```bash
ros2 service call /spawn turtlesim/srv/Spawn "{x: 2.0, y: 2.0, theta: 0.0, name: 'turtle2'}"
```

你会看到窗口中出现第二只小乌龟！

### 查看服务类型

```bash
ros2 service type /spawn
```

输出：`turtlesim/srv/Spawn`

---

## ⚙️ 五、参数（Parameter）系统

### 什么是参数？

**参数**是节点的配置变量，可以在运行时动态修改。

### 查看节点参数

```bash
ros2 param list /turtlesim
```

输出可能包含：
```
background_b
background_g
background_r
use_sim_time
```

### 获取参数值

```bash
ros2 param get /turtlesim background_b
```

### 修改参数值

让我们改变背景颜色：

```bash
ros2 param set /turtlesim background_r 150
ros2 param set /turtlesim background_g 50
ros2 param set /turtlesim background_b 150
```

你会发现小乌龟窗口的背景色变成了紫色！

### 保存参数配置

```bash
ros2 param dump /turtlesim > turtlesim_params.yaml
```

这个 YAML 文件可以用来恢复参数配置。

---

## 🛠️ 六、常见问题排查

### 问题 1：turtlesim 窗口无法启动

**症状**：
```bash
ros2 run turtlesim turtlesim_node
```
执行后没有任何反应或报错。

**解决方案**：
1. 检查环境变量是否正确加载：
```bash
echo $ROS_DISTRO
```
应该输出 `humble`

2. 确保没有其他 turtlesim 实例在运行：
```bash
pkill -f turtlesim
```

3. 重新加载环境：
```bash
source /opt/ros/humble/setup.bash
```

### 问题 2：键盘控制没有响应

**症状**：运行 `turtle_teleop_key` 后，按方向键小乌龟不动。

**解决方案**：
1. 确保 `turtle_teleop_key` 终端处于**激活状态**（点击该终端窗口）
2. 检查 turtlesim 是否正在运行：
```bash
ros2 node list
```
应该能看到 `/turtlesim` 和 `/teleop_turtle`

3. 查看话题是否正常发布：
```bash
ros2 topic hz /turtle1/cmd_vel
```

### 问题 3：命令不识别

**症状**：
```bash
ros2: command not found
```

**解决方案**：
1. 重新加载环境：
```bash
source /opt/ros/humble/setup.bash
```

2. 检查环境是否正确设置：
```bash
which ros2
```
应该显示 ROS2 安装路径

---

## 🎯 七、综合练习：让小乌龟画正方形

让我们综合运用学到的知识，编写一个简单的程序让小乌龟画正方形。

### 方法 1：直接命令行操作

```bash
# 前进 2 秒
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
sleep 2

# 转弯 90 度（1.57 弧度）
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.57}}"
sleep 1

# 重复 3 次完成正方形
```

### 方法 2：使用循环脚本

创建一个简单的 bash 脚本 `draw_square.sh`：

```bash
#!/bin/bash

for i in {1..4}
do
    echo "绘制第 $i 条边..."
    # 前进
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
    sleep 2

    # 转弯
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.57}}"
    sleep 1
done

echo "正方形绘制完成！"
```

运行脚本：
```bash
chmod +x draw_square.sh
./draw_square.sh
```

### 进阶挑战

1. **画五角星**：尝试计算正确的角度和步长
2. **画螺旋**：逐渐减小线段长度
3. **创建彩色轨迹**：结合参数修改来改变颜色

---

## 🧠 八、关键概念回顾

通过 turtlesim 示例，我们掌握了 ROS2 的四个核心概念：

### 数据流示例

当我们按下方向键时：
1. `turtle_teleop_key` 节点接收到键盘输入
2. 通过话题 `/turtle1/cmd_vel` 发布速度消息
3. `turtlesim_node` 节点订阅这个话题
4. 根据接收到的速度指令更新小乌龟位置
5. 通过话题 `/turtle1/pose` 发布新的位置信息

### 命令速查表

| 功能 | 命令 |
|------|------|
| 查看节点 | `ros2 node list` |
| 查看话题 | `ros2 topic list` |
| 查看服务 | `ros2 service list` |
| 查看参数 | `ros2 param list <node_name>` |
| 监控话题 | `ros2 topic echo <topic_name>` |
| 发布消息 | `ros2 topic pub <options> <topic> <type> <data>` |
| 调用服务 | `ros2 service call <service> <type> <data>` |

---

## ✅ 九、总结

| 概念 | 作用 | 常用命令 | 理解要点 |
|------|------|----------|----------|
| **节点 (Node)** | 独立的功能单元 | `ros2 node list/info` | 一个程序，负责特定任务 |
| **话题 (Topic)** | 异步通信 | `ros2 topic list/info/echo/pub` | 发布-订阅模式，一对多 |
| **服务 (Service)** | 同步通信 | `ros2 service list/call/type` | 请求-响应模式，一对一 |
| **参数 (Parameter)** | 配置管理 | `ros2 param list/get/set` | 运行时可修改的配置变量 |

### 关键收获

1. **节点是基础**：理解了节点是 ROS2 的最小执行单元
2. **话题是核心**：大部分通信都通过话题进行，掌握了发布-订阅机制
3. **服务是补充**：用于需要即时响应的场景
4. **参数是配置**：让节点行为可动态调整
5. **命令行工具很重要**：`ros2 node/topic/service/param` 系列命令是调试利器

### 下一步学习方向

- 学习创建自己的 ROS2 包和节点
- 理解消息（Message）和服务（Service）定义
- 掌握启动文件（Launch File）的使用
- 了解动作（Action）和参数服务器的进阶用法

---

📘 下一章：ROS2 编程入门 - 创建你的第一个节点
