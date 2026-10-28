"""Check square timing and command transitions without a GUI."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    'draw_square', Path(__file__).parents[1] / 'examples/turtlesim/draw_square.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SquareTests(unittest.TestCase):
    def test_wait_continuous_publish_turn_and_stop(self):
        # Exercise the callback with a controlled clock and publisher.
        node = Mock(stage=0, started=None, finished=False)
        node.publisher.get_subscription_count.return_value = 0
        module.SquarePublisher.tick(node)
        node.publisher.publish.assert_not_called()
        node.publisher.get_subscription_count.return_value = 1
        with patch.object(module.time, 'monotonic', side_effect=[0.0, 0.5, 1.0, 1.5]):
            for _ in range(4):
                module.SquarePublisher.tick(node)
        commands = [call.args[0] for call in node.publisher.publish.call_args_list]
        self.assertEqual([msg.linear.x for msg in commands], [1.0, 1.0, 1.0, 0.0])
        self.assertEqual(commands[-1].angular.z, 1.0)
        node.stage = 7
        with patch.object(module.time, 'monotonic', return_value=4.0):
            module.SquarePublisher.tick(node)
        self.assertTrue(node.finished)
        stop = node.publisher.publish.call_args.args[0]
        self.assertEqual((stop.linear.x, stop.angular.z), (0.0, 0.0))


if __name__ == '__main__':
    unittest.main()
