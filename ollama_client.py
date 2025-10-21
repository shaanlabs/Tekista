import os
import requests
from typing import List, Dict

# These align with Config defaults so you can control via .env or process env
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

def chat(messages: List[Dict[str, str]], *, num_predict: int = 500, temperature: float = 0.7, low_vram: bool = False) -> str:
    """Call Ollama /api/chat with role-preserving messages.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    returns: assistant message content (str)
    """
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "low_vram": low_vram,
        },
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        # Expected schema: { "message": { "role": "assistant", "content": "..." }, ... }
        msg = data.get("message") or {}
        return (msg.get("content") or "").strip()
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama chat request failed: {e}") from e

# Example:
# from ollama_client import chat
# text = chat([
#     {"role": "system", "content": "You are helpful."},
#     {"role": "user", "content": "Hello"}
# ])
