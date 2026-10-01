"""Local Ollama chat client shared by the API and the styling agent."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def chat(messages, *, temperature=0.7, max_tokens=512, tools=None):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if tools is not None:
        payload["tools"] = tools

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat", json=payload, timeout=(5, 240)
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"Ollama'ya bağlanılamadı ({OLLAMA_HOST}). Ollama'nın açık olduğundan emin olun."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        detail = response.text[:300]
        raise RuntimeError(
            f"Ollama isteği başarısız (HTTP {response.status_code}, model={OLLAMA_MODEL}): {detail}"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Ollama yanıtı zaman aşımına uğradı.") from exc

    result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get("message"), dict):
        raise RuntimeError("Ollama beklenen sohbet yanıtını döndürmedi.")
    return result
