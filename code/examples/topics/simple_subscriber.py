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


class MinimalSubscriber(Node):
    """
    A minimal ROS2 subscriber that listens to string messages.

    This node demonstrates basic ROS2 subscriber functionality by
    receiving and logging messages from a topic.
    """

    def __init__(self):
        super().__init__('minimal_subscriber')

        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('Minimal subscriber node has been started')

    def listener_callback(self, msg):
        """
        Callback function called when a new message is received.

        Args:
            msg: The String message received from the topic
        """
        self.get_logger().info('I heard: "%s"' % msg.data)


def main(args=None):
    """
    Main function to initialize and run the minimal subscriber node.
    """
    rclpy.init(args=args)

    try:
        minimal_subscriber = MinimalSubscriber()
        rclpy.spin(minimal_subscriber)
    except KeyboardInterrupt:
        minimal_subscriber.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        minimal_subscriber.get_logger().error(f'Error in main: {e}')
    finally:
        minimal_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)