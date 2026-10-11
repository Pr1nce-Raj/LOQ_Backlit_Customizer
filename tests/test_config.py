import unittest
import os
import tempfile
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

class TestConfig(unittest.TestCase):

    def test_default_config_fields(self):
        cfg = config.DEFAULT_CONFIG
        self.assertIn("shortcut", cfg)
        self.assertIn("effect", cfg)
        self.assertIn("power_saving_enabled", cfg)
        self.assertIn("idle_timeout_seconds", cfg)
        self.assertEqual(cfg["idle_timeout_seconds"], 30)

    def test_load_and_save_config(self):
        orig_path = config.CONFIG_PATH
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_path = tf.name

        try:
            config.CONFIG_PATH = temp_path
            test_data = {
                "shortcut": "ctrl+alt+k",
                "effect": "Wave",
                "speed": 1.5,
                "power_saving_enabled": False,
                "idle_timeout_seconds": 45
            }
            res = config.save_config(test_data)
            self.assertTrue(res)

            loaded = config.load_config()
            self.assertEqual(loaded["shortcut"], "ctrl+alt+k")
            self.assertEqual(loaded["effect"], "Wave")
            self.assertEqual(loaded["speed"], 1.5)
            self.assertFalse(loaded["power_saving_enabled"])
            self.assertEqual(loaded["idle_timeout_seconds"], 45)
            # Check default fallback for unmentioned keys
            self.assertTrue("minimize_to_tray" in loaded)
        finally:
            config.CONFIG_PATH = orig_path
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_config_auto_creates_file_if_missing(self):
        orig_path = config.CONFIG_PATH
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "test_backlight_config.json")
        try:
            config.CONFIG_PATH = temp_path
            self.assertFalse(os.path.exists(temp_path))
            loaded = config.load_config()
            self.assertEqual(loaded["effect"], "Breathing")
            self.assertTrue(os.path.exists(temp_path))
        finally:
            config.CONFIG_PATH = orig_path
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    def test_save_config_returns_false_on_invalid_path(self):
        orig_path = config.CONFIG_PATH
        try:
            # Illegal path on Windows
            config.CONFIG_PATH = "Z:\\NonExistentDrive\\some_dir\\config.json"
            res = config.save_config({"test": 123})
            self.assertFalse(res)
        finally:
            config.CONFIG_PATH = orig_path

if __name__ == "__main__":
    unittest.main()
