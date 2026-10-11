import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import installer


class TestInstaller(unittest.TestCase):

    def test_default_install_dir(self):
        d = installer.get_default_install_dir()
        self.assertIn("LenovoLOQBacklightCustomizer", d)
        self.assertTrue(os.path.isabs(d))

    def test_get_bundle_dir(self):
        b = installer.get_bundle_dir()
        self.assertTrue(os.path.exists(b))

    @patch("installer.winreg.CreateKey")
    @patch("installer.winreg.SetValueEx")
    @patch("installer.winreg.CloseKey")
    def test_register_in_windows_uninstall(self, mock_close, mock_set, mock_create):
        res = installer.register_in_windows_uninstall(
            install_dir="C:\\test\\dir",
            main_exe="C:\\test\\dir\\app.exe",
            uninstall_exe="C:\\test\\dir\\uninstall.exe",
            icon_path="C:\\test\\dir\\app.ico"
        )
        self.assertTrue(res)
        mock_create.assert_called_once()
        self.assertGreaterEqual(mock_set.call_count, 8)

    @patch("installer.winreg.OpenKey")
    @patch("installer.winreg.SetValueEx")
    @patch("installer.winreg.CloseKey")
    def test_set_startup_registry_enable(self, mock_close, mock_set, mock_open):
        res = installer.set_startup_registry("C:\\test\\dir\\app.exe", enable=True)
        self.assertTrue(res)
        mock_set.assert_called_once()

    @patch("installer.winreg.OpenKey")
    @patch("installer.winreg.DeleteValue")
    @patch("installer.winreg.CloseKey")
    def test_set_startup_registry_disable(self, mock_close, mock_del, mock_open):
        res = installer.set_startup_registry("C:\\test\\dir\\app.exe", enable=False)
        self.assertTrue(res)
        mock_del.assert_called_once()

    @patch("installer.subprocess.run")
    @patch("installer.os.path.exists", return_value=True)
    def test_create_windows_shortcut(self, mock_exists, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = installer.create_windows_shortcut("target.exe", "shortcut.lnk")
        self.assertTrue(res)
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
