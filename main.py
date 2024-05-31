from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv(".env")
from src import base

app = FastAPI()
app.include_router(base.router)
