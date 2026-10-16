"""One function to call any model. Returns the same shape for every provider."""
import json

import anthropic
import config  # loads .env and exposes the API keys

# How much thinking to buy. OpenAI takes the word; Claude takes a token budget.
THINKING_BUDGET = {"low": 2000, "medium": 6000, "high": 12000}


def complete(model, system, user, max_tokens, effort="high", json_schema=None):
    """Send one system prompt + one user message.

    effort      -- "low" | "medium" | "high". Without it these models barely think:
                   gpt-6.1-sol defaults to ~125 reasoning tokens, which is the main
                   reason API output looked worse than the same prompt in the web UI.
    json_schema -- JSON Schema dict. The provider then guarantees valid JSON, so we
                   no longer have to slice the reply from the first "{" to the last "}".

    Returns (text, was_truncated, usage) where usage is a dict we can print.
    """
    # Provider is chosen from the model name, so config.WRITER_MODEL is the only switch.
    if model.startswith("claude-"):
        return _complete_claude(model, system, user, max_tokens, effort, json_schema)
    if model.startswith("gpt-"):
        return _complete_openai(model, system, user, max_tokens, effort, json_schema)
    raise ValueError(f"Unknown model '{model}'. Expected a name starting with 'claude-' or 'gpt-'.")


def _complete_claude(model, system, user, max_tokens, effort, json_schema):
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    budget = THINKING_BUDGET[effort]

    # Claude has no JSON mode: ask in words and prefill "{" so the reply starts there.
    # Prefill is incompatible with extended thinking, so only one of the two is used.
    messages = [{"role": "user", "content": user}]
    arguments = {
        "model": model,
        # max_tokens covers thinking + text on Claude, so the budget must fit inside it.
        "max_tokens": max_tokens + budget,
        "system": system,
        "messages": messages,
        "thinking": {"type": "enabled", "budget_tokens": budget},
    }
    if json_schema:
        arguments["system"] = (
            system + "\n\nReturn only one JSON object matching this schema, "
            "with no Markdown fences:\n" + json.dumps(json_schema)
        )

    response = client.messages.create(**arguments)

    # Keep only text blocks (skip thinking blocks)
    text = ""
    thinking_tokens = 0
    for block in response.content:
        if block.type == "text":
            text += block.text
        if block.type == "thinking":
            thinking_tokens += len(block.thinking) // 4  # rough; Claude does not itemise it
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "reasoning_tokens": thinking_tokens,
    }
    return text, response.stop_reason == "max_tokens", usage


def _complete_openai(model, system, user, max_tokens, effort, json_schema):
    # Imported here so Claude-only runs work even if `openai` is not installed.
    from openai import OpenAI

    # Pass the key explicitly: our .env variable is OPEN_AI_KEY, not the SDK's default name.
    client = OpenAI(api_key=config.OPEN_AI_KEY)

    arguments = {
        "model": model,
        # Reasoning tokens are billed against this ceiling too, so leave room for both.
        "max_completion_tokens": max_tokens + THINKING_BUDGET[effort],
        "reasoning_effort": effort,
        "messages": [
            {"role": "developer", "content": system},  # OpenAI's name for the system prompt
            {"role": "user", "content": user},
        ],
    }
    if json_schema:
        arguments["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "output", "strict": True, "schema": json_schema},
        }

    response = client.chat.completions.create(**arguments)
    choice = response.choices[0]
    details = response.usage.completion_tokens_details
    usage = {
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "reasoning_tokens": getattr(details, "reasoning_tokens", 0),
    }
    return choice.message.content or "", choice.finish_reason == "length", usage
