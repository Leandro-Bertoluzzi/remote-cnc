from components.cards.RequestCard import RequestCard
from core.database.base import Session as SessionLocal
from core.database.models import TASK_PENDING_APPROVAL_STATUS
from core.database.repositories.taskRepository import TaskRepository
from views.BaseListView import BaseListView


class RequestsView(BaseListView):
    def __init__(self, parent=None):
        super(RequestsView, self).__init__(parent)
        self.setItemListFromValues(
            'SOLICITUDES',
            'No hay tareas pendientes de aprobación',
            self.createRequestCard
        )
        self.refreshLayout()

    def createRequestCard(self, item):
        return RequestCard(item, parent=self)

    def getItems(self):
        db_session = SessionLocal()
        repository = TaskRepository(db_session)
        return repository.get_all_tasks(status=TASK_PENDING_APPROVAL_STATUS)
