"""Text conversion operations used by the JSON/XML toolbox."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any

from fileforge.models import generate_models


OPERATIONS = {
    "json_to_string",
    "string_to_json",
    "format_json",
    "xml_to_string",
    "string_to_xml",
    "json_to_model",
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


def process_text(
    operation: str,
    text: str,
    class_name: str = "RootModel",
    model_target: str = "dataclass",
) -> dict[str, Any]:
    """Perform a single JSON/XML action and return data for the UI."""
    if operation not in OPERATIONS:
        raise ValueError(f"Tác vụ không được hỗ trợ: {operation}")
    if not text.strip():
        raise ValueError("Hãy nhập dữ liệu trước khi thực hiện.")

    result: dict[str, Any] = {
        "output": "",
        "input_json": None,
        "output_json": None,
        "output_kind": "text",
    }

    if operation in {"json_to_string", "string_to_json", "format_json", "json_to_model"}:
        data = json.loads(text)
        result["input_json"] = data

        if operation == "json_to_string":
            result["output"] = json.dumps(
                data, ensure_ascii=False, separators=(",", ":")
            )
            result["output_json"] = data
            result["output_kind"] = "json"
        elif operation == "string_to_json":
            result["output"] = json.dumps(data, ensure_ascii=False, indent=2)
            result["output_json"] = data
            result["output_kind"] = "json"
        elif operation == "format_json":
            result["output"] = json.dumps(data, ensure_ascii=False, indent=2)
            result["output_json"] = data
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

    return result
