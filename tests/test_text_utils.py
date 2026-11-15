import unittest

from fileforge.text_utils import process_text


class TextConversionTests(unittest.TestCase):
    def test_json_to_quoted_string_and_back(self):
        source = '{"name": "An", "count": 2}'
        encoded = process_text("json_to_string", source)["output"]
        self.assertTrue(encoded.startswith('"') and encoded.endswith('"'))
        decoded = process_text("string_to_json", encoded)
        self.assertEqual(decoded["output_json"], {"name": "An", "count": 2})
        self.assertIn('\n  "name"', decoded["output"])

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

    def test_html_to_quoted_string_and_back(self):
        source = '<div class="greeting">Hello\\n<span>FileForge</span></div>'
        encoded = process_text("html_to_string", source)["output"]
        self.assertEqual(encoded, '"<div class=\\"greeting\\">Hello\\\\n<span>FileForge</span></div>"')

        decoded = process_text("string_to_html", encoded)["output"]
        self.assertIn('<div class="greeting">', decoded)
        self.assertIn('  <span>', decoded)
        self.assertIn('    FileForge', decoded)
        self.assertIn('  </span>', decoded)
        self.assertIn('</div>', decoded)

    def test_json_xml_and_xml_format_minify_pairs(self):
        source = '{"root":{"@attributes":{"id":"x"},"name":"FileForge","item":["a","b"]}}'
        xml = process_text("act_json_to_xml", source, indent_size=4)["output"]
        self.assertIn('id="x"', xml)
        self.assertIn('    <name>FileForge</name>', xml)
        converted = process_text("act_xml_to_json", xml)
        self.assertEqual(converted["output_json"]["root"]["item"], ["a", "b"])

        pretty = process_text("format_xml", "<root><a>1</a><b>2</b></root>", indent_size=4)["output"]
        self.assertIn('    <a>1</a>', pretty)
        compact = process_text("minify_xml", pretty)["output"]
        self.assertEqual(compact, "<root><a>1</a><b>2</b></root>")

    def test_string_to_html_decodes_newlines_tabs_and_indent_choice(self):
        encoded = '"<div>first\\nsecond\\tvalue</div>"'
        output = process_text("string_to_html", encoded, indent_size=4)["output"]
        self.assertIn("    first", output)
        self.assertIn("    second", output)
        self.assertIn("second\tvalue", output)
        self.assertNotIn("\\n", output)

    def test_string_to_html_accepts_raw_html_and_rejects_non_html(self):
        raw = process_text("string_to_html", "<main><p>Hi</p></main>")["output"]
        self.assertIn("<main>", raw)
        self.assertIn("  <p>", raw)
        with self.assertRaisesRegex(ValueError, "Không tìm thấy thẻ HTML"):
            process_text("string_to_html", "just a string")

    def test_handles_one_hundred_fifty_thousand_character_value(self):
        payload = '{"message":"' + ("x" * 150000) + '"}'
        formatted = process_text("format_json", payload)
        encoded = process_text("json_to_string", formatted["output"])
        decoded = process_text("string_to_json", encoded["output"])
        self.assertEqual(len(formatted["input_json"]["message"]), 150000)
        self.assertEqual(len(formatted["output_json"]["message"]), 150000)
        self.assertEqual(len(decoded["output_json"]["message"]), 150000)
        self.assertEqual(len(encoded["output"]), 150016)

    def test_rejects_invalid_json_and_xml(self):
        with self.assertRaises(ValueError):
            process_text("format_json", '{"broken": ')
        with self.assertRaises(Exception):
            process_text("string_to_xml", "<root>")


if __name__ == "__main__":
    unittest.main()
