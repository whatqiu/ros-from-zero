# 🤖 ROS2 From Zero — 从零学习 ROS2 实战系列

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/build-passing-brightgreen)

> 🚀 从零开始学习 ROS2 的完整系列教程  
> 从环境配置、通信机制、构建与仿真，到完整机器人项目实战。  
> 每篇文档都记录了真实踩坑过程与解决方案。

---

## 🧭 项目简介

本仓库记录了我 **从零开始学习 ROS2（Robot Operating System 2）** 的全过程。  
适合初学者、ROS1 转 ROS2 的开发者，以及希望系统掌握机器人框架的人。

内容涵盖：
- Ubuntu 虚拟机环境配置与网络修复
- ROS2 节点 / 话题 / 服务 / 动作等基础机制
- colcon 构建、Launch 文件、参数服务器
- Rviz2、Gazebo、URDF、TF 等可视化与仿真
- Docker 环境、OpenCV 集成与多机通信

---

## 📚 教程目录

| 阶段 | 标题 | 文件 |
|------|------|------|
| 1️⃣ | 🚀【ROS2 入门系列 #1】Ubuntu 22.04 从零配置 ROS2 Humble（含虚拟机网络修复） | [docs/01_install_ros2_humble.md](docs/01_install_ros2_humble.md) |
| 2️⃣ | ⚙️【ROS2 入门系列 #2】ROS2 架构与基础概念全解析（节点 / 话题 / 服务 / 参数） | [docs/02_ros2_basics.md](docs/02_ros2_basics.md) |
| 3️⃣ | 🧩【ROS2 入门系列 #3】创建第一个 ROS2 工作空间与 Python 节点 | [docs/03_first_workspace_and_node.md](docs/03_first_workspace_and_node.md) |
| 4️⃣ | 🧰【ROS2 入门系列 #4】ROS2 常用命令行工具与调试技巧（ros2 node / topic / run） | [docs/04_ros2_cli_tools.md](docs/04_ros2_cli_tools.md) |
| 5️⃣ | 🔄【ROS2 入门系列 #5】话题通信详解（Publisher / Subscriber / QoS） | [docs/05_topics_pub_sub.md](docs/05_topics_pub_sub.md) |
| 6️⃣ | 🔧【ROS2 入门系列 #6】服务与动作机制（Service / Client / Action） | [docs/06_services_and_actions.md](docs/06_services_and_actions.md) |
| 7️⃣ | ⚗️【ROS2 入门系列 #7】参数服务器与动态参数管理（Parameter YAML 配置） | [docs/07_parameters_and_config.md](docs/07_parameters_and_config.md) |
| 8️⃣ | 🚦【ROS2 入门系列 #8】Launch 文件使用与多节点启动管理 | [docs/08_ros2_launch.md](docs/08_ros2_launch.md) |
| 9️⃣ | 🧰【ROS2 进阶系列 #9】colcon 构建系统与依赖管理详解 | [docs/09_colcon_build.md](docs/09_colcon_build.md) |
| 🔟 | 🧬【ROS2 进阶系列 #10】C++ 与 Python 节点混合开发（rclcpp vs rclpy） | [docs/10_cpp_python_nodes.md](docs/10_cpp_python_nodes.md) |
| 11 | 🧭【ROS2 进阶系列 #11】Rviz2 与 rqt 可视化调试工具使用指南 | [docs/11_rviz_rqt_debug.md](docs/11_rviz_rqt_debug.md) |
| 12 | 🌍【ROS2 实战系列 #12】Gazebo 仿真环境搭建与机器人启动 | [docs/12_gazebo_setup.md](docs/12_gazebo_setup.md) |
| 13 | 🦾【ROS2 实战系列 #13】URDF 模型创建与机器人可视化（Rviz 展示） | [docs/13_urdf_visualization.md](docs/13_urdf_visualization.md) |
| 14 | 📡【ROS2 实战系列 #14】TF 坐标变换详解（tf2 广播与监听） | [docs/14_tf2_basics.md](docs/14_tf2_basics.md) |
| 15 | 🚗【ROS2 实战系列 #15】键盘控制小车运动（cmd_vel 实战） | [docs/15_robot_keyboard_control.md](docs/15_robot_keyboard_control.md) |
| 16 | 🧠【ROS2 高级系列 #16】ROS2 与 OpenCV 集成（图像处理与话题传输） | [docs/16_opencv_integration.md](docs/16_opencv_integration.md) |
| 17 | 🐳【ROS2 高级系列 #17】使用 Docker 构建与部署 ROS2 环境 | [docs/17_docker_ros2.md](docs/17_docker_ros2.md) |
| 18 | 🌐【ROS2 高级系列 #18】多机通信与 DDS 配置优化（FastDDS / CycloneDDS） | [docs/18_dds_networking.md](docs/18_dds_networking.md) |
| 19 | 🧩【ROS2 高级系列 #19】ROS2 常见错误与踩坑记录（持续更新） | [docs/19_ros2_debug_notes.md](docs/19_ros2_debug_notes.md) |
| 20 | 🚀【ROS2 实战系列 #20】综合项目实战：自主小车仿真系统 | [docs/20_final_project_car_sim.md](docs/20_final_project_car_sim.md) |

---

## 🧰 环境说明

| 名称 | 版本 |
|------|------|
| 操作系统 | Ubuntu 22.04 LTS |
| ROS 版本 | ROS 2 Humble Hawksbill |
| 虚拟化 | VMware Workstation / VirtualBox |
| 编程语言 | Python 3.10 / C++17 |
| 编辑器 | VSCode + ROS2 Extension |

---

## 🧑‍💻 作者

**whatqiu**  
📍 GitHub：[whqiu](https://github.com/whqiu)  
💬 欢迎提 Issue / PR，一起完善这个系列教程。

---

## 📄 License
本项目采用 [MIT License](LICENSE)。

---

> 💬 “记录每一次踩坑，就是在铺路给后来的人。”  
> —— whatqiu
