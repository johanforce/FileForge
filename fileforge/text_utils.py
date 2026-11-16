"""Text conversion operations used by the JSON/XML/HTML toolbox."""
from __future__ import annotations

import copy
import json
import re
import xml.dom.minidom
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any

from fileforge.models import generate_models


OPERATIONS = {
    "json_to_string",
    "string_to_json",
    "format_json",
    "minify_json",
    "act_json_to_xml",
    "act_xml_to_json",
    "format_xml",
    "minify_xml",
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


def _xml_elem_to_dict(elem):
    data = {}
    if elem.attrib:
        data["@attributes"] = dict(elem.attrib)
    children = list(elem)
    if children:
        for child in children:
            value = _xml_elem_to_dict(child)
            if child.tag in data:
                if not isinstance(data[child.tag], list):
                    data[child.tag] = [data[child.tag]]
                data[child.tag].append(value)
            else:
                data[child.tag] = value
        return data
    text = (elem.text or "").strip()
    if data:
        if text:
            data["#text"] = text
        return data
    return text if text else ""


def _dict_to_xml_elem(tag, value):
    elem = ET.Element(tag.replace(" ", "_"))
    if isinstance(value, dict):
        value = copy.deepcopy(value)
        attrs = value.pop("@attributes", {})
        for key, item in attrs.items():
            elem.set(key, str(item))
        text = value.pop("#text", None)
        if text is not None:
            elem.text = str(text)
        for key, item in value.items():
            if isinstance(item, list):
                for child in item:
                    elem.append(_dict_to_xml_elem(key, child))
            else:
                elem.append(_dict_to_xml_elem(key, item))
    elif isinstance(value, list):
        for item in value:
            elem.append(_dict_to_xml_elem(tag, item))
    else:
        elem.text = str(value) if value is not None else ""
    return elem


def _json_to_xml(value: str, indent: int = 2) -> str:
    data = json.loads(value)
    if not isinstance(data, dict) or len(data) != 1:
        data = {"root": data}
    tag = next(iter(data))
    root = _dict_to_xml_elem(tag, data[tag])
    raw = ET.tostring(root, encoding="unicode")
    pretty = xml.dom.minidom.parseString(raw).toprettyxml(indent=" " * indent)
    lines = pretty.splitlines()
    if lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _xml_to_json(value: str, indent: int = 2):
    root = ET.fromstring(value)
    return json.dumps({root.tag: _xml_elem_to_dict(root)}, indent=indent, ensure_ascii=False)


def _strip_xml_whitespace(elem):
    if elem.text is not None and not elem.text.strip():
        elem.text = None
    for child in elem:
        _strip_xml_whitespace(child)
        if child.tail is not None and not child.tail.strip():
            child.tail = None


def _format_xml(value: str, indent: int = 2) -> str:
    root = ET.fromstring(value)
    raw = ET.tostring(root, encoding="unicode")
    pretty = xml.dom.minidom.parseString(raw).toprettyxml(indent=" " * indent)
    lines = pretty.splitlines()
    if lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _minify_xml(value: str) -> str:
    root = ET.fromstring(value)
    _strip_xml_whitespace(root)
    return ET.tostring(root, encoding="unicode")


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



BLOCK_HTML_TAGS = {
    "address", "article", "aside", "blockquote", "body", "caption", "dd",
    "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hr", "html",
    "li", "main", "nav", "ol", "p", "section", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "ul",
}


def _minify_html(value: str) -> str:
    """Remove formatting whitespace while preserving meaningful inline and raw-text content."""
    token_re = re.compile(
        r"(?is)(<(script|style|pre|textarea|code)\\b[^>]*>.*?</\\2\\s*>"
        r"|<!--.*?-->|<![^>]*>|</?[^>]+>)|([^<]+)"
    )
    tokens = [match.group(0) for match in token_re.finditer(value)]
    output: list[str] = []

    def tag_info(token: str):
        match = re.match(r"</?\\s*([\\w:-]+)", token)
        if not match:
            return None, False
        return match.group(1).lower(), token.startswith("</")

    for index, token in enumerate(tokens):
        if token.startswith("<"):
            output.append(token)
            continue

        if not token:
            continue
        if token.isspace():
            previous = next((item for item in reversed(tokens[:index]) if item.startswith("<")), "")
            following = next((item for item in tokens[index + 1:] if item.startswith("<")), "")
            prev_name, _ = tag_info(previous)
            next_name, _ = tag_info(following)
            if (prev_name in BLOCK_HTML_TAGS) or (next_name in BLOCK_HTML_TAGS):
                continue
            if previous and following:
                output.append(" ")
            continue

        # HTML collapses ordinary text whitespace visually; retain a single separator.
        output.append(re.sub(r"[\\t\\r\\n\\f ]+", " ", token))

    return "".join(output).strip()


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
            for text_line in text.splitlines() or [text]:
                stripped = text_line.strip()
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
    """Run JSON, XML or HTML conversion operations."""
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

    if operation in {"format_json", "minify_json", "json_to_string", "string_to_json", "json_to_model", "act_json_to_xml"}:
        if operation == "string_to_json":
            raw = text.strip()
            if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
                raw = json.loads(raw)
            elif len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
                raw = _decode_html_escapes(raw[1:-1])
            data = json.loads(raw)
        else:
            data = json.loads(text)
        result["input_json"] = data
        result["input_json_valid"] = True

        if operation == "format_json":
            result["output"] = json.dumps(data, ensure_ascii=False, indent=indent_size)
            result["output_json"] = data
            result["output_json_valid"] = True
            result["output_kind"] = "json"
        elif operation == "minify_json":
            result["output"] = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            result["output_json"] = data
            result["output_json_valid"] = True
            result["output_kind"] = "json"
        elif operation == "json_to_string":
            inner = json.dumps(data, ensure_ascii=False)
            escaped = (inner.replace("\\", "\\\\").replace('"', '\\"')
                       .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))
            result["output"] = f'"{escaped}"'
        elif operation == "string_to_json":
            result["output"] = json.dumps(data, ensure_ascii=False, indent=indent_size)
            result["output_json"] = data
            result["output_json_valid"] = True
            result["output_kind"] = "json"
        elif operation == "act_json_to_xml":
            result["output"] = _json_to_xml(text, indent_size)
        else:
            result["output"] = generate_models(data, class_name, model_target)

    elif operation == "act_xml_to_json":
        data = json.loads(_xml_to_json(text, indent_size))
        result["output"] = json.dumps(data, ensure_ascii=False, indent=indent_size)
        result["output_json"] = data
        result["output_json_valid"] = True
        result["output_kind"] = "json"

    elif operation == "format_xml":
        result["output"] = _format_xml(text, indent_size)

    elif operation == "minify_xml":
        result["output"] = _minify_xml(text)

    elif operation == "xml_to_string":
        root = ET.fromstring(text)
        result["output"] = ET.tostring(root, encoding="unicode", short_empty_elements=True)

    elif operation == "string_to_xml":
        root = _load_xml_string(text)
        ET.indent(root, space=" " * indent_size)
        result["output"] = ET.tostring(root, encoding="unicode", short_empty_elements=True)

    elif operation == "html_to_string":
        compact = _minify_html(_decode_html_escapes(text))
        escaped = (compact.replace("\\\\", "\\\\\\\\").replace('"', '\\\\"')
                   .replace("\\t", "\\\\t").replace("\\r", "\\\\r")
                   .replace("\\n", "\\\\n"))
        result["output"] = f'"{escaped}"'

    elif operation == "string_to_html":
        html = _unwrap_html_string(text)
        if not re.search(r"<[a-zA-Z!]", html):
            raise ValueError("Không tìm thấy thẻ HTML trong chuỗi.")
        result["output"] = _pretty_html(html, indent_size=indent_size)

    return result
