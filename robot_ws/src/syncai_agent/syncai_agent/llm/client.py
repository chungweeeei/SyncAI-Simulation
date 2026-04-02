import structlog
from openai import OpenAI


class LLMClient:

    def __init__(self, logger: structlog.stdlib.BoundLogger, api_key: str, model: str):
        self._logger = logger
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def chat(self, messages: list, tools: list):
        self._logger.debug("[LLMClient] Sending request", model=self._model, num_messages=len(messages))
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
        )
        return response
