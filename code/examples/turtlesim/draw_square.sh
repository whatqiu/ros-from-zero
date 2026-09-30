#!/bin/bash

# ROS2 小乌龟画正方形脚本
# 使用方法：
# 1. 确保 turtlesim 正在运行
# 2. chmod +x draw_square.sh
# 3. ./draw_square.sh
#
# 原理说明：
#   cmd_vel 是【速度指令】不是位置指令。turtlesim 收到一次指令后会
#   持续运动，直到收到新指令或撞到墙。所以用「速度 × 时间」来控制位移。
#
#   边长 = linear.x × 前进秒数
#   转角 = angular.z × 转向秒数
#
#   注意：turtlesim 画布约 11x11，海龟从中心 (5.5, 5.5) 出发，
#   单边长度不宜超过 2.0，否则会撞墙导致后续轨迹错乱。
#   转弯必须在原地进行，所以 linear.x 必须归零。

set -e

echo "开始绘制正方形..."

# 参数：边长 1.5 米（安全范围内），速度 1.0 m/s
SIDE_SPEED=1.0
SIDE_TIME=1.5      # 1.0 × 1.5 = 1.5 米

# 转角：90 度 = 1.5708 弧度，转速 1.5708 rad/s 时用时 1 秒
TURN_SPEED=1.5708
TURN_TIME=1.0

# 停止指令（转弯和结束时都要先停下）
STOP_TWIST="{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

for i in {1..4}
do
    echo "绘制第 $i 条边..."

    # 前进：先确保姿态是直线，再给线速度
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
      "{linear: {x: $SIDE_SPEED, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
    sleep "$SIDE_TIME"

    # 关键：先停车，再转弯。否则会边走边转，画出弧线而不是直角
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "$STOP_TWIST"
    sleep 0.2

    # 原地转弯：线速度必须为 0
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
      "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: $TURN_SPEED}}"
    sleep "$TURN_TIME"
done

# 结束后停车，否则海龟会一直转下去
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "$STOP_TWIST"

echo "正方形绘制完成！"