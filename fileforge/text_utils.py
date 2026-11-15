"""Text conversion operations used by the JSON/XML/HTML toolbox."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any

from fileforge.models import generate_models


OPERATIONS = {
    "json_to_string",
    "string_to_json",
    "format_json",
    "xml_to_string",
    "string_to_xml",
    "html_to_string",
    "string_to_html",
    "json_to_model",
}

VOID_HTML_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


def _load_xml_string(value: str) -> ET.Element:
    raw = value.strip()
    if raw.startswith('"'):
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, str):
                raw = decoded
        except json.JSONDecodeError:
            pass
    if not raw:
        raise ValueError("Chưa có nội dung XML.")
    return ET.fromstring(raw)


def _unwrap_html_string(value: str) -> str:
    """Decode a JSON-quoted HTML string, or accept raw HTML unchanged."""
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        decoded = json.loads(raw)
        if not isinstance(decoded, str):
            raise ValueError("Chuỗi đầu vào phải chứa nội dung HTML.")
        return decoded
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        # Accept the single-quoted form used by some editors.
        inner = raw[1:-1]
        return inner.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\'", "'").replace("\\\\", "\\")
    return raw


class _HTMLPrettyPrinter(HTMLParser):
    """Small fragment formatter; it does not attempt browser DOM correction."""

    def __init__(self, indent_size: int = 2):
        super().__init__(convert_charrefs=False)
        self.indent_size = indent_size
        self.depth = 0
        self.lines: list[str] = []

    def _line(self, value: str, depth: int | None = None):
        level = self.depth if depth is None else depth
        self.lines.append(" " * (self.indent_size * max(level, 0)) + value)

    def handle_starttag(self, tag: str, attrs):
        raw = self.get_starttag_text() or f"<{tag}>"
        self._line(raw)
        if tag.lower() not in VOID_HTML_TAGS:
            self.depth += 1

    def handle_startendtag(self, tag: str, attrs):
        self._line(self.get_starttag_text() or f"<{tag} />")

    def handle_endtag(self, tag: str):
        if tag.lower() not in VOID_HTML_TAGS:
            self.depth = max(0, self.depth - 1)
        self._line(f"</{tag}>")

    def handle_data(self, data: str):
        value = data.strip()
        if value:
            self._line(value)

    def handle_entityref(self, name: str):
        self._line(f"&{name};")

    def handle_charref(self, name: str):
        self._line(f"&#{name};")

    def handle_comment(self, data: str):
        self._line(f"<!--{data}-->")

    def handle_decl(self, decl: str):
        self._line(f"<!{decl}>")

    def unknown_decl(self, data: str):
        self._line(f"<![{data}]>")


def _pretty_html(value: str, indent_size: int = 2) -> str:
    parser = _HTMLPrettyPrinter(indent_size)
    parser.feed(value)
    parser.close()
    return "\n".join(parser.lines)


def process_text(
    operation: str,
    text: str,
    class_name: str = "RootModel",
    model_target: str = "dataclass",
) -> dict[str, Any]:
    """Perform a single JSON/XML/HTML action and return data for the UI."""
    if operation not in OPERATIONS:
        raise ValueError(f"Tác vụ không được hỗ trợ: {operation}")
    if not text.strip():
        raise ValueError("Hãy nhập dữ liệu trước khi thực hiện.")

    result: dict[str, Any] = {
        "output": "",
        "input_json": None,
        "output_json": None,
        "output_kind": "text",
        "input_json_valid": False,
        "output_json_valid": False,
    }

    if operation in {"json_to_string", "string_to_json", "format_json", "json_to_model"}:
        data = json.loads(text)
        result["input_json"] = data
        result["input_json_valid"] = True

        if operation == "json_to_string":
            result["output"] = json.dumps(
                data, ensure_ascii=False, separators=(",", ":")
            )
            result["output_json"] = data
            result["output_json_valid"] = True
            result["output_kind"] = "json"
        elif operation in {"string_to_json", "format_json"}:
            result["output"] = json.dumps(data, ensure_ascii=False, indent=2)
            result["output_json"] = data
            result["output_json_valid"] = True
            result["output_kind"] = "json"
        else:
            result["output"] = generate_models(data, class_name, model_target)

    elif operation == "xml_to_string":
        root = ET.fromstring(text)
        result["output"] = ET.tostring(
            root, encoding="unicode", short_empty_elements=True
        )

    elif operation == "string_to_xml":
        root = _load_xml_string(text)
        ET.indent(root, space="  ")
        result["output"] = ET.tostring(
            root, encoding="unicode", short_empty_elements=True
        )

    elif operation == "html_to_string":
        escaped = (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        result["output"] = f'"{escaped}"'

    elif operation == "string_to_html":
        html = _unwrap_html_string(text)
        if not re.search(r"<[a-zA-Z!]", html):
            raise ValueError("Không tìm thấy thẻ HTML trong chuỗi.")
        result["output"] = _pretty_html(html, indent_size=2)

    return result
