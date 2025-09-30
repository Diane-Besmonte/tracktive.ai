from __future__ import annotations
from typing import Any, Dict, List, Optional
import asyncio
import os  # NEW
from openai import OpenAI
from .config import settings

# prefer settings, else real environment var, else let SDK read env itself
_api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

_client = OpenAI(api_key=_api_key) if _api_key else OpenAI()

async def chat_json(system: str, user: str, model: str = "gpt-4o-mini", max_tokens: int = 800) -> str:
    def _call():
        resp = _client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    return await asyncio.to_thread(_call)
