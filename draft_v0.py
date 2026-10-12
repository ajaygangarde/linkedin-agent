"""step 1: Tuen URL's into linkedIn Draft with one Claude call"""
import re
from datetime import datetime
from pathlib import Path

import anthropic
import httpx
import config
# ---- Edit these, then run: python3 draft_v0.py ----
URLS = ["https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills"]  # use a specific article
NOTE = "focus on what a working engineer can use"
MAX_CHARS = 12000  # cap page length so one page doesn't cost too much

ROOT = Path(__file__).parent

def fetch_page(url):
    response = httpx.get(url, follow_redirects= True, timeout=20)
    response.raise_for_status()
    html = response.text
    # Remove scripts and styles together with their content
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    # Remove every other tag, keep only the text
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_CHARS]

def write_draft(pages):
    system_prompt = (ROOT / "prompts" / "writer_system.md").read_text()
    sources = ""
    for url, text in pages:
        sources += f'<source url="{url}"> {text}</source> \n\n'

    user_message = (
        sources
        + f"Author's note on the angle: {NOTE}\n\n"
        + "Write the post now."
    )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=config.WRITER_MODEL,
        max_tokens=1000,
        system= system_prompt,
        messages=[{"role": "user", "content": user_message}]
     )
    draft = ""
    for block in response.content:
        if block.type == "text":
            draft += block.text
    return draft, response.usage

def main():
    pages = []
    for url in URLS:
        try:
            pages.append((url, fetch_page(url)))
            print("Fetched", url)
        except httpx.HTTPError as error:
            print("Skipping", error)
    if not pages:
        print("No pages fetched. Nothing to write about.")
        return
    # 2. Ask Claude for a draft
    draft, usage = write_draft(pages)

    # 3. Save it to out/ and print it
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"draft_{datetime.now():%Y%m%d_%H%M%S}.md"
    out_file.write_text(draft)

    print("\n" + draft + "\n")
    print("Saved to", out_file)
    print("Tokens: input", usage.input_tokens, "output", usage.output_tokens)

main()