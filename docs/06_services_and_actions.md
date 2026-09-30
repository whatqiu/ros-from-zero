# 🔧【ROS2 入门系列 #6】服务与动作机制（Service / Client / Action）

> 作者：whatqiu
> 更新时间：2026-09-30
> 环境：Ubuntu 22.04 + ROS2 Humble（Jazzy 差异见文末对照）

---

## 🧭 前言

在前面几章里，我们用一个「话题（Topic）」打通了发布者和订阅者。话题是**单向、异步、一对多**的数据流，非常适合传感器数据、状态广播这类场景。

但现实中还有很多需求，话题搞不定：

- 「帮我算一下 3 + 5 等于几」——我需要拿到**结果**，而不是发个广播等回音
- 「让机器人移动到 (5, 3) 这个点」——这是个**耗时几十秒**的任务，中途我还想知道进度，甚至想取消

前者需要**服务（Service）**，后者需要**动作（Action）**。

本章目标：

- 理解服务与服务端/客户端的工作机制
- 理解动作的 Goal / Feedback / Result 三要素
- 动手写自定义 `.srv` 和 `.action` 接口
- 掌握「什么时候该用 Topic / Service / Action」的判断标准

**预计学习时间**：60-75 分钟

**前置章节**：

- [02 - ROS2 架构与基础概念全解析](02_ros2_basics.md)
- [03 - 创建第一个 ROS2 工作空间与 Python 节点](03_first_workspace_and_node.md)
- [05 - 话题通信详解（Publisher / Subscriber / QoS）](05_topics_pub_sub.md)

---

## 🧱 一、主要内容

### 1.1 三种通信机制的定位

先建立一张全局地图，这是本章最核心的认知：

| 机制 | 通信模式 | 同步性 | 返回值 | 适用场景 |
| ------ | ------------ | ----------- | -------- | ----------------- |
| **Topic** | 发布 / 订阅（一对多） | 异步 | 无 | 传感器数据、状态广播、cmd_vel |
| **Service** | 请求 / 响应（一对一） | 同步（阻塞） | 有 | 查询状态、触发标定、一次性计算 |
| **Action** | 目标 / 反馈 / 结果 | 异步（可等可不等） | 有 + 中途反馈 | 导航到点、机械臂抓取、耗时任务 |

**一句话口诀**：

> 数据流用 Topic，算一次用 Service，干长活用 Action。

### 1.2 为什么话题不够用

用话题实现「请求-响应」会很难受，看个反面例子：

```text
话题方案：客户端发 /add_request，服务端算完发 /add_response
问题 1：多个客户端同时发请求，响应怎么区分是给谁的？
问题 2：客户端怎么知道结果什么时候回来？只能靠轮询，很笨
问题 3：服务端不在线时，请求发出去石沉大海，客户端不知道
```

服务机制就是为了解决这三个问题而生的：**有请求头、有响应码、有超时、天然一对一**。

### 1.3 服务（Service）的工作机制

```text
客户端（Client）                    服务端（Server）
     │                                    │
     │  ── 请求（Request）─────>          │
     │                                    │  处理中……
     │  <──── 响应（Response）──          │
     │                                    │
   收到结果，继续执行                    等待下一个请求
```

关键特征：

1. **同步阻塞**——客户端调用后**卡住等待**，直到收到响应或超时
2. **一对一**——一个请求只会被一个服务端处理
3. **双向数据结构**——`.srv` 文件里同时定义请求和响应

### 1.4 动作（Action）的工作机制

动作本质上**是基于服务 + 话题封装出来的**，但用起来简单得多：

```text
客户端（Action Client）              服务端（Action Server）
     │                                    │
     │  ── Goal（目标）────────>          │  开始干活
     │                                    │
     │  <──── Feedback（反馈）───         │  进度 30%...
     │  <──── Feedback（反馈）───         │  进度 60%...
     │  <──── Feedback（反馈）───         │  进度 90%...
     │  <──── Result（结果）─────         │  完成！
     │                                    │
  也可以中途发送 Cancel 取消
```

三要素必须记牢：

| 名称 | 方向 | 含义 | 必填 |
| ----------- | ---- | ------------- | ---- |
| **Goal** | 客户端 → 服务端 | 我要做什么 | 是 |
| **Feedback** | 服务端 → 客户端 | 现在做到哪了 | 可选 |
| **Result** | 服务端 → 客户端 | 最终结果 | 是 |

**动作的杀手锏是「可取消」**。想象一下：你让机器人导航到 100 米外的点，走到一半发现路封了，想让它回来——Service 只能干等它跑完，Action 一个 Cancel 就搞定了。

---

## 🧩 二、示例与讲解

### 2.1 现成接口体验：turtlesim 演示

在写代码前，先用官方示例建立直观感受。

#### 步骤 1：启动海龟仿真器

```bash
# 终端 1
ros2 run turtlesim turtlesim_node
```

#### 步骤 2：查看有哪些服务

```bash
# 终端 2
ros2 service list
```

输出：

```text
/clear
/kill
/reset
/spawn
/turtle1/set_pen
/turtle1/teleport_absolute
/turtle1/teleport_relative
/turtlesim/describe_parameters
/turtlesim/get_parameters
...
```

#### 步骤 3：查看某个服务的接口定义

```bash
ros2 service type /clear
```

输出：

```text
std_srvs/srv/Empty
```

再看这个接口里有什么：

```bash
ros2 interface show std_srvs/srv/Empty
```

输出：

```text
---
```

就三条横线，**前面是空请求，后面是空响应**——`/clear` 不需要传参也不需要返回值，所以两边都空。

再换个有参数的：

```bash
ros2 interface show turtlesim/srv/TeleportAbsolute
```

输出：

```text
float32 x
float32 y
float32 theta
---
# 横线之后是响应，这里是空的
```

`---` 是 `.srv` 文件的分隔符，**上面是 Request，下面是 Response**，这个规则要记住。

#### 步骤 4：调用服务

```bash
ros2 service call /turtle1/teleport_absolute turtlesim/srv/TeleportAbsolute \
  "{x: 5.5, y: 5.5, theta: 0.0}"
```

看到海龟瞬移到画布中心了。这就是服务的典型用法：**发一个请求，立刻拿到结果**。

#### 步骤 5：体验动作

```bash
# 列出所有动作
ros2 action list
```

输出：

```text
/turtle1/rotate_absolute
```

查看它的接口：

```bash
ros2 action info /turtle1/rotate_absolute
```

输出：

```text
Action: /turtle1/rotate_absolute
Action clients: 0
Action servers: 1
    /turtlesim [turtlesim/action/RotateAbsolute]
```

`Action clients: 0` 表示现在没有客户端在用。我们手动发一个目标：

```bash
ros2 action send_goal /turtle1/rotate_absolute turtlesim/action/RotateAbsolute \
  "{theta: 1.57}" --feedback
```

输出：

```text
Waiting for an action server to become available...
Sending goal:
     theta: 1.57

Goal accepted with ID: 07d1e8b3...

Feedback:
    remaining: 1.194444

Feedback:
    remaining: 0.904444

...
Result:
    delta: -1.569999
```

看 `--feedback` 参数的效果：**服务端每 100ms 左右推一次剩余量**。这就是 Action 相对 Service 的最大优势——长任务过程中能实时看到进度。

---

### 2.2 编写自定义服务：整数加法器

现在从零写一个服务。目标是实现一个「整数加法器」，客户端传两个数，服务端返回和。

#### 步骤 1：创建功能包

服务接口需要编译，所以要用 `ament_cmake` 而不是纯 Python 包：

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake \
  --dependencies rclpy std_msgs rosidl_default_generators \
  service_demo
```

#### 步骤 2：定义服务接口

创建 `~/ros2_ws/src/service_demo/srv/AddTwoInts.srv`：

```text
int64 a
int64 b
---
int64 sum
```

**注意**：用 `int64` 而不是 `int32`。ROS2 里 Python 的整数默认是 64 位，用 int32 会在边界值上踩坑（后续章节会展开）。

#### 步骤 3：配置 CMakeLists.txt

在 `service_demo/CMakeLists.txt` 中，找到 `find_package` 段落，加上接口定义：

```cmake
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 关键：声明要生成的接口文件
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/AddTwoInts.srv"
)
```

并在文件**末尾**（`ament_package()` 之前）加上依赖声明：

```cmake
ament_export_dependencies(rosidl_default_runtime)
```

#### 步骤 4：配置 package.xml

在 `service_demo/package.xml` 的 `<buildtool_depend>` 区域后，加入：

```xml
<buildtool_depend>ament_cmake</buildtool_depend>
<buildtool_depend>rosidl_default_generators</buildtool_depend>

<depend>rclpy</depend>
<depend>std_msgs</depend>

<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

> `rosidl_default_generators` 和 `rosidl_default_runtime` 分别管**编译期**和**运行期**，两个都要有。`member_of_group` 那行告诉 ROS2「这个包里有接口定义」，漏了会编译不过。

#### 步骤 5：编写服务端

创建 `~/ros2_ws/src/service_demo/service_demo/add_two_ints_server.py`：

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

# 从自定义包导入服务接口
from service_demo.srv import AddTwoInts


class AddTwoIntsServer(Node):
    def __init__(self):
        super().__init__('add_two_ints_server')

        # 创建服务端：服务名 'add_two_ints'，类型 AddTwoInts，回调 handle_add
        self.srv = self.create_service(
            AddTwoInts,
            'add_two_ints',
            self.handle_add
        )

        self.get_logger().info('加法服务端已启动，等待请求……')

    def handle_add(self, request, response):
        """服务回调：收到请求后自动被调用

        参数：
            request: 请求对象，含 request.a 和 request.b
            response: 响应对象，需要填 response.sum 后返回
        """
        response.sum = request.a + request.b

        self.get_logger().info(
            f'收到请求: {request.a} + {request.b} = {response.sum}'
        )

        # 必须返回 response，否则客户端会一直等
        return response


def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsServer()

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

**这里有个新手最容易犯的错**：忘了 `return response`。结果是客户端**永远阻塞**等不到响应，而服务端日志看起来一切正常——非常难排查。记住服务回调**必须有返回值**。

#### 步骤 6：编写客户端

创建 `~/ros2_ws/src/service_demo/service_demo/add_two_ints_client.py`：

```python
#!/usr/bin/env python3

import sys
import rclpy
from rclpy.node import Node

from service_demo.srv import AddTwoInts


class AddTwoIntsClient(Node):
    def __init__(self):
        super().__init__('add_two_ints_client')

        # 创建客户端：只声明服务名和类型，不传回调
        self.client = self.create_client(AddTwoInts, 'add_two_ints')

        # 等待服务端上线，最多等 5 秒
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('服务未上线，继续等待……')

    def send_request(self, a, b):
        """发送请求并等待响应"""
        request = AddTwoInts.Request()
        request.a = a
        request.b = b

        # call_async 返回 Future 对象，不阻塞
        self.future = self.client.call_async(request)

        # 阻塞等待 Future 完成
        rclpy.spin_until_future_complete(self, self.future)

        return self.future.result()


def main(args=None):
    rclpy.init(args=args)

    node = AddTwoIntsClient()

    # 从命令行读参数，默认算 3 + 5
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    response = node.send_request(a, b)

    if response is not None:
        node.get_logger().info(f'结果: {a} + {b} = {response.sum}')
    else:
        node.get_logger().error('服务调用失败')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**关键点解析**：

**1. 等待服务上线**

```python
while not self.client.wait_for_service(timeout_sec=1.0):
```

直接调用不存在的服务会抛异常。**必须**先等待。这是新手第二个高频错误。

**2. 异步调用 + 等待完成**

```python
self.future = self.client.call_async(request)
rclpy.spin_until_future_complete(self, self.future)
```

`call_async` 是异步的（返回 Future），配合 `spin_until_future_complete` 就实现了同步等待的效果。这种「异步 + 阻塞等待」是 ROS2 里处理服务的标准姿势。

#### 步骤 7：配置 setup.py

创建 `service_demo/setup.py`（因为包是 ament_cmake 类型，需要手动加 Python 安装规则）：

```python
from setuptools import setup

package_name = 'service_demo'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='whatqiu',
    maintainer_email='whatqiu@example.com',
    description='ROS2 服务与动作示例',
    license='MIT',
    entry_points={
        'console_scripts': [
            'add_two_ints_server = service_demo.add_two_ints_server:main',
            'add_two_ints_client = service_demo.add_two_ints_client:main',
        ],
    },
)
```

同时在 `CMakeLists.txt` 末尾加上 Python 安装：

```cmake
install(PROGRAMS
  service_demo/add_two_ints_server.py
  service_demo/add_two_ints_client.py
  DESTINATION lib/${PROJECT_NAME}
)
```

#### 步骤 8：编译并测试

```bash
cd ~/ros2_ws
colcon build --packages-select service_demo
source install/setup.bash
```

**验证接口已生成**：

```bash
ros2 interface show service_demo/srv/AddTwoInts
```

输出：

```text
int64 a
int64 b
---
int64 sum
```

**终端 1** 启动服务端：

```bash
source ~/ros2_ws/install/setup.bash
ros2 run service_demo add_two_ints_server
```

输出：

```text
[INFO] [add_two_ints_server]: 加法服务端已启动，等待请求……
```

**终端 2** 运行客户端：

```bash
source ~/ros2_ws/install/setup.bash
ros2 run service_demo add_two_ints_client 10 25
```

客户端输出：

```text
[INFO] [add_two_ints_client]: 结果: 10 + 25 = 35
```

服务端同时输出：

```text
[INFO] [add_two_ints_server]: 收到请求: 10 + 25 = 35
```

**再试试命令行直接调用**：

```bash
ros2 service call /add_two_ints service_demo/srv/AddTwoInts "{a: 100, b: 200}"
```

输出：

```text
response:
service_demo.srv.AddTwoInts_Response(sum=300)
```

命令行能调通，说明接口定义没问题。

---

### 2.3 编写自定义动作：倒计时任务

现在写一个动作。用一个「倒计时」任务来演示，因为它天然需要反馈。

#### 步骤 1：定义动作接口

创建 `~/ros2_ws/src/service_demo/action/CountDown.action`：

```text
# Goal：目标，客户端告诉服务端要做什么
int32 target
---
# Result：最终结果，任务结束时返回
bool success
string message
---
# Feedback：过程反馈，服务端周期性推送
int32 current
```

**注意 `.action` 是两段 `---` 分成三块**，顺序固定：**Goal / Result / Feedback**。这个顺序很多人记错，尤其容易把 Result 和 Feedback 弄反。

#### 步骤 2：更新 CMakeLists.txt

```cmake
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/AddTwoInts.srv"
  "action/CountDown.action"
)
```

动作接口依赖 `action_msgs`，补充依赖：

```cmake
find_package(action_msgs REQUIRED)
```

#### 步骤 3：编译验证

```bash
cd ~/ros2_ws
colcon build --packages-select service_demo
source install/setup.bash

ros2 interface show service_demo/action/CountDown
```

输出：

```text
int32 target
---
bool success
string message
---
int32 current
```

三段结构清晰可见。

#### 步骤 4：编写动作服务端

创建 `~/ros2_ws/src/service_demo/service_demo/countdown_server.py`：

```python
#!/usr/bin/env python3

import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup

from service_demo.action import CountDown


class CountDownServer(Node):
    def __init__(self):
        super().__init__('countdown_server')

        # 可重入回调组：允许回调之间并行执行
        # 默认回调组是互斥的，会导致反馈发送时阻塞
        self.callback_group = ReentrantCallbackGroup()

        self._action_server = ActionServer(
            self,
            CountDown,
            'countdown',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group,
        )

        self.get_logger().info('倒计时动作服务端已启动')

    def goal_callback(self, goal_request):
        """决定是否接受这个目标"""
        self.get_logger().info(f'收到目标: {goal_request.target}')

        if goal_request.target <= 0:
            self.get_logger().warn('目标值必须大于 0，拒绝')
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """决定是否接受取消请求"""
        self.get_logger().info('收到取消请求，接受')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        """真正的执行逻辑，会跑在一个独立线程里"""
        self.get_logger().info('开始执行倒计时……')

        feedback_msg = CountDown.Feedback()
        target = goal_handle.request.target

        for i in range(target):
            # 关键：每次循环检查是否被取消
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('任务已取消')

                result = CountDown.Result()
                result.success = False
                result.message = f'在 {i} 处被取消'
                return result

            feedback_msg.current = i
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'反馈: {i}')

            time.sleep(1)

        # 任务完成
        goal_handle.succeed()

        result = CountDown.Result()
        result.success = True
        result.message = f'倒计时 {target} 完成'
        self.get_logger().info('任务完成')

        return result


def main(args=None):
    rclpy.init(args=args)
    node = CountDownServer()

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

**三个关键点，全是新手必踩的坑**：

**1. 必须用 `ReentrantCallbackGroup`**

```python
from rclpy.callback_groups import ReentrantCallbackGroup
self.callback_group = ReentrantCallbackGroup()
```

默认的回调组是**互斥**的。如果 `execute_callback` 正在跑（里面有个 `time.sleep(1)` 循环），而你想在循环中发取消请求——**取消回调根本没机会执行**，因为它在等 execute 结束。

用 Reentrant 回调组，两个回调能并行，取消才能真正生效。

**2. 每次循环都要检查取消状态**

```python
if goal_handle.is_cancel_requested:
    goal_handle.canceled()
    ...
    return result
```

只在开头检查一次是不够的。**长时间循环必须逐次检查**，否则取消反应迟钝。

**3. 返回前必须调用 `succeed()` / `canceled()` / `abort()`**

```python
goal_handle.succeed()   # 成功
goal_handle.canceled()  # 取消
goal_handle.abort()     # 失败
```

漏掉这一步，客户端会一直处于「等待结果」状态，即使服务端代码已经 return 了。

#### 步骤 5：编写动作客户端

创建 `~/ros2_ws/src/service_demo/service_demo/countdown_client.py`：

```python
#!/usr/bin/env python3

import sys
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from service_demo.action import CountDown


class CountDownClient(Node):
    def __init__(self):
        super().__init__('countdown_client')
        self._action_client = ActionClient(self, CountDown, 'countdown')

    def send_goal(self, target):
        """发送目标并注册所有回调"""
        # 等待服务端可用
        self.get_logger().info('等待动作服务端……')
        self._action_client.wait_for_server()

        goal_msg = CountDown.Goal()
        goal_msg.target = target

        self.get_logger().info(f'发送目标: {target}')

        # 三步注册：目标响应 / 反馈 / 结果
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback,
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """服务端是否接受目标"""
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().info('目标被拒绝')
            return

        self.get_logger().info('目标已接受，等待结果……')

        # 目标被接受后，才去请求最终结果
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        """接收过程反馈"""
        feedback = feedback_msg.feedback
        self.get_logger().info(f'[反馈] 当前: {feedback.current}')

    def get_result_callback(self, future):
        """接收最终结果"""
        result = future.result().result
        status = future.result().status

        self.get_logger().info(f'[结果] success={result.success}, msg={result.message}')
        self.get_logger().info(f'[状态码] {status}')

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = CountDownClient()

    target = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    node.send_goal(target)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
```

**客户端的三步注册流程**是整个动作机制里最容易搞混的部分，画个图理清：

```text
send_goal_async(goal, feedback_callback)
        │
        │  第一步：等目标是否被接受
        ▼
goal_response_callback(future)
        │  future.result() 得到 goal_handle
        │  检查 goal_handle.accepted
        ▼
goal_handle.get_result_async()
        │
        │  第二步：等最终结果
        ▼
get_result_callback(future)
        future.result().result  ← 结果数据
        future.result().status  ← 状态码
```

**反馈回调在第一步就注册了**（作为 `send_goal_async` 的参数），而**结果要等目标被接受后才能请求**。这个不对称设计是很多人的困惑点。

#### 步骤 6：注册并测试

在 `setup.py` 的 `entry_points` 加上：

```python
'countdown_server = service_demo.countdown_server:main',
'countdown_client = service_demo.countdown_client:main',
```

在 `CMakeLists.txt` 的 `install(PROGRAMS ...)` 里加上这两个文件。

```bash
cd ~/ros2_ws
colcon build --packages-select service_demo
source install/setup.bash
```

**终端 1** 启动服务端：

```bash
ros2 run service_demo countdown_server
```

**终端 2** 运行客户端：

```bash
ros2 run service_demo countdown_client 5
```

客户端输出：

```text
[INFO] [countdown_client]: 等待动作服务端……
[INFO] [countdown_client]: 发送目标: 5
[INFO] [countdown_client]: 目标已接受，等待结果……
[INFO] [countdown_client]: [反馈] 当前: 0
[INFO] [countdown_client]: [反馈] 当前: 1
[INFO] [countdown_client]: [反馈] 当前: 2
[INFO] [countdown_client]: [反馈] 当前: 3
[INFO] [countdown_client]: [反馈] 当前: 4
[INFO] [countdown_client]: [结果] success=True, msg=倒计时 5 完成
```

**再测取消功能**——这是 Action 最有价值的地方。用命令行发目标，然后按 Ctrl+C：

```bash
ros2 action send_goal /countdown service_demo/action/CountDown "{target: 20}" --feedback
```

跑几秒后按 Ctrl+C，观察服务端输出：

```text
[INFO] [countdown_server]: 收到取消请求，接受
[INFO] [countdown_server]: 任务已取消
```

**取消生效了**。如果服务端报 `Task was destroyed but it is pending` 或者客户端一直等不到结果，回头看前面那三个关键点。

---

### 2.4 Topic / Service / Action 决策树

面对一个需求，这样判断：

```text
需要返回值吗？
├─ 不需要，只是广播数据 ────────────────> Topic
└─ 需要
    ├─ 任务能在几十毫秒内做完吗？
    │   ├─ 能 ─────────────────────────> Service
    │   └─ 不能（耗时数秒以上）
    │       ├─ 需要中途进度反馈吗？────> Action
    │       └─ 需要能取消吗？─────────> Action
```

具体到机器人开发，常见选择的对照：

| 需求 | 选择 | 理由 |
| ---------------- | -------- | ---------------------- |
| 发布激光雷达数据 | Topic | 高频、单向、无需回复 |
| 发布里程计 | Topic | 持续输出状态 |
| 速度指令 cmd_vel | Topic | 高频、不关心是否被收到 |
| 查询电池电量 | Service | 一问一答，快速 |
| 触发相机标定 | Service | 一次性动作，要结果 |
| 清空地图 | Service | 快速、要确认 |
| 导航到目标点 | **Action** | 耗时长、要进度、要能取消 |
| 机械臂抓取 | **Action** | 耗时长、要进度、可能失败 |
| 保存地图到文件 | Service | 通常很快 |

**一个实战判断技巧**：如果这个操作的耗时**依赖于外部物理过程**（开过去、抓起来、转到位），那基本就是 Action。

---

### 2.5 常见错误速查

| 报错 / 现象 | 原因 | 解决 |
| -------------------------------------------- | ------------------- | ---------------------------- |
| 客户端一直阻塞，服务端日志正常 | 服务回调忘了 `return response` | 检查回调最后一行 |
| `Service not available` | 服务端没启动 / 服务名拼错 | `ros2 service list` 确认 |
| 编译报 `rosidl_generate_interfaces` 相关错误 | package.xml 缺 `rosidl_default_generators` | 补上依赖 |
| `ros2 interface show` 找不到自定义接口 | 编译后没 source | `source install/setup.bash` |
| 改了 `.srv` 但接口没变 | 增量编译没检测到 | `colcon build --packages-select xxx` 或删 `build/ install/` 重编 |
| 动作取消没反应 | 用了默认互斥回调组 | 改用 `ReentrantCallbackGroup` |
| 动作执行完客户端一直等 | 忘了调 `succeed()` / `canceled()` | 每个返回路径都要调 |
| `.action` 文件编译报错 | 三段顺序写错 | 顺序固定为 Goal / Result / Feedback |

#### 关于「改了接口不生效」的深挖

这是最高频的坑。原因是接口生成的文件在 `build/` 和 `install/` 里，增量编译有时不会重新生成。

```bash
# 单个包强制重编
rm -rf build/service_demo install/service_demo
colcon build --packages-select service_demo
source install/setup.bash
```

更彻底的做法：

```bash
rm -rf build/ install/ log/
colcon build
source install/setup.bash
```

**另一个隐蔽原因**：同时开了多个终端，只在其中一个执行了 `source`。新终端必须重新 source，否则用的是旧接口。

---

## 🔄 Humble 与 Jazzy 差异对照

本章内容在两个版本间基本通用，主要差异：

| 项目 | Humble (22.04) | Jazzy (24.04) |
| ------------------ | ------------------- | -------------------- |
| 包名 | `ros-humble-rclpy` | `ros-jazzy-rclpy` |
| Python 版本 | 3.10 | 3.12 |
| `rclpy` 服务 API | 无变化 | 无变化 |
| Action 回调组 | 无变化 | 无变化 |
| 自定义接口生成 | 无变化 | 无变化 |
| 服务超时参数 | `wait_for_service` | 同名，行为一致 |

**结论**：服务与动作这一章，Humble 和 Jazzy 的代码可以**直接互用**，只需把环境变量里的 `humble` 换成 `jazzy`。

---

## ✅ 总结

### 核心知识点回顾

| 概念 | 说明 | 关键代码 |
| ------------------- | -------------- | ------------------------------------------- |
| **Service** | 同步请求-响应 | `create_service(type, name, callback)` |
| **Service Client** | 发起请求 | `create_client(type, name)` |
| **Action** | 异步长任务 | `ActionServer(node, type, name, ...)` |
| **Action Client** | 发起目标 | `ActionClient(node, type, name)` |
| **Goal / Feedback / Result** | 动作三要素 | `GoalResponse.ACCEPT` 等 |
| **ReentrantCallbackGroup** | 让回调可并行 | `ReentrantCallbackGroup()` |
| **`.srv` 分隔符** | 上请求下响应 | `---` |
| **`.action` 三段** | Goal/Result/Feedback | 两个 `---` |

### 代码模板速查

> ⚠️ **下面的模板为了突出重点，省略了 try/except 错误处理**，直接用是可以跑的。
> 但在生产代码里请套上完整的错误处理——尤其注意「**在 try 外面先把节点变量初始化为 None**」，
> 否则节点构造失败时，`finally` 里引用未赋值的变量会抛 `UnboundLocalError`，
> 把真正的错误信息盖掉，排查起来很痛苦。
>
> ```python
> node = None                          # 必须在 try 外
> try:
>     node = MyNode()
>     rclpy.spin(node)
> except KeyboardInterrupt:
>     pass
> finally:
>     if node is not None:             # 防御性检查
>         node.destroy_node()
>     rclpy.try_shutdown()             # 比 shutdown() 更安全
> ```

#### 服务端模板

```python
import rclpy
from rclpy.node import Node
from my_pkg.srv import MyService

class MyServer(Node):
    def __init__(self):
        super().__init__('my_server')
        self.srv = self.create_service(MyService, 'my_service', self.handle)

    def handle(self, request, response):
        response.result = request.input * 2
        return response   # 别忘了！

def main():
    rclpy.init()
    node = MyServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

#### 客户端模板

```python
import rclpy
from rclpy.node import Node
from my_pkg.srv import MyService

class MyClient(Node):
    def __init__(self):
        super().__init__('my_client')
        self.client = self.create_client(MyService, 'my_service')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('等待服务……')

    def call(self, value):
        req = MyService.Request()
        req.input = value
        future = self.client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()
```

#### 动作服务端模板

```python
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup

class MyActionServer(Node):
    def __init__(self):
        super().__init__('my_action_server')
        self._server = ActionServer(
            self, MyAction, 'my_action',
            execute_callback=self.execute,
            goal_callback=lambda req: GoalResponse.ACCEPT,
            cancel_callback=lambda h: CancelResponse.ACCEPT,
            callback_group=ReentrantCallbackGroup(),   # 支持取消的关键
        )

    def execute(self, goal_handle):
        for i in range(10):
            if goal_handle.is_cancel_requested:     # 逐次检查
                goal_handle.canceled()
                return MyAction.Result(success=False)
            goal_handle.publish_feedback(MyAction.Feedback(progress=i))
            time.sleep(0.5)

        goal_handle.succeed()                       # 必须调
        return MyAction.Result(success=True)
```

#### 动作客户端模板

```python
from rclpy.action import ActionClient

class MyActionClient(Node):
    def __init__(self):
        super().__init__('my_action_client')
        self._client = ActionClient(self, MyAction, 'my_action')

    def send(self, target):
        self._client.wait_for_server()
        goal = MyAction.Goal(target=target)
        future = self._client.send_goal_async(goal, feedback_callback=self.on_feedback)
        future.add_done_callback(self.on_goal_response)

    def on_goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            return
        handle.get_result_async().add_done_callback(self.on_result)

    def on_feedback(self, msg):
        self.get_logger().info(f'进度: {msg.feedback.progress}')

    def on_result(self, future):
        self.get_logger().info(f'结果: {future.result().result}')
```

### 三种机制选择指南

| 场景 | 选择 | History/Reliability 建议 |
| ---------------------- | ------- | ------------------- |
| 传感器数据流 | Topic | KEEP_LAST + BEST_EFFORT |
| 控制指令 | Topic | KEEP_LAST + RELIABLE |
| 状态查询 | Service | — |
| 一次性触发 | Service | — |
| 耗时任务 + 进度 | Action | — |
| 需要可取消的任务 | Action | — |

### 下一步学习方向

下一章我们把「参数」补齐——你会发现，前五章代码里那些写死的数字，都可以变成可配置的参数。

- 📘 [07 - 参数服务器与动态参数管理](07_parameters_and_config.md)
- 📘 [08 - ROS2 Launch 文件](08_ros2_launch.md)
- 📘 [19 - ROS2 常见错误与踩坑记录](19_ros2_debug_notes.md)

---

📘 下一章：[07 - 参数服务器与动态参数管理](07_parameters_and_config.md)
