"""Multi-provider LLM adapter for opt-in advisory verification and explanation."""
import re
import httpx
from typing import Dict, Any, List
from app.core.config import settings


class LLMClient:
    @classmethod
    def _redact_key(cls, error_msg: str) -> str:
        if settings.LLM_API_KEY:
            error_msg = error_msg.replace(settings.LLM_API_KEY, "[REDACTED_API_KEY]")
        error_msg = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer [REDACTED]', error_msg)
        return re.sub(r'key=[A-Za-z0-9_\-\.]+', 'key=[REDACTED]', error_msg)

    @classmethod
    async def generate_advisory_explanation(
        cls, claim_text: str, passage_texts: List[str], audit_status: str, discrepancies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        prov = settings.LLM_PROVIDER.lower()
        if not settings.LLM_API_KEY and prov not in {"ollama", "local"}:
            return {
                "advisory_text": f"Deterministic verification classified claim as '{audit_status}'. LLM advisory synthesis is opt-in and disabled because no operator LLM_API_KEY is configured. Deterministic findings are authoritative.",
                "provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL,
                "grounded_evidence": passage_texts[:3], "is_advisory": True, "configured": False
            }

        prompt = (
            f"You are an advisory RAG citation auditor. Verify claim solely using evidence.\n"
            f"Claim: {claim_text}\nAuditor Status: {audit_status}\nDiscrepancies: {discrepancies}\n"
            f"Evidence:\n" + "\n---\n".join(passage_texts[:5]) + "\n\nConcise 2-sentence verification."
        )

        timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if prov in {"openai-compatible", "openai", "openrouter", "litellm"}:
                    r = await client.post(
                        f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
                        json={"model": settings.LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
                    )
                    r.raise_for_status()
                    content = r.json()["choices"][0]["message"]["content"]
                elif prov == "anthropic":
                    r = await client.post(
                        f"{settings.LLM_BASE_URL.rstrip('/')}/v1/messages",
                        headers={"x-api-key": settings.LLM_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                        json={"model": settings.LLM_MODEL, "max_tokens": 512, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
                    )
                    r.raise_for_status()
                    content = r.json()["content"][0]["text"]
                elif prov == "gemini":
                    r = await client.post(
                        f"{settings.LLM_BASE_URL.rstrip('/')}/v1beta/models/{settings.LLM_MODEL}:generateContent?key={settings.LLM_API_KEY}",
                        headers={"Content-Type": "application/json"},
                        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0}}
                    )
                    r.raise_for_status()
                    content = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                elif prov == "ollama":
                    r = await client.post(
                        f"{settings.LLM_BASE_URL.rstrip('/')}/api/chat",
                        headers={"Content-Type": "application/json"},
                        json={"model": settings.LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False}
                    )
                    r.raise_for_status()
                    content = r.json()["message"]["content"]
                else:
                    return {"advisory_text": f"Unsupported provider: {settings.LLM_PROVIDER}.", "provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL, "grounded_evidence": passage_texts[:3], "is_advisory": True, "configured": False}

                return {"advisory_text": content.strip(), "provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL, "grounded_evidence": passage_texts[:3], "is_advisory": True, "configured": True}
        except Exception as e:
            return {"advisory_text": f"Provider error: {cls._redact_key(str(e))}", "provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL, "grounded_evidence": passage_texts[:3], "is_advisory": True, "error": True}
