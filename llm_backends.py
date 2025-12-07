from __future__ import annotations

import os
from typing import Callable

import openai

from vireon_hle_engine import LLMCall


def _dummy_call(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    Dummy backend: no external API call.

    Always returns a simple explanation and the letter B so that
    VireonHLEEngine can parse a valid answer during CI.
    """
    return (
        "This is the dummy backend. "
        "No real model was called.\n\n"
        "Final answer: B"
    )


def _make_xai_call() -> LLMCall:
    """
    Build an LLMCall that talks to xAI's Grok endpoint using the
    OpenAI-compatible client.
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY is not set but VIREON_BACKEND=xai")

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )
    model = os.getenv("XAI_MODEL", "grok-4")

    def _call(system_prompt: str, user_prompt: str, temperature: float) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ""

    return _call


def _make_openai_call() -> LLMCall:
    """
    Build an LLMCall that talks to OpenAI's chat completions API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set but VIREON_BACKEND=openai")

    client = openai.OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-5.1-mini")

    def _call(system_prompt: str, user_prompt: str, temperature: float) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ""

    return _call


def get_llm_call() -> LLMCall:
    """
    Select the backend based on VIREON_BACKEND env var.

    - VIREON_BACKEND=xai    -> Grok via xAI
    - VIREON_BACKEND=openai -> OpenAI models
    - VIREON_BACKEND=dummy  -> local dummy (no network)
    """
    backend = os.getenv("VIREON_BACKEND", "dummy").lower()

    if backend == "xai":
        return _make_xai_call()
    elif backend == "openai":
        return _make_openai_call()
    elif backend == "dummy":
        return _dummy_call
    else:
        print(f"[WARN] Unknown VIREON_BACKEND={backend!r}, falling back to dummy.")
        return _dummy_call
