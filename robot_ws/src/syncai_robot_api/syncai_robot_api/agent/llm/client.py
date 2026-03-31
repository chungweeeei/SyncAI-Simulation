import os

import httpx


class LLMClient:

    def __init__(self):
        self._provider = os.getenv("SYNCAI_LLM_PROVIDER", "ollama")
        self._model = os.getenv("SYNCAI_LLM_MODEL", "llama3.2")
        self._api_key = os.getenv("SYNCAI_LLM_API_KEY", "")
        self._ollama_url = os.getenv("SYNCAI_OLLAMA_URL", "http://localhost:11434")
        self._http_client = httpx.AsyncClient(timeout=60.0)

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self._provider == "ollama":
            return await self._generate_ollama(system_prompt, user_prompt)
        elif self._provider == "claude":
            return await self._generate_claude(system_prompt, user_prompt)
        elif self._provider == "openai":
            return await self._generate_openai(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self._provider}")

    async def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        resp = await self._http_client.post(
            f"{self._ollama_url}/api/chat",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    async def _generate_claude(self, system_prompt: str, user_prompt: str) -> str:
        resp = await self._http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        if resp.status_code != 200:
            body = resp.text
            raise RuntimeError(
                f"Claude API error {resp.status_code}: {body}"
            )
        data = resp.json()
        return data["content"][0]["text"]

    async def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        resp = await self._http_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
