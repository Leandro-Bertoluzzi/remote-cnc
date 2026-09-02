#!/usr/bin/env python3

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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
from core.adapters.database.base import check_db_connection, dispose_db
from core.adapters.logging.logger_factory import setup_stream_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = setup_stream_logger("api", logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: runs startup checks and graceful shutdown."""
    # --- Startup ---
    logger.info("Starting up API server...")

    # Verify DB connectivity
    try:
        check_db_connection()
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Database connection failed — the API will start but DB queries may fail")

    yield

    # --- Shutdown ---
    logger.info("Shutting down API server...")
    dispose_db()
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
