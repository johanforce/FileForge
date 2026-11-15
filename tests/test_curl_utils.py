import unittest

from fileforge.curl_utils import parse_http_request


class CurlConversionTests(unittest.TestCase):
    def test_parses_markdown_request_with_headers_and_cookie(self):
        source = """**HTTP/1.1GET www.youtube.com**

# REQUEST

## METHOD:

 GET

## URL

[https://www.youtube.com/s/desktop/style.css](https://www.youtube.com/s/desktop/style.css)

## HEADERS

Accept:text/css,*/*;q=0.1

Cookie:__Secure-YNID=abc; GPS=1; YSC=xyz

User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64)
"""
        result = parse_http_request(source)
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["url"], "https://www.youtube.com/s/desktop/style.css")
        self.assertEqual(result["headers"][0], ("Accept", "text/css,*/*;q=0.1"))
        self.assertEqual(result["headers"][1], ("Cookie", "__Secure-YNID=abc; GPS=1; YSC=xyz"))
        self.assertIn("--request GET", result["curl"])
        self.assertIn("--header", result["curl"])
        self.assertIn("GPS=1", result["curl"])

    def test_accepts_special_spaces_and_markdown_escaped_underscores(self):
        source = """# REQUEST
## METHOD
POST
## URL
https://example.com/api
## HEADERS
X-Test: value
X-Token: abc\\_def
"""
        result = parse_http_request(source)
        self.assertEqual(result["headers"], [("X-Test", "value"), ("X-Token", "abc_def")])

    def test_rejects_missing_url(self):
        with self.assertRaisesRegex(ValueError, "URL"):
            parse_http_request("# REQUEST\n## METHOD\nGET\n## HEADERS\nAccept: */*")

    def test_accepts_raw_http_request(self):
        result = parse_http_request("GET /api/items HTTP/1.1\nHost: example.com\nAccept: application/json\n\n")
        self.assertEqual(result["url"], "https://example.com/api/items")
        self.assertIn("--request GET", result["curl"])


if __name__ == "__main__":
    unittest.main()
