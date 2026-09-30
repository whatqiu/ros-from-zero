#!/usr/bin/env python3

# Copyright 2024 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalPublisher(Node):
    """
    A minimal ROS2 publisher that publishes string messages periodically.

    This node demonstrates basic ROS2 publisher functionality with
    periodic message publishing using a timer.
    """

    def __init__(self):
        super().__init__('minimal_publisher')

        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

        self.get_logger().info('Minimal publisher node has been started')

    def timer_callback(self):
        """
        Callback function called periodically by the timer.

        Creates and publishes a String message with a counter.
        """
        msg = String()
        msg.data = 'Hello World: %d' % self.i
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1


def main(args=None):
    """
    Main function to initialize and run the minimal publisher node.
    """
    rclpy.init(args=args)

    # 注意：必须先在 try 外面初始化为 None。
    # 如果写成 "try 里面赋值"，那么当 MinimalPublisher() 构造抛异常时，
    # finally 块里的 minimal_publisher 变量还没被赋值，
    # 会引发 UnboundLocalError，把真正的错误掩盖掉。
    minimal_publisher = None

    try:
        minimal_publisher = MinimalPublisher()
        rclpy.spin(minimal_publisher)
    except KeyboardInterrupt:
        # 用 print 而非 get_logger，因为此时节点可能还没创建成功
        if minimal_publisher is not None:
            minimal_publisher.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        if minimal_publisher is not None:
            minimal_publisher.get_logger().error(f'Error in main: {e}')
        else:
            print(f'Failed to start node: {e}', file=sys.stderr)
    finally:
        if minimal_publisher is not None:
            minimal_publisher.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main(sys.argv)