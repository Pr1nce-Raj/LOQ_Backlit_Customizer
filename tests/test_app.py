import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Lenovo_LOQ_Backlight_Customizer import BacklightApplication

class TestApp(unittest.TestCase):

    @patch("Lenovo_LOQ_Backlight_Customizer.ModernBacklightGUI")
    @patch("Lenovo_LOQ_Backlight_Customizer.SystemTrayManager")
    @patch("Lenovo_LOQ_Backlight_Customizer.LenovoDriver")
    @patch("Lenovo_LOQ_Backlight_Customizer.keyboard")
    def test_save_all_settings_reporting(self, mock_kbd, mock_drv, mock_tray, mock_gui):
        app = BacklightApplication()

        # 1. Normal save succeeds
        with patch("Lenovo_LOQ_Backlight_Customizer.save_config", return_value=True), \
             patch("Lenovo_LOQ_Backlight_Customizer.set_startup_enabled", return_value=True):
            res = app.save_all_settings({"effect": "Breathing", "shortcut": "ctrl+alt+x"})
            self.assertTrue(res["success"])
            self.assertEqual(len(res["errors"]), 0)

        # 2. Config save failure reports error
        with patch("Lenovo_LOQ_Backlight_Customizer.save_config", return_value=False), \
             patch("Lenovo_LOQ_Backlight_Customizer.set_startup_enabled", return_value=True):
            res = app.save_all_settings({"effect": "Breathing"})
            self.assertFalse(res["success"])
            self.assertIn("Failed to write backlight_config.json", res["errors"])

        # 3. Registry startup failure reports error
        with patch("Lenovo_LOQ_Backlight_Customizer.save_config", return_value=True), \
             patch("Lenovo_LOQ_Backlight_Customizer.set_startup_enabled", return_value=False):
            res = app.save_all_settings({"start_with_windows": True})
            self.assertFalse(res["success"])
            self.assertIn("Failed to configure Windows startup registry", res["errors"])

        # 4. Invalid hotkey reports error
        mock_kbd.add_hotkey.side_effect = ValueError("Invalid hotkey syntax")
        with patch("Lenovo_LOQ_Backlight_Customizer.save_config", return_value=True), \
             patch("Lenovo_LOQ_Backlight_Customizer.set_startup_enabled", return_value=True):
            res = app.save_all_settings({"shortcut": "invalid!!hotkey"})
            self.assertFalse(res["success"])
            self.assertTrue(any("Invalid hotkey" in e for e in res["errors"]))
        mock_kbd.add_hotkey.side_effect = None

if __name__ == "__main__":
    unittest.main()
