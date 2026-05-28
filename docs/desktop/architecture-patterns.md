# Desktop UI Architecture Patterns

This document outlines best practices for extending the desktop UI while respecting the hierarchical signal-based decoupling defined in [DR 0008](../dr/dr-0008-hierarchical-ui-decoupling.md).

## Overview: Three-Level Signal Propagation

```
┌─────────────────┐
│  Card Widget    │  Level 1: Cards emit update/remove signals
│                 │  (e.g., TaskCard.update_requested)
└────────┬────────┘
         │ signal
         ▼
┌─────────────────┐
│  View Container │  Level 2: Views collect cards, emit navigation/task signals
│  (BaseListView) │  (e.g., TasksView.task_dispatched)
└────────┬────────┘
         │ signal
         ▼
┌─────────────────┐
│  MainWindow     │  Level 3: MainWindow wire all signals, owns GatewayMonitor
│                 │  and all services
└────────┬────────┘
         │
         └────────▶ AppContext (services, session factory)
```

## Level 1: Adding a New Card Widget

### Template

```python
# src/desktop/desktop/components/MyCard.py

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout

class MyCard(QWidget):
    """Displays a single entity and emits update/remove signals."""

    # Signals: emit when user interacts with the card
    update_requested = pyqtSignal(object)  # Emit the updated entity
    remove_requested = pyqtSignal(object)  # Emit the entity to remove

    def __init__(self, entity, parent=None):
        super().__init__(parent)
        self.entity = entity
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Edit button: emit update_requested when clicked
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit)

        # Delete button: emit remove_requested when clicked
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete)

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.setLayout(layout)

    def _on_edit(self):
        """User clicked edit; notify parent view of intent."""
        self.update_requested.emit(self.entity)

    def _on_delete(self):
        """User clicked delete; notify parent view of intent."""
        self.remove_requested.emit(self.entity)
```

### Integration with BaseListView

Your view (inheriting from `BaseListView`) automatically receives and handles these signals:

```python
# src/desktop/desktop/views/MyListView.py

from desktop.views.BaseListView import BaseListView
from desktop.components.MyCard import MyCard

class MyListView(BaseListView):
    """List container for MyCard widgets."""

    def getItems(self):
        """Fetch items from service."""
        return self._context.my_service.get_all_items()

    def createCard(self, item):
        """Factory method: create a card for each item."""
        card = MyCard(item)
        # Connect card signals:
        card.update_requested.connect(self._on_card_update)
        card.remove_requested.connect(self._on_card_remove)
        return card

    def createToolBar(self):
        """Optional: create toolbar for this view."""
        toolbar = ToolBar(options=["Add"], parent=self)
        toolbar.toolbar_added.connect(self._on_toolbar_added)
        return toolbar

    def _on_card_update(self, item):
        """Handle update_requested from a card."""
        # Example: emit a signal or call a service
        self.task_dispatched.emit(item)

    def _on_card_remove(self, item):
        """Handle remove_requested from a card."""
        # Example: delete and refresh list
        try:
            self._context.my_service.delete_item(item.id)
            self.refreshLayout()
        except Exception as e:
            self._show_error(f"Delete failed: {e}")
```

### Testing Card Signals

```python
# src/desktop/tests/test_my_card.py

import pytest
from pytestqt.qtbot import QtBot
from desktop.components.MyCard import MyCard

def test_card_emits_update_requested_on_edit_click(qtbot: QtBot):
    """Clicking Edit button emits update_requested signal."""
    entity = {"id": 1, "name": "Test"}
    card = MyCard(entity)
    qtbot.addWidget(card)

    # Find and click the Edit button
    edit_btn = card.findChild(QPushButton, "Edit")

    # Assert the signal is emitted with the entity
    with qtbot.waitSignal(card.update_requested) as blocker:
        edit_btn.click()

    assert blocker.args[0] == entity

def test_card_emits_remove_requested_on_delete_click(qtbot: QtBot):
    """Clicking Delete button emits remove_requested signal."""
    entity = {"id": 1, "name": "Test"}
    card = MyCard(entity)
    qtbot.addWidget(card)

    delete_btn = card.findChild(QPushButton, "Delete")

    with qtbot.waitSignal(card.remove_requested) as blocker:
        delete_btn.click()

    assert blocker.args[0] == entity
```

---

## Level 2: Adding a New View

### Template

```python
# src/desktop/desktop/views/MyView.py

from PyQt5.QtWidgets import QVBoxLayout
from desktop.views.BaseListView import BaseListView
from desktop.components.MyCard import MyCard
from gateway.GatewayMonitor import GatewayMonitor
from core.AppContext import AppContext

class MyView(BaseListView):
    """
    Display list of entities and allow CRUD operations.

    Signals defined by BaseView:
    - back_requested: User clicked back; return to MainMenu.
    - toolbar_added(ToolBar): View added a toolbar.
    - toolbar_removed(ToolBar): View removed its toolbar.
    - task_dispatched(Task): View created/updated a task; start worker.
    """

    def __init__(self, context: AppContext, *, gateway_monitor: GatewayMonitor = None, **kwargs):
        """
        Initialize the view with dependencies injected.

        Args:
            context: AppContext providing all services (task_service, etc.).
            gateway_monitor: Optional GatewayMonitor for task monitoring.
            **kwargs: Additional arguments passed to BaseListView.
        """
        super().__init__(context, gateway_monitor=gateway_monitor, **kwargs)
        self._gateway_monitor = gateway_monitor

    def getItems(self):
        """Fetch items from service; handles errors via BaseListView."""
        items = self._context.my_service.get_all_items()
        return items

    def createCard(self, item):
        """Factory: wrap each item in a card widget."""
        card = MyCard(item)
        card.update_requested.connect(self._on_card_update)
        card.remove_requested.connect(self._on_card_remove)
        return card

    def createToolBar(self):
        """Optional: create toolbar with action buttons."""
        from desktop.components.ToolBar import ToolBar
        toolbar = ToolBar(
            options=["Add New", "Export"],
            parent=self
        )
        # ControlView detects toolbar_added signal and propagates upward
        self.toolbar_added.emit(toolbar)
        return toolbar

    def _on_card_update(self, item):
        """Custom update logic (optional)."""
        # Example: emit task_dispatched to start monitoring updates
        self.task_dispatched.emit(item)

    def _on_card_remove(self, item):
        """Custom delete logic (optional)."""
        try:
            self._context.my_service.delete_item(item.id)
            self.refreshLayout()
        except Exception as e:
            self._show_error(f"Delete failed: {e}")
```

### Integration with MainWindow

After MainWindow instantiates your view, it auto-connects all signals:

```python
# In MainWindow.changeView() or similar:

view = MyView(self.app_context, gateway_monitor=self.gateway_monitor)
self._connect_view_signals(view)  # Auto-wires all view signals
```

### Testing View Signals

```python
# src/desktop/tests/test_my_view.py

import pytest
from pytestqt.qtbot import QtBot
from unittest.mock import MagicMock
from desktop.views.MyListView import MyView
from core.AppContext import AppContext

@pytest.fixture
def mock_context():
    """Create a mock AppContext with services."""
    context = MagicMock(spec=AppContext)
    context.my_service.get_all_items.return_value = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ]
    return context

def test_my_view_emits_back_requested_on_back_button(qtbot: QtBot, mock_context):
    """Clicking back button emits back_requested signal."""
    view = MyView(mock_context)
    qtbot.addWidget(view)

    # MyView (or BaseListView) has a back button; find and click it
    back_btn = view.findChild(QPushButton)  # Assume first button is back

    with qtbot.waitSignal(view.back_requested):
        back_btn.click()

def test_my_view_emits_task_dispatched_on_card_update(qtbot: QtBot, mock_context):
    """Updating a card emits task_dispatched signal."""
    view = MyView(mock_context)
    qtbot.addWidget(view)

    # When a card emits update_requested, MyView should:
    # 1. Call service.update_item()
    # 2. Emit task_dispatched with the task

    updated_task = {"id": 1, "name": "Updated"}
    mock_context.my_service.update_item.return_value = {"task_id": 123}

    with qtbot.waitSignal(view.task_dispatched):
        view._on_card_update(updated_task)

    mock_context.my_service.update_item.assert_called_once_with(updated_task)

def test_my_view_does_not_emit_signals_before_user_action(qtbot: QtBot, mock_context):
    """Signals are NOT emitted on initialization; only on user action."""
    view = MyView(mock_context)
    qtbot.addWidget(view)

    # View is created but no user interaction yet
    with qtbot.assertNotEmitted(view.back_requested):
        with qtbot.assertNotEmitted(view.task_dispatched):
            # Simulate some internal state change (not user action)
            view.refreshLayout()
```

---

## Level 3: MainWindow Signal Wiring

### Pattern

```python
# In MainWindow.py

def _connect_view_signals(self, view: BaseView) -> None:
    """
    Auto-connect all signals from a view to MainWindow handlers.

    This method encapsulates the three-level signal propagation:
    - back_requested: Return to menu
    - toolbar_added/removed: Manage toolbars
    - task_dispatched: Start worker to execute task
    """
    view.back_requested.connect(self.backToMenu)
    view.toolbar_added.connect(lambda tb: self.addToolBar(Qt.TopToolBarArea, tb))
    view.toolbar_removed.connect(self.removeToolBar)
    view.task_dispatched.connect(self.startWorkerMonitor)

def changeView(self, view_widget: BaseView) -> None:
    """Switch to a new view and wire its signals."""
    # Remove signals from the old view (if any)
    if hasattr(self, '_current_view') and self._current_view:
        self._disconnect_view_signals(self._current_view)

    # Set the new view
    self.setCentralWidget(view_widget)
    self._current_view = view_widget

    # Connect the new view's signals
    self._connect_view_signals(view_widget)

def _disconnect_view_signals(self, view: BaseView) -> None:
    """Disconnect all signals from a view (cleanup)."""
    try:
        view.back_requested.disconnect(self.backToMenu)
        view.toolbar_added.disconnect()
        view.toolbar_removed.disconnect()
        view.task_dispatched.disconnect()
    except RuntimeError:
        # Signals might already be disconnected; ignore
        pass
```

### Testing MainWindow Signal Routing

```python
# src/desktop/tests/test_main_window.py

def test_main_window_connects_view_signals(qtbot: QtBot, main_window_fixture):
    """MainWindow auto-connects all view signals on changeView()."""
    view = MyView(main_window_fixture.app_context)
    main_window_fixture.changeView(view)

    # Verify signals are connected by emitting them
    with qtbot.waitSignal(main_window_fixture.back_button_clicked):
        view.back_requested.emit()

def test_main_window_disconnects_old_view_signals(qtbot: QtBot, main_window_fixture):
    """Switching views disconnects signals from the old view."""
    view1 = MyView(main_window_fixture.app_context)
    view2 = OtherView(main_window_fixture.app_context)

    main_window_fixture.changeView(view1)
    main_window_fixture.changeView(view2)

    # view1 signals should be disconnected
    with qtbot.assertNotEmitted(main_window_fixture.back_button_clicked):
        view1.back_requested.emit()  # Should not trigger anything
```

---

## Common Patterns & Scenarios

### Pattern: View Needs Custom Toolbar

**When**: A view has unique actions (e.g., Tasks view has "Run All" button).

**How**:

1. Create ToolBar with custom options.
2. Connect ToolBar button signals to view methods.
3. Emit `toolbar_added(toolbar)` to propagate upward.

```python
class TasksView(BaseListView):
    def createToolBar(self):
        toolbar = ToolBar(options=["Run All", "Pause All"], parent=self)
        toolbar.button_clicked.connect(self._on_toolbar_action)
        self.toolbar_added.emit(toolbar)
        return toolbar

    def _on_toolbar_action(self, action):
        ...
```

### Pattern: View Depends on GatewayMonitor

**When**: View displays real-time status updates (e.g., monitor view).

**How**:

1. Accept `gateway_monitor: GatewayMonitor | None` parameter.
2. Connect to `gateway_monitor.new_status` to receive updates.
3. Handle `None` gracefully (monitor not available).

```python
class MonitorView(BaseView):
    def __init__(self, context, *, gateway_monitor=None, **kwargs):
        super().__init__(context, **kwargs)
        self._gateway_monitor = gateway_monitor
        if self._gateway_monitor:
            self._gateway_monitor.new_status.connect(self._on_status_update)

    def _on_status_update(self, status):
        """Display the latest CNC status."""
        self.status_label.setText(f"Status: {status}")
```

### Pattern: Handle Service Errors

**When**: A service call fails (network, database, etc.).

**How**:
BaseListView.refreshLayout() catches exceptions and displays `ConnectionErrorWidget` automatically. Override `getItems()` if you need custom error handling.

```python
class MyView(BaseListView):
    def getItems(self):
        try:
            items = self._context.my_service.get_all_items()
            # Custom validation (optional)
            if not items:
                self._show_info("No items available")
            return items
        except ConnectionError as e:
            # BaseListView will catch this and show error widget
            raise
```

---

## Checklist: Adding a New Feature

- [ ] **Card**: Define and emit signals for each user interaction.
- [ ] **Card**: Write tests with `qtbot.waitSignal()`.
- [ ] **View**: Implement `getItems()` to fetch entities.
- [ ] **View**: Implement `createCard()` factory.
- [ ] **View**: Write tests that signal emission without mocking MainWindow.
- [ ] **MainWindow**: No changes needed; `_connect_view_signals()` is automatic.
- [ ] **Tests**: Update `conftest.py` if new services/fixtures needed.
- [ ] **Docs**: Add example to this file if pattern is novel.
