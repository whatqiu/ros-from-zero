#!/usr/bin/env python3
"""Draw an approximate square using continuous, timed velocity commands."""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class SquarePublisher(Node):
    def __init__(self):
        super().__init__('square_publisher')
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.stage = 0
        self.started = None
        self.finished = False
        self.timer = self.create_timer(0.05, self.tick)

    def tick(self):
        # Wait for discovery before measuring movement time.
        if self.publisher.get_subscription_count() == 0:
            self.started = None
            return
        now = time.monotonic()
        if self.started is None:
            self.started = now
        duration = 1.5 if self.stage % 2 == 0 else math.pi / 2
        if now - self.started >= duration:
            self.stage += 1
            self.started = now
        msg = Twist()
        if self.stage >= 8:
            self.finished = True
        elif self.stage % 2 == 0:
            msg.linear.x = 1.0
        else:
            msg.angular.z = 1.0
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SquarePublisher()
        node.get_logger().info('Waiting for turtlesim; drawing an approximate 1.5 m square')
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            try:
                if rclpy.ok():
                    node.publisher.publish(Twist())
            finally:
                node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
