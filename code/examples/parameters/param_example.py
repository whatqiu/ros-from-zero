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

import math
import sys

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult


class MinimalParam(Node):
    """
    A minimal ROS2 node that demonstrates parameter functionality.

    This node shows how to declare parameters, set parameter callbacks,
    and use parameter values in node behavior.
    """

    def __init__(self):
        super().__init__('minimal_param_node')

        # Declare parameters with default values
        self.declare_parameter('my_parameter', 'world')
        self.declare_parameter('update_frequency', 1.0)
        self.declare_parameter('enable_logging', True)

        # Create timer based on frequency parameter
        frequency = self.get_parameter('update_frequency').value
        if not math.isfinite(frequency) or not 0.1 <= frequency <= 1000.0:
            raise ValueError('update_frequency must be finite and between 0.1 and 1000.0 Hz')
        timer_period = 1.0 / frequency
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0

        # Add parameter callback
        self.add_on_set_parameters_callback(self.parameter_callback)

        self.get_logger().info('Minimal parameter node has been started')
        self.get_logger().info('Current parameters:')
        self.get_logger().info('  my_parameter: %s' % self.get_parameter('my_parameter').value)
        self.get_logger().info('  update_frequency: %.1f Hz' % self.get_parameter('update_frequency').value)
        self.get_logger().info('  enable_logging: %s' % self.get_parameter('enable_logging').value)

    def parameter_callback(self, parameters):
        """
        Callback function called when parameters are being set.

        Args:
            parameters: List of Parameter objects to be set

        Returns:
            SetParametersResult indicating success or failure
        """
        # Only validate here: a later callback may still reject the transaction.
        for param in parameters:
            if param.name == 'update_frequency':
                if (type(param.value) is not float
                        or not math.isfinite(param.value) or not 0.1 <= param.value <= 1000.0):
                    return SetParametersResult(
                        successful=False,
                        reason='update_frequency must be a finite double between 0.1 and 1000.0 Hz')
            elif param.name == 'my_parameter':
                if not isinstance(param.value, str):
                    return SetParametersResult(successful=False, reason='my_parameter must be a string')
            elif param.name == 'enable_logging':
                if not isinstance(param.value, bool):
                    return SetParametersResult(successful=False, reason='enable_logging must be a boolean')
        return SetParametersResult(successful=True)

    def timer_callback(self):
        """
        Callback function called periodically by the timer.
        """
        my_param = self.get_parameter('my_parameter').value
        # Read the committed value on the next tick; compatible with Humble/Jazzy.
        period_ns = round(1e9 / self.get_parameter('update_frequency').value)
        if self.timer.timer_period_ns != period_ns:
            self.timer.timer_period_ns = period_ns
            self.timer.reset()
        enable_logging = self.get_parameter('enable_logging').value

        if enable_logging:
            self.get_logger().info('Hello %s! Count: %d' % (my_param, self.count))
        else:
            self.get_logger().debug('Timer callback triggered (logging disabled)')

        self.count += 1


def main(args=None):
    """
    Main function to initialize and run the minimal parameter node.
    """
    rclpy.init(args=args)

    # 先在 try 外初始化，避免构造失败时 finally 里出现 UnboundLocalError
    minimal_param = None

    try:
        minimal_param = MinimalParam()
        rclpy.spin(minimal_param)
    except KeyboardInterrupt:
        if minimal_param is not None:
            minimal_param.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        if minimal_param is not None:
            minimal_param.get_logger().error(f'Error in main: {e}')
        else:
            print(f'Failed to start node: {e}', file=sys.stderr)
    finally:
        if minimal_param is not None:
            minimal_param.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main(sys.argv)
