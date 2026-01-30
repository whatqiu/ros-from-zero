#!/bin/bash

# ROS2 小乌龟画正方形脚本
# 使用方法：
# 1. 确保 turtlesim 正在运行
# 2. chmod +x draw_square.sh
# 3. ./draw_square.sh

echo "开始绘制正方形..."

for i in {1..4}
do
    echo "绘制第 $i 条边..."

    # 前进 2 秒
    echo "  前进中..."
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
    sleep 2

    # 转弯 90 度（1.57 弧度）
    echo "  转弯中..."
    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.57}}"
    sleep 1
done

echo "正方形绘制完成！🎉"