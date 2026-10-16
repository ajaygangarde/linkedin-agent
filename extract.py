"""Turn a URL into readable Markdown-ish text.

draft_v0.fetch_page strips every tag, which flattens headings, lists and code
blocks into one run-on paragraph and keeps the site's nav and footer. That is the
biggest difference between pasting an article into a chat panel and sending it
through the API: the model receives the same words with none of the structure.
This keeps the structure and drops the page chrome, with no new dependencies.
"""
import html
import re

import httpx

MAX_CHARS = 20000  # structure costs some characters; the body still fits comfortably


def fetch_page(url):
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; linkedin-agent/1.0)"},
    )
    response.raise_for_status()
    return html_to_text(response.text)[:MAX_CHARS]


def html_to_text(page):
    # 1. Drop elements whose content is never article text.
    for tag in ("script", "style", "noscript", "svg", "nav", "header", "footer",
                "aside", "form", "button", "iframe"):
        page = re.sub(rf"(?is)<{tag}\b.*?</{tag}>", " ", page)

    # 2. Keep only the main article when the page marks one.
    for pattern in (r"(?is)<article\b[^>]*>(.*?)</article>",
                    r"(?is)<main\b[^>]*>(.*?)</main>"):
        match = re.search(pattern, page)
        if match and len(match.group(1)) > 500:
            page = match.group(1)
            break

    # 3. Turn the structural tags into Markdown before stripping the rest.
    page = re.sub(r"(?is)<pre\b[^>]*>(.*?)</pre>", _code_block, page)
    page = re.sub(r"(?is)<code\b[^>]*>(.*?)</code>", r"`\1`", page)
    for level in range(1, 7):
        page = re.sub(rf"(?is)<h{level}\b[^>]*>(.*?)</h{level}>",
                      lambda m, level=level: f"\n\n{'#' * level} {m.group(1).strip()}\n", page)
    page = re.sub(r"(?is)<li\b[^>]*>(.*?)</li>", r"\n- \1", page)
    page = re.sub(r"(?is)<(p|div|tr|blockquote)\b[^>]*>", "\n\n", page)
    page = re.sub(r"(?is)<br\s*/?>", "\n", page)

    # 4. Strip what is left, then undo HTML entities (&#x27; etc.).
    text = re.sub(r"<[^>]+>", " ", page)
    text = html.unescape(text)

    # 5. Tidy whitespace without collapsing the line structure we just recovered.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _code_block(match):
    """<pre> content becomes a fenced block so the model sees it as code."""
    body = re.sub(r"<[^>]+>", "", match.group(1))
    body = html.unescape(body).strip()
    return f"\n\n```\n{body}\n```\n\n"
