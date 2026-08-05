# DR 0011: Centralize Reusable Infrastructure Adapters

## Status

Proposed

## Date

2026-08-01

## Context and Problem

DR-0010 formalized the existing `core` package as the project's **Shared Kernel**, establishing it as the canonical home for shared domain concepts and contracts.

During that review, another architectural issue became apparent.

The project currently contains several infrastructure implementations that are shared by multiple applications, including:

* repository implementations;
* logging implementations;
* file storage implementations;
* publish/subscribe implementations;
* Gateway clients;
* Worker clients;
* external service integrations.

Historically, many of these implementations have been located inside `core` because they are reused by multiple applications.

Although this avoids duplication, it introduces an architectural inconsistency.

The Shared Kernel represents the common **domain model** of the CNC Management bounded context.

Infrastructure implementations are not part of that domain model.

They are implementation details that satisfy ports defined by the applications or the Shared Kernel.

Keeping infrastructure inside `core` gradually blurs the distinction between:

* business abstractions;
* implementation details.

Conversely, duplicating identical infrastructure implementations inside every application would introduce unnecessary maintenance costs and increase the probability of behavioral divergence.

The architecture therefore requires a location where reusable infrastructure implementations can reside without becoming part of the domain model.

---

## Options Considered

### 1. Duplicate infrastructure per application

Each application owns its own repository implementations, logging adapters, storage implementations and external clients.

**Pros**

* Clear ownership.
* Strong application isolation.

**Cons**

* Significant duplication.
* Higher maintenance costs.
* Increased risk of implementation drift.
* Difficult to apply infrastructure improvements consistently.

This option was rejected because the duplicated components would represent identical implementations rather than different business behaviors.

---

### 2. Keep infrastructure inside `core`

Continue storing shared infrastructure implementations inside the Shared Kernel.

**Pros**

* Minimal repository changes.
* No refactoring required.
* Easy code reuse.

**Cons**

* Mixes domain and infrastructure.
* Violates the architectural responsibility established by DR-0010.
* Makes the Shared Kernel progressively harder to understand.
* Encourages treating `core` as a generic shared package.

This option was rejected because it weakens the conceptual separation introduced by Hexagonal Architecture.

---

### 3. Move infrastructure into each deployment package

Store infrastructure implementations inside:

* Manager
* Worker
* Gateway

depending on where they are currently used.

**Pros**

* Clear ownership.

**Cons**

* Shared implementations become fragmented.
* Increased duplication.
* Makes reuse more difficult.
* Infrastructure becomes coupled to application packages.

Although viable for application-specific adapters, this option is not appropriate for implementations intentionally shared across multiple applications.

---

### 4. Introduce a shared infrastructure package

Create a dedicated top-level package responsible exclusively for reusable infrastructure implementations.

**Pros**

* Preserves separation between domain and infrastructure.
* Eliminates duplicated implementations.
* Makes dependency direction explicit.
* Improves discoverability.
* Aligns with Ports & Adapters.

**Cons**

* Introduces another top-level package.
* Requires migrating existing adapters.

---

## Decision

Adopt **Option 4**.

Introduce a new top-level package:

```text
infrastructure/
```

The package contains reusable implementations of outbound adapters shared by multiple applications.

Typical contents include:

```text
infrastructure/
    repositories/
    logging/
    storage/
    pubsub/
    gateway_client/
    worker_client/
```

The package contains implementations only.

Ports remain owned by the consuming application or by the Shared Kernel.

For example:

```text
core/
    ports/
        task_repository.py
        logger.py
        gateway_client.py
```

may be implemented by:

```text
infrastructure/
    repositories/
        sqlalchemy_task_repository.py

    logging/
        structlog_logger.py

    gateway_client/
        http_gateway_client.py
```

Applications depend only on the ports.

Composition roots decide which implementation should be instantiated.

---

## Principles

The following principles govern the infrastructure layer.

### Ports define required capabilities

Applications and the Shared Kernel define the capabilities they require through ports.

Infrastructure satisfies those contracts.

Ownership of a port always belongs to its consumer rather than its implementation.

---

### Infrastructure implements, but never defines, business behavior

Infrastructure is responsible for technical concerns such as:

* persistence;
* messaging;
* logging;
* file systems;
* external APIs;
* communication protocols.

It does not define business rules.

Business behavior remains inside the application and domain layers.

---

### Infrastructure may be reused

Unlike application services, infrastructure implementations are intentionally reusable.

Multiple applications may safely depend on the same repository implementation or logging adapter provided they satisfy the same port.

This reuse is considered an implementation optimization rather than shared business logic.

---

### Infrastructure depends inward

Infrastructure may depend on:

* `core`;
* Manager;
* Worker;
* Gateway.

Applications must never depend on infrastructure abstractions.

Instead, they depend exclusively on ports.

Dependency injection performed by composition roots connects applications with their infrastructure implementations.

---

### Composition roots assemble the application

Applications never instantiate infrastructure directly.

Instead, each deployment entrypoint is responsible for selecting and wiring concrete implementations.

This principle complements the repository organization introduced in DR-0009.

---

## Migration Strategy

The migration should be incremental.

### Phase 1 — Create the infrastructure package

Introduce the new top-level package while preserving the existing implementations.

No behavioral changes are required.

---

### Phase 2 — Move reusable adapters

Relocate reusable implementations from `core` into the new package.

Typical candidates include:

* repository implementations;
* logging adapters;
* storage implementations;
* messaging adapters;
* Gateway clients;
* Worker clients.

Ports remain unchanged.

---

### Phase 3 — Update composition roots

Modify each deployment entrypoint to instantiate infrastructure from the new package.

Applications should continue depending exclusively on ports.

---

### Phase 4 — Remove obsolete implementations

Once all applications have migrated, remove duplicated infrastructure implementations and any remaining implementation code from `core`.

The Shared Kernel should contain contracts only.

---

### Phase 5 — Review future additions

Future infrastructure implementations should be evaluated according to the following criteria:

* Does this implement an existing port?
* Is it reused by multiple applications?
* Does it contain only technical concerns?

If so, it belongs in `infrastructure`.

Otherwise, it should remain owned by the corresponding application.

---

## Consequences

### Positive

* **[+]** Clear separation between domain and infrastructure.
* **[+]** The Shared Kernel remains focused on business concepts.
* **[+]** Infrastructure implementations are no longer duplicated.
* **[+]** Dependency direction becomes more explicit.
* **[+]** Future infrastructure technologies can be introduced without modifying business logic.

### Negative

* **[-]** Additional top-level package increases repository size.
* **[-]** Existing imports require migration.
* **[-]** Developers must distinguish carefully between reusable infrastructure and application-specific adapters.

---

## Relationship to Other Decisions

This decision completes the architectural organization introduced by the previous ADRs.

* **DR-0007** established Hexagonal Architecture.
* **DR-0009** separated architectural modules from deployment artifacts.
* **DR-0010** formalized `core` as the Shared Kernel.

This decision defines where reusable implementations of ports belong, ensuring that:

* business concepts remain inside the Shared Kernel;
* business orchestration remains inside the applications;
* reusable infrastructure remains inside `infrastructure`;
* deployment-specific composition remains inside `apps`.

Together, these decisions establish a consistent separation of responsibilities across the entire repository.

---

## Next Steps

* [ ] Create the `infrastructure` package.
* [ ] Move reusable repository implementations from `core`.
* [ ] Move logging implementations from `core`.
* [ ] Move storage implementations from `core`.
* [ ] Move messaging implementations from `core`.
* [ ] Move Gateway and Worker client implementations from `core`.
* [ ] Update composition roots to instantiate infrastructure from the new package.
* [ ] Remove remaining infrastructure implementations from the Shared Kernel.
