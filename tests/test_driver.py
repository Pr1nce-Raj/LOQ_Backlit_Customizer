import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from driver import LenovoDriver

class TestDriver(unittest.TestCase):

    def test_mock_driver(self):
        drv = LenovoDriver(mock=True)
        self.assertTrue(drv.is_connected())

        # Test level setting
        self.assertTrue(drv.set_level(0))
        self.assertEqual(drv.get_level(), 0)

        self.assertTrue(drv.set_level(1))
        self.assertEqual(drv.get_level(), 1)

        self.assertTrue(drv.set_level(2))
        self.assertEqual(drv.get_level(), 2)

        # Clamping test
        self.assertTrue(drv.set_level(-10))
        self.assertEqual(drv.get_level(), 0)

        self.assertTrue(drv.set_level(10))
        self.assertEqual(drv.get_level(), 2)

        drv.close()

    def test_real_driver_connection(self):
        # On this Lenovo laptop, real driver should open successfully
        drv = LenovoDriver(mock=False)
        is_conn = drv.is_connected()
        print(f"Real driver connected: {is_conn}")
        if is_conn:
            lvl = drv.get_level()
            self.assertIn(lvl, [0, 1, 2])
            # Restore
            drv.restore_initial()
        drv.close()

    def test_reconnect_does_not_deadlock(self):
        # Driver pointing to non-existent device should fail gracefully without deadlock
        drv = LenovoDriver(driver_path="\\\\.\\NonExistentEnergyDrvMockDevice", mock=False)
        self.assertFalse(drv.is_connected())

        # Calling get_raw_status or set_level when disconnected used to deadlock on self._lock
        # Now it must cleanly return None / False without hanging
        raw = drv.get_raw_status()
        self.assertIsNone(raw)

        ok = drv.set_level(1)
        self.assertFalse(ok)

        drv.close()

if __name__ == "__main__":
    unittest.main()
