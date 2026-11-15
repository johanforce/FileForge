import unittest

from fileforge.curl_utils import build_curl_command, parse_http_request


class CurlConversionTests(unittest.TestCase):
    SAMPLE = """**HTTP/1.1GET www . youtube . com**

# REQUEST

## METHOD:

 GET

## URL

[https://www.youtube.com/s/desktop/bb2198ae/cssbin/www-onepick.css](https://www.youtube.com/s/desktop/bb2198ae/cssbin/www-onepick.css)

## HEADERS

Accept:text/css,\\* /\\*;q=0.1

Accept-Encoding:gzip, deflate, br, zstd

Cookie:__Secure-YNID=abc; GPS=1; YSC=xyz

Host:www\\.youtube\\.com

Referer:[https://www.youtube.com/?app=desktop&hl=vi](https://www.youtube.com/?app=desktop\\&hl=vi)

sec-ch-ua:"Not-A.Brand";v="99"; "Google Chrome";v="157"

X-Browser-Validation:abc==
"""

    def test_parses_sample_markdown_and_preserves_headers(self):
        # The escaped asterisks/dots/ampersand emulate Markdown-rendered copy.
        result = parse_http_request(self.SAMPLE)
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["url"], "https://www.youtube.com/s/desktop/bb2198ae/cssbin/www-onepick.css")
        values = dict(result["headers"])
        self.assertEqual(values["Accept"], "text/css,* /*;q=0.1")
        self.assertEqual(values["Cookie"], "__Secure-YNID=abc; GPS=1; YSC=xyz")
        self.assertEqual(values["Host"], "www.youtube.com")
        self.assertEqual(values["Referer"], "https://www.youtube.com/?app=desktop&hl=vi")
        self.assertEqual(values["sec-ch-ua"], '"Not-A.Brand";v="99"; "Google Chrome";v="157"')
        self.assertIn("X-Browser-Validation: abc==", result["curl"])

    def test_preserves_accept_wildcard_without_markdown_emphasis_stripping(self):
        source = "# REQUEST\n## METHOD\nGET\n## URL\nhttps://example.com\n## HEADERS\nAccept:text/css,*/*;q=0.1"
        self.assertEqual(dict(parse_http_request(source)["headers"])["Accept"], "text/css,*/*;q=0.1")

    def test_handles_special_spaces_and_escaped_punctuation(self):
        source = "# REQUEST\n## METHOD\nPOST\n## URL\nhttps://example.com/api\n## HEADERS\nX-Test: a\\_b\\*c\\&d"
        self.assertEqual(dict(parse_http_request(source)["headers"])["X-Test"], "a_b*c&d")

    def test_rejects_missing_url_and_invalid_scheme(self):
        with self.assertRaisesRegex(ValueError, "URL"):
            parse_http_request("# REQUEST\n## METHOD\nGET\n## HEADERS\nAccept: */*")
        with self.assertRaisesRegex(ValueError, "http"):
            parse_http_request("# REQUEST\n## METHOD\nGET\n## URL\nftp://example.com")

    def test_accepts_raw_http_request(self):
        result = parse_http_request("GET /api/items HTTP/1.1\nHost: example.com\nAccept: application/json\n\n")
        self.assertEqual(result["url"], "https://example.com/api/items")
        self.assertIn("--request GET", result["curl"])

    def test_posix_quotes_special_values(self):
        command = build_curl_command("POST", "https://example.com/a?x=1&y=2", [("X-Test", "a'b $x; c")], "posix")
        self.assertIn("'X-Test: a'\"'\"'b $x; c'", command)
        self.assertTrue(command.startswith("curl "))

    def test_powershell_quotes_special_values_and_uses_curl_exe(self):
        command = build_curl_command("POST", "https://example.com/a?x=1&y=2", [("X-Test", "a'b $x; c")], "powershell")
        self.assertTrue(command.startswith("curl.exe "))
        self.assertIn("'X-Test: a''b $x; c'", command)

    def test_rejects_unsupported_shell(self):
        with self.assertRaisesRegex(ValueError, "Shell"):
            build_curl_command("GET", "https://example.com", [], "cmd")


if __name__ == "__main__":
    unittest.main()
