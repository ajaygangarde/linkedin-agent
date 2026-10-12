from pathlib import Path
from dotenv import load_dotenv
import os                      # add at the top, with the other imports


load_dotenv()

PROJECT_ROOT = Path(__file__).parent

DEFAULT_PROFILE = "ajay"
# Read the key that load_dotenv() put into the environment.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Verify these against the official models page before relying on them.
WRITER_MODEL = "claude-sonnet-5-5"
TRIAGE_MODEL = "claude-haiku-4-5-20251001"
