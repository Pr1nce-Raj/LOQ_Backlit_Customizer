import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from idle_tracker import get_system_idle_seconds, IdleMonitor

class TestIdleTracker(unittest.TestCase):

    def test_get_system_idle_seconds(self):
        sec = get_system_idle_seconds()
        self.assertIsInstance(sec, float)
        self.assertGreaterEqual(sec, 0.0)

    def test_idle_monitor_lifecycle(self):
        ticks = []
        idles = []
        wakes = []

        monitor = IdleMonitor(
            timeout_seconds=0.3,
            enabled=True,
            on_idle=lambda: idles.append(True),
            on_wake=lambda: wakes.append(True),
            on_tick=lambda s: ticks.append(s),
            poll_interval=0.05
        )

        monitor.start()
        time.sleep(0.2)
        self.assertGreater(len(ticks), 0)

        # Toggle enabled off
        monitor.set_enabled(False)
        self.assertFalse(monitor.enabled)

        # Toggle back on
        monitor.set_enabled(True)
        self.assertTrue(monitor.enabled)

        monitor.stop()
        self.assertFalse(monitor._running)

    def test_idle_monitor_wake(self):
        wakes = []
        monitor = IdleMonitor(
            timeout_seconds=10.0,
            enabled=True,
            on_wake=lambda: wakes.append(True)
        )
        monitor._is_sleeping = True
        self.assertTrue(monitor.is_sleeping())

        monitor.wake()
        self.assertFalse(monitor.is_sleeping())
        self.assertEqual(len(wakes), 1)

    def test_idle_monitor_reentrant_state_reads(self):
        # Verify that on_wake callback can query monitor.is_sleeping() without deadlocking
        states_seen = []
        monitor = IdleMonitor(
            timeout_seconds=10.0,
            enabled=True
        )
        def on_wake_callback():
            states_seen.append(monitor.is_sleeping())

        monitor.on_wake = on_wake_callback
        monitor._is_sleeping = True

        # Test wake()
        monitor.wake()
        self.assertFalse(monitor.is_sleeping())
        self.assertEqual(states_seen, [False])

        # Test set_enabled(False) while sleeping
        states_seen.clear()
        monitor._is_sleeping = True
        monitor.set_enabled(False)
        self.assertFalse(monitor.is_sleeping())
        self.assertEqual(states_seen, [False])

if __name__ == "__main__":
    unittest.main()
