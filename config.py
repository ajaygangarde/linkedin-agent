from pathlib import Path
from dotenv import load_dotenv
import os                      # add at the top, with the other imports
load_dotenv()

PROJECT_ROOT = Path(__file__).parent

DEFAULT_PROFILE = "ajay"
# Read the key that load_dotenv() put into the environment.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
# Verify these against the official models page before relying on them.
# WRITER_MODEL = "claude-sonnet-5-5"


TRIAGE_MODEL = "claude-haiku-4-5-20251001"
# Verify these against the provider model pages before relying on them.
MODELS = {
    "sonnet": "claude-sonnet-5-5",
    "sol": "gpt-6.1-sol",
    "luna": "gpt-6-luna",   # check spelling
}
WRITER_MODEL = MODELS["sol"]