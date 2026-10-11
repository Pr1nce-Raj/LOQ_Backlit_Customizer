import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import uninstall


class TestUninstall(unittest.TestCase):

    @patch("uninstall.subprocess.run")
    def test_kill_running_processes(self, mock_run):
        res = uninstall.kill_running_processes()
        self.assertTrue(res)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("taskkill", args)
        self.assertIn("Lenovo_LOQ_Backlight_Customizer.exe", args)

    @patch("uninstall.winreg.OpenKey")
    @patch("uninstall.winreg.DeleteValue")
    @patch("uninstall.winreg.CloseKey")
    def test_remove_run_registry_entry(self, mock_close, mock_del, mock_open):
        res = uninstall.remove_run_registry_entry()
        self.assertTrue(res)
        mock_del.assert_called_once()

    @patch("uninstall.winreg.OpenKey")
    @patch("uninstall.winreg.DeleteKey")
    @patch("uninstall.winreg.CloseKey")
    def test_remove_uninstall_registry_entry(self, mock_close, mock_del, mock_open):
        res = uninstall.remove_uninstall_registry_entry()
        self.assertTrue(res)
        mock_del.assert_called_once()

    def test_remove_install_directory(self):
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("hello")
        self.assertTrue(os.path.exists(temp_dir))

        res = uninstall.remove_install_directory(temp_dir)
        self.assertTrue(res)
        self.assertFalse(os.path.exists(temp_dir))

    @patch("uninstall.kill_running_processes")
    @patch("uninstall.remove_run_registry_entry")
    @patch("uninstall.remove_uninstall_registry_entry")
    @patch("uninstall.remove_shortcuts")
    @patch("uninstall.remove_user_data")
    @patch("uninstall.remove_install_directory")
    @patch("uninstall.os.path.exists", return_value=True)
    def test_perform_uninstall_pipeline(
        self, mock_exists, mock_rm_dir, mock_rm_user, mock_rm_sc, mock_rm_unreg, mock_rm_run, mock_kill
    ):
        res = uninstall.perform_uninstall("C:\\fake\\dir", purge_data=True)
        self.assertTrue(res)
        mock_kill.assert_called_once()
        mock_rm_run.assert_called_once()
        mock_rm_unreg.assert_called_once()
        mock_rm_sc.assert_called_once()
        mock_rm_user.assert_called_once()
        mock_rm_dir.assert_called_once_with("C:\\fake\\dir")

    def test_remove_shortcuts_from_tools_and_desktop(self):
        temp_dir = tempfile.mkdtemp()
        tools_dir = os.path.join(temp_dir, "Tools")
        desktop_dir = os.path.join(temp_dir, "Desktop")
        os.makedirs(tools_dir, exist_ok=True)
        os.makedirs(desktop_dir, exist_ok=True)

        tool_lnk = os.path.join(tools_dir, "Lenovo LOQ Backlight Customizer.lnk")
        uninstall_lnk = os.path.join(tools_dir, "Uninstall Lenovo LOQ Backlight Customizer.lnk")
        desktop_lnk = os.path.join(desktop_dir, "Lenovo LOQ Backlight Customizer.lnk")

        for f in [tool_lnk, uninstall_lnk, desktop_lnk]:
            with open(f, "w") as fp:
                fp.write("dummy")

        with patch.dict(os.environ, {
            "APPDATA": os.path.join(temp_dir, "appdata"),
            "USERPROFILE": temp_dir
        }):
            appdata_tools = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Tools")
            os.makedirs(appdata_tools, exist_ok=True)
            t_lnk = os.path.join(appdata_tools, "Lenovo LOQ Backlight Customizer.lnk")
            with open(t_lnk, "w") as fp:
                fp.write("dummy")

            self.assertTrue(os.path.exists(t_lnk))
            self.assertTrue(os.path.exists(desktop_lnk))

            res = uninstall.remove_shortcuts()
            self.assertTrue(res)
            self.assertFalse(os.path.exists(t_lnk))
            self.assertFalse(os.path.exists(desktop_lnk))

        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
