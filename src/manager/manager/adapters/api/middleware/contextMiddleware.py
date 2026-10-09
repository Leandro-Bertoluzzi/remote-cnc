"""FastAPI dependencies for application services."""

from typing import Annotated

from core.ports.gateway_client import IGatewayClient
from fastapi import Depends, Request
from manager.adapters.api.context import AppContext
from manager.application.device_service import DeviceService
from manager.application.file_service import FileService
from manager.application.log_service import LogService
from manager.application.material_service import MaterialService
from manager.application.task_service import TaskService
from manager.application.tool_service import ToolService
from manager.application.user_service import UserService
from manager.ports.worker_client import IWorkerClient


def get_app_context(request: Request) -> AppContext:
    return request.app.state.context

## Services

def get_device_service(context: Annotated[AppContext, Depends(get_app_context)]) -> DeviceService:
    return context.device_service


def get_file_service(context: Annotated[AppContext, Depends(get_app_context)]) -> FileService:
    return context.file_service


def get_log_service(context: Annotated[AppContext, Depends(get_app_context)]) -> LogService:
    return context.log_service


def get_material_service(
    context: Annotated[AppContext, Depends(get_app_context)],
) -> MaterialService:
    return context.material_service


def get_task_service(context: Annotated[AppContext, Depends(get_app_context)]) -> TaskService:
    return context.task_service


def get_tool_service(context: Annotated[AppContext, Depends(get_app_context)]) -> ToolService:
    return context.tool_service


def get_user_service(context: Annotated[AppContext, Depends(get_app_context)]) -> UserService:
    return context.user_service

## Clients

def get_gateway_client(context: Annotated[AppContext, Depends(get_app_context)]) -> IGatewayClient:
    return context.gateway

def get_worker_client(context: Annotated[AppContext, Depends(get_app_context)]) -> IWorkerClient:
    return context.worker

## Dependency Annotations for FastAPI

GetDeviceService = Annotated[DeviceService, Depends(get_device_service)]
GetFileService = Annotated[FileService, Depends(get_file_service)]
GetLogService = Annotated[LogService, Depends(get_log_service)]
GetMaterialService = Annotated[MaterialService, Depends(get_material_service)]
GetTaskService = Annotated[TaskService, Depends(get_task_service)]
GetToolService = Annotated[ToolService, Depends(get_tool_service)]
GetUserService = Annotated[UserService, Depends(get_user_service)]
GetGateway = Annotated[IGatewayClient, Depends(get_gateway_client)]
GetWorker = Annotated[IWorkerClient, Depends(get_worker_client)]
