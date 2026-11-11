"""Turn an image into a short spoken-style description.

Two backends, picked with the LLM_BACKEND setting:
  - "claude": Anthropic API (needs ANTHROPIC_API_KEY, paid per use)
  - "local":  LM Studio running on your own PC (free, needs a vision model loaded)

Both call `on_text(chunk)` as text arrives, so the dashboard can show
"LLM responding..." and fill the textbox live.
"""

import base64
import os
from typing import Callable

import httpx

SYSTEM_PROMPT = (
    "You help a visually impaired person understand what is in front of them. "
    "Describe the image in one or two short sentences, as if speaking to them. "
    "Mention hazards, obstacles, people and any readable text first. "
    "No preamble, no lists, no guessing about things you cannot see."
)
USER_PROMPT = "What is in front of me?"


async def describe_image(image_bytes: bytes, media_type: str, on_text: Callable[[str], None]) -> str:
    backend = os.getenv("LLM_BACKEND", "local").lower()
    if backend == "claude":
        return await _describe_with_claude(image_bytes, media_type, on_text)
    if backend == "local":
        return await _describe_with_local(image_bytes, media_type, on_text)
    raise RuntimeError(f"Unknown LLM_BACKEND '{backend}', use 'claude' or 'local'")


async def _describe_with_claude(image_bytes: bytes, media_type: str, on_text: Callable[[str], None]) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY from the environment
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    # Streaming so the dashboard can show the text as it is written.
    # "fallbacks" lets the API retry on another model if this one declines.
    async with client.beta.messages.stream(
        model=os.getenv("CLAUDE_MODEL", "claude-opus-5-5"),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_config={"effort": "low"},  # short descriptive task: keep it fast and cheap
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                    },
                    {"type": "text", "text": USER_PROMPT},
                ],
            }
        ],
    ) as stream:
        async for text in stream.text_stream:
            on_text(text)
        message = await stream.get_final_message()

    if message.stop_reason == "refusal":
        raise RuntimeError("The model declined to describe this image")
    return "".join(block.text for block in message.content if block.type == "text").strip()


async def _describe_with_local(image_bytes: bytes, media_type: str, on_text: Callable[[str], None]) -> str:
    """LM Studio exposes an OpenAI-style chat endpoint on http://localhost:1234."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": os.getenv("LOCAL_LLM_MODEL", "gemma-3-4b-it"),
        "max_tokens": 200,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
                    {"type": "text", "text": USER_PROMPT},
                ],
            },
        ],
    }
    url = os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1/chat/completions")
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
    on_text(text)
    return text
