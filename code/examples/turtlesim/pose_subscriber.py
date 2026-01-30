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
from turtlesim.msg import Pose


class PoseSubscriber(Node):
    """
    A simple ROS2 subscriber that listens to turtle pose information.

    This node subscribes to the /turtle1/pose topic and logs turtle position data.
    """

    def __init__(self):
        super().__init__('pose_subscriber')

        # Create subscriber with QoS profile
        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('Pose subscriber node has been started')

    def listener_callback(self, msg):
        """
        Callback function called when a new pose message is received.

        Args:
            msg: The Pose message containing turtle position and orientation
        """
        # Log turtle position information
        self.get_logger().info(
            f'Turtle position: x={msg.x:.2f}, y={msg.y:.2f}, '
            f'theta={msg.theta:.2f}, linear_velocity={msg.linear_velocity:.2f}, '
            f'angular_velocity={msg.angular_velocity:.2f}'
        )


def main(args=None):
    """
    Main function to initialize and run the pose subscriber node.
    """
    rclpy.init(args=args)

    try:
        pose_subscriber = PoseSubscriber()

        # Spin the node so callbacks are called
        rclpy.spin(pose_subscriber)

    except KeyboardInterrupt:
        pose_subscriber.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        pose_subscriber.get_logger().error(f'Error in main: {e}')
    finally:
        # Clean up
        pose_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)