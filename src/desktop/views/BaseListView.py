from abc import abstractmethod
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from desktop.components.cards.MsgCard import MsgCard
from desktop.components.buttons.MenuButton import MenuButton
from database.models import Base
from typing import Callable, TYPE_CHECKING
from typing_extensions import TypedDict
from desktop.views.BaseView import BaseView

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


ViewList = TypedDict('ViewList', {
    'title': str,
    'empty_msg': str,
    'create_btn_text': str,
    'items': list[Base],
    'create_btn_action': Callable[[], None],
    'get_item_widget': Callable[[Base], QWidget]
})


class BaseListView(BaseView):
    def __init__(self, parent: 'MainWindow'):
        super(BaseListView, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Default attributes
        self.lists: list[ViewList] = []
        self.current_index = 0

    def refreshLayout(self):
        """Re-draw the view, updating the inside widgets.
        """
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.current_index = 0
        for list_definition in self.lists:
            try:
                list_definition['items'] = self.getItems()
                self.current_index += 1
            except Exception as error:
                self.showError(
                    'Error de base de datos',
                    str(error)
                )
                return

        for list_definition in self.lists:
            if list_definition['title']:
                self.layout().addWidget(QLabel(list_definition['title']))

            if list_definition['create_btn_text']:
                self.layout().addWidget(
                    MenuButton(
                        list_definition['create_btn_text'],
                        list_definition['create_btn_action']
                    )
                )

            for item in list_definition['items']:
                self.layout().addWidget(list_definition['get_item_widget'](item))

            if not list_definition['items'] and list_definition['empty_msg']:
                self.layout().addWidget(
                    MsgCard(list_definition['empty_msg'], self)
                )

        self.layout().addWidget(
            MenuButton('Volver al menú', onClick=self.getWindow().backToMenu)
        )
        self.update()

    # Attributes

    def setItemList(self, list_definition: ViewList):
        self.lists.append(list_definition)

    def setItemListFromValues(
        self,
        title: str,
        empty_msg: str,
        get_item_widget: Callable[[Base], QWidget],
        create_btn_text: str = '',
        create_btn_action: Callable[[], None] = lambda: None,
        items: list[Base] = []
    ):
        list_definition: ViewList = {
            'title': title,
            'empty_msg': empty_msg,
            'get_item_widget': get_item_widget,
            'create_btn_text': create_btn_text,
            'create_btn_action': create_btn_action,
            'items': items
        }
        self.setItemList(list_definition)

    # Abstract methods

    @abstractmethod
    def getItems(self) -> list[Base]:
        raise NotImplementedError    # pragma: no cover
