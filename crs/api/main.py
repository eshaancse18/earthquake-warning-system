"""
FastAPI Application
"""

from fastapi import FastAPI

from api.routes import router
from config.config import config


app = FastAPI(

    title=config.get(
        "api",
        "title"
    ),

    version=config.get(
        "api",
        "version"
    )

)

app.include_router(router)