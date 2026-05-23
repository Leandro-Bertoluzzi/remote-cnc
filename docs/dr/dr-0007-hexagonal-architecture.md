# DR 0007: Adopt Hexagonal Architecture (Ports & Adapters) Across the Monorepo

## Status

Accepted

## Date

2026-05-19

## Context and Problem

All application modules in the monorepo (`api`, `worker`, `desktop`, `gateway`) depend
directly on concrete infrastructure implementations:

- `GrblController` — the class owning the serial connection to the CNC device.
- `redis.Redis` — the Redis client used for queuing, pub/sub, and state storage.
- SQLAlchemy models — ORM entities used directly in business logic.
- Other concrete adapters (serial ports, file system helpers, etc.)

This tight coupling produces several recurring problems at every level:

1. **Testing**: unit tests must instantiate or mock concrete classes that carry
   heavyweight dependencies (serial ports, live Redis, database sessions).
   Pylance/pyright also reports type errors when lightweight test fakes are
   passed where concrete classes are expected (e.g. `FakeController` for
   `GrblController`).

2. **Replaceability**: swapping an implementation (e.g. replacing `redis.Redis`
   with an in-process mock, or `GrblController` with a simulation backend)
   requires modifying the consuming code rather than just supplying a different
   object.

3. **Layer boundary clarity**: it is not obvious from reading application code
   which dependencies are _capabilities needed_ (ports) versus _chosen
   implementations_ (adapters). This makes the architecture harder to reason
   about and document.

The problem is not isolated to any single module; it is a cross-cutting concern
shared by all packages in the monorepo.

## Options Considered

1. **Status quo — no abstraction layer**
    - Pros: no additional files, no learning curve.
    - Cons: the three problems above persist and worsen as the codebase grows.

2. **Abstract base classes (`abc.ABC`)**
    - Pros: familiar Python pattern; explicit method contracts.
    - Cons: requires modifying existing classes (`GrblController`, `redis.Redis`)
      to add inheritance — invasive and not feasible for third-party code.

3. **`typing.Protocol` — structural subtyping (PEP 544)**
    - Pros: no modification of existing classes required; `GrblController` and
      `redis.Redis` satisfy protocols automatically by their shape (_duck typing_
      verified statically by Pylance/pyright); lightweight; the idiomatic modern
      Python approach for this pattern.
    - Cons: slight increase in the number of files; protocols must be kept in
      sync with the actual interface they describe.

4. **Full hexagonal architecture with explicit adapter wrappers**
    - Pros: maximum separation; each adapter is its own class.
    - Cons: significant upfront work; premature for the current project size.

## Decision

Adopt the **Ports & Adapters** pattern (also known as _Hexagonal Architecture_)
across the entire monorepo, implemented via `typing.Protocol`.

### Principles

- **Ports** are `typing.Protocol` classes that describe exactly the capabilities
  a module _needs_. They live in the module that _consumes_ them, not in the
  module that provides the implementation.
- **Adapters** are the concrete implementations (e.g. `GrblController`,
  `redis.Redis`). They are never imported by application-layer code, only by
  _composition roots_ (`main.py`, application factories, test fixtures).
- **Shared ports** (abstractions used by more than one package) are placed in
  `core/core/ports/` to avoid duplication.
- **Composition roots** are the only places where adapters are instantiated and
  injected.

### Domain and persistence boundaries

- SQLAlchemy ORM models are infrastructure concerns and live exclusively under
  `core/core/adapters/database/`.
- Domain/application layers (`core/domain`, ports, API routes, worker tasks,
  desktop services/views/components) must consume **domain entities**, never
  ORM classes.
- Repository adapters are responsible for mapping ORM ↔ domain through explicit
  mappers.

### Migration strategy

The adoption is incremental to minimize risk:

- **Phase 1 — `gateway` (this decision):** define `CncController` and
  `RedisClient` protocols; update all gateway components to depend on protocols
  only. Validate that tests pass and Pylance reports zero errors. Move `core.utilities.grbl.*`
  (currently used only by `gateway`) into the `gateway` package, making it a
  proper adapter hidden behind `CncController`.
- **Phase 2 — `api` and `worker`:** apply the same pattern to their Redis
  usage and any other infrastructure dependencies.
- **Phase 3 — `desktop`:** apply to Qt-independent business logic.

## Consequences

- **[+]** Unit tests can pass lightweight fakes (e.g. `FakeController`) without
  type errors from linters.
- **[+]** Application modules are decoupled from third-party library internals;
  replacing `redis.Redis` with a different client only requires the new class to
  satisfy the protocol.
- **[+]** Layer boundaries are explicit and machine-verifiable: if an
  application file imports a concrete adapter, the type checker can flag it.
- **[+]** `typing.Protocol` requires zero changes to `GrblController` or
  `redis.Redis`.
- **[-]** Each module grows a `ports/` sub-package that must be maintained in
  sync with the protocols it defines.
- **[-]** Developers unfamiliar with the pattern may initially place imports in
  the wrong layer; code review must enforce the composition-root rule.

## Next Steps

- [ ] Phase 1: implement `core/core/ports/redis_client.py` and
      `gateway/gateway/ports/cnc_controller.py`; update all four gateway components.
- [ ] Phase 2: extend `RedisClient` usage to `api` and `worker` packages.
- [ ] Phase 3: apply to `desktop`.
