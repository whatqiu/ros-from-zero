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
from rcl_interfaces.msg import SetParametersResult
from rclpy.parameter import Parameter


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
        timer_period = 1.0 / self.get_parameter('update_frequency').value
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
        result = SetParametersResult()

        for param in parameters:
            if param.name == 'my_parameter':
                if isinstance(param.value, str):
                    result.successful = True
                else:
                    result.reason = 'my_parameter must be a string'
                    result.successful = False

            elif param.name == 'update_frequency':
                if isinstance(param.value, (int, float)) and param.value > 0:
                    # Update timer frequency
                    self.timer.destroy()
                    new_timer_period = 1.0 / param.value
                    self.timer = self.create_timer(new_timer_period, self.timer_callback)
                    result.successful = True
                    self.get_logger().info('Update frequency changed to %.1f Hz' % param.value)
                else:
                    result.reason = 'update_frequency must be a positive number'
                    result.successful = False

            elif param.name == 'enable_logging':
                if isinstance(param.value, bool):
                    result.successful = True
                else:
                    result.reason = 'enable_logging must be a boolean'
                    result.successful = False

            else:
                result.successful = False

        return result

    def timer_callback(self):
        """
        Callback function called periodically by the timer.
        """
        my_param = self.get_parameter('my_parameter').value
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

    try:
        minimal_param = MinimalParam()
        rclpy.spin(minimal_param)
    except KeyboardInterrupt:
        minimal_param.get_logger().info('Keyboard interrupt, shutting down')
    except Exception as e:
        minimal_param.get_logger().error(f'Error in main: {e}')
    finally:
        minimal_param.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)