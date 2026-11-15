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


def _decode_html_escapes(value: str) -> str:
    """Decode escaped whitespace and quotes into their real characters."""
    out: list[str] = []
    i = 0
    mapping = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "'": "'", "\\": "\\"}
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt in mapping:
                out.append(mapping[nxt])
                i += 2
                continue
        out.append(value[i])
        i += 1
    return "".join(out)


def _unwrap_html_string(value: str) -> str:
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        decoded = json.loads(raw)
        if not isinstance(decoded, str):
            raise ValueError("Chuỗi đầu vào phải chứa nội dung HTML.")
        return decoded
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        raw = raw[1:-1]
    return _decode_html_escapes(raw)


def _pretty_html(value: str, indent_size: int = 2) -> str:
    """Format HTML fragments and break tags with multiple attributes onto lines."""
    token_re = re.compile(
        r"(<!--.*?-->)|(<!DOCTYPE[^>]*>)|(<\s*/\s*[\w:-]+\s*>)"
        r"|(<\s*[\w:-]+(?:\s[^>]*)?\s*/>)"
        r"|(<\s*[\w:-]+(?:\s[^>]*)?>)|([^<]+)",
        re.DOTALL | re.IGNORECASE,
    )
    attr_re = re.compile(
        r"""([\w:-]+)\s*(=)\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|([\w:-]+)""",
        re.DOTALL,
    )
    lines: list[str] = []
    depth = 0
    pad = " " * indent_size

    for match in token_re.finditer(value):
        comment, doctype, close, selfclose, opentag, text = match.groups()
        if comment:
            lines.append(pad * depth + comment.strip())
        elif doctype:
            lines.append(pad * depth + doctype.strip())
        elif close:
            depth = max(0, depth - 1)
            lines.append(pad * depth + close.strip())
        elif selfclose or opentag:
            raw = (selfclose or opentag).strip()
            is_self = selfclose is not None
            inner = raw[1:-2].rstrip() if is_self else raw[1:-1].rstrip()
            tag_match = re.match(r"\s*([\w:-]+)(.*)", inner, re.DOTALL)
            if not tag_match:
                lines.append(pad * depth + raw)
                continue
            tag_name, rest = tag_match.groups()
            attrs = []
            for attr in attr_re.finditer(rest):
                if attr.group(1):
                    attrs.append(f"{attr.group(1)}{attr.group(2)}{attr.group(3)}")
                elif attr.group(4):
                    attrs.append(attr.group(4))
            if len(attrs) >= 2:
                lines.append(pad * depth + f"<{tag_name}")
                lines.extend(pad * (depth + 1) + attr for attr in attrs)
                lines.append(pad * depth + ("/>" if is_self else ">"))
            else:
                lines.append(pad * depth + raw)
            if not is_self and tag_name.lower() not in VOID_HTML_TAGS:
                depth += 1
        elif text:
            stripped = text.strip()
            if stripped:
                lines.append(pad * depth + stripped)
    return "\n".join(lines)



def process_text(
    operation: str,
    text: str,
    class_name: str = "RootModel",
    model_target: str = "dataclass",
    indent_size: int = 2,
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
        result["output"] = _pretty_html(html, indent_size=indent_size)

    return result
