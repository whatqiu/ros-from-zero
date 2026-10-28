# 💻 ROS2 代码示例

这个目录包含了 ROS2 入门教程中的所有示例代码，代码遵循 ROS2 官方文档的最佳实践和标准。

## 📁 目录结构

```
code/
├── README.md                 # 本文件
└── examples/                 # 示例代码目录
    ├── turtlesim/            # turtlesim 相关示例
    │   ├── turtle_publisher.py    # 小乌龟速度发布者
    │   ├── pose_subscriber.py     # 小乌龟位置订阅者
    │   ├── draw_square.py          # 20 Hz 持续发布，定时画近似正方形
    │   └── draw_square.sh          # Python 节点的启动入口
    ├── topics/               # 话题通信示例
    │   ├── simple_publisher.py     # 最小发布者示例
    │   └── simple_subscriber.py    # 最小订阅者示例
    ├── services/             # 服务通信示例
    │   ├── add_two_ints_server.py  # 两数相加服务端
    │   └── add_two_ints_client.py  # 两数相加客户端
    └── parameters/           # 参数系统示例
        └── param_example.py         # 参数系统示例
```

## 🚀 代码特点

### 官方标准风格
- ✅ 包含 Apache 2.0 许可证头部
- ✅ 遵循 PEP 8 编码规范
- ✅ 使用标准的类和方法命名
- ✅ 包含详细的文档字符串
- ✅ 完善的错误处理和异常管理
- ✅ 规范的日志记录

### 最佳实践
- ✅ 使用异步服务客户端
- ✅ 参数类型验证
- ✅ 资源清理和优雅关闭
- ✅ QoS 配置
- ✅ 防止未使用变量警告

## 🔧 运行示例

### 🐢 turtlesim 示例
```bash
# 终端 1: 启动 turtlesim
ros2 run turtlesim turtlesim_node

# 终端 2: 运行速度发布者（小乌龟自动画圈）
cd code/examples/turtlesim
python3 turtle_publisher.py

# 终端 3: 运行位置订阅者（实时显示小乌龟位置）
cd code/examples/turtlesim
python3 pose_subscriber.py

# 或者执行画正方形脚本
cd code/examples/turtlesim
chmod +x draw_square.sh
./draw_square.sh
# 也可以直接运行（不需要设置执行权限）
python3 draw_square.py
```

画方形节点会等待 turtlesim 订阅者出现。Humble turtlesim 在约 1 秒没有新速度指令时自动停车，因此不能用单次发布加长时间 sleep 控制运动。示例每 0.05 秒发布一次；边长约 1.5 米，采用定时开环控制，调度延迟会产生误差。请从默认中心位置运行，并关闭其他速度发布者。

### 📢 topics 示例
```bash
# 终端 1: 启动订阅者
cd code/examples/topics
python3 simple_subscriber.py

# 终端 2: 启动发布者（会看到 "Hello World" 消息）
cd code/examples/topics
python3 simple_publisher.py
```

### 🤝 services 示例
```bash
# 终端 1: 启动服务端
cd code/examples/services
python3 add_two_ints_server.py

# 终端 2: 调用服务（带参数）
cd code/examples/services
python3 add_two_ints_client.py 5 3

# 或使用默认值
python3 add_two_ints_client.py
```

客户端只接受零个或两个整数；服务等待和响应等待分别最多 10 秒，超时返回非零状态。支持在整数之后附加 `--ros-args` 参数。

### ⚙️ parameters 示例
```bash
# 启动参数示例
cd code/examples/parameters
python3 param_example.py

# 在另一个终端动态修改参数
ros2 param set /minimal_param_node my_parameter "ROS2"
ros2 param set /minimal_param_node update_frequency 2.0
ros2 param set /minimal_param_node enable_logging false

# 查看所有参数
ros2 param list /minimal_param_node

# 查看参数值
ros2 param get /minimal_param_node my_parameter
```

`update_frequency` 使用 double 类型，请写 `2.0`。允许范围为 0.1–1000.0 Hz，拒绝零、负数和非有限值。回调先校验整组参数；通过后的频率在下一个定时器回调生效（默认最多约 1 秒，0.1 Hz 时最多约 10 秒）。

## 📝 环境准备

### 1. 确保 ROS2 环境
```bash
source /opt/ros/humble/setup.bash
echo $ROS_DISTRO  # 应该输出 humble
```

### 2. 安装依赖包
```bash
sudo apt update
sudo apt install -y ros-humble-example-interfaces ros-humble-turtlesim ros-humble-geometry-msgs
```

### 3. 设置权限
```bash
# 给所有 Python 脚本添加执行权限
find code/examples -name "*.py" -exec chmod +x {} \;

# 给 Shell 脚本添加执行权限
# 注意：bash 默认不递归展开 **，要用 globstar 或直接 find
shopt -s globstar
chmod +x code/examples/**/*.sh
# 更稳妥的写法（不依赖 shell 选项）
find code/examples -name "*.sh" -exec chmod +x {} \;
```

## 🧪 测试和调试

### 验证节点状态
```bash
# 查看所有运行的节点
ros2 node list

# 查看节点信息
ros2 node info /minimal_publisher

# 查看话题列表
ros2 topic list

# 查看话题频率
ros2 topic hz /topic
```

### 查看日志
```bash
# 查看节点日志文件（ROS2 把日志写在 ~/.ros/log/ 下）
ls -lt ~/.ros/log/ | head

# 实时查看最新日志
tail -f $(ls -t ~/.ros/log/latest/rclpy.*.log 2>/dev/null | head -1)

# 调整节点的日志级别（启动时）
ros2 run turtlesim turtlesim_node --ros-args --log-level DEBUG

# 运行中动态调整某个节点的日志级别
ros2 service call /turtlesim/set_logger_levels \
  rcl_interfaces/srv/SetLoggerLevels \
  "{levels: [{logger: 'turtlesim', level: 10}]}"
```

> ⚠️ **关于 `ros2 log`**：ROS2 **没有** `ros2 log info` 这个子命令（ROS1 的 `roslaunch` 才有类似的日志工具）。
> ROS2 里查看日志用两种方式：一是直接读 `~/.ros/log/` 下的文件，二是通过 `--log-level` 参数控制输出级别。
> 输入 `ros2 log` 会提示 `invalid choice`。

## 🔗 相关文档

- **[ROS2 官方 Python 教程](https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html)**
- **[ROS2 基础概念教程](../docs/02_ros2_basics.md)**
- **[ROS2 安装指南](../docs/01_install_ros2_humble.md)**
- **[ROS2 设计原则](https://design.ros2.org/articles/design_principles.html)**

---

> 💡 **学习建议**：建议按照 turtlesim → topics → services → parameters 的顺序学习，
> 这样可以循序渐进地掌握 ROS2 的核心概念。每个示例都展示了不同层次的 ROS2 功能。
