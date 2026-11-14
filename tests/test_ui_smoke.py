import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QThread, QTimer
from PySide6.QtWidgets import QApplication

from main import JSONTreeWidget, MainWindow, TextTaskWorker


class UISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_json_xml_tab_switches_to_text_tool(self):
        window = MainWindow()
        window.show()
        self.app.processEvents()

        self.assertEqual(window.tabs.count(), 4)
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
        self.assertEqual(root.child(649).text(0), "field_649")
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
