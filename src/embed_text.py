import os
from typing import List
from httpx import ConnectError

import ollama


class Embed:
    def __init__(self) -> None:
        self._model = os.getenv("ollama_model")
        self._host = os.getenv("host")
        self.client = ollama.Client(host=self._host)
        ## preparation
        self._prepare()

    def _prepare(self) -> None:
        try:
            models = self.client.list()
            models_lst = [
                model['name'] for model in models['models'] 
            ]
            if len(models['models'])==0:
                self.client.pull(self._model)
            else:
                if self._model not in models_lst:
                    self.client.pull(self._model)
        except ConnectError:
            models = ollama.list()
            models_lst = [
                model['name'] for model in models['models'] 
            ]
            if len(models['models'])==0:
                ollama.pull(self._model)
            else:
                if self._model not in models_lst:
                    ollama.pull(self._model)

    def embed(self, text: str) -> List[float]:
        if isinstance(text, str):
            try:
                result = self.client.embeddings(
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
