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

from time import sleep

import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class MinimalClientAsync(Node):
    """
    A minimal ROS2 service client that calls the add two integers service.

    This client demonstrates basic ROS2 service client functionality by
    making asynchronous service calls.
    """

    def __init__(self):
        super().__init__('minimal_client_async')
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = AddTwoInts.Request()

    def send_request(self, a, b):
        """
        Send a request to the add_two_ints service.

        Args:
            a: First integer to add
            b: Second integer to add
        """
        self.req.a = a
        self.req.b = b
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()


def main(args=None):
    """
    Main function to initialize and run the minimal client node.
    """
    rclpy.init(args=args)

    minimal_client = MinimalClientAsync()

    # Use default values if no arguments provided
    if len(sys.argv) > 2:
        try:
            a = int(sys.argv[1])
            b = int(sys.argv[2])
        except ValueError:
            minimal_client.get_logger().error('Please provide valid integers')
            return 1
    else:
        a = 2
        b = 3
        minimal_client.get_logger().info('Using default values: a=2, b=3')

    try:
        response = minimal_client.send_request(a, b)
        minimal_client.get_logger().info(
            'Result of add_two_ints: for %d + %d = %d' % (a, b, response.sum))
    except Exception as e:
        minimal_client.get_logger().error(f'Service call failed: {e}')
        return 1
    finally:
        minimal_client.destroy_node()
        rclpy.shutdown()

    return 0


if __name__ == '__main__':
    sys.exit(main())