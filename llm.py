"""Thin wrapper over the Anthropic Messages API with web search + JSON coercion."""
from __future__ import annotations

import json
import re
import time
from typing import Any, Type, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from .config import CONFIG

T = TypeVar("T", bound=BaseModel)

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=CONFIG.anthropic_api_key)
    return _client


def _text_of(message: Any) -> str:
    parts = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def _extract_json(raw: str) -> Any:
    """Models sometimes wrap JSON in prose or fences. Dig it out."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost brace-balanced object.
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in model output:\n{raw[:800]}")
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(cleaned[start:], start=start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start : i + 1])
    raise ValueError(f"Unbalanced JSON in model output:\n{raw[:800]}")


def call(
    *,
    model: str,
    system: str,
    prompt: str,
    max_tokens: int = 8000,
    web_search: bool = False,
    retries: int = 3,
) -> str:
    tools = []
    if web_search:
        tools.append({**WEB_SEARCH_TOOL, "max_uses": CONFIG.max_search_uses})

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            msg = client().messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                tools=tools or anthropic.NOT_GIVEN,
            )
            return _text_of(msg)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as err:
            last_err = err
            sleep = 2 ** attempt * 5
            print(f"  API error ({err}); retrying in {sleep}s")
            time.sleep(sleep)
    raise RuntimeError(f"Anthropic API failed after {retries} attempts: {last_err}")


def call_structured(
    schema: Type[T],
    *,
    model: str,
    system: str,
    prompt: str,
    max_tokens: int = 8000,
    web_search: bool = False,
    repair_attempts: int = 2,
) -> T:
    """Call the model and coerce the reply into `schema`, repairing on validation failure."""
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    full_prompt = (
        f"{prompt}\n\n"
        "Return ONLY a single JSON object matching this JSON Schema. "
        "No markdown fences, no preamble, no trailing commentary.\n\n"
        f"<json_schema>\n{schema_json}\n</json_schema>"
    )

    raw = call(
        model=model,
        system=system,
        prompt=full_prompt,
        max_tokens=max_tokens,
        web_search=web_search,
    )

    for attempt in range(repair_attempts + 1):
        try:
            return schema.model_validate(_extract_json(raw))
        except (ValidationError, ValueError) as err:
            if attempt == repair_attempts:
                raise
            print(f"  Schema validation failed, repairing (attempt {attempt + 1}): {err}")
            raw = call(
                model=model,
                system="You fix malformed JSON. Output only valid JSON.",
                prompt=(
                    "This JSON failed validation. Fix it so it validates against the schema. "
                    "Preserve all content; only correct structure, types and missing required fields.\n\n"
                    f"<errors>\n{err}\n</errors>\n\n<json_schema>\n{schema_json}\n</json_schema>\n\n"
                    f"<broken_json>\n{raw[:60000]}\n</broken_json>"
                ),
                max_tokens=max_tokens,
            )
    raise RuntimeError("unreachable")
