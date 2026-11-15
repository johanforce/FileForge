"""Offline text and structural JSON diff helpers for FileForge."""
from __future__ import annotations

import difflib
import html
import json
import re
from collections import Counter
from typing import Any


def _text_tokens(value: str, mode: str) -> list[str]:
    if mode == "line":
        return value.splitlines(keepends=True)
    if mode == "word":
        return re.findall(r"\s+|\w+|[^\w\s]+", value, flags=re.UNICODE)
    if mode == "character":
        return list(value)
    raise ValueError("Chế độ so sánh văn bản không hợp lệ.")


def _token_key(token: str, mode: str, ignore_case: bool, ignore_whitespace: bool) -> str:
    value = token
    if ignore_whitespace:
        value = re.sub(r"\s+", "", value)
    if ignore_case:
        value = value.casefold()
    return value


def _render_diff_tokens(tokens: list[str], opcodes, side: str) -> str:
    chunks: list[str] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if side == "before":
            selected = tokens[i1:i2] if tag in {"equal", "replace", "delete"} else []
            css = "diff-removed" if tag in {"replace", "delete"} else ""
        else:
            selected = tokens[j1:j2] if tag in {"equal", "replace", "insert"} else []
            css = "diff-added" if tag in {"replace", "insert"} else ""
        if not selected:
            continue
        escaped = html.escape("".join(selected))
        # Preserve line breaks, tabs and spaces in the fixed-width diff view.
        if css:
            chunks.append(f'<span class="{css}">{escaped}</span>')
        else:
            chunks.append(escaped)
    return "".join(chunks)


def compare_text(
    before: str,
    after: str,
    mode: str = "line",
    *,
    ignore_case: bool = False,
    ignore_whitespace: bool = False,
    ignore_blank_lines: bool = False,
) -> dict[str, Any]:
    """Compare two text values and return escaped, ready-to-display HTML."""
    if mode not in {"line", "word", "character"}:
        raise ValueError("Chế độ so sánh phải là line, word hoặc character.")

    left = _text_tokens(before, mode)
    right = _text_tokens(after, mode)

    if ignore_blank_lines and mode == "line":
        left = [token for token in left if token.strip()]
        right = [token for token in right if token.strip()]

    left_keys = [
        _token_key(token, mode, ignore_case, ignore_whitespace)
        for token in left
    ]
    right_keys = [
        _token_key(token, mode, ignore_case, ignore_whitespace)
        for token in right
    ]
    matcher = difflib.SequenceMatcher(None, left_keys, right_keys, autojunk=False)
    opcodes = matcher.get_opcodes()

    added = removed = changed = 0
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "replace":
            changed += max(i2 - i1, j2 - j1)

    return {
        "before_html": _render_diff_tokens(left, opcodes, "before"),
        "after_html": _render_diff_tokens(right, opcodes, "after"),
        "added": added,
        "removed": removed,
        "changed": changed,
        "equal": matcher.get_matching_blocks()[-1].size if matcher.get_matching_blocks() else 0,
    }


_MISSING = object()


def _json_path(parent: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{parent}[{key}]"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return f"{parent}.{key}" if parent != "$" else f"$.{key}"
    return f'{parent}[{json.dumps(key, ensure_ascii=False)}]'


def _display_json(value: Any) -> str:
    if value is _MISSING:
        return "—"
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compare_json_values(
    before: Any,
    after: Any,
    *,
    ignore_array_order: bool = False,
    path: str = "$",
) -> list[dict[str, str]]:
    """Compare parsed JSON structurally; object key order is always ignored."""
    differences: list[dict[str, str]] = []

    def add(kind: str, current_path: str, old: Any, new: Any):
        differences.append({
            "kind": kind,
            "path": current_path,
            "before": _display_json(old),
            "after": _display_json(new),
        })

    def walk(old: Any, new: Any, current_path: str):
        if isinstance(old, dict) and isinstance(new, dict):
            keys = sorted(set(old) | set(new), key=str)
            for key in keys:
                next_path = _json_path(current_path, str(key))
                if key not in old:
                    add("added", next_path, _MISSING, new[key])
                elif key not in new:
                    add("removed", next_path, old[key], _MISSING)
                else:
                    walk(old[key], new[key], next_path)
            return

        if isinstance(old, list) and isinstance(new, list):
            if ignore_array_order:
                old_counts = Counter(_canonical_json(item) for item in old)
                new_counts = Counter(_canonical_json(item) for item in new)
                old_by_key = {_canonical_json(item): item for item in old}
                new_by_key = {_canonical_json(item): item for item in new}
                removed_items = []
                added_items = []
                for key in sorted(old_counts.keys() | new_counts.keys()):
                    delta = old_counts[key] - new_counts[key]
                    if delta > 0:
                        removed_items.extend([old_by_key[key]] * delta)
                    elif delta < 0:
                        added_items.extend([new_by_key[key]] * (-delta))
                for item in removed_items:
                    add("removed", current_path + "[]", item, _MISSING)
                for item in added_items:
                    add("added", current_path + "[]", _MISSING, item)
                return

            max_length = max(len(old), len(new))
            for index in range(max_length):
                next_path = _json_path(current_path, index)
                if index >= len(old):
                    add("added", next_path, _MISSING, new[index])
                elif index >= len(new):
                    add("removed", next_path, old[index], _MISSING)
                else:
                    walk(old[index], new[index], next_path)
            return

        if type(old) is type(new) and old == new:
            return
        add("changed", current_path, old, new)

    walk(before, after, path)
    return differences


def compare_json(
    before_text: str,
    after_text: str,
    *,
    ignore_array_order: bool = False,
) -> dict[str, Any]:
    """Parse and compare JSON texts, with useful line/column errors."""
    try:
        before = json.loads(before_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON bên Trước không hợp lệ (dòng {exc.lineno}, cột {exc.colno}): {exc.msg}"
        ) from exc
    try:
        after = json.loads(after_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON bên Sau không hợp lệ (dòng {exc.lineno}, cột {exc.colno}): {exc.msg}"
        ) from exc

    differences = compare_json_values(
        before, after, ignore_array_order=ignore_array_order
    )
    counts = Counter(item["kind"] for item in differences)
    return {
        "differences": differences,
        "added": counts["added"],
        "removed": counts["removed"],
        "changed": counts["changed"],
        "total": len(differences),
    }


def format_text_diff_report(result: dict[str, Any]) -> str:
    """Return a plain-text report suitable for clipboard copying."""
    rows = []
    for item in result["differences"]:
        if item["kind"] == "added":
            rows.append(f'+ {item["path"]}: {item["after"]}')
        elif item["kind"] == "removed":
            rows.append(f'- {item["path"]}: {item["before"]}')
        else:
            rows.append(
                f'~ {item["path"]}: {item["before"]} → {item["after"]}'
            )
    return "\n".join(rows)
