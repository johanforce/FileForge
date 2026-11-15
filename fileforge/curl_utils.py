"""Parse copied HTTP request text into a reproducible cURL command."""
from __future__ import annotations

import os
import re
import shlex
import unicodedata
from urllib.parse import urlsplit

_ZERO_WIDTH = re.compile("[\u200b-\u200f\u2060\ufeff]")
_SECTION_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(METHOD|URL|HEADERS|BODY|DATA)"
    r"\s*:?\s*(.*?)\s*(?:\*\*)?\s*$",
    re.I,
)
_HEADER_RE = re.compile(r"^\s*([!#$%&'*+.^_|~0-9A-Za-z-]+)\s*:\s*(.*?)\s*$")


def _clean_text(value: str) -> str:
    """Normalize copied Markdown, escaped punctuation and invisible Unicode spaces."""
    value = value.replace("\ufeff", "")
    value = _ZERO_WIDTH.sub("", value)
    value = "".join(" " if unicodedata.category(char) == "Zs" else char for char in value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")

    # Some copy sources represent each line break as backslash + newline.
    value = re.sub(r"\\[ \t]*\n", "\n", value)
    # Also tolerate a single-line escaped representation: \**HEADER**\**VALUE**
    value = re.sub(
        r"\\(?=\s*\*\*(?:METHOD|URL|HEADERS|BODY|DATA|[A-Za-z0-9-]+\s*:))",
        "\n",
        value,
        flags=re.I,
    )

    # Remove paired Markdown bold delimiters, but retain literal asterisks in values.
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value, flags=re.S)
    # Undo Markdown backslash escapes (e.g. https\\://, www\\.example.com, \\_token).
    value = re.sub(r"\\([^\w\s])", r"\1", value)
    return value.strip()


def _extract_url(value: str) -> str:
    value = value.strip()
    markdown = re.search(r"\[[^\]]*\]\s*\(\s*(https?://[^)\s]+)\s*\)", value)
    if markdown:
        value = markdown.group(1)
    else:
        plain = re.search(r"https?://[^\s)\]]+", value)
        if plain:
            value = plain.group(0)
    return value.strip().rstrip(".,;)")


def _shell_quote(value: str, shell: str) -> str:
    if shell == "powershell":
        # PowerShell single-quoted strings escape a single quote by doubling it.
        return "'" + value.replace("'", "''") + "'"
    return shlex.quote(value)


def build_curl_command(
    method: str,
    url: str,
    headers: list[tuple[str, str]],
    shell: str | None = None,
    body: str | None = None,
) -> str:
    """Build cURL for POSIX shells or PowerShell (not legacy cmd.exe)."""
    if shell is None:
        shell = "powershell" if os.name == "nt" else "posix"
    if shell not in {"posix", "powershell"}:
        raise ValueError("Shell chỉ hỗ trợ posix hoặc powershell.")

    executable = "curl.exe" if shell == "powershell" else "curl"
    quote = lambda item: _shell_quote(item, shell)
    parts = [executable, "--location", "--request", method, quote(url)]
    for name, header_value in headers:
        parts.extend(["--header", quote(f"{name}: {header_value}")])
    if body is not None and body != "":
        parts.extend(["--data-raw", quote(body)])
    return " ".join(parts)


def parse_http_request(value: str, shell: str | None = None) -> dict:
    """Parse Markdown-style request exports and raw HTTP requests."""
    text = _clean_text(value)
    if not text:
        raise ValueError("Hãy dán nội dung HTTP request vào ô đầu vào.")

    method = ""
    url = ""
    headers: list[tuple[str, str]] = []
    body_lines: list[str] = []
    section = None
    pending_header: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        section_match = _SECTION_RE.match(line)
        if section_match:
            new_section = section_match.group(1).upper()
            inline_value = section_match.group(2).strip()
            if pending_header is not None:
                headers.append((pending_header, ""))
                pending_header = None
            section = new_section
            if new_section == "METHOD" and inline_value:
                method = inline_value.split()[0].upper()
            elif new_section == "URL" and inline_value:
                url = _extract_url(inline_value)
            elif new_section in {"BODY", "DATA"} and inline_value:
                body_lines.append(inline_value)
            continue

        if section == "METHOD":
            if not method:
                method = line.split()[0].upper()
        elif section == "URL":
            if not url:
                url = _extract_url(line)
        elif section == "HEADERS":
            header_match = _HEADER_RE.match(line)
            if header_match:
                if pending_header is not None:
                    headers.append((pending_header, ""))
                name, header_value = header_match.groups()
                if header_value:
                    headers.append((name, header_value))
                    pending_header = None
                else:
                    pending_header = name
            elif pending_header is not None:
                headers.append((pending_header, line))
                pending_header = None
            elif line.startswith("#"):
                continue
            # Ignore free text that is not a syntactically valid header.
        elif section in {"BODY", "DATA"}:
            body_lines.append(raw_line)

    if pending_header is not None:
        headers.append((pending_header, ""))

    if not method:
        # Raw request line fallback, e.g. POST /api HTTP/1.1.
        raw_match = re.search(r"(?im)^\s*([A-Z][A-Z0-9!#$%&'*+.^_|~-]*)\s+(\S+)\s+HTTP/\d(?:\.\d)?\s*$", text)
        if raw_match:
            method, target = raw_match.groups()
            host = next((v for k, v in headers if k.lower() == "host"), "")
            if target.startswith(("http://", "https://")):
                url = target
            elif host:
                url = f"https://{host}{target if target.startswith('/') else '/' + target}"

    if not method:
        raise ValueError("Không tìm thấy METHOD. Hãy nhập METHOD: GET/POST hoặc dòng request như GET /path HTTP/1.1.")
    if not re.fullmatch(r"[A-Z][A-Z0-9!#$%&'*+.^_|~-]*", method):
        raise ValueError(f"HTTP method không hợp lệ: {method}")
    if not url:
        raise ValueError("Không tìm thấy URL. Hãy nhập URL đầy đủ bắt đầu bằng http:// hoặc https://.")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL phải bắt đầu bằng http:// hoặc https://.")

    body = "\n".join(body_lines) if body_lines else None
    return {
        "method": method,
        "url": url,
        "headers": headers,
        "body": body,
        "curl": build_curl_command(method, url, headers, shell=shell, body=body),
    }
