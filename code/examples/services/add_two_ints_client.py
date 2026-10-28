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

import argparse
import sys

import rclpy
from rclpy.node import Node
from rclpy.utilities import remove_ros_args
from rclpy.executors import ExternalShutdownException
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
        self.req = AddTwoInts.Request()

    def send_request(self, a, b, timeout=10.0):
        """
        Send a request to the add_two_ints service.

        Args:
            a: First integer to add
            b: Second integer to add
        """
        if not self.cli.wait_for_service(timeout_sec=timeout):
            raise TimeoutError('add_two_ints service did not become available')
        self.req.a = a
        self.req.b = b
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future, timeout_sec=timeout)
        if not self.future.done():
            self.cli.remove_pending_request(self.future)
            self.future.cancel()
            raise TimeoutError('add_two_ints response timed out')
        return self.future.result()


def main(args=None):
    """
    Main function to initialize and run the minimal client node.
    """
    parser = argparse.ArgumentParser(description='Call add_two_ints (defaults: 2 + 3)')
    parser.add_argument('numbers', nargs='*', type=int)
    parsed = parser.parse_args(remove_ros_args(args=args)[1:])
    if len(parsed.numbers) not in (0, 2):
        parser.error('provide exactly two integers, or none for defaults')
    a, b = parsed.numbers or (2, 3)
    if any(not -(2**63) <= value < 2**63 for value in (a, b, a + b)):
        parser.error('inputs and their sum must fit in signed 64-bit integers')
    rclpy.init(args=args)
    minimal_client = None
    try:
        minimal_client = MinimalClientAsync()
        response = minimal_client.send_request(a, b)
        minimal_client.get_logger().info(
            'Result of add_two_ints: for %d + %d = %d' % (a, b, response.sum))
    except (KeyboardInterrupt, ExternalShutdownException):
        return 130
    except Exception as e:
        print(f'Service call failed: {e}', file=sys.stderr)
        return 1
    finally:
        if minimal_client is not None:
            minimal_client.destroy_node()
        rclpy.try_shutdown()

    return 0


if __name__ == '__main__':
    sys.exit(main())
