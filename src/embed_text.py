import os
from typing import List
from httpx import ConnectError

import ollama


class Embed:
    def __init__(self) -> None:
        self._model = os.getenv("ollama_model")
        self._host = os.getenv("host")

    def embed(self, text: str) -> List[float]:
        if isinstance(text, str):
            try:
                client = ollama.Client(host=self._host)
                result = client.embeddings(
                    model="nomic-embed-text",
                    prompt=text,
                )
                return result["embedding"]
            except ConnectError: ### to handle if ollama runs locally
                result = ollama.embeddings(
                    model="nomic-embed-text",
                    prompt=text,
                )
                return result["embedding"]
        else:
            raise ValueError("text must be str")
