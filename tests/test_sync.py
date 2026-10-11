import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from driver import LenovoDriver
from effects import EffectEngine

class TestCrossSync(unittest.TestCase):

    def test_cross_sync_external_override(self):
        driver = LenovoDriver(mock=True)
        driver.set_level(0)

        overrides = []
        engine = EffectEngine(
            driver=driver,
            mode="Off",
            on_external_override=lambda lvl: overrides.append(lvl)
        )
        engine.start()
        time.sleep(0.15)

        # Simulate user pressing Fn+Space: hardware level becomes 1 externally
        with driver._lock:
            driver.mock_hardware_level = 1
            driver.last_set_timestamp = time.time() - 0.1  # Happened outside app

        # Wait for engine's _wait_for_change to detect it
        time.sleep(0.25)
        engine.stop()
        driver.close()

        # Engine should have caught external level change
        self.assertIn(1, overrides)

if __name__ == "__main__":
    unittest.main()
