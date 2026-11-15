import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QThread, QTimer
from PySide6.QtWidgets import QApplication, QListView

from main import JSONTreeWidget, MainWindow, StyledComboBox, TextTaskWorker


class UISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_dropdown_uses_custom_chevron_and_rounded_popup_frame(self):
        combo = StyledComboBox()
        combo.addItems(["Theo dòng", "Theo mục", "Tự động"])
        self.assertIsInstance(combo.view(), QListView)
        self.assertEqual(combo.view().objectName(), "ComboPopupView")
        self.assertIsNotNone(combo._popup_container)
        self.assertEqual(combo._popup_container.objectName(), "ComboPopupContainer")
        combo.close()
        combo.deleteLater()
        self.app.processEvents()

    def test_json_xml_tab_switches_to_text_tool(self):
        window = MainWindow()
        window.show()
        self.app.processEvents()

        self.assertEqual(window.tabs.count(), 6)
        window.tabs.setCurrentIndex(3)
        self.app.processEvents()
        self.assertEqual(window.mode, "text")
        self.assertTrue(window.text_panel.isVisible())
        self.assertFalse(window.drop_area.isVisible())

        window.tabs.setCurrentIndex(0)
        self.app.processEvents()
        self.assertEqual(window.mode, "zip")
        self.assertTrue(window.drop_area.isVisible())
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_json_tree_paginates_large_objects_without_dropping_fields(self):
        tree = JSONTreeWidget()
        tree.resize(600, 400)
        tree.show()
        value = {f"field_{index}": index for index in range(650)}
        tree.set_json(value)
        self.app.processEvents()

        root = tree.topLevelItem(0)
        self.assertEqual(root.childCount(), 301)  # 300 fields + load-more row
        more = root.child(300)
        self.assertTrue(more.data(0, JSONTreeWidget.MORE_ROLE))
        tree._load_more(more, 0)
        self.app.processEvents()
        self.assertEqual(root.childCount(), 601)  # 600 fields + next-page row

        final_page = root.child(600)
        self.assertTrue(final_page.data(0, JSONTreeWidget.MORE_ROLE))
        tree._load_more(final_page, 0)
        self.app.processEvents()

        self.assertEqual(root.childCount(), 650)  # all 650 fields are accessible
        field_names = {
            root.child(index).text(0)
            for index in range(root.childCount())
        }
        self.assertIn("field_649", field_names)
        self.assertIn("field_0", field_names)
        tree.close()
        tree.deleteLater()
        self.app.processEvents()

    def test_json_tree_expands_nested_objects_on_demand(self):
        tree = JSONTreeWidget()
        tree.resize(600, 400)
        tree.show()
        tree.set_json({
            "profile": {"name": "FileForge", "active": True},
            "items": [{"id": 1}, {"id": 2}],
        })
        self.app.processEvents()

        root = tree.topLevelItem(0)
        self.assertEqual(root.childCount(), 2)
        profile = next(
            root.child(index)
            for index in range(root.childCount())
            if root.child(index).text(0) == "profile"
        )
        self.assertEqual(profile.childCount(), 1)  # lazy placeholder
        profile.setExpanded(True)
        self.app.processEvents()
        self.assertEqual(profile.childCount(), 2)
        child_names = {
            profile.child(index).text(0)
            for index in range(profile.childCount())
        }
        self.assertEqual(child_names, {"name", "active"})
        tree.close()
        tree.deleteLater()
        self.app.processEvents()

    def test_input_editor_accepts_150k_characters(self):
        window = MainWindow()
        payload = '{"message":"' + ("x" * 150000) + '"}'
        window.input_editor.setPlainText(payload)
        self.app.processEvents()
        self.assertEqual(len(window.input_editor.toPlainText()), len(payload))
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_model_target_includes_java_kotlin_and_c(self):
        window = MainWindow()
        targets = {
            window.text_model_target.itemData(index)
            for index in range(window.text_model_target.count())
        }
        self.assertTrue({"java", "kotlin", "c"}.issubset(targets))
        self.assertEqual(window.input_editor.objectName(), "CodeEditor")
        self.assertEqual(window.output_editor.objectName(), "CodeEditor")
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_text_tool_shows_only_the_top_operation_toolbar(self):
        window = MainWindow()
        self.app.processEvents()
        self.assertTrue(window.text_pair_tabs.isHidden())
        self.assertFalse(window.text_operation.isHidden())
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_html_output_to_input_uses_clean_html_not_fold_markers(self):
        window = MainWindow()
        clean_html = '<div>\\n  <p>hello</p>\\n</div>'
        window.text_html_mode = True
        window._text_output_plain = clean_html
        window.output_editor.setPlainText('▼ <div>\\n  ▼ <p>hello</p>\\n  </div>')
        self.assertEqual(window._plain_text_result(), clean_html)
        self.assertNotIn('▼', window._plain_text_result())
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_compare_tab_exposes_text_and_json_diff_tools(self):
        window = MainWindow()
        window.show()
        self.app.processEvents()

        self.assertEqual(window.tabs.count(), 5)
        window.tabs.setCurrentIndex(4)
        self.app.processEvents()
        self.assertEqual(window.mode, "compare")
        self.assertTrue(window.compare_panel.isVisible())
        self.assertEqual(window.compare_tabs.count(), 2)
        self.assertEqual(window.json_before["source"].count(), 2)
        self.assertEqual(window.json_after["source"].count(), 2)

        window.compare_tabs.setCurrentIndex(0)
        window.string_before["editor"].setPlainText("old line\nkeep")
        window.string_after["editor"].setPlainText("new line\nkeep")
        window.run_string_compare()
        self.assertIn("Sửa", window.string_diff_summary.text())

        window.compare_tabs.setCurrentIndex(1)
        window.load_json_diff_sample()
        window.run_json_diff()
        self.assertEqual(window.json_diff_table.rowCount(), 3)
        self.assertIn("3 khác biệt", window.json_diff_summary.text())

        window.close()
        window.deleteLater()
        self.app.processEvents()


    def test_curl_tab_parses_sample_and_exposes_copy_action(self):
        window = MainWindow()
        window.show()
        self.app.processEvents()
        self.assertEqual(window.tabs.count(), 6)
        window.tabs.setCurrentIndex(5)
        self.app.processEvents()
        self.assertEqual(window.mode, "curl")
        self.assertTrue(window.curl_panel.isVisible())
        window.curl_input.setPlainText(
            "# REQUEST\\n## METHOD\\nGET\\n## URL\\n"
            "https://example.com/assets/app.css\\n## HEADERS\\n"
            "Accept:text/css,*/*;q=0.1\\nCookie:a=1; b=2"
        )
        window.convert_to_curl()
        output = window.curl_output.toPlainText()
        self.assertIn("--request GET", output)
        self.assertIn("text/css,*/*;q=0.1", output)
        self.assertIn("a=1; b=2", output)
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_text_conversion_runs_in_worker_thread(self):
        source = '{"payload":"' + ("x" * 150000) + '"}'
        worker = TextTaskWorker("format_json", source, "RootModel", "dataclass")
        self.assertIsInstance(worker, QThread)

        loop = QEventLoop()
        results = []
        errors = []

        def on_complete(result):
            results.append(result)
            loop.quit()

        def on_error(message):
            errors.append(message)
            loop.quit()

        worker.completed.connect(on_complete)
        worker.failed.connect(on_error)
        worker.start()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        worker.wait()
        worker.deleteLater()
        self.app.processEvents()

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]["input_json"]["payload"]), 150000)


if __name__ == "__main__":
    unittest.main()
