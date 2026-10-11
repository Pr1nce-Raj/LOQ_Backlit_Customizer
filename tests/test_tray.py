import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tray import create_tray_image, SystemTrayManager

class TestTray(unittest.TestCase):

    def test_create_tray_image(self):
        img_active = create_tray_image(width=64, height=64, active=True)
        self.assertEqual(img_active.size, (64, 64))

        img_inactive = create_tray_image(width=32, height=32, active=False)
        self.assertEqual(img_inactive.size, (32, 32))

    def test_tray_menu_structure(self):
        tray = SystemTrayManager(
            on_show_ui=lambda: None,
            on_set_mode=lambda m: None,
            on_toggle_power_saving=lambda: None,
            on_exit=lambda: None,
            get_current_mode=lambda: "Breathing",
            is_power_saving_enabled=lambda: True
        )
        menu = tray._build_menu()
        self.assertIsNotNone(menu)
        # Verify items exist
        self.assertTrue(len(list(menu.items)) > 3)

if __name__ == "__main__":
    unittest.main()
