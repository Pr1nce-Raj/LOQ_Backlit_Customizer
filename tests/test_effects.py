import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from driver import LenovoDriver
from effects import EffectEngine, ALL_MODES

class TestEffects(unittest.TestCase):

    def test_all_modes_exist(self):
        expected = ["Breathing", "Pulse", "Wave", "Police", "SOS", "Blink x3", "Solid High", "Solid Low", "Off"]
        for m in expected:
            self.assertIn(m, ALL_MODES)
        # Ensure Strobe was completely removed as requested
        self.assertNotIn("Strobe", ALL_MODES)

    def test_effect_engine_execution(self):
        driver = LenovoDriver(mock=True)
        levels_seen = []
        override_events = []

        engine = EffectEngine(
            driver=driver,
            mode="Breathing",
            speed=2.5, # Fast speed for unit testing
            on_level_changed=lambda lvl: levels_seen.append(lvl),
            on_external_override=lambda lvl: override_events.append(lvl)
        )

        engine.start()
        time.sleep(0.3)
        self.assertGreater(len(levels_seen), 0)

        # Test mode switching
        engine.set_mode("Wave")
        self.assertEqual(engine.get_mode(), "Wave")
        time.sleep(0.2)

        # Test pause (power saving)
        engine.set_paused(True)
        self.assertTrue(engine.is_paused())
        self.assertEqual(driver.get_level(), 0)

        # Test resume
        engine.set_paused(False)
        self.assertFalse(engine.is_paused())
        time.sleep(0.2)

        # Test stop
        engine.stop()
        self.assertFalse(engine._running)
        driver.close()

    def test_static_modes_do_not_spam_driver(self):
        driver = LenovoDriver(mock=True)
        set_level_calls = []
        original_set = driver.set_level

        def counting_set_level(lvl):
            set_level_calls.append(lvl)
            return original_set(lvl)

        driver.set_level = counting_set_level

        engine = EffectEngine(
            driver=driver,
            mode="Solid High"
        )
        engine.start()
        time.sleep(0.3)
        # Should only have been called once on entry, not 30 times
        self.assertLessEqual(len(set_level_calls), 2)

        set_level_calls.clear()
        engine.set_mode("Solid Low")
        time.sleep(0.3)
        self.assertLessEqual(len(set_level_calls), 2)

        engine.stop()
        driver.close()

if __name__ == "__main__":
    unittest.main()
