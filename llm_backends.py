"""
llm_backends.py

Backend adapters for Vireon-HLE-Engine.

All backends expose:

    llm_call(system_prompt: str, user_prompt: str, temperature: float) -> str

Select backend via VIREON_BACKEND env var:

- VIREON_BACKEND=xai      → Grok (xAI) via OpenAI-compatible client
- VIREON_BACKEND=openai   → OpenAI models (gpt-4.x, gpt-5.x, etc.)
- VIREON_BACKEND=dummy    → simple stub (for tests)
"""

from __future__ import annotations
import os

from vireon_hle_engine import LLMFn

try:
    import openai  # used for both OpenAI and xAI backends
except ImportError:
    openai = None  # type: ignore


def _xai_llm_call(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    Grok via xAI API (OpenAI-compatible client).

    Required env:
    - XAI_API_KEY
    Optional:
    - XAI_MODEL (default: "grok-4")
    """
    if openai is None:
        raise RuntimeError("openai package not installed. pip install openai")

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set XAI_API_KEY env var for xAI backend.")

    model = os.getenv("XAI_MODEL", "grok-4")

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=4096,
    )
    return resp.choices[0].message.content  # type: ignore[return-value]


def _openai_llm_call(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    OpenAI backend.

    Required env:
    - OPENAI_API_KEY
    Optional:
    - OPENAI_MODEL (default: "gpt-5.1-thinking")
    """
    if openai is None:
        raise RuntimeError("openai package not installed. pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY env var for OpenAI backend.")

    model = os.getenv("OPENAI_MODEL", "gpt-5.1-thinking")

    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=4096,
    )
    return resp.choices[0].message.content  # type: ignore[return-value]


def _dummy_llm_call(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    Dummy backend for wiring tests (no real AI).
    Always answers 'B'.
    """
    return (
        "I will answer this exam question.\n"
        "Given no real model is wired, I default to a dummy choice.\n"
        "Answer: B"
    )


def get_llm_call() -> LLMFn:
    """
    Select an LLM backend based on VIREON_BACKEND env var.

    Supported:
    - "xai"      → Grok via xAI
    - "openai"   → OpenAI
    - "dummy"    → dummy echo backend
    """
    backend = os.getenv("VIREON_BACKEND", "xai").lower()

    if backend == "xai":
        return _xai_llm_call
    elif backend == "openai":
        return _openai_llm_call
    elif backend == "dummy":
        return _dummy_llm_call
    else:
        raise ValueError(
            f"Unknown VIREON_BACKEND={backend}. "
            "Use one of: xai, openai, dummy."
        )
