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
from geometry_msgs.msg import Twist


class TurtlePublisher(Node):
    """
    A simple ROS2 publisher that makes the turtle draw circles.

    This node publishes velocity commands to the /turtle1/cmd_vel topic.
    """

    def __init__(self):
        super().__init__('turtle_publisher')

        # Create publisher with QoS profile
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # Create timer to publish messages periodically
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0

        self.get_logger().info('Turtle publisher node has been started')

    def timer_callback(self):
        """
        Callback function called periodically by the timer.
        Publishes velocity commands to make the turtle move in circles.
        """
        msg = Twist()

        # Set linear and angular velocities for circular motion
        msg.linear.x = 2.0
        msg.angular.z = 1.0

        # Publish the message
        self.publisher_.publish(msg)

        # Log the published message
        self.get_logger().debug(f'Publishing: linear.x={msg.linear.x}, angular.z={msg.angular.z}')

        self.count += 1


def main(args=None):
    """
    Main function to initialize and run the turtle publisher node.
    """
    rclpy.init(args=args)

    try:
        turtle_publisher = TurtlePublisher()

        # Spin the node so callbacks are called
        rclpy.spin(turtle_publisher)

    except KeyboardInterrupt:
        turtle_publisher.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        turtle_publisher.get_logger().error(f'Error in main: {e}')
    finally:
        # Clean up
        turtle_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)