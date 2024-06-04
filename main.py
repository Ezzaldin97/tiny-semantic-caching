from fastapi import FastAPI  # Import the FastAPI class
from dotenv import (
    load_dotenv,
)  # Import the load_dotenv function to load environment variables from a.env file

# Load environment variables from a.env file
load_dotenv(".env")

# Import the base module from the src package
from src import base

# Create a FastAPI application instance
app = FastAPI()

# Include the router from the base module into the FastAPI application
app.include_router(base.router)
