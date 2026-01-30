# 🔄【ROS2 入门系列 #5】话题通信详解（Publisher / Subscriber / QoS）

> 作者：whatqiu
> 更新时间：2025-11-12
> 环境：Ubuntu 22.04 + ROS2 Humble

---

## 🧭 前言

在上一章中，我们学习了 ROS2 常用的命令行工具，可以查看和调试节点、话题、服务等。但是，要真正理解 ROS2 的通信机制，我们需要深入了解话题（Topic）的发布-订阅模型以及如何在代码中实现。

本章将带你深入话题通信的实现细节：
- 如何编写发布者（Publisher）节点
- 如何编写订阅者（Subscriber）节点
- 理解消息（Message）类型
- QoS（服务质量）配置详解
- 实战案例：温度监控系统

**预计学习时间**：45-60 分钟

**前置章节**：
- [02 - ROS2 架构与基础概念全解析](02_ros2_basics.md)
- [03 - 创建第一个 ROS2 工作空间与 Python 节点](03_first_workspace_and_node.md)
- [04 - ROS2 常用命令行工具与调试技巧](04_ros2_cli_tools.md)

---

## 🧱 一、主要内容

### 1.1 话题通信核心概念

**发布-订阅模式**是 ROS2 中最常用的通信机制：

```
发布者（Publisher） → 话题（Topic） → 订阅者（Subscriber）
```

- **发布者**：向话题发送数据的节点
- **订阅者**：从话题接收数据的节点
- **话题**：通信的中间通道，用名称标识（如 `/turtle1/cmd_vel`）
- **消息**：话题中传输的数据，有特定的数据类型

### 1.2 发布者-订阅者工作流程

1. **发布者创建**：节点创建发布者，指定话题名称和消息类型
2. **订阅者创建**：节点创建订阅者，指定话题名称、消息类型和回调函数
3. **数据发送**：发布者创建消息对象并发布
4. **数据接收**：订阅者通过回调函数接收并处理消息

---

## 🧩 二、示例与讲解

### 2.1 消息（Message）类型基础

在编写发布者和订阅者之前，需要了解消息类型。

#### 常见的标准消息类型

| 包名 | 消息类型 | 用途 |
|------|----------|------|
| `std_msgs/msg/String` | 字符串消息 | 文本数据 |
| `std_msgs/msg/Int32` | 32位整数 | 数值数据 |
| `std_msgs/msg/Float64` | 64位浮点数 | 浮点数值 |
| `geometry_msgs/msg/Twist` | 速度消息 | 线速度+角速度 |
| `sensor_msgs/msg/LaserScan` | 激光扫描 | 激光雷达数据 |
| `sensor_msgs/msg/Image` | 图像消息 | 摄像头图像 |

#### 查看消息结构

```bash
# 查看 Twist 消息的详细结构
ros2 interface show geometry_msgs/msg/Twist
```

输出：
```
# This message expresses a velocity in free space broken into its linear and angular parts.
Vector3  linear
Vector3  angular
```

`Vector3` 是一个三维向量，包含 `x`、`y`、`z` 三个字段。

#### 自定义消息类型

除了使用标准消息，我们也可以创建自定义消息（将在后续章节详细介绍）。

---

### 2.2 编写发布者节点（Publisher）

让我们创建一个实际的发布者节点，发布温度数据。

#### 步骤 1：创建新的功能包

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python \
  --dependencies rclpy std_msgs \
  topic_demo
```

#### 步骤 2：编写温度发布者

创建文件 `~/ros2_ws/src/topic_demo/topic_demo/temperature_publisher.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import random


class TemperaturePublisher(Node):
    def __init__(self):
        super().__init__('temperature_publisher')

        # 创建发布者，话题名为 'temperature'，队列大小为 10
        self.publisher = self.create_publisher(Float32, 'temperature', 10)

        # 创建定时器，每 1 秒调用一次回调函数
        timer_period = 1.0  # 单位：秒
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info('温度发布者已启动')
        self.temperature = 25.0  # 初始温度

    def timer_callback(self):
        # 创建消息对象
        msg = Float32()

        # 模拟温度变化（±1度随机波动）
        self.temperature += random.uniform(-1.0, 1.0)

        # 限制温度范围
        self.temperature = max(20.0, min(30.0, self.temperature))

        # 设置消息数据
        msg.data = self.temperature

        # 发布消息
        self.publisher.publish(msg)

        # 打印日志
        self.get_logger().info(f'发布温度: {msg.data:.2f}°C')


def main(args=None):
    rclpy.init(args=args)
    temperature_publisher = TemperaturePublisher()

    try:
        rclpy.spin(temperature_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        temperature_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 关键代码解析

**1. 创建发布者**：
```python
self.publisher = self.create_publisher(Float32, 'temperature', 10)
```
- `Float32`：消息类型
- `'temperature'`：话题名称
- `10`：队列大小（QoS 参数，后面详细介绍）

**2. 创建定时器**：
```python
self.timer = self.create_timer(timer_period, self.timer_callback)
```
定时器会定期调用回调函数，无需手动循环。

**3. 发布消息**：
```python
msg = Float32()           # 创建消息对象
msg.data = self.temperature  # 设置数据
self.publisher.publish(msg)  # 发布消息
```

#### 步骤 3：配置 setup.py

编辑 `~/ros2_ws/src/topic_demo/setup.py`，添加入口点：

```python
entry_points={
    'console_scripts': [
        'temperature_publisher = topic_demo.temperature_publisher:main',
    ],
},
```

---

### 2.3 编写订阅者节点（Subscriber）

现在创建一个订阅者来接收温度数据。

创建文件 `~/ros2_ws/src/topic_demo/topic_demo/temperature_subscriber.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class TemperatureSubscriber(Node):
    def __init__(self):
        super().__init__('temperature_subscriber')

        # 创建订阅者
        # 话题名: 'temperature'
        # 消息类型: Float32
        # 回调函数: self.temperature_callback
        # 队列大小: 10
        self.subscription = self.create_subscription(
            Float32,
            'temperature',
            self.temperature_callback,
            10
        )

        # 防止订阅者被 Python 垃圾回收
        self.subscription  # 避免未使用变量警告

        self.get_logger().info('温度订阅者已启动')

        # 用于计算平均值
        self.temperatures = []
        self.max_history = 5

    def temperature_callback(self, msg):
        # 当接收到消息时，此函数被自动调用
        temperature = msg.data

        # 记录温度
        self.temperatures.append(temperature)
        if len(self.temperatures) > self.max_history:
            self.temperatures.pop(0)

        # 计算平均值
        avg_temp = sum(self.temperatures) / len(self.temperatures)

        # 打印信息
        self.get_logger().info(
            f'当前温度: {temperature:.2f}°C, '
            f'最近 {len(self.temperatures)} 次平均: {avg_temp:.2f}°C'
        )

        # 温度警告
        if temperature > 28.0:
            self.get_logger().warn(f'⚠️ 温度过高: {temperature:.2f}°C')
        elif temperature < 22.0:
            self.get_logger().warn(f'⚠️ 温度过低: {temperature:.2f}°C')


def main(args=None):
    rclpy.init(args=args)
    temperature_subscriber = TemperatureSubscriber()

    try:
        rclpy.spin(temperature_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        temperature_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 关键代码解析

**1. 创建订阅者**：
```python
self.subscription = self.create_subscription(
    Float32,
    'temperature',
    self.temperature_callback,  # 消息到达时调用的函数
    10
)
```

**2. 回调函数**：
```python
def temperature_callback(self, msg):
    temperature = msg.data
    # 处理接收到的数据
```
当有消息到达时，ROS2 会自动调用这个回调函数。

**3. 防止垃圾回收**：
```python
self.subscription  # 避免未使用变量警告
```
这行代码确保订阅者对象不会被 Python 垃圾回收机制回收。

#### 配置 setup.py

编辑 `~/ros2_ws/src/topic_demo/setup.py`，添加订阅者入口：

```python
entry_points={
    'console_scripts': [
        'temperature_publisher = topic_demo.temperature_publisher:main',
        'temperature_subscriber = topic_demo.temperature_subscriber:main',
    ],
},
```

---

### 2.4 编译和运行

#### 编译工作空间

```bash
cd ~/ros2_ws
colcon build --packages-select topic_demo
```

#### Source 环境

打开新终端：
```bash
source ~/ros2_ws/install/setup.bash
```

#### 运行发布者

**终端 1**：
```bash
ros2 run topic_demo temperature_publisher
```

你应该看到：
```
[INFO] [temperature_publisher]: 温度发布者已启动
[INFO] [temperature_publisher]: 发布温度: 25.23°C
[INFO] [temperature_publisher]: 发布温度: 24.87°C
...
```

#### 运行订阅者

**终端 2**：
```bash
ros2 run topic_demo temperature_subscriber
```

你应该看到：
```
[INFO] [temperature_subscriber]: 温度订阅者已启动
[INFO] [temperature_subscriber]: 当前温度: 25.23°C, 近 1 次平均: 25.23°C
[INFO] [temperature_subscriber]: 当前温度: 24.87°C, 近 2 次平均: 25.05°C
...
```

#### 使用命令行工具验证

**终端 3**：

**查看话题列表**：
```bash
ros2 topic list
```
应该包含 `/temperature` 话题。

**查看话题详细信息**：
```bash
ros2 topic info /temperature
```
输出：
```
Type: std_msgs/msg/Float32
Publisher count: 1
Subscription count: 1
```

**实时监控话题数据**：
```bash
ros2 topic echo /temperature
```

**查看话题发布频率**：
```bash
ros2 topic hz /temperature
```

---

### 2.5 多个订阅者示例

话题支持一对多通信，多个订阅者可以同时订阅同一个话题。

创建第二个订阅者 `~/ros2_ws/src/topic_demo/topic_demo/temperature_logger.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from datetime import datetime


class TemperatureLogger(Node):
    def __init__(self):
        super().__init__('temperature_logger')

        self.subscription = self.create_subscription(
            Float32,
            'temperature',
            self.temperature_callback,
            10
        )

        self.subscription

        self.get_logger().info('温度日志记录器已启动')
        self.log_count = 0

    def temperature_callback(self, msg):
        self.log_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_msg = f"[{timestamp}] 温度记录 #{self.log_count}: {msg.data:.2f}°C"
        self.get_logger().info(log_msg)

        # 写入文件（实际应用中应该使用 ROS2 的日志系统）
        # with open('temperature_log.txt', 'a') as f:
        #     f.write(log_msg + '\n')


def main(args=None):
    rclpy.init(args=args)
    temperature_logger = TemperatureLogger()

    try:
        rclpy.spin(temperature_logger)
    except KeyboardInterrupt:
        pass
    finally:
        temperature_logger.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 配置和运行

添加到 `setup.py`：
```python
'temperature_logger = topic_demo.temperature_logger:main',
```

重新编译后，可以同时运行：
- 1 个发布者
- 2 个订阅者（`temperature_subscriber` 和 `temperature_logger`）

三个节点会同时工作，发布者发布的每条消息都会被两个订阅者接收到！

---

### 2.6 QoS（服务质量）配置详解

QoS（Quality of Service）是 ROS2 中非常重要的概念，用于控制通信的行为。

#### 什么是 QoS？

QoS 策略决定了：
- 消息如何传输
- 消息丢失时如何处理
- 订阅者何时能接收到消息

#### 默认 QoS 策略

当我们使用 `10` 作为队列大小时，实际上使用的是默认 QoS 配置：

```python
# 这两行代码是等价的
self.publisher = self.create_publisher(Float32, 'temperature', 10)
self.publisher = self.create_publisher(Float32, 'temperature', qos_profile=10)
```

#### 自定义 QoS 配置

```python
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy, QoSDurabilityPolicy

# 创建自定义 QoS 配置
qos_profile = QoSProfile(
    history=QoSHistoryPolicy.KEEP_LAST,    # 保留最后 N 条消息
    depth=10,                               # 队列大小
    reliability=QoSReliabilityPolicy.RELIABLE,  # 可靠传输（确保消息送达）
    durability=QoSDurabilityPolicy.VOLATILE     # 易失性（不保存历史消息）
)

self.publisher = self.create_publisher(Float32, 'temperature', qos_profile)
```

#### QoS 策略详解

##### 1. 历史策略（History Policy）

| 策略 | 说明 |
|------|------|
| `KEEP_LAST` | 只保留最后 N 条消息（N = depth） |
| `KEEP_ALL` | 保留所有消息（直到队列满） |

##### 2. 可靠性策略（Reliability Policy）

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `RELIABLE` | 确保消息可靠传输，丢失会重传 | 关键数据（命令、配置） |
| `BEST_EFFORT` | 尽力传输，不保证可靠性 | 高频数据（传感器、视频） |

##### 3. 持久性策略（Durability Policy）

| 策略 | 说明 |
|------|------|
| `VOLATILE` | 不保存历史消息，订阅者只能收到订阅后的消息 |
| `TRANSIENT_LOCAL` | 保存最后一条消息，新订阅者会立即收到 |

#### 实战示例：配置不同 QoS 策略

**场景 1：高速传感器数据（使用 BEST_EFFORT）**

```python
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

qos_profile = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT
)

self.publisher = self.create_publisher(Float32, 'sensor_data', qos_profile)
```

**场景 2：配置参数（使用 TRANSIENT_LOCAL）**

```python
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

qos_profile = QoSProfile(
    depth=1,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
)

self.publisher = self.create_publisher(String, 'config', qos_profile)
```

新订阅者订阅后会立即收到最后一条配置消息。

**场景 3：完整配置示例**

```python
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy, QoSDurabilityPolicy

qos_profile = QoSProfile(
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=5,
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.VOLATILE
)

self.publisher = self.create_publisher(Float32, 'temperature', qos_profile)
self.subscription = self.create_subscription(
    Float32,
    'temperature',
    self.callback,
    qos_profile
)
```

#### QoS 策略匹配规则

**重要**：发布者和订阅者的 QoS 策略必须兼容才能通信！

| 发布者 | 订阅者 | 能否通信 |
|--------|--------|----------|
| RELIABLE | RELIABLE | ✅ |
| RELIABLE | BEST_EFFORT | ✅ |
| BEST_EFFORT | RELIABLE | ❌（不兼容） |
| BEST_EFFORT | BEST_EFFORT | ✅ |
| VOLATILE | VOLATILE | ✅ |
| VOLATILE | TRANSIENT_LOCAL | ✅ |
| TRANSIENT_LOCAL | VOLATILE | ❌（不兼容） |

**口诀**：订阅者的要求不能比发布者高。

---

### 2.7 进阶示例：文本聊天系统

让我们创建一个简单的文本聊天系统，演示多个节点之间的通信。

#### 聊天消息发布者

创建 `~/ros2_ws/src/topic_demo/topic_demo/chat_publisher.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys


class ChatPublisher(Node):
    def __init__(self, username):
        super().__init__(f'{username}_chat_publisher')
        self.username = username

        self.publisher = self.create_publisher(String, 'chat_room', 10)

        self.get_logger().info(f'{username} 已加入聊天室')
        self.get_logger().info('输入消息（Ctrl+C 退出）:')

    def send_message(self, message):
        msg = String()
        msg.data = f'[{self.username}]: {message}'
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    # 获取用户名参数
    username = 'User'
    if len(sys.argv) > 1:
        username = sys.argv[1]

    chat_publisher = ChatPublisher(username)

    try:
        while True:
            message = input()
            if message.strip():
                chat_publisher.send_message(message)
    except KeyboardInterrupt:
        pass
    finally:
        chat_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 聊天消息订阅者

创建 `~/ros2_ws/src/topic_demo/topic_demo/chat_subscriber.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ChatSubscriber(Node):
    def __init__(self):
        super().__init__('chat_subscriber')

        self.subscription = self.create_subscription(
            String,
            'chat_room',
            self.chat_callback,
            10
        )

        self.subscription

        self.get_logger().info('聊天室监听器已启动')

    def chat_callback(self, msg):
        # 使用 print 而不是 logger，避免日志前缀
        print(f'\n{msg.data}')


def main(args=None):
    rclpy.init(args=args)
    chat_subscriber = ChatSubscriber()

    try:
        rclpy.spin(chat_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        chat_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 配置 setup.py

```python
entry_points={
    'console_scripts': [
        'temperature_publisher = topic_demo.temperature_publisher:main',
        'temperature_subscriber = topic_demo.temperature_subscriber:main',
        'temperature_logger = topic_demo.temperature_logger:main',
        'chat_publisher = topic_demo.chat_publisher:main',
        'chat_subscriber = topic_demo.chat_subscriber:main',
    ],
},
```

#### 测试聊天系统

**终端 1** - 运行订阅者（监听所有消息）：
```bash
source ~/ros2_ws/install/setup.bash
ros2 run topic_demo chat_subscriber
```

**终端 2** - 运行第一个发布者：
```bash
source ~/ros2_ws/install/setup.bash
ros2 run topic_demo chat_publisher Alice
```

**终端 3** - 运行第二个发布者：
```bash
source ~/ros2_ws/install/setup.bash
ros2 run topic_demo chat_publisher Bob
```

现在你可以在终端 2 和 3 中输入消息，所有消息都会显示在终端 1 中！

---

### 2.8 发布者和订阅者最佳实践

#### 1. 使用有意义的话题名称

```python
# ❌ 坏的命名
self.publisher = self.create_publisher(Float32, 'data1', 10)

# ✅ 好的命名
self.publisher = self.create_publisher(Float32, 'sensor/temperature', 10)
self.publisher = self.create_publisher(Float32, '/robot/sensor/temperature', 10)  # 绝对路径
```

#### 2. 选择合适的队列大小

```python
# 高频传感器数据（100Hz+）
self.publisher = self.create_publisher(Float32, 'imu_data', 100)

# 低频控制命令（1-10Hz）
self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

# 配置参数（很少变化）
self.publisher = self.create_publisher(String, 'config', 1)
```

#### 3. 及时处理消息

订阅者的回调函数应该尽快执行完毕，避免阻塞：

```python
# ❌ 避免在回调中做耗时操作
def bad_callback(self, msg):
    result = self.heavy_computation(msg.data)  # 耗时操作
    self.publisher.publish(result)

# ✅ 使用异步或线程
def good_callback(self, msg):
    self.get_logger().info('收到消息')
    self.last_msg = msg.data
    self.need_processing = True

def timer_callback(self):
    if self.need_processing:
        result = self.heavy_computation(self.last_msg)
        self.publisher.publish(result)
        self.need_processing = False
```

#### 4. 使用消息过滤

```python
def temperature_callback(self, msg):
    # 只处理有意义的数据
    if msg.data < 0 or msg.data > 100:
        self.get_logger().warn(f'无效温度值: {msg.data}')
        return

    # 正常处理
    self.process_temperature(msg.data)
```

---

## ✅ 总结

### 核心知识点回顾

| 概念 | 说明 | 关键代码 |
|------|------|----------|
| **发布者** | 向话题发送数据 | `create_publisher(type, topic, qos)` |
| **订阅者** | 从话题接收数据 | `create_subscription(type, topic, callback, qos)` |
| **消息类型** | 定义数据格式 | `std_msgs/msg/Float32`, `geometry_msgs/msg/Twist` |
| **回调函数** | 处理接收到的消息 | `def callback(self, msg):` |
| **QoS** | 控制通信质量 | `QoSProfile(history, reliability, durability)` |

### 代码模板速查

#### 发布者模板

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class MyPublisher(Node):
    def __init__(self):
        super().__init__('my_publisher')
        self.publisher = self.create_publisher(Float32, 'my_topic', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        msg = Float32()
        msg.data = 1.0
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = MyPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

#### 订阅者模板

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class MySubscriber(Node):
    def __init__(self):
        super().__init__('my_subscriber')
        self.subscription = self.create_subscription(
            Float32, 'my_topic', self.callback, 10
        )

    def callback(self, msg):
        self.get_logger().info(f'收到: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = MySubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### QoS 策略选择指南

| 场景 | History | Reliability | Durability |
|------|---------|-------------|------------|
| 高频传感器 | KEEP_LAST | BEST_EFFORT | VOLATILE |
| 控制命令 | KEEP_LAST | RELIABLE | VOLATILE |
| 配置参数 | KEEP_LAST | RELIABLE | TRANSIENT_LOCAL |
| 日志数据 | KEEP_ALL | BEST_EFFORT | VOLATILE |

### 下一步学习方向

- 📘 [06 - 服务与动作通信（Service / Action）](06_services_and_actions.md)
- 📘 [07 - 参数服务器与动态参数管理](07_parameters_and_config.md)
- 📘 [08 - ROS2 Launch 文件](08_ros2_launch.md)

---

📘 下一章：[06 - 服务与动作通信（Service / Action）](06_services_and_actions.md)
