"""ROS-backed regressions: run after sourcing the ROS environment."""

import importlib.util
from pathlib import Path
import unittest

import rclpy
from rclpy.parameter import Parameter

spec = importlib.util.spec_from_file_location(
    'param_example', Path(__file__).parents[1] / 'examples/parameters/param_example.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ParameterTests(unittest.TestCase):
    def setUp(self):
        rclpy.init(args=[])
        self.node = module.MinimalParam()

    def tearDown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()

    def test_batch_rejection_does_not_change_timer_or_parameters(self):
        old_period = self.node.timer.timer_period_ns
        result = self.node.set_parameters_atomically([
            Parameter('update_frequency', value=0.0),
            Parameter('enable_logging', value=False),
        ])
        self.assertFalse(result.successful)
        self.assertEqual(self.node.get_parameter('update_frequency').value, 1.0)
        self.assertTrue(self.node.get_parameter('enable_logging').value)
        self.assertEqual(self.node.timer.timer_period_ns, old_period)

    def test_frequency_applies_after_commit(self):
        result = self.node.set_parameters_atomically([
            Parameter('update_frequency', value=2.0),
        ])
        self.assertTrue(result.successful)
        self.node.timer_callback()
        self.assertEqual(self.node.timer.timer_period_ns, 500_000_000)

    def test_nonfinite_and_out_of_range_frequencies_rejected(self):
        for value in (float('inf'), float('nan'), -1.0, 0.0, 0.01, 1001.0):
            with self.subTest(value=value):
                result = self.node.set_parameters_atomically([
                    Parameter('update_frequency', value=value),
                ])
                self.assertFalse(result.successful)


if __name__ == '__main__':
    unittest.main()
