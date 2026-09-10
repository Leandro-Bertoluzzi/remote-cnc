"""Gateway infrastructure constants.

They should NOT be imported by domain or application code; use
``core.domain.gateway`` for business-level constants instead.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Session defaults
# ---------------------------------------------------------------------------

SESSION_TTL_SECONDS = 300  # 5 minutes
