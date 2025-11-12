# 🚀【ROS2 入门系列 #1】Ubuntu 22.04 从零配置 ROS2 Humble（含虚拟机网络修复）

> 作者：whatqiu  
> 更新时间：2025-11-04  
> 环境：Ubuntu 22.04 + ROS2 Humble  

---

## 🧭 前言

这篇文章记录了我在 **Ubuntu 22.04 虚拟机** 上从零成功配置 ROS2 Humble 的完整过程。

中间经历了：

- 虚拟机断网、桥接模式失效  
- ROS2 源码下载失败 (`not found`)  
- `ros2 not found` 的环境问题  

经过一系列排查，最终成功构建 ROS2 并让命令行工具正常运行。

---

## 🌐 一、虚拟机网络修复过程（<span style="text-decoration: underline wavy;">也有可能没有用管理员权限打开VM ware</span>）

最初因为设置了系统代理，后来关机重启后，发现 Ubuntu 里：

- 右上角没有网络图标  
- 无法打开任何网页  
- “Connected” 显示为灰色，不可点击  

连 VMware 的桥接模式都导致虚拟机打不开。

---

### 🧩 1. 检查主机网络设置

在宿主机（Windows）执行以下操作：

1. 打开  

控制面板 → 网络和 Internet → 网络连接

2. 找到你正在使用的真实网卡（Wi-Fi 或 以太网）  
3. **右键 → 属性**  
4. 确保：

- ✅ **VMware Bridge Protocol** 被勾选  
- ✅ **IPv4 / IPv6** 都保持勾选  

---

### 🔄 2. 重启 VMware 网络服务

1. 点击 VMware 顶部菜单：

2. Edit → Virtual Network Editor

3. 找到你正在使用的真实网卡（Wi-Fi 或 以太网）  

   **右键 → 属性**  

   确保：

- ✅ **VMware Bridge Protocol** 被勾选  
- ✅ **IPv4 / IPv6** 都保持勾选  

4. 启动 Ubuntu 后修复网络

   进入虚拟机后，在终端执行：

   ```bash
   sudo systemctl restart NetworkManager
   sudo nmcli networking on
   sudo dhclient -v

说明：

- `NetworkManager`：负责管理网络连接
- `nmcli networking on`：开启网络
- `dhclient -v`：重新向 DHCP 请求 IP

执行完毕后，网页恢复正常 ✅。

## 🧱 二、ROS2 环境安装

确认网络正常后，开始安装 ROS2 Humble：

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install software-properties-common
sudo add-apt-repository universe
```

导入密钥与源：

```bash
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

安装公共包：

```bash
$ sudo apt update && sudo apt install -y \
  python3-flake8-docstrings \
  python3-pip \
  python3-pytest-cov \
  ros-dev-tools
```

安装Ubuntu22.04或后面的版本：

```bash
$ sudo apt install -y \
   python3-flake8-blind-except \
   python3-flake8-builtins \
   python3-flake8-class-newline \
   python3-flake8-comprehensions \
   python3-flake8-deprecated \
   python3-flake8-import-order \
   python3-flake8-quotes \
   python3-pytest-repeat \
   python3-pytest-rerunfailures
```



------

## 🧬 三、下载 ROS2 源码（修复仓库问题）

最开始执行：

```bash
vcs import src < ros2.repos
```

报错：

```
fatal: repository 'https://mirrors.tuna.tsinghua.edu.cn/git/ament/ament_cmake.git/' not found
```

原因：清华镜像仓库已失效。

解决方案：使用官方源。

```bash
wget https://raw.githubusercontent.com/ros2/ros2/humble/ros2.repos
vcs import src < ros2.repos
```

------

## ⚙️ 四、编译 ROS2

```bash
colcon build --symlink-install
```

第一次构建时 `python_cmake_module` 报错，原因是部分包下载失败。
 重新执行一次：

```bash
colcon build --symlink-install
```

即可正常完成构建 ✅。

------

## 🧠 五、加载环境变量

运行：

```bash
source install/setup.bash
```

验证命令：

```bash
ros2
```

输出：

```
usage: ros2 [-h] [--use-python-default-buffering] <command> ...
```

说明 ROS2 已安装并加载成功。

------

## 🧩 六、让环境自动加载

每次手动 `source` 很麻烦，可将其写入 `~/.bashrc`：

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

之后每次打开终端都会自动加载 ROS2 环境。

------

## ✅ 七、总结

| 阶段                | 问题                  | 解决方案                                             |
| ------------------- | --------------------- | ---------------------------------------------------- |
| VMware 无法联网     | 桥接协议未勾选        | 勾选 VMware Bridge Protocol(或者用管理员打开VM ware) |
| 网络连接灰色        | NetworkManager 未启动 | `sudo systemctl restart NetworkManager`              |
| vcs import 报错     | 清华镜像失效          | 使用官方源                                           |
| ros2 not found      | 环境未加载            | `source setup.bash`                                  |
| ros2 --version 无效 | 命令不支持            | 使用 `ros2 doctor --report`                          |



##  📚 八、 延伸阅读

- [ROS2 官方安装指南](https://docs.ros.org/en/humble/Installation.html)
- [colcon build 教程](https://colcon.readthedocs.io/en/released/)
- [ROS2 CLI 命令参考](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools.html)

------

## 🎯 最终结果

至此，ROS2 Humble 在 Ubuntu 22.04 + VMware 上成功安装并能运行命令。
 网络修复、仓库下载、依赖构建全部顺利完成 ✅。

------

> 💬 本文记录了 Ubuntu 虚拟机下 ROS2 安装与网络修复的完整过程，
> 希望能帮助到遇到同样问题的你。

---

📘 下一章：敬请期待
