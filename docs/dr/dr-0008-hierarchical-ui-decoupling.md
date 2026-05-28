# DR 0008: Hierarchical UI Decoupling via PyQt Signals and Constructor Injection

## Status

Accepted

## Date

2026-05-28

## Context and Problem

The desktop UI layer (`src/desktop/`) maintains tight coupling across multiple levels:

1. **Cards** (component-level widgets) directly call methods on parent **Views** via `getView()`.
2. **Views** directly call methods on **MainWindow** via `getWindow()` to trigger cross-view actions (back navigation, toolbar management, worker monitoring).
3. **Components** (ToolBar) explicitly accept `MainWindow` as a parameter and self-register.

This creates several problems:

- **Testing**: Unit tests cannot isolate views/cards without mocking the entire `MainWindow`. Mock setup is complex and brittle.
- **Replaceability**: Swapping a view's dependency (e.g., `GatewayMonitor` for a different monitor) requires modifying constructors throughout the codebase.
- **Layer boundary blur**: It is unclear which UI components are _capable_ (can they work standalone?) versus _dependent_ (they must have a MainWindow).
- **Circular reasoning**: Views cannot be reasoned about independently; understanding their behavior requires tracing all `getWindow()` calls.

## Options Considered

1. **Keep current coupling with `getWindow()` pattern**
    - Pros: minimal refactoring, developers understand it.
    - Cons: testing remains difficult, layer boundaries remain blurred.

2. **Implement a global event bus across all UI**
    - Pros: decouples all layers uniformly, event semantics are clear.
    - Cons: overengineered for the current scope; introduces a new abstraction layer; harder to trace event flow.

3. **Use PyQt signals throughout three hierarchical levels (selected)**
    - Pros: leverages PyQt5's native event system; low ceremony; familiar to PyQt developers; enables `qtbot.waitSignal()` for testing.
    - Cons: requires explicit connection code in MainWindow; connections must be maintained as new views are added.

## Decision

Implement **hierarchical UI decoupling** using PyQt5 signals and constructor injection across three levels:

### Level 1: Cards → Views (via signals)

- **Card** emits `update_requested` / `remove_requested` when user interacts with card widgets.
- **View** (BaseListView) connects these signals and calls appropriate service methods.
- Benefits: Isolates card styling from service logic; testable in isolation.

### Level 2: Views → MainWindow (via signals)

- **View** (BaseView subclass) defines four signals:
    - `back_requested`: User clicked back button; return to menu.
    - `toolbar_added(ToolBar)`: View wants to add a toolbar.
    - `toolbar_removed(ToolBar)`: View wants to remove its toolbar.
    - `task_dispatched(Task)`: View created/updated a task; start worker to execute it.
- **MainWindow** auto-connects these signals in `changeView(view)` method.
- Benefits: Views are testable without MainWindow; clear contract of what each view can communicate; dependency injection is explicit and type-safe.

### Level 3: ToolBar → MainWindow (via signals)

- **ToolBar** no longer accepts `MainWindow` as constructor parameter.
- **View** emits signals `toolbar_added` / `toolbar_removed`.
- **MainWindow** listens for these signals and adds/removes the toolbar from the UI hierarchy.
- Benefits: ToolBar has no knowledge of UI hierarchy; reusable in other contexts.

### Dependency Injection Pattern

- **Services** (gateway, task_service, device_service, asset_service) injected via `AppContext` constructor parameter.
- **GatewayMonitor** (stateful monitor instance) injected explicitly where needed (TasksView, MonitorView, ControlView).
- No component uses `getWindow()` nor `getView()` to access dependencies; all are explicit parameters.

## Consequences

### Positive [`+`]

- **Testability**: Components can be unit tested with `qtbot.waitSignal(...)` without instantiating MainWindow.
- **Clear contracts**: Each component's public interface is defined by its signal emissions; no hidden `getWindow()` or `getView()` calls.
- **Type safety**: Constructor parameters are explicit and type-hinted; type checkers catch missing dependencies at development time.
- **Replaceability**: Swapping a dependency (e.g., a test GatewayMonitor) is explicit and local to the component being modified.
- **Scalability**: Adding a new component is straightforward: define signals, inject dependencies, emit signals — MainWindow auto-connects.
- **Documentation**: The three levels and their signal contracts become the primary documentation of the UI architecture.

### Negative [`-`]

- **Connection overhead**: MainWindow must maintain `_connect_view_signals()` and connect each view after instantiation.
- **Traceability**: Signal connections are implicit in `_connect_view_signals()` — a developer must read that method to understand the flow.
- **Lifecycle management**: Views must be created before MainWindow can connect their signals; ordering matters.

### Trade-offs

- **Ceremony vs. safety**: The explicit signal definitions and connections add 50-100 lines of boilerplate but eliminate 100x more complex mock setup in tests.
- **Implicit effects**: Signal connections look like "magic" at first glance but follow the Qt language; documented patterns and examples mitigate this.

## Next Steps

1. **✅ Completed**: Implement signal definitions in `BaseView`.
2. **✅ Completed**: Refactor all views to inject `GatewayMonitor` and emit signals.
3. **✅ Completed**: Update MainWindow `_connect_view_signals()` method.
4. **✅ Completed**: Rewrite all 831 tests to use `qtbot.waitSignal()` / `qtbot.assertNotEmitted()`.
5. **📝 TODO**: Create `docs/desktop/architecture-patterns.md` with templates for adding new cards, views, and testing patterns.
6. **⏳ FUTURE**: Add optional debugging logging wrapper around signal connections for troubleshooting (out of current scope).

## References

- **Related ADRs**:
    - [DR 0007: Hexagonal Architecture](dr-0007-hexagonal-architecture.md) — Informs port/adapter pattern at service layer
    - [DR 0001: CNC Gateway Process](dr-0001-cnc-gateway-process.md) — Context on gateway monitoring

- **PyQt5 Documentation**:
    - [PyQt5 Signals and Slots](https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html)
    - [pytest-qt: qtbot.waitSignal()](https://pytest-qt.readthedocs.io/en/latest/signals.html)
