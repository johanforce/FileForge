import unittest

from fileforge.text_utils import process_text


class TextConversionTests(unittest.TestCase):
    def test_json_to_compact_string(self):
        result = process_text("json_to_string", '{"name": "An", "count": 2}')
        self.assertEqual(result["output"], '{"name":"An","count":2}')
        self.assertTrue(result["input_json_valid"])
        self.assertTrue(result["output_json_valid"])

    def test_string_to_json_and_format(self):
        source = '{"name":"An","items":[1,2]}'
        parsed = process_text("string_to_json", source)
        formatted = process_text("format_json", source)
        self.assertIn('\n  "name": "An"', parsed["output"])
        self.assertIn('\n  "items": [', formatted["output"])

    def test_xml_to_compact_string_and_back(self):
        source = '<root><name>FileForge</name><count>2</count></root>'
        compact = process_text("xml_to_string", source)["output"]
        self.assertEqual(compact, source)
        pretty = process_text("string_to_xml", compact)["output"]
        self.assertIn('\n  <name>FileForge</name>', pretty)

    def test_unquotes_json_string_before_parsing_xml(self):
        escaped = '"<root><item>ok</item></root>"'
        result = process_text("string_to_xml", escaped)
        self.assertIn("<root>", result["output"])

    def test_rejects_invalid_json_and_xml(self):
        with self.assertRaises(ValueError):
            process_text("format_json", '{"broken": ')
        with self.assertRaises(Exception):
            process_text("string_to_xml", "<root>")


if __name__ == "__main__":
    unittest.main()
