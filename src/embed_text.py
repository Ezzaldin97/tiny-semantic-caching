import os
from typing import List

import ollama


class Embed:
    def __init__(self) -> None:
        self._model = os.getenv("ollama_model")

    def embed(self, text: str) -> List[float]:
        if isinstance(text, str):
            result = ollama.embeddings(
                model="nomic-embed-text",
                prompt=text,
            )
            return result["embedding"]
        else:
            raise ValueError("text must be str")
