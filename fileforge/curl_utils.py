"""Parse copied HTTP request text into a reproducible cURL command."""
from __future__ import annotations

import re
import shlex
from urllib.parse import urlsplit

_ZERO_WIDTH = re.compile("[\u200b-\u200f\u2060\ufeff]")
_SECTION = re.compile(r"^\s*#{1,6}\s*(METHOD|URL|HEADERS)\s*:?[ \t]*$", re.I)


def _clean_text(value: str) -> str:
    value = _ZERO_WIDTH.sub("", value)
    value = value.replace("\u00a0", " ").replace("\u202f", " ").replace("\u2009", " ")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", value)
    value = re.sub(r"\\([_*\[\]])", r"\1", value)
    return value.strip()


def _extract_url(value: str) -> str:
    value = value.strip()
    markdown = re.search(r"\[[^\]]*\]\((https?://[^)]+)\)", value)
    if markdown:
        value = markdown.group(1)
    else:
        plain = re.search(r"https?://[^\s)]+", value)
        if plain:
            value = plain.group(0)
    return value.strip().rstrip(".,;)")


def parse_http_request(value: str) -> dict:
    """Return method, URL, ordered headers and a shell-safe cURL command."""
    text = _clean_text(value)
    if not text:
        raise ValueError("Hãy dán nội dung HTTP request vào ô đầu vào.")

    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        match = _SECTION.match(line.strip())
        if match:
            current = match.group(1).upper()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    method = ""
    url = ""
    headers: list[tuple[str, str]] = []

    if sections:
        method = " ".join(" ".join(sections.get("METHOD", [])).split()).upper()
        url = _extract_url("\n".join(sections.get("URL", [])))
        for line in sections.get("HEADERS", []):
            candidate = line.strip()
            if not candidate or candidate.startswith("#"):
                continue
            candidate = re.sub(r"^[-*]\s+", "", candidate)
            if ":" not in candidate:
                continue
            name, header_value = candidate.split(":", 1)
            name = name.strip()
            if name and re.fullmatch(r"[!#$%&'*+.^_|~0-9A-Za-z-]+", name):
                headers.append((name, header_value.strip()))
    else:
        lines = text.splitlines()
        request_index = next((i for i, line in enumerate(lines)
                              if re.match(r"^[A-Z]+\s+\S+\s+HTTP/\d", line.strip(), re.I)), None)
        if request_index is not None:
            parts = lines[request_index].split()
            method, target = parts[0].upper(), parts[1]
            for line in lines[request_index + 1:]:
                if not line.strip():
                    break
                if ":" in line:
                    name, header_value = line.split(":", 1)
                    headers.append((name.strip(), header_value.strip()))
            host = next((v for k, v in headers if k.lower() == "host"), "")
            if target.startswith(("http://", "https://")):
                url = target
            elif host:
                url = f"https://{host}{target if target.startswith('/') else '/' + target}"

    if not method:
        raise ValueError("Không tìm thấy METHOD. Hãy dùng mục ## METHOD: và ghi GET, POST, PUT…")
    if not re.fullmatch(r"[A-Z][A-Z0-9!#$%&'*+.^_|~-]*", method):
        raise ValueError(f"HTTP method không hợp lệ: {method}")
    if not url:
        raise ValueError("Không tìm thấy URL đầy đủ trong mục ## URL.")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL phải bắt đầu bằng http:// hoặc https://.")

    parts = ["curl", "--location", "--request", method, shlex.quote(url)]
    for name, header_value in headers:
        parts.extend(["--header", shlex.quote(f"{name}: {header_value}")])
    return {"method": method, "url": url, "headers": headers, "curl": " ".join(parts)}
