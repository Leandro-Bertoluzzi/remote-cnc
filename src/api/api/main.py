#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.cncRoutes import cncRoutes
from api.routes.fileRoutes import fileRoutes
from api.routes.logRoutes import logRoutes
from api.routes.materialRoutes import materialRoutes
from api.routes.monitorRoutes import monitorRoutes
from api.routes.rootRoutes import rootRoutes
from api.routes.toolRoutes import toolRoutes
from api.routes.taskRoutes import taskRoutes
from api.routes.userRoutes import userRoutes
from api.routes.workerRoutes import workerRoutes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
