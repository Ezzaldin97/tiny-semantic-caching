import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from src.embed_text import Embed
from src.vector_db import VectorStore

# Create an APIRouter instance with a prefix and tags
router = APIRouter(
    prefix="/api",
    tags=["semantic-caching"],
)

# Initialize a VectorStore instance
vs = VectorStore()


@router.get("/")
async def root():
    """
    Root endpoint to check the health of the application.
    
    Returns a JSON response with a message and application details.
    """
    return {
        "message": "app is healthy, and safely running",
        "data": {
            "app_name": os.getenv("app_name"),
            "app_version": os.getenv("app_version"),
        },
    }


@router.get("/vectorize/{text}")
async def vectorize(text: str):
    """
    Endpoint to vectorize input text using an Embed instance.
    
    Args:
    text (str): The input text to be vectorized.
    
    Returns a JSON response with a message and the vectorized result.
    """
    embedder = Embed()
    result = embedder.embed(text)
    return {"message": "embeddings created successfully", "data": {"response": result}}


@router.post("/insertion/{text}")
async def insert_embedding(
    text: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None
):
    """
    Endpoint to insert a vectorized text into the vector database.
    
    Args:
    text (str): The input text.
    embedding (List[float]): The vectorized representation of the input text.
    metadata (Optional[Dict[str, Any]], optional): Additional metadata for the input text. Defaults to None.
    
    Returns a JSON response with a message indicating the insertion status.
    """
    vs.insert(text, embedding, metadata)
    return {
        "message": "data saved in vector database",
        "data": {"response": f"embeddings of {text} saved"},
    }


@router.post("/search/{text}")
async def search(text: str):
    """
    Endpoint to search for similar texts in the vector database.
    
    Args:
    text (str): The input text to search for.
    
    Returns a JSON response with a message, the search result, and the distance score.
    """
    embeddings_result = await vectorize(text)
    ## search first
    results_df = vs.search(embeddings_result["data"]["response"])
    result = results_df[results_df["distance_score"] <= float(os.getenv("threshold"))]
    if not len(result) > 0:
        score = None
        result = None
    else:
        score = result["distance_score"].tolist()[0]
        result = result["text"].tolist()[0]
    ### must be saved directly
    await insert_embedding(text, embeddings_result["data"]["response"])
    return {"message": "data saved in vector database", "data": {"response": result, "score": score}}


@router.delete("/refresh/")
async def refresh():
    """
    Endpoint to refresh the vector database.
    
    Returns a JSON response with a message indicating the refresh status.
    """
    vs.refresh()
    return {
        "message": "database refreshed",
        "data": {
            "response": None,
        },
    }