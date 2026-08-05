# DR 0010: Formalize `core` as the Shared Kernel

## Status

Proposed

## Date

2026-08-01

## Context and Problem

DR-0007 established Hexagonal Architecture (Ports & Adapters) as the project's architectural style, while DR-0009 reorganized the repository around **business applications** rather than **deployment artifacts**.

During that architectural review, another question emerged:

> Where should concepts that are legitimately shared by multiple applications live?

The project currently contains a top-level package named `core`, which is consumed by the Manager, Worker and Gateway applications.

Over time, `core` has evolved into the place where common abstractions are implemented, including:

* domain events;
* shared domain concepts;
* ports (repository interfaces, service interfaces, protocols);
* common contracts;
* infrastructure adapter implementations.

Although this organization has worked well in practice, the architectural role of `core` has never been explicitly defined.

This creates several risks:

* developers may treat `core` as a generic utilities package;
* application-specific code may gradually migrate into `core`;
* new contributors may assume that all code should be moved into `core` simply because it is reusable;
* the package name obscures its relationship with Domain-Driven Design.

The problem is not that `core` exists.

The problem is that its architectural role has never been explicitly documented.

This decision formalizes that role.

---

## Options Considered

### 1. Keep `core` as a generic shared package

Continue using `core` as a place for reusable code without defining architectural constraints.

**Pros**

* No refactoring required.
* Maximum flexibility.

**Cons**

* No clear ownership.
* High risk of becoming a miscellaneous package.
* Difficult to distinguish domain concepts from implementation details.
* Encourages accidental coupling between applications.

---

### 2. Duplicate domain concepts across applications

Treat Manager, Worker and Gateway as completely independent bounded contexts.

Each application owns its own:

* entities;
* events;
* ports;
* repository interfaces;
* contracts.

**Pros**

* Strong isolation.
* Clear ownership of each model.

**Cons**

* Significant code duplication.
* Increased maintenance.
* High probability of model divergence.
* Does not accurately represent the business domain.

This option was rejected because the current architecture does not contain multiple bounded contexts.

Instead, it contains multiple applications collaborating within a single bounded context.

---

### 3. Introduce a new Shared Kernel package

Rename `core` to a package such as `cnc_domain` or `shared_kernel`.

**Pros**

* Explicit DDD terminology.
* Clear architectural intent.

**Cons**

* Requires extensive refactoring.
* Large number of import changes.
* Little practical benefit beyond improved naming.

Although this option better reflects DDD terminology, the migration cost outweighs the benefits.

The existing package name is well established throughout the project and changing it would provide limited architectural value.

---

### 4. Formalize `core` as the Shared Kernel

Retain the existing package name while explicitly documenting its architectural role.

**Pros**

* No unnecessary refactoring.
* Preserves existing imports.
* Makes the architecture explicit.
* Aligns with the DDD Shared Kernel pattern.

**Cons**

* The package name does not explicitly communicate its purpose.
* Developers must understand the architectural documentation rather than relying solely on naming.

---

## Decision

Adopt **Option 4**.

The package named `core` will remain in the repository.

However, its architectural role is formally redefined as the project's **Shared Kernel**, as described by Domain-Driven Design.

The Shared Kernel represents the common model shared by every application that participates in the CNC Management bounded context.

It is **not**:

* a utilities package;
* a collection of helper functions;
* a dumping ground for reusable code.

Instead, it represents the canonical implementation of concepts that belong to the ubiquitous language shared by multiple applications.

---

## Principles

The following principles govern the evolution of the Shared Kernel.

### The Shared Kernel belongs to a single bounded context

The Shared Kernel exists because the Manager, Worker and Gateway collaborate within the same CNC Management bounded context.

Sharing domain concepts inside a bounded context is encouraged.

Sharing them across unrelated bounded contexts is not.

---

### Shared concepts belong in `core`

Only concepts that are genuinely part of the ubiquitous language should reside in the Shared Kernel.

Typical examples include:

* domain events;
* shared entities;
* value objects;
* identifiers;
* repository interfaces;
* service contracts.

These concepts should have a single canonical implementation.

---

### Application orchestration does not belong in `core`

The Shared Kernel does not coordinate business workflows.

Application services, use cases and orchestration logic remain owned by the corresponding applications.

For example:

* Manager owns business workflows.
* Worker owns background execution workflows.
* Gateway owns gateway-specific application services.

---

### Infrastructure does not belong in the Shared Kernel

Although infrastructure implementations may be shared, they are not part of the domain model.

Repository implementations, logging, storage, messaging and external clients should live outside the Shared Kernel.

This separation is deferred to a future architectural decision.

---

### The Shared Kernel is intentionally conservative

Adding a new component to `core` should require answering the following questions:

* Is this concept part of the CNC Management domain?
* Is it required by multiple applications?
* Would duplicating it create multiple definitions of the same business concept?

If the answer to any of these questions is "no", the component likely belongs elsewhere.

---

## Migration Strategy

The migration should be performed incrementally.

### Phase 1 — Document the Shared Kernel

Retain the existing package structure while documenting `core` as the project's Shared Kernel.

No behavioral changes are required.

---

### Phase 2 — Identify application-specific code

Review the contents of `core` and classify components as:

* shared domain concepts;
* application logic;
* infrastructure.

Application-specific logic should be scheduled for migration into the owning application.

---

### Phase 3 — Preserve shared contracts

Ensure that:

* repository interfaces;
* service interfaces;
* domain events;
* shared value objects;
* identifiers;
* common contracts

remain centralized inside the Shared Kernel.

---

### Phase 4 — Prevent scope expansion

Future pull requests introducing new components into `core` should explicitly justify why those components belong to the Shared Kernel rather than to an individual application.

---

## Consequences

### Positive

* **[+]** The architectural role of `core` becomes explicit.
* **[+]** Shared business concepts have a single canonical implementation.
* **[+]** Unnecessary duplication is avoided.
* **[+]** The repository more closely follows Domain-Driven Design.
* **[+]** Existing imports remain unchanged, minimizing migration effort.

### Negative

* **[-]** The package name alone does not communicate its architectural purpose.
* **[-]** Changes to the Shared Kernel require additional review because they may affect multiple applications.
* **[-]** Developers must exercise discipline to prevent `core` from becoming a generic utilities package.

---

## Relationship to Other Decisions

This decision builds upon:

* **DR-0007**, which introduced Hexagonal Architecture.
* **DR-0009**, which distinguished business applications from deployment artifacts.

While DR-0009 defines **where applications live**, this decision defines **where the common domain model lives**.

---

## Next Steps

* [ ] Document the architectural role of `core` in the project documentation.
* [ ] Review the contents of `core` and classify each component as domain, application or infrastructure.
* [ ] Remove application-specific orchestration from the Shared Kernel.
* [ ] Require architectural review for future additions to `core`.
