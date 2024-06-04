import os
from typing import List
from httpx import ConnectError

import ollama


class Embed:
    def __init__(self) -> None:
        # Get the ollama model and host from environment variables
        self._model = os.getenv("ollama_model")
        self._host = os.getenv("host")

        # Initialize the ollama client with the host
        self.client = ollama.Client(host=self._host)

        # Prepare the model by pulling it if necessary
        self._prepare()

    def _prepare(self) -> None:
        try:
            # Try to list the available models using the client
            models = self.client.list()
            models_lst = [model["name"] for model in models["models"]]

            # If there are no models, pull the specified model
            if len(models["models"]) == 0:
                self.client.pull(self._model)
            else:
                # If the specified model is not in the list, pull it
                if self._model not in models_lst:
                    self.client.pull(self._model)
        except ConnectError:
            # If a connection error occurs, try listing the models locally
            models = ollama.list()
            models_lst = [model["name"] for model in models["models"]]

            # If there are no models, pull the specified model locally
            if len(models["models"]) == 0:
                ollama.pull(self._model)
            else:
                # If the specified model is not in the list, pull it locally
                if self._model not in models_lst:
                    ollama.pull(self._model)

    def embed(self, text: str) -> List[float]:
        # Check if the input is a string
        if isinstance(text, str):
            try:
                # Try to get the embeddings using the client
                result = self.client.embeddings(
                    model="nomic-embed-text",
                    prompt=text,
                )
                # Return the embedding
                return result["embedding"]
            except ConnectError:
                # If a connection error occurs, try getting the embeddings locally
                result = ollama.embeddings(
                    model="nomic-embed-text",
                    prompt=text,
                )
                # Return the embedding
                return result["embedding"]
        else:
            # Raise a value error if the input is not a string
            raise ValueError("text must be str")
