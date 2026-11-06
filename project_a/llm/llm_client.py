"""
Lightweight, resilient LLM client supporting both OpenAI-compatible and Google Gemini endpoints.
Uses standard library urllib to avoid third-party SDK dependencies.
Automatically loads .env if present.
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


def _load_env_file():
    """Lightweight .env loader without external dependencies."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


_load_env_file()


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30
    ):
        _load_env_file()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.api_key = api_key or self.openai_key or self.gemini_key

        if self.gemini_key and not self.openai_key:
            self.provider = "gemini"
            self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
            self.model = model or os.getenv("LLM_MODEL") or "gemini-flash-lite-latest"
        else:
            self.provider = "openai"
            self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
            self.model = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def call_chat_completion(
        self,
        messages: list,
        temperature: float = 0.0,
        response_format: Optional[Dict[str, str]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        metadata = {
            "configured": self.is_configured(),
            "provider": self.provider,
            "model": self.model,
            "latency_ms": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "error": None,
        }

        if not self.is_configured():
            metadata["error"] = "API key not configured (set OPENAI_API_KEY or GEMINI_API_KEY)."
            return None, metadata

        # Route to Gemini Native or OpenAI-compatible
        if self.provider == "gemini":
            return self._call_gemini_native(messages, temperature, metadata)
        else:
            return self._call_openai_compatible(messages, temperature, response_format, metadata)

    def _call_gemini_native(
        self,
        messages: list,
        temperature: float,
        metadata: dict
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        # Format Gemini contents
        full_text_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            full_text_parts.append(f"[{role.upper()}]:\n{content}")
        combined_prompt = "\n\n".join(full_text_parts)

        # Gemini model endpoint
        model_name = self.model
        if not model_name.startswith("gemini"):
            model_name = "gemini-flash-lite-latest"

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": combined_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        start_time = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                resp_data = json.loads(resp.read().decode("utf-8"))

                # Extract generated text
                candidates = resp_data.get("candidates", [])
                if not candidates:
                    metadata.update({"latency_ms": elapsed_ms, "error": "No candidates returned by Gemini."})
                    return None, metadata

                text_content = candidates[0]["content"]["parts"][0]["text"]
                usage = resp_data.get("usageMetadata", {})
                p_tokens = usage.get("promptTokenCount", 0)
                c_tokens = usage.get("candidatesTokenCount", 0)
                t_tokens = usage.get("totalTokenCount", p_tokens + c_tokens)

                # Gemini 1.5 Flash pricing: free tier / $0.075 per 1M input, $0.30 per 1M output
                cost = (p_tokens * 0.000000075) + (c_tokens * 0.00000030)

                # Format like OpenAI chat completion response for compatibility
                normalized_resp = {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": text_content
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": p_tokens,
                        "completion_tokens": c_tokens,
                        "total_tokens": t_tokens
                    }
                }

                metadata.update({
                    "latency_ms": elapsed_ms,
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "total_tokens": t_tokens,
                    "estimated_cost_usd": cost,
                })
                return normalized_resp, metadata

        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_body = e.read().decode("utf-8", errors="ignore")
            # If native failed, try OpenAI-compatible endpoint as fallback
            return self._call_gemini_openai_compat(messages, temperature, metadata)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            metadata.update({"latency_ms": elapsed_ms, "error": str(e)})
            return None, metadata

    def _call_gemini_openai_compat(
        self,
        messages: list,
        temperature: float,
        metadata: dict
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        payload = {
            "model": self.model if self.model.startswith("gemini") else "gemini-1.5-flash",
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        start_time = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                resp_data = json.loads(resp.read().decode("utf-8"))
                usage = resp_data.get("usage", {})
                p_tokens = usage.get("prompt_tokens", 0)
                c_tokens = usage.get("completion_tokens", 0)
                t_tokens = usage.get("total_tokens", p_tokens + c_tokens)
                cost = (p_tokens * 0.000000075) + (c_tokens * 0.00000030)

                metadata.update({
                    "latency_ms": elapsed_ms,
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "total_tokens": t_tokens,
                    "estimated_cost_usd": cost,
                })
                return resp_data, metadata
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            metadata.update({"latency_ms": elapsed_ms, "error": f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}"})
            return None, metadata
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            metadata.update({"latency_ms": elapsed_ms, "error": str(e)})
            return None, metadata

    def _call_openai_compatible(
        self,
        messages: list,
        temperature: float,
        response_format: Optional[Dict[str, str]],
        metadata: dict
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        start_time = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                resp_data = json.loads(resp.read().decode("utf-8"))
                usage = resp_data.get("usage", {})
                p_tokens = usage.get("prompt_tokens", 0)
                c_tokens = usage.get("completion_tokens", 0)
                t_tokens = usage.get("total_tokens", p_tokens + c_tokens)
                cost = (p_tokens * 0.00000015) + (c_tokens * 0.00000060)

                metadata.update({
                    "latency_ms": elapsed_ms,
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "total_tokens": t_tokens,
                    "estimated_cost_usd": cost,
                })
                return resp_data, metadata
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            metadata.update({"latency_ms": elapsed_ms, "error": f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}"})
            return None, metadata
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            metadata.update({"latency_ms": elapsed_ms, "error": str(e)})
            return None, metadata
