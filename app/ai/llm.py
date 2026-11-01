"""One small client for the language model, through any OpenAI-compatible API (OpenRouter by default).

Every AI piece that uses it asks for a JSON object and validates what comes back. Anything unexpected
(network error, timeout, rate limit, text that isn't the JSON asked for) raises LLMError, and the caller
falls back to its rule-based version, so a model outage never breaks the app.
"""

import json
import logging
import re
import time

import httpx

from app.core.config import settings

log = logging.getLogger("egyptora.llm")


class LLMError(Exception):
    pass


def parse_json_object(text: str) -> dict:
    """The model's reply as a dict. Accepts a bare object, a ```json fenced block, or an object inside prose."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    elif not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("the model did not return a JSON object")
        text = text[start : end + 1]
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"the model returned invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LLMError("the model returned JSON that is not an object")
    return value


def complete_json(system: str, user: str, *, max_tokens: int = 900) -> dict:
    """Sends one system + user message and returns the JSON object the model answered with."""
    if not settings.llm_api_key:
        raise LLMError("no LLM_API_KEY configured")
    started = time.perf_counter()
    try:
        response = httpx.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                # OpenRouter shows these on its dashboard; other providers ignore them
                "X-Title": "Egyptora",
            },
            json={
                "model": settings.llm_model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.2,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=settings.llm_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise LLMError(f"could not reach the model: {exc.__class__.__name__}") from exc
    elapsed = round((time.perf_counter() - started) * 1000)
    if response.status_code != 200:
        log.warning("LLM %s answered %s in %s ms", settings.llm_model, response.status_code, elapsed)
        raise LLMError(f"the model API answered {response.status_code}")
    try:
        content = response.json()["choices"][0]["message"]["content"] or ""
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("unexpected response from the model API") from exc
    log.info("LLM %s answered in %s ms", settings.llm_model, elapsed)
    return parse_json_object(content)
