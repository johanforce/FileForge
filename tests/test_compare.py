import unittest

from fileforge.compare import compare_json, compare_json_values, compare_text


class TextDiffTests(unittest.TestCase):
    def test_line_diff_highlights_added_and_removed_lines(self):
        result = compare_text("alpha\nbeta\n", "alpha\ngamma\n", "line")
        self.assertIn('class="diff-removed"', result["before_html"])
        self.assertIn('class="diff-added"', result["after_html"])
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["added"], 1)

    def test_word_and_character_diff_find_small_changes(self):
        word = compare_text("the quick fox", "the quiet fox", "word")
        char = compare_text("colour", "color", "character")
        self.assertIn("quick", word["before_html"])
        self.assertIn("quiet", word["after_html"])
        self.assertGreater(word["changed"], 0)
        self.assertGreater(char["changed"], 0)

    def test_ignore_case_whitespace_and_blank_lines(self):
        result = compare_text(
            "Hello  World\n\n",
            "hello World\n",
            "line",
            ignore_case=True,
            ignore_whitespace=True,
            ignore_blank_lines=True,
        )
        self.assertEqual(result["added"], 0)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["changed"], 0)


class JsonDiffTests(unittest.TestCase):
    def test_object_key_order_and_formatting_do_not_count_as_changes(self):
        result = compare_json(
            '{"name":"FileForge","meta":{"active":true,"v":1}}',
            '{ "meta": { "v": 1, "active": true }, "name": "FileForge" }',
        )
        self.assertEqual(result["total"], 0)

    def test_reports_added_removed_and_changed_paths(self):
        result = compare_json(
            '{"user":{"name":"An","age":20},"obsolete":true}',
            '{"user":{"name":"Binh","age":20},"active":true}',
        )
        rows = {item["path"]: item["kind"] for item in result["differences"]}
        self.assertEqual(rows["$.user.name"], "changed")
        self.assertEqual(rows["$.active"], "added")
        self.assertEqual(rows["$.obsolete"], "removed")
        self.assertEqual(result["added"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["changed"], 1)

    def test_arrays_compare_by_position_or_ignore_order(self):
        before = [1, 2, 2, 3]
        after = [3, 2, 1, 2]
        positional = compare_json_values(before, after)
        unordered = compare_json_values(before, after, ignore_array_order=True)
        self.assertGreater(len(positional), 0)
        self.assertEqual(unordered, [])

        duplicate_change = compare_json_values(
            [1, 2, 2], [1, 2, 3], ignore_array_order=True
        )
        self.assertEqual(
            [item["kind"] for item in duplicate_change], ["removed", "added"]
        )

    def test_array_nested_paths_and_unusual_object_keys(self):
        result = compare_json_values(
            {"items": [{"odd key": 1}]},
            {"items": [{"odd key": 2}]},
        )
        self.assertEqual(result[0]["path"], '$.items[0]["odd key"]')

    def test_invalid_json_reports_line_and_column(self):
        with self.assertRaisesRegex(
            ValueError, r"JSON bên Trước không hợp lệ \(dòng 2, cột"
        ):
            compare_json('{"x":\n}', '{"x":1}')


if __name__ == "__main__":
    unittest.main()
