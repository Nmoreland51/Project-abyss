"""Versioned ranking formulas. See docs/adr/0003-ranking-and-pagination.md.

These are this platform's own published formulas; they are not claimed to match any other
service's ranking. Changing a formula requires a new version string and a recorded decision."""

import math
from datetime import UTC, datetime

HOT_FORMULA_VERSION = "hot-v1"
CONTROVERSY_FORMULA_VERSION = "controversy-v1"

# Fixed epoch keeps the time term numerically small and stable across deployments.
RANK_EPOCH = datetime(2026, 1, 1, tzinfo=UTC)
HOT_TIME_DIVISOR = 45000.0


def hot_rank(score: int, created_at: datetime) -> float:
    order = math.log10(max(abs(score), 1))
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = (created_at - RANK_EPOCH).total_seconds()
    return round(sign * order + seconds / HOT_TIME_DIVISOR, 7)


def controversy(upvotes: int, downvotes: int) -> float:
    if upvotes <= 0 or downvotes <= 0:
        return 0.0
    magnitude = upvotes + downvotes
    balance = min(upvotes, downvotes) / max(upvotes, downvotes)
    return round(magnitude**balance, 7)
