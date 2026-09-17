# Manager Architecture

## Responsibility

`manager` is the application module for CNC Management. It contains the
application services that coordinate use cases shared by the REST API and the
Qt Desktop application.

The Manager does not represent a deployment process. API and Desktop are two
inbound adapters that expose the same application through different interaction
models.

## Package Structure

```text
src/manager/manager/
├── application/              # Application services and use-case orchestration
├── ports/                    # Ports owned by Manager
└── adapters/
    ├── api/                  # FastAPI inbound adapter
    └── desktop/              # Qt inbound adapter and presentation
```

The application services include device, file, material, task, tool and user
operations. The API adapter also exposes log-related operations, while the
Desktop adapter contains Qt views, widgets and presentation coordination.

## Deployment Composition Roots

Deployment-specific startup and dependency wiring live under `src/apps/`:

```text
src/apps/
├── api/
│   ├── main.py               # FastAPI startup
│   └── context.py            # API composition root
└── desktop/
    ├── main.py               # Qt startup
    └── context.py            # Desktop composition root
```

Each composition root is responsible for reading environment or local
configuration, selecting concrete outbound adapters and injecting them into
the corresponding Manager adapter context. The Manager package must remain
usable without importing FastAPI, PyQt, Redis, Celery or SQLAlchemy.

## Context Objects

`manager.adapters.api.context.AppContext` and
`manager.adapters.desktop.context.AppContext` are dependency containers for
their respective inbound adapters. They expose port-compatible dependencies
and Manager application services to routes or views.

Concrete adapters are instantiated outside these contexts, in:

- `src/apps/api/context.py`
- `src/apps/desktop/context.py`

This keeps framework startup and infrastructure configuration at the boundary
of the system.

## Rules for New Code

- Put business orchestration in `manager/application/`.
- Put API-specific parsing, validation and serialization in `manager/adapters/api/`.
- Put Qt-specific presentation code in `manager/adapters/desktop/`.
- Define a required capability as a port owned by the consuming module.
- Instantiate concrete infrastructure only from an `apps/*` composition root or
  a test fixture.
- Do not import `infrastructure` from Manager application services.
