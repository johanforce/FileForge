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
    r"\s*:\s*(.*?)\s*(?:\*\*)?\s*$",
    re.I,
)
_SECTION_BARE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(METHOD|URL|HEADERS|BODY|DATA)\s*(?:\*\*)?\s*$",
    re.I,
)
_HEADER_RE = re.compile(r"^\s*([!#$%&'*+.^_|~0-9A-Za-z-]+)\s*:\s*(.*?)\s*$")


def _clean_text(value: str) -> str:
    """Normalize copied Markdown, escaped punctuation and invisible Unicode spaces."""
    value = value.replace("\ufeff", "")
    value = _ZERO_WIDTH.sub("", value)
    value = "".join(" " if unicodedata.category(char) == "Zs" else char for char in value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")

    # A trailing backslash is often used by clipboard/Markdown views as a line join.
    value = re.sub(r"\\[ \t]*\n", "\n", value)
    # Tolerate one-line escaped copies such as **METHOD: POST**\**URL**\**...
    value = re.sub(
        r"\\(?=\s*\*\*(?:METHOD|URL|HEADERS|BODY|DATA|[A-Za-z0-9-]+\s*:))",
        "\n",
        value,
        flags=re.I,
    )
    # Remove only paired bold wrappers; preserve literal asterisks such as */*.
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value, flags=re.S)
    # Undo Markdown backslash escaping: https\://, www\.host, \_\_token.
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


def parse_http_request(
    value: str,
    shell: str | None = None,
    body_override: str | None = None,
) -> dict:
    """Parse both section-style requests and bold, one-field-per-line exports.

    In HEADERS, a name ending in ':' with no same-line value consumes the next
    non-empty line verbatim. We intentionally test pending_header before trying
    to parse a new header so values containing ':' are never split or discarded.
    """
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

        # A split header value is an opaque data line. Consume it before
        # checking for section headings or another colon-containing header.
        if section == "HEADERS" and pending_header is not None:
            headers.append((pending_header, line))
            pending_header = None
            continue

        bare_section = _SECTION_BARE_RE.match(line)
        inline_section = _SECTION_RE.match(line)
        if bare_section or inline_section:
            if pending_header is not None:
                headers.append((pending_header, ""))
                pending_header = None
            match = bare_section or inline_section
            new_section = match.group(1).upper()
            inline_value = "" if bare_section else inline_section.group(2).strip()
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
                name, header_value = header_match.groups()
                if header_value:
                    headers.append((name, header_value))
                else:
                    pending_header = name
            elif line.startswith("#"):
                continue
        elif section in {"BODY", "DATA"}:
            body_lines.append(raw_line)

    if pending_header is not None:
        headers.append((pending_header, ""))

    if not method:
        raw_match = re.search(
            r"(?im)^\s*([A-Z][A-Z0-9!#$%&'*+.^_|~-]*)\s+(\S+)\s+HTTP/\d(?:\.\d)?\s*$",
            text,
        )
        if raw_match:
            method, target = raw_match.groups()
            host = next((v for k, v in headers if k.lower() == "host"), "")
            if target.startswith(("http://", "https://")):
                url = target
            elif host:
                url = f"https://{host}{target if target.startswith('/') else '/' + target}"

    if not method:
        raise ValueError(
            "Không tìm thấy METHOD. Hãy nhập METHOD: GET/POST hoặc dòng request như GET /path HTTP/1.1."
        )
    if not re.fullmatch(r"[A-Z][A-Z0-9!#$%&'*+.^_|~-]*", method):
        raise ValueError(f"HTTP method không hợp lệ: {method}")
    if not url:
        raise ValueError("Không tìm thấy URL. Hãy nhập URL đầy đủ bắt đầu bằng http:// hoặc https://.")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL phải bắt đầu bằng http:// hoặc https://.")

    parsed_body = "\n".join(body_lines) if body_lines else None
    body = body_override if body_override is not None and body_override != "" else parsed_body
    return {
        "method": method,
        "url": url,
        "headers": headers,
        "body": body,
        "curl": build_curl_command(method, url, headers, shell=shell, body=body),
    }
