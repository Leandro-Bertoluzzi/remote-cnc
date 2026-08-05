# DR 0009: Separate Architectural Modules from Deployment Artifacts

## Status

Proposed

## Date

2026-08-01

## Context and Problem

DR-0007 established **Hexagonal Architecture (Ports & Adapters)** as the architectural style adopted across the monorepo. During that migration, the project progressively decoupled application logic from infrastructure through ports and adapters, making business rules independent from frameworks and external technologies.

Although the internal architecture now follows Hexagonal principles, the repository organization still reflects **deployment artifacts** rather than **application boundaries**.

Currently, the project contains independent top-level packages for:

* `api` — FastAPI application.
* `desktop` — Qt desktop application.
* `worker` — Celery worker.
* `gateway` — CNC Gateway service.

This organization mirrors how the software is deployed:

* the API runs inside a Docker container;
* the Desktop application runs locally on the user's machine;
* the Worker runs as an independent background process;
* the Gateway runs as a dedicated always-on service.

While convenient from an operational perspective, this layout unintentionally suggests that each deployment artifact represents an independent application.

A review of the business architecture showed that this is not the case.

The FastAPI API and the Qt Desktop application expose exactly the same business capabilities. Both invoke the same use cases, manipulate the same domain model, and operate over the same bounded context. Their differences are limited to presentation concerns and user interaction.

Treating them as separate applications increases the risk of:

* duplicating application services;
* implementing equivalent use cases multiple times;
* allowing business rules to migrate into framework-specific code;
* coupling repository organization to deployment decisions.

Conversely, the Worker and Gateway represent specialized runtime components that support the same CNC Management domain, but expose different application services.

The architecture therefore lacks an explicit distinction between:

* **architectural modules**, which represent business capabilities;
* **deployment artifacts**, which represent independently executable programs.

This decision formalizes that distinction.

---

## Options Considered

### 1. Keep the current organization

Maintain `api`, `desktop`, `worker`, and `gateway` as independent top-level application modules.

**Pros**

* Mirrors deployment layout.
* Minimal refactoring.
* Existing imports remain unchanged.

**Cons**

* Suggests that API and Desktop are different applications.
* Encourages duplication of application services.
* Couples architectural organization to operational concerns.
* Makes Hexagonal Architecture less explicit.

---

### 2. Merge deployment and architecture

Collapse all runtime components into a single application.

**Pros**

* Simple repository layout.
* Single entrypoint.

**Cons**

* Prevents independent deployment.
* Ignores operational requirements.
* Does not reflect the need for dedicated Worker and Gateway processes.

---

### 3. Separate architectural modules from deployment artifacts

Organize the repository according to business applications while introducing dedicated composition roots for each deployment artifact.

API and Desktop become alternative inbound adapters of the same application.

Worker and Gateway remain independent runtime applications.

Deployment entrypoints become explicit composition roots.

**Pros**

* Aligns repository organization with Hexagonal Architecture.
* Prevents duplication of application logic.
* Preserves independent deployment.
* Makes architectural boundaries explicit.

**Cons**

* Requires package reorganization.
* Existing imports must be updated.
* Build and deployment scripts require minor changes.

---

## Decision

Adopt **Option 3**.

The repository will distinguish between **business applications** and **deployment artifacts**.

A new **Manager** application becomes the canonical implementation of the CNC Management use cases.

The FastAPI API and the Qt Desktop application become alternative **inbound adapters** of the Manager application.

A new top-level `apps/` directory will contain deployment-specific composition roots responsible for:

* dependency injection;
* adapter selection;
* framework initialization;
* application startup.

The composition roots are deployment-specific, while the application remains deployment-independent.

A simplified target structure is:

```text
apps/
    api/
    desktop/
    worker/
    gateway/

manager/
    application/
    domain/
    ports/

    adapters/
        in/
            api/
            desktop/
```

The Worker and Gateway remain independently deployable applications because they provide specialized runtime responsibilities that are not presentation concerns.

This decision intentionally separates repository organization from deployment strategy.

---

## Principles

The following principles govern future repository organization.

### Application boundaries represent business capabilities

- Applications exist to implement business use cases.
- They are not defined by the technology used to expose them.
- Changing a user interface must not require creating a new application.

---

### Deployment artifacts do not define architectural boundaries

- An independently deployable executable does not necessarily represent an independent application.
- Different deployment artifacts may expose the same application through different adapters.
- Deployment concerns are operational decisions rather than architectural ones.

---

### Multiple inbound adapters may target the same application

The same application may be accessed through multiple presentation mechanisms, including:

* REST APIs;
* desktop user interfaces;
* command-line interfaces;
* background workers;
* messaging systems.

These adapters should invoke the same application services rather than implementing their own business logic.

---

### Composition roots belong to deployment artifacts

Each deployment artifact is responsible for:

* selecting adapter implementations;
* configuring dependency injection;
* framework initialization;
* startup and shutdown logic.

Business logic must remain independent of these responsibilities.

---

### Presentation layers remain thin

Framework-specific code should remain limited to:

* request parsing;
* validation;
* authentication;
* serialization;
* presentation logic.

Business rules belong exclusively to the application and domain layers.

---

## Migration Strategy

The migration will be performed incrementally.

### Phase 1 — Introduce deployment entrypoints

Create an `apps/` directory containing independent composition roots for:

* API
* Desktop
* Worker
* Gateway

Initially, these entrypoints may continue referencing the existing packages.

---

### Phase 2 — Introduce the Manager application

Create a new `manager` module containing:

* application services;
* use cases;
* domain orchestration;
* inbound adapters.

Initially, only new functionality should target this structure.

---

### Phase 3 — Migrate presentation adapters

Move framework-specific code into:

```text
manager/
    adapters/
        in/
            api/
            desktop/
```

Routes, controllers, presenters and UI-specific coordination logic should migrate without changing business behavior.

---

### Phase 4 — Consolidate application services

Remove duplicated application logic from the legacy API and Desktop packages.

Each business capability should exist exactly once.

---

### Phase 5 — Remove obsolete packages

After migration is complete:

* remove obsolete top-level API and Desktop application packages;
* update build scripts;
* update Dockerfiles;
* update packaging scripts;
* simplify dependency injection.

---

## Consequences

### Positive

* **[+]** Repository organization better reflects Hexagonal Architecture.
* **[+]** Business logic has a single canonical implementation.
* **[+]** API and Desktop remain independently deployable while sharing the same application.
* **[+]** Framework-specific code becomes easier to identify and review.
* **[+]** Future presentation adapters (CLI, gRPC, WebSocket, etc.) can be introduced without creating additional applications.
* **[+]** The distinction between application code and deployment code becomes explicit.

### Negative

* **[-]** Initial refactoring requires updating imports and package names.
* **[-]** Build scripts, Dockerfiles and packaging configuration require minor updates.
* **[-]** Developers unfamiliar with the distinction between applications and deployment artifacts may initially expect each executable to correspond to a separate application.

---

## Relationship to Other Decisions

This decision extends DR-0007.

DR-0007 defines how applications are internally structured through Ports & Adapters.

This decision defines how those applications are organized within the repository.

---

## Next Steps

* [ ] Create the `apps/` directory and migrate existing entrypoints.
* [ ] Introduce the `manager` application.
* [ ] Move FastAPI routes under `manager/adapters/in/api`.
* [ ] Move Qt presentation logic under `manager/adapters/in/desktop`.
* [ ] Update Dockerfiles and packaging scripts to reference the new composition roots.
