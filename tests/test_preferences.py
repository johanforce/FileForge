import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from fileforge.preferences import PreferencesDialog


class PreferencesDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_preferences_load_and_save(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = str(Path(temp_dir) / "settings.ini")
            settings = QSettings(settings_path, QSettings.Format.IniFormat)
            settings.setValue("preferences/restore_session", False)
            settings.setValue("preferences/remember_last_directory", True)
            settings.setValue("preferences/remember_operation_options", False)
            settings.setValue("preferences/minimize_to_tray", True)
            settings.setValue("preferences/show_notifications", False)
            settings.setValue("preferences/language", "en")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            dialog = PreferencesDialog(settings, tray_available=True)
            self.assertFalse(dialog.restore_session.isChecked())
            self.assertTrue(dialog.remember_last_directory.isChecked())
            self.assertFalse(dialog.remember_operation_options.isChecked())
            self.assertTrue(dialog.minimize_to_tray.isChecked())
            self.assertFalse(dialog.show_notifications.isChecked())
            self.assertEqual(dialog.language_combo.currentData(), "en")

            dialog.restore_session.setChecked(True)
            dialog.remember_last_directory.setChecked(False)
            dialog.remember_operation_options.setChecked(True)
            dialog.minimize_to_tray.setChecked(False)
            dialog.show_notifications.setChecked(True)
            dialog.language_combo.setCurrentIndex(dialog.language_combo.findData("vi"))
            dialog.output_directory.setText(str(output_dir))
            self.assertTrue(dialog.is_output_directory_valid())
            dialog.save_to_settings()

            self.assertTrue(settings.value("preferences/restore_session", type=bool))
            self.assertFalse(
                settings.value("preferences/remember_last_directory", type=bool)
            )
            self.assertTrue(
                settings.value("preferences/remember_operation_options", type=bool)
            )
            self.assertEqual(
                settings.value("paths/default_output_directory"), str(output_dir)
            )
            self.assertFalse(settings.value("preferences/minimize_to_tray", type=bool))
            self.assertTrue(settings.value("preferences/show_notifications", type=bool))
            self.assertEqual(settings.value("preferences/language"), "vi")
            dialog.close()

    def test_tray_options_are_disabled_without_system_tray(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = QSettings(
                str(Path(temp_dir) / "settings.ini"), QSettings.Format.IniFormat
            )
            dialog = PreferencesDialog(settings, tray_available=False)
            self.assertFalse(dialog.minimize_to_tray.isEnabled())
            self.assertFalse(dialog.show_notifications.isEnabled())
            dialog.close()

    def test_invalid_output_directory_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = QSettings(
                str(Path(temp_dir) / "settings.ini"), QSettings.Format.IniFormat
            )
            dialog = PreferencesDialog(settings)
            dialog.output_directory.setText(str(Path(temp_dir) / "missing"))
            self.assertFalse(dialog.is_output_directory_valid())
            self.assertEqual(settings.value("paths/default_output_directory"), None)
            dialog.close()

    def test_empty_output_directory_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = QSettings(
                str(Path(temp_dir) / "settings.ini"), QSettings.Format.IniFormat
            )
            dialog = PreferencesDialog(settings)
            dialog.output_directory.clear()
            self.assertTrue(dialog.is_output_directory_valid())
            dialog.close()


if __name__ == "__main__":
    unittest.main()
