# ⚗️【ROS2 入门系列 #7】参数服务器与动态参数管理（Parameter YAML 配置）

> 作者：whatqiu
> 更新时间：2026-09-30
> 环境：Ubuntu 22.04 + ROS2 Humble（Jazzy 差异见文末对照）

---

## 🧭 前言

回头看前几章的代码，你会发现到处都是写死的数字：

```python
timer_period = 1.0                    # 1 秒发一次
self.temperature = 25.0               # 初始温度写死
```

这些「魔法数字」带来三个问题：

1. **改一次要重编译**——调个周期从 1.0 到 0.5，得重新 `colcon build`
2. **同一份代码没法多场景复用**——仿真用一套参数，真机用另一套，只能改代码
3. **运行时没法调**——PID 参数想现场微调，做不到

**参数（Parameter）就是解决这个问题的**。它让节点的配置从代码里剥离出来，变成可以在启动时传入、运行中修改的外部输入。

更重要的是——**参数是 Launch 文件的核心用途之一**（第 08 章），两者配合才能实现「一套代码，多场景部署」。

本章目标：

- 理解 ROS2 参数的存储机制（**重要：不是 ROS1 那样的全局服务器**）
- 掌握参数声明、读取、修改的完整 API
- 会用 YAML 文件组织参数
- 会写参数回调，实现运行中动态响应
- 知道参数在什么场景下会「改了不生效」

**预计学习时间**：50-65 分钟

**前置章节**：

- [03 - 创建第一个 ROS2 工作空间与 Python 节点](03_first_workspace_and_node.md)
- [04 - ROS2 常用命令行工具与调试技巧](04_ros2_cli_tools.md)
- [06 - 服务与动作机制](06_services_and_actions.md)

---

## 🧱 一、主要内容

### 1.1 一个必须先纠正的认知

**ROS2 没有全局参数服务器。**

这是从 ROS1 转过来的开发者最容易搞错的地方。对比一下：

| 项目 | ROS1 | ROS2 |
| ---------- | ------------------- | ------------------ |
| 存储位置 | 集中式 Parameter Server | **每个节点自己持有** |
| 访问方式 | 全局查询 | 只能访问自己的参数 |
| 节点关系 | 参数独立于节点存在 | **参数属于节点**，节点销毁参数就没了 |
| 修改方式 | `rosparam set` 全局生效 | `ros2 param set` 只改那个节点 |

**关键推论**：你不能「给别的节点设参数」，每个节点的参数由它自己声明和管理。所谓「传参」，实际上是**启动时把参数交给节点**。

### 1.2 参数的三个核心 API

在 ROS2 里，参数的使用严格遵循三步：

```text
① declare_parameter()  声明参数（含默认值和类型）
        ↓
② get_parameter()      读取参数值
        ↓
③ add_on_set_parameters_callback()   注册修改回调（可选）
```

**为什么必须先声明？**

这是 ROS2 的设计哲学：**节点必须显式声明自己接受哪些参数**。

好处是：参数名写错了、类型给错了、给了不存在的参数，都会**立刻报错**，而不是静默失败。这比 ROS1 的宽松模式安全得多。

**不声明就用会怎样？**

```python
# 没声明就 get
value = self.get_parameter('my_param').value
# 报错：Parameter 'my_param' not declared
```

```bash
# 启动时传入未声明的参数
ros2 run pkg node --ros-args -p undeclared:=100
# 报错：Parameter 'undeclared' is not declared
```

甚至想在运行时修改未声明的参数，也会被拒绝。**声明是第一道门。**

### 1.3 参数的数据类型

ROS2 参数支持 5 种类型（Python 侧）：

| 类型 | Python 类型 | 示例 | YAML 写法 |
| ------ | ------------- | ------------------ | ------------- |
| 布尔 | `bool` | `True` | `true` |
| 整数 | `int` | `42` | `42` |
| 浮点 | `float` | `3.14` | `3.14` |
| 字符串 | `str` | `"hello"` | `"hello"` |
| 数组 | `list` | `[1, 2, 3]` | `[1, 2, 3]` |

**注意类型陷阱**：

```python
self.declare_parameter('rate', 1.0)   # 默认值是 float
```

```bash
# 传参时如果写 -p rate:=1，类型可能被推断成 int → 类型冲突报错
```

**解决方案**：传参时显式写类型：

```bash
ros2 run my_pkg my_node --ros-args -p rate:=1.0    # 浮点，明确带小数点
ros2 run my_pkg my_node --ros-args -p count:=1     # 整数
ros2 run my_pkg my_node --ros-args -p name:="abc"  # 字符串，加引号
```

### 1.4 参数与命名空间

参数名支持命名空间前缀，这在多机器人场景很重要：

```python
self.declare_parameter('max_speed', 1.0)                  # 相对名
self.declare_parameter('robot1.max_speed', 1.0)           # 带前缀
```

节点启动时如果有命名空间，相对参数名会自动加前缀：

```bash
ros2 run my_pkg my_node --ros-args -r __ns:=/robot1
# 'max_speed' 实际变成 '/robot1/max_speed'
```

**这个机制有个坑**：一旦有了 `__ns`，YAML 文件里的参数名**必须带完整前缀**，否则对不上。后面第 2.5 节会专门演示。

---

## 🧩 二、示例与讲解

### 2.1 命令行体验：先看看别人怎么用

在写代码前，用 turtlesim 感受一下参数的完整生命周期。

#### 步骤 1：启动海龟并列出参数

```bash
# 终端 1
ros2 run turtlesim turtlesim_node
```

```bash
# 终端 2
ros2 param list
```

输出：

```text
/turtlesim:
  background_b
  background_g
  background_r
  qos_overrides./parameter_events.publisher.depth
  qos_overrides./parameter_events.publisher.durability
  use_sim_time
```

注意 `qos_overrides.*` 这些是 ROS2 **自动添加**的，不是用户声明的。任何节点都会自动带上这些参数。

#### 步骤 2：读取参数

```bash
ros2 param get /turtlesim background_r
```

输出：

```text
Integer value is: 69
```

注意返回的措辞是 `Integer value is:`——参数 API 返回的是**带类型标记的对象**，不只是裸值。

#### 步骤 3：修改参数

```bash
ros2 param set /turtlesim background_r 200
```

输出：

```text
Set parameter successful
```

但你会发现**海龟的背景色没变**。这是个特别好的教学案例：

**参数改了，但节点业务逻辑没响应**——因为 turtlesim 没有为 `background_r` 注册修改回调，参数值变了，但没人去用这个新值重绘背景。

> 这就是「**参数修改不等于业务响应**」。想让参数真正生效，必须在代码里注册回调。2.4 节会教你写。

#### 步骤 4：导出参数快照

```bash
ros2 param dump /turtlesim
```

输出：

```yaml
/turtlesim:
  ros__parameters:
    background_b: 255
    background_g: 86
    background_r: 200
    use_sim_time: false
```

**这个输出的格式非常重要**——它就是 YAML 参数文件的标准格式：

- 顶层是**节点名**
- 第二层必须是 `ros__parameters`（**两个下划线**，写成一个会静默失效）
- 然后才是参数键值对

直接保存成文件就能用：

```bash
ros2 param dump /turtlesim > turtle_params.yaml
```

#### 步骤 5：从文件加载参数

重启 turtlesim，这次带参数文件：

```bash
# 先 Ctrl+C 停掉原来的
ros2 run turtlesim turtlesim_node --ros-args --params-file turtle_params.yaml
```

背景色这次**直接就是蓝色**（因为启动时就传入了）。

**对比出结论**：

- 启动时传入参数 → 影响节点初始化行为 ✅
- 运行中修改参数 → 只有注册了回调才有响应 ⚠️

---

### 2.2 编写带参数的节点

现在自己写。做一个「可配置的数据发布器」：周期、话题名、初始值都通过参数控制。

#### 步骤 1：创建功能包

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python \
  --dependencies rclpy std_msgs \
  param_demo
```

#### 步骤 2：编写参数化节点

创建 `~/ros2_ws/src/param_demo/param_demo/configurable_publisher.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

# 定义默认值常量，便于维护
DEFAULT_TOPIC_NAME = 'sensor_value'
DEFAULT_PUBLISH_RATE = 1.0
DEFAULT_INITIAL_VALUE = 25.0
DEFAULT_DRIFT_STEP = 0.5


class ConfigurablePublisher(Node):
    def __init__(self):
        super().__init__('configurable_publisher')

        # ========== 第一步：声明所有参数 ==========
        # 声明时必须给默认值，ROS2 会据此推断类型
        self.declare_parameter('topic_name', DEFAULT_TOPIC_NAME)
        self.declare_parameter('publish_rate', DEFAULT_PUBLISH_RATE)
        self.declare_parameter('initial_value', DEFAULT_INITIAL_VALUE)
        self.declare_parameter('drift_step', DEFAULT_DRIFT_STEP)
        self.declare_parameter('enable_drift', True)

        # ========== 第二步：读取参数值 ==========
        topic_name = self.get_parameter('topic_name').value
        publish_rate = self.get_parameter('publish_rate').value
        self.current_value = self.get_parameter('initial_value').value
        self.drift_step = self.get_parameter('drift_step').value
        self.enable_drift = self.get_parameter('enable_drift').value

        # ========== 第三步：用参数初始化业务 ==========
        self.publisher = self.create_publisher(Float32, topic_name, 10)

        timer_period = 1.0 / publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(
            f'节点已启动 | 话题={topic_name} | 频率={publish_rate}Hz '
            f'| 初值={self.current_value} | 漂移={self.enable_drift}'
        )

    def timer_callback(self):
        msg = Float32()

        if self.enable_drift:
            self.current_value += self.drift_step

        msg.data = self.current_value
        self.publisher.publish(msg)

        self.get_logger().info(f'发布: {msg.data:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = ConfigurablePublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**关键代码解析**：

**1. 声明参数**

```python
self.declare_parameter('topic_name', DEFAULT_TOPIC_NAME)
```

- 第一个参数是名字
- 第二个是默认值，**ROS2 用它的类型推断参数类型**
- 也可以显式指定类型：

```python
from rclpy.parameter import Parameter
self.declare_parameter('count', 10, Parameter.Type.INTEGER)
```

**2. 读取参数**

```python
value = self.get_parameter('topic_name').value
```

**注意那个 `.value`**——`get_parameter` 返回的是 `Parameter` 对象，不是裸值。忘了 `.value` 会得到 `<rclpy.parameter.Parameter object>`，非常常见的新手错误。

**3. 注册 entry_point**

编辑 `setup.py`：

```python
entry_points={
    'console_scripts': [
        'configurable_publisher = '
        'param_demo.configurable_publisher:main',
    ],
},
```

#### 步骤 3：编译并测试默认值

```bash
cd ~/ros2_ws
colcon build --packages-select param_demo
source install/setup.bash
```

```bash
ros2 run param_demo configurable_publisher
```

输出：

```text
[INFO] [configurable_publisher]: 节点已启动 | 话题=sensor_value | 频率=1.0Hz | 初值=25.0 | 漂移=True
[INFO] [configurable_publisher]: 发布: 25.50
[INFO] [configurable_publisher]: 发布: 26.00
```

#### 步骤 4：通过命令行覆盖参数

```bash
ros2 run param_demo configurable_publisher --ros-args \
  -p topic_name:="my_sensor" \
  -p publish_rate:=5.0 \
  -p initial_value:=100.0 \
  -p drift_step:=2.0 \
  -p enable_drift:=false
```

输出：

```text
[INFO] [configurable_publisher]: 节点已启动 | 话题=my_sensor | 频率=5.0Hz | 初值=100.0 | 漂移=False
[INFO] [configurable_publisher]: 发布: 100.00
[INFO] [configurable_publisher]: 发布: 100.00
```

**同一份代码，完全不同的行为**——这就是参数的价值。注意 `--ros-args` 后面才跟 `-p`，写错顺序会报错。

用另一个终端验证话题名确实变了：

```bash
ros2 topic list | grep sensor
```

输出：

```text
/my_sensor
```

---

### 2.3 YAML 参数文件

命令行传参适合调试，但参数多了就难管。真实项目用 YAML 文件。

#### 步骤 1：编写 YAML 文件

创建 `~/ros2_ws/src/param_demo/config/params.yaml`：

```yaml
/configurable_publisher:
  ros__parameters:
    topic_name: "sensor_from_yaml"
    publish_rate: 2.0
    initial_value: 50.0
    drift_step: 1.5
    enable_drift: true
```

**三个必须记住的规则**：

1. **顶层是节点名**，要注意这里的节点名是 `configurable_publisher`（与代码里 `super().__init__()` 的名字一致），而不是包名
2. **第二层必须是 `ros__parameters`**，中间是**两个下划线**，写成 `ros_parameters`（一个下划线）**不会报错，但参数全都不生效**——最难查的坑之一
3. **YAML 对缩进敏感**，用空格不用 Tab

#### 步骤 2：更新 setup.py 安装 config 目录

config 文件不会被自动打包，必须手动声明：

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
        # 关键：把 config 下的 yaml 安装到 share/param_demo/config/
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='whatqiu',
    maintainer_email='whatqiu@example.com',
    description='ROS2 参数示例',
    license='MIT',
    entry_points={
        'console_scripts': [
            'configurable_publisher = '
            'param_demo.configurable_publisher:main',
        ],
    },
)
```

**漏掉 `data_files` 会怎样？** 编译成功，但运行时报 `file not found`——因为 YAML 根本没被安装到 `share/` 目录。这是新手高频错误。

#### 步骤 3：编译测试

```bash
cd ~/ros2_ws
colcon build --packages-select param_demo
source install/setup.bash

# 确认文件真的被安装了
ls install/param_demo/share/param_demo/config/
```

输出：

```text
params.yaml
```

运行：

```bash
ros2 run param_demo configurable_publisher --ros-args \
  --params-file install/param_demo/share/param_demo/config/params.yaml
```

输出：

```text
[INFO] [configurable_publisher]: 节点已启动 | 话题=sensor_from_yaml | 频率=2.0Hz | 初值=50.0 | 漂移=True
```

**更优雅的写法**：用包查找方式，不依赖当前工作目录。

```bash
ros2 run param_demo configurable_publisher --ros-args \
  --params-file $(ros2 pkg prefix param_demo)/share/param_demo/config/params.yaml
```

`ros2 pkg prefix` 会自动找到包的安装路径。

#### 步骤 4：多组参数配置

真实项目往往需要「仿真一套、真机一套」。建两个文件：

`config/sim_params.yaml`：

```yaml
/configurable_publisher:
  ros__parameters:
    topic_name: "sim_sensor"
    publish_rate: 10.0
    initial_value: 0.0
    drift_step: 0.1
```

`config/real_params.yaml`：

```yaml
/configurable_publisher:
  ros__parameters:
    topic_name: "real_sensor"
    publish_rate: 1.0
    initial_value: 25.0
    drift_step: 0.5
```

切换场景只需换文件，**代码一行不改**：

```bash
# 仿真模式
ros2 run param_demo configurable_publisher --ros-args \
  --params-file install/param_demo/share/param_demo/config/sim_params.yaml

# 真机模式
ros2 run param_demo configurable_publisher --ros-args \
  --params-file install/param_demo/share/param_demo/config/real_params.yaml
```

> **这就是参数系统的核心价值**。第 08 章的 Launch 文件会让它更强大——一个 `ros2 launch` 命令切换整套配置。

---

### 2.4 动态参数回调（重点）

前面 turtlesim 的例子说明了：**改参数不等于生效**。要让参数修改真正起作用，需要注册回调。

#### 步骤 1：编写带回调的节点

创建 `~/ros2_ws/src/param_demo/param_demo/dynamic_tuner.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Float32


class DynamicTuner(Node):
    def __init__(self):
        super().__init__('dynamic_tuner')

        # 声明参数
        self.declare_parameter('publish_rate', 1.0)
        self.declare_parameter('amplitude', 10.0)
        self.declare_parameter('offset', 0.0)

        # 读取初始值
        self.publish_rate = self.get_parameter('publish_rate').value
        self.amplitude = self.get_parameter('amplitude').value
        self.offset = self.get_parameter('offset').value

        # 发布器
        self.publisher = self.create_publisher(Float32, 'tuned_value', 10)

        # 定时器
        self.timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        # ========== 关键：注册参数修改回调 ==========
        self.add_on_set_parameters_callback(self.parameters_callback)

        self.get_logger().info(
            f'已启动 | rate={self.publish_rate} amplitude={self.amplitude} '
            f'offset={self.offset}'
        )

    def parameters_callback(self, params):
        """参数修改回调

        参数：
            params: 一个 Parameter 对象的列表（一次可能改多个）

        返回：
            SetParametersResult(successful=True/False, reason="...")
            - 返回 successful=False 会拒绝本次修改
            - 只要有一个参数被拒绝，整批修改都会被回滚
        """
        for param in params:
            if param.name == 'publish_rate':
                # 校验：频率必须为正
                if param.value <= 0:
                    self.get_logger().warn(
                        f'publish_rate 必须 > 0，拒绝修改（收到 {param.value}）'
                    )
                    return SetParametersResult(
                        successful=False,
                        reason='publish_rate must be positive'
                    )

                self.publish_rate = param.value

                # 重建定时器以应用新频率
                self.destroy_timer(self.timer)
                self.timer_period = 1.0 / self.publish_rate
                self.timer = self.create_timer(
                    self.timer_period, self.timer_callback
                )

                self.get_logger().info(f'频率已更新为 {self.publish_rate} Hz')

            elif param.name == 'amplitude':
                self.amplitude = param.value
                self.get_logger().info(f'幅值已更新为 {self.amplitude}')

            elif param.name == 'offset':
                self.offset = param.value
                self.get_logger().info(f'偏置已更新为 {self.offset}')

        # 全部校验通过
        return SetParametersResult(successful=True)

    def timer_callback(self):
        msg = Float32()
        msg.data = self.amplitude + self.offset
        self.publisher.publish(msg)
        self.get_logger().info(
            f'发布: {msg.data:.2f} (rate={self.publish_rate})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = DynamicTuner()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**回调机制的关键点**：

**1. 回调是「批量」的**

```python
def parameters_callback(self, params):
    for param in params:
        ...
```

`params` 是**列表**，因为一次 `ros2 param set` 可能改多个参数（或通过 YAML 加载时一次改很多）。

**2. 返回值必须显式构造**

```python
return SetParametersResult(successful=True)
```

**不返回会怎样？** 回调返回 `None`，ROS2 会认为校验失败，**参数修改被静默拒绝**。这是最容易忽略的坑之一——你会看到 `ros2 param set` 报 `Setting parameter failed`，但日志里什么都没有。

**3. 拒绝修改要给出原因**

```python
return SetParametersResult(successful=False, reason='...')
```

`reason` 会返回给调用方，便于排查。

**4. 改定时器频率必须重建**

```python
self.destroy_timer(self.timer)
self.timer = self.create_timer(self.timer_period, self.timer_callback)
```

ROS2 的定时器**创建后不能改周期**，只能销毁重建。这一点比想象中容易忘。

#### 步骤 2：注册并测试

在 `setup.py` 的 `entry_points` 加上：

```python
'dynamic_tuner = param_demo.dynamic_tuner:main',
```

```bash
cd ~/ros2_ws
colcon build --packages-select param_demo
source install/setup.bash
```

**终端 1** 启动节点：

```bash
ros2 run param_demo dynamic_tuner
```

输出：

```text
[INFO] [dynamic_tuner]: 已启动 | rate=1.0 amplitude=10.0 offset=0.0
[INFO] [dynamic_tuner]: 发布: 10.00 (rate=1.0)
```

**终端 2** 动态改参数：

```bash
# 改幅值
ros2 param set /dynamic_tuner amplitude 99.0
```

终端 1 立刻响应：

```text
[INFO] [dynamic_tuner]: 幅值已更新为 99.0
[INFO] [dynamic_tuner]: 发布: 99.00 (rate=1.0)
```

**改频率（观察速度变化）**：

```bash
ros2 param set /dynamic_tuner publish_rate 5.0
```

终端 1：

```text
[INFO] [dynamic_tuner]: 频率已更新为 5.0 Hz
```

发布速度明显加快 → **定时器重建成功**。

**测试拒绝逻辑**：

```bash
ros2 param set /dynamic_tuner publish_rate -1.0
```

终端 2 输出：

```text
Setting parameter failed: publish_rate must be positive
```

终端 1：

```text
[WARN] [dynamic_tuner]: publish_rate 必须 > 0，拒绝修改（收到 -1.0）
```

**校验生效了**。这就是「参数守卫」的价值——防止误操作把系统搞挂。

---

### 2.5 命名空间与参数的配合（易错点）

前面提到过，一旦用了 `__ns`，YAML 里参数名要带前缀。这里完整演示。

#### 步骤 1：直接启动，带命名空间

```bash
ros2 run param_demo configurable_publisher --ros-args \
  -r __ns:=/robot1 \
  -p topic_name:="sensor"
```

查看话题：

```bash
ros2 topic list | grep sensor
```

输出：

```text
/robot1/sensor
```

**注意**：话题名自动加了 `/robot1` 前缀。这是 ROS2 的命名空间机制——**相对名称自动加前缀**。

#### 步骤 2：YAML 文件要怎么写？

如果要用 YAML 给带命名空间的节点传参，文件必须写成：

```yaml
/robot1/configurable_publisher:
  ros__parameters:
    topic_name: "sensor"
    publish_rate: 2.0
```

**关键**：节点名前带 `/robot1` 前缀。

如果写成不带前缀的：

```yaml
configurable_publisher:     # 加不了前缀，参数传不进去
  ros__parameters:
    topic_name: "sensor"
```

参数会**静默失效**——不报错，但用的是默认值。这类问题排查起来很痛苦，因为看不出任何异常。

#### 步骤 3：通配符写法

多机器人场景可以用通配符：

```yaml
/**:
  ros__parameters:
    publish_rate: 10.0          # 所有节点共享这个默认值

/robot1/**:
  ros__parameters:
    topic_name: "robot1_sensor" # 只作用于 robot1 下的节点
```

`/**` 匹配任意层级的节点名，适合设置全局默认值。

---

### 2.6 参数的三个时间点

这是本章最需要建立的时间感。参数在不同时机传入，效果完全不同：

| 时机 | 方式 | 效果 |
| ---------- | -------------------------------- | ------------------------- |
| **启动前** | 命令行 `-p` / `--params-file` | 影响节点初始化，最完整 |
| **运行时** | `ros2 param set` | 仅当注册了回调才生效 |
| **代码中** | `declare_parameter` 的默认值 | 兜底，优先级最低 |

**优先级**（从高到低）：

```text
命令行 -p  >  --params-file  >  代码里的默认值
```

**为什么命令行优先级最高？** 因为它是「最后覆盖」。这个设计让你可以用命令行临时覆盖 YAML 配置，而不用改文件：

```bash
ros2 run param_demo configurable_publisher --ros-args \
  --params-file params.yaml \
  -p publish_rate:=20.0        # 覆盖 YAML 里的值
```

调试时特别好用。

---

### 2.7 实战案例：可配置的 PID 控制器

把学到的串起来。这是个真实场景：PID 参数经常需要现场调，绝不能写死在代码里。

#### 完整代码

创建 `~/ros2_ws/src/param_demo/param_demo/pid_controller.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Float32


class PIDController(Node):
    def __init__(self):
        super().__init__('pid_controller')

        # ---- 声明 PID 参数 ----
        self.declare_parameter('kp', 1.0)
        self.declare_parameter('ki', 0.0)
        self.declare_parameter('kd', 0.0)
        self.declare_parameter('output_limit', 100.0)
        self.declare_parameter('integral_limit', 50.0)

        # ---- 读取 ----
        self.kp = self.get_parameter('kp').value
        self.ki = self.get_parameter('ki').value
        self.kd = self.get_parameter('kd').value
        self.output_limit = self.get_parameter('output_limit').value
        self.integral_limit = self.get_parameter('integral_limit').value

        # ---- PID 内部状态 ----
        self.integral = 0.0
        self.prev_error = 0.0

        # ---- 设置点与当前值（由话题更新） ----
        self.setpoint = 0.0
        self.current = 0.0

        self.create_subscription(
            Float32, 'setpoint', self.setpoint_callback, 10)
        self.create_subscription(
            Float32, 'feedback', self.feedback_callback, 10)

        self.publisher = self.create_publisher(Float32, 'control_output', 10)

        # 100Hz 控制环
        self.timer = self.create_timer(0.01, self.control_loop)

        # 参数回调
        self.add_on_set_parameters_callback(self.parameters_callback)

        self.get_logger().info(
            f'PID 控制器已启动 | kp={self.kp} ki={self.ki} kd={self.kd}'
        )

    def setpoint_callback(self, msg):
        self.setpoint = msg.data

    def feedback_callback(self, msg):
        self.current = msg.data

    def parameters_callback(self, params):
        """PID 参数热更新，带合理性校验"""
        for param in params:
            if param.name == 'kp':
                if param.value < 0:
                    return SetParametersResult(
                        successful=False, reason='kp 不能为负')
                self.kp = param.value
                self.get_logger().info(f'kp 更新为 {self.kp}')

            elif param.name == 'ki':
                if param.value < 0:
                    return SetParametersResult(
                        successful=False, reason='ki 不能为负')
                self.ki = param.value
                self.get_logger().info(f'ki 更新为 {self.ki}')

            elif param.name == 'kd':
                if param.value < 0:
                    return SetParametersResult(
                        successful=False, reason='kd 不能为负')
                self.kd = param.value
                self.get_logger().info(f'kd 更新为 {self.kd}')

            elif param.name == 'output_limit':
                self.output_limit = param.value
                self.get_logger().info(
                    f'output_limit 更新为 {self.output_limit}')

        return SetParametersResult(successful=True)

    def control_loop(self):
        dt = 0.01

        error = self.setpoint - self.current

        # 积分项（带抗饱和）
        self.integral += error * dt
        self.integral = max(-self.integral_limit,
                            min(self.integral_limit, self.integral))

        # 微分项
        derivative = (error - self.prev_error) / dt
        self.prev_error = error

        # PID 输出
        output = (self.kp * error
                  + self.ki * self.integral
                  + self.kd * derivative)

        # 输出限幅
        output = max(-self.output_limit, min(self.output_limit, output))

        msg = Float32()
        msg.data = output
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PIDController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 配套 YAML

`config/pid_params.yaml`：

```yaml
/pid_controller:
  ros__parameters:
    kp: 2.5
    ki: 0.1
    kd: 0.05
    output_limit: 50.0
    integral_limit: 20.0
```

#### 运行与调参

```bash
colcon build --packages-select param_demo
source install/setup.bash

ros2 run param_demo pid_controller --ros-args \
  --params-file install/param_demo/share/param_demo/config/pid_params.yaml
```

**现场调参流程**：

```bash
# 观察当前控制效果后，动态调 kp
ros2 param set /pid_controller kp 5.0

# 看效果，继续调
ros2 param set /pid_controller ki 0.5

# 调完把最终值存下来
ros2 param dump /pid_controller > tuned_pid.yaml
```

**`param dump` 导出的文件可以直接作为下次的启动配置**——这个「调参 → 导出 → 固化」的闭环，是工程上非常实用的技巧。

---

### 2.8 常见错误速查

| 报错 / 现象 | 原因 | 解决 |
| ------------------------------------------------ | ------------------------ | ------------------------------ |
| `Parameter 'xxx' not declared` | 用了但没声明 | 先 `declare_parameter` |
| 启动时报 `is not declared` | 传了未声明的参数 | 声明它，或用 `automatically_declare` |
| 拿到 `<Parameter object>` 而不是值 | 忘了 `.value` | `get_parameter('x').value` |
| YAML 参数不生效，但没报错 | 第二层写成 `ros_parameters`（单下划线） | 必须是 `ros__parameters` |
| YAML 参数不生效 | 顶层节点名与代码里不一致 | 名字要完全匹配 |
| 加了 `__ns` 后 YAML 失效 | YAML 里节点名没带命名空间前缀 | 写成 `/ns/node_name` |
| 运行时 `ros2 param set` 成功但没反应 | 没注册回调 | 加 `add_on_set_parameters_callback` |
| `Setting parameter failed` 但无日志 | 回调没返回值 | 显式 return `SetParametersResult` |
| `file not found` 找不到 yaml | setup.py 没加 config 的 `data_files` | 补上 glob 安装规则 |
| 改了参数名后旧参数还能读到 | 旧参数缓存在 `install/` | 删除 `build/ install/` 重编 |
| 参数类型冲突 | 传参时类型推断不一致 | 显式写 `1.0` / `1` / `"str"` |

#### 深挖：「YAML 不生效但没报错」

这是最让人抓狂的一类问题。按这个顺序排查：

**① 检查第二层键名**

```yaml
/node_name:             # 顶层必须是节点名
  ros__parameters:      # 这里必须是两个下划线
    param: 1
```

用编辑器搜索确认，不要靠肉眼。

**② 检查节点名是否匹配**

```bash
# 先启动节点，看实际名字
ros2 node list
```

如果代码里是 `super().__init__('my_node')`，YAML 顶层就必须是 `my_node`。

**③ 检查是否有命名空间**

```bash
ros2 node list
```

如果输出是 `/robot1/my_node`，YAML 顶层必须写 `/robot1/my_node`。

**④ 验证参数是否真的传进去了**

```bash
ros2 param get /node_name param_name
```

如果返回默认值而非 YAML 里的值，说明没传进去。

**⑤ 检查文件是否真被安装**

```bash
ls install/<pkg>/share/<pkg>/config/
```

文件不在 → `setup.py` 的 `data_files` 写错了。

---

## 🔄 Humble 与 Jazzy 差异对照

| 项目 | Humble (22.04) | Jazzy (24.04) |
| ------------------- | ------------------ | ------------------ |
| Python 版本 | 3.10 | 3.12 |
| `declare_parameter` | 一致 | 一致 |
| `get_parameter` | 一致 | 一致 |
| 参数回调 API | `add_on_set_parameters_callback` | 一致 |
| `SetParametersResult` | `rcl_interfaces.msg` | 一致 |
| YAML 格式 | `ros__parameters` | 一致 |
| `ros2 param` CLI | 一致 | 一致 |

**结论**：参数机制在 Humble 与 Jazzy 之间**完全兼容**，代码可直接互用。

**一个小差异**：Jazzy 对参数类型检查更严格。在 Jazzy 上，`declare_parameter('rate', 1)` 后传入 `1.5` 会比 Humble 更早报类型错误。这其实是好事——早暴露问题。

---

## ✅ 总结

### 核心知识点回顾

| 概念 | 说明 | 关键代码 |
| ----------------------- | ------------------ | ---------------------------------------------- |
| **参数归属** | 每个节点自己持有，无全局服务器 | — |
| **声明** | 必须显式声明，否则报错 | `declare_parameter(name, default)` |
| **读取** | 返回 Parameter 对象 | `get_parameter(name).value` |
| **动态回调** | 修改时触发，可校验可拒绝 | `add_on_set_parameters_callback` |
| **YAML 结构** | 节点名 + `ros__parameters` | 两个下划线，不可错 |
| **优先级** | 命令行 > YAML > 代码默认值 | — |
| **命名空间** | 相对名自动加前缀 | `-r __ns:=/ns` |

### 代码模板速查

#### 基础参数节点模板

```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')

        # 声明
        self.declare_parameter('rate', 1.0)
        self.declare_parameter('name', 'default')

        # 读取（注意 .value）
        self.rate = self.get_parameter('rate').value
        self.name = self.get_parameter('name').value

        self.get_logger().info(f'rate={self.rate} name={self.name}')
```

#### 带校验的参数回调模板

```python
from rcl_interfaces.msg import SetParametersResult

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.declare_parameter('rate', 1.0)
        self.add_on_set_parameters_callback(self.parameters_callback)

    def parameters_callback(self, params):
        for param in params:
            if param.name == 'rate':
                if param.value <= 0:
                    return SetParametersResult(
                        successful=False,
                        reason='rate must be positive'
                    )
                self.rate = param.value

        return SetParametersResult(successful=True)  # 必须返回
```

#### YAML 文件模板

```yaml
/node_name:
  ros__parameters:
    rate: 1.0
    name: "hello"
    enable: true
    limits: [1.0, 2.0, 3.0]
```

#### 多机器人 YAML 模板

```yaml
/**:
  ros__parameters:
    common_rate: 10.0

/robot1/**:
  ros__parameters:
    wheel_radius: 0.05

/robot2/**:
  ros__parameters:
    wheel_radius: 0.06
```

### 参数调试命令速查

| 目的 | 命令 |
| -------------------------- | ------------------------------------ |
| 列出所有参数 | `ros2 param list` |
| 查看某节点参数 | `ros2 param list /node_name` |
| 读取单个参数 | `ros2 param get /node param` |
| 修改参数 | `ros2 param set /node param value` |
| 导出参数 | `ros2 param dump /node` |
| 导出到文件 | `ros2 param dump /node > p.yaml` |
| 启动时加载 | `--ros-args --params-file p.yaml` |
| 启动时覆盖 | `--ros-args -p param:=value` |
| 查找包路径 | `ros2 pkg prefix pkg_name` |

### 参数 vs 其他配置方式

| 方式 | 改后是否需重编译 | 能否运行时修改 | 适用场景 |
| -------------- | ------- | ------------ | ------------------ |
| 代码硬编码 | 需要 | 不能 | 常量（如 π） |
| **参数** | **不需要** | **能** | **可调配置、多场景部署** |
| 环境变量 | 不需要 | 不能 | 路径、密钥 |
| 配置文件直接读 | 不需要 | 不能 | 复杂结构化配置 |

### 下一步学习方向

参数学会了，但「启动时加载 YAML」目前还得手打一长串 `--ros-args`。下一章的 **Launch 文件**会把它变成一条命令。

- 📘 [08 - ROS2 Launch 文件](08_ros2_launch.md)
- 📘 [09 - colcon 构建系统与依赖管理详解](09_colcon_build.md)
- 📘 [19 - ROS2 常见错误与踩坑记录](19_ros2_debug_notes.md)

---

📘 下一章：[08 - ROS2 Launch 文件](08_ros2_launch.md)
