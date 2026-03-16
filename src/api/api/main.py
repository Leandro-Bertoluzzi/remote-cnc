#!/usr/bin/env python3

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.database.base import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.exceptions import register_exception_handlers
from api.routes.cncRoutes import cncRoutes
from api.routes.fileRoutes import fileRoutes
from api.routes.logRoutes import logRoutes
from api.routes.materialRoutes import materialRoutes
from api.routes.monitorRoutes import monitorRoutes
from api.routes.rootRoutes import rootRoutes
from api.routes.taskRoutes import taskRoutes
from api.routes.toolRoutes import toolRoutes
from api.routes.userRoutes import userRoutes
from api.routes.workerRoutes import workerRoutes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: runs startup checks and graceful shutdown."""
    # --- Startup ---
    logger.info("Starting up API server...")

    # Verify DB connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Database connection failed — the API will start but DB queries may fail")

    yield

    # --- Shutdown ---
    logger.info("Shutting down API server...")
    engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Routes
app.include_router(cncRoutes)
app.include_router(fileRoutes)
app.include_router(logRoutes)
app.include_router(materialRoutes)
app.include_router(monitorRoutes)
app.include_router(rootRoutes)
app.include_router(toolRoutes)
app.include_router(taskRoutes)
app.include_router(userRoutes)
app.include_router(workerRoutes)
