import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"


class LLMError(Exception):
    pass


class LLMNotConfiguredError(LLMError):
    """Raised when no provider API key is available."""


class LLMProviderError(LLMError):
    """Raised when the upstream LLM API returns an error."""


def _has_llm_provider() -> bool:
    return bool(settings.openai_api_key.strip() or settings.anthropic_api_key.strip())


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1200,
) -> str:
    """Send a chat completion request; OpenAI first, Anthropic as fallback."""
    if not _has_llm_provider():
        raise LLMNotConfiguredError(
            "No LLM API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment."
        )

    errors: list[str] = []

    if settings.openai_api_key.strip():
        try:
            return await _openai_chat(
                messages,
                model=model or settings.llm_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LLMProviderError as exc:
            errors.append(f"OpenAI: {exc}")
            logger.warning("OpenAI chat completion failed, trying fallback if available: %s", exc)

    if settings.anthropic_api_key.strip():
        try:
            return await _anthropic_chat(
                messages,
                model=settings.anthropic_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LLMProviderError as exc:
            errors.append(f"Anthropic: {exc}")
            logger.error("Anthropic chat completion failed: %s", exc)

    if errors:
        raise LLMProviderError("; ".join(errors))
    raise LLMNotConfiguredError(
        "No LLM API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment."
    )


async def _openai_chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key.strip()}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENAI_CHAT_URL, headers=headers, json=payload)

    if response.status_code >= 400:
        detail = _extract_error_detail(response)
        raise LLMProviderError(f"OpenAI HTTP {response.status_code}: {detail}")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise LLMProviderError("OpenAI returned no choices")

    content = choices[0].get("message", {}).get("content")
    if not content or not str(content).strip():
        raise LLMProviderError("OpenAI returned empty content")
    return str(content).strip()


async def _anthropic_chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    system_parts: list[str] = []
    anthropic_messages: list[dict[str, str]] = []

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            system_parts.append(content)
            continue
        anthropic_messages.append(
            {
                "role": "assistant" if role == "assistant" else "user",
                "content": content,
            }
        )

    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": anthropic_messages,
    }
    if system_parts:
        payload["system"] = "\n\n".join(system_parts)

    headers = {
        "x-api-key": settings.anthropic_api_key.strip(),
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(ANTHROPIC_MESSAGES_URL, headers=headers, json=payload)

    if response.status_code >= 400:
        detail = _extract_error_detail(response)
        raise LLMProviderError(f"Anthropic HTTP {response.status_code}: {detail}")

    data = response.json()
    content_blocks = data.get("content") or []
    text_parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
    content = "".join(text_parts).strip()
    if not content:
        raise LLMProviderError("Anthropic returned empty content")
    return content


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                return str(err.get("message") or err)
            return str(body.get("message") or body)
    except json.JSONDecodeError:
        pass
    return response.text[:500] if response.text else "unknown error"


def parse_json_object(raw: str) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from LLM output (handles fenced code blocks)."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    return parsed if isinstance(parsed, dict) else None
