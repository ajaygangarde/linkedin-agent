""" Step II voice file  + structure JSON Output"""

from datetime import datetime 
from pydantic import ValidationError
import config
from llm import complete
from draft_v0 import ROOT, URLS, NOTE
from extract import fetch_page  # keeps headings, lists and code; drops nav and footer
from schema import Draft, DRAFT_SCHEMA

PROFILE = config.DEFAULT_PROFILE


def build_system_prompt():
    rules = (ROOT / "prompts" / "writer_system.md").read_text();
    voice = (ROOT / "profiles" / PROFILE / "voice.md").read_text()
    return rules + "\n\n Voice \n\n" + voice

def build_user_message(pages):
    sources = ""
    for url, text in pages:
        sources += f'<source url="{url}">\n{text}\n</source>\n\n'
    return sources + f"Author's note on the angle: {NOTE}\n\nWrite the article now."

def get_draft(system_promopt, user_message):
    for attempt in (1, 2):

        # llm.complete hides which provider (Claude / OpenAI) config.WRITER_MODEL is
        text, truncated, usage = complete(
            config.WRITER_MODEL,
            system_promopt,
            user_message,
            max_tokens=6000,  # article + thinking needs far more room than a post
            effort="high",    # without this the model spends ~125 tokens thinking
            json_schema=DRAFT_SCHEMA,
        )
        print(f"  tokens: in {usage['input_tokens']}, out {usage['output_tokens']}, "
              f"reasoning {usage['reasoning_tokens']}")

        # A cut-off reply is incomplete JSON. Retrying would cost the same again.
        if truncated:
            raise SystemExit("Reply cut off at max_tokens. Raise max_tokens.")

        # Cut from the first "{" to the last "}" in case of stray words
        json_text = text[text.find("{"): text.rfind("}") + 1]

        try:
            return Draft.model_validate_json(json_text) # parse + validate
        except ValidationError as error:
            print(f"Attempt {attempt}: invalid JSON from the model: {error}")
    raise SystemExit("The model did not return valid JSON twice : stopping")
     
def main():
    pages = []
    for url in URLS:
        try:
            pages.append((url, fetch_page(url)))
            print("Fetched", url)
        except Exception as error:
            print("Skipping", url, "-", error)
    if not pages:
        raise SystemExit("No pages fetched.")

    draft = get_draft(build_system_prompt(), build_user_message(pages))

    # Claude may have chosen to skip: not enough material
    if draft.skip_reason:
        print("SKIPPED:", draft.skip_reason)
        return

    # // check url is not available
    for url in draft.sources:
        if url not in [u for u, _ in pages]:
            print("WARNING: unknown source")

    # Markdown file: metadata on top, then the article
    markdown = (
        "---\n"
        f"profile: {PROFILE}\n"
        f"date: {datetime.now():%Y-%m-%d}\n"
        f"source: {pages[0][0]}\n"
        "status: draft\n"
        "---\n\n"
        f"# {draft.title}\n\n"
        f"*{draft.subtitle}*\n\n"
        f"{draft.article}\n"
    )

    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (out_dir / f"article_{stamp}.md").write_text(markdown)
    (out_dir / f"article_{stamp}.json").write_text(draft.model_dump_json(indent=2))

    print("\n" + markdown)


if __name__ == "__main__":
    main()
    





