"""Test 1: dump the exact messages we send, without calling any API.

Run: python3 inspect_prompt.py
Writes out/debug/system.txt, user.txt, source_only.txt and prints a fidelity report.
"""

import json
from pathlib import Path

import config
from draft_v0 import ROOT, URLS, NOTE
from extract import fetch_page, MAX_CHARS
from draft_v1 import build_system_prompt, build_user_message

DEBUG = ROOT / "out" / "debug"


def main():
    DEBUG.mkdir(parents=True, exist_ok=True)

    pages = [(url, fetch_page(url)) for url in URLS]
    system = build_system_prompt()
    user = build_user_message(pages)

    (DEBUG / "system.txt").write_text(system)
    (DEBUG / "user.txt").write_text(user)
    for index, (url, text) in enumerate(pages):
        (DEBUG / f"source_{index}.txt").write_text(f"{url}\n\n{text}")

    rules = (ROOT / "prompts" / "writer_system.md").read_text()
    voice = (ROOT / "profiles" / config.DEFAULT_PROFILE / "voice.md").read_text()

    print("=== Fidelity report ===")
    print(f"model              : {config.WRITER_MODEL}")
    print(f"system chars       : {len(system)}  (~{len(system)//4} tokens)")
    print(f"  writer_system.md : {len(rules)} chars, present: {rules.strip() in system}")
    print(f"  voice.md         : {len(voice)} chars, present: {voice.strip() in system}")
    print(f"user chars         : {len(user)}  (~{len(user)//4} tokens)")

    for url, text in pages:
        truncated = len(text) >= MAX_CHARS
        print(f"\n--- source: {url}")
        print(f"  extracted chars  : {len(text)}  truncated at MAX_CHARS: {truncated}")
        print(f"  first 300 chars  : {text[:300]!r}")
        print(f"  last 300 chars   : {text[-300:]!r}")
        # Rough boilerplate signal: does the text look like prose or like nav/JS leftovers?
        words = text.split()
        long_words = [w for w in words if len(w) > 25]
        print(f"  words            : {len(words)}, suspicious long tokens: {len(long_words)}")
        if long_words[:5]:
            print(f"  samples          : {long_words[:5]}")
        for marker in ("cookie", "Subscribe", "{", "function(", "css", "svg", "nav"):
            print(f"  contains {marker!r:14}: {marker.lower() in text.lower()}")

    print("\nWrote payload to", DEBUG)
    print(json.dumps({"system_chars": len(system), "user_chars": len(user)}, indent=2))


if __name__ == "__main__":
    main()
