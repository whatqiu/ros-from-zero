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
from example_interfaces.srv import AddTwoInts


class MinimalService(Node):
    """
    A minimal ROS2 service server that adds two integers.

    This service demonstrates basic ROS2 service functionality by
    providing an add two integers operation.
    """

    def __init__(self):
        super().__init__('minimal_service')

        self.srv = self.create_service(AddTwoInts, 'add_two_ints', self.add_two_ints_callback)
        self.get_logger().info('Minimal service node has been started')

    def add_two_ints_callback(self, request, response):
        """
        Callback function called when a service request is received.

        Args:
            request: The AddTwoInts request containing two integers
            response: The AddTwoInts response to be filled

        Returns:
            The response with the sum of the two integers
        """
        response.sum = request.a + request.b

        self.get_logger().info(
            'Incoming request\na: %d b: %d' % (request.a, request.b))

        self.get_logger().info(
            'sending back response: [sum: %d]' % response.sum)

        return response


def main(args=None):
    """
    Main function to initialize and run the minimal service node.
    """
    rclpy.init(args=args)

    try:
        minimal_service = MinimalService()
        rclpy.spin(minimal_service)
    except KeyboardInterrupt:
        minimal_service.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        minimal_service.get_logger().error(f'Error in main: {e}')
    finally:
        minimal_service.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)