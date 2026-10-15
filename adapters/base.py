"""Channel contract — one interface, many delivery surfaces."""
from __future__ import annotations

import abc

CARD_FIELDS = (
    "city",
    "disease",
    "risk_level",
    "confidence",
    "drivers",
    "recommendation",
)


class Channel(abc.ABC):
    """A delivery surface for a risk card.

    A card is the dict emitted by outbreak_sentinel.py:
    {city, disease, risk_level, confidence, drivers[], recommendation}
    plus an optional receipt_id when the card was published to the ledger.

    Implementations must not raise from send(): return False instead, so one
    dead channel can never take down a fan-out.
    """

    name: str = "channel"

    @abc.abstractmethod
    async def send(self, card: dict) -> bool:
        """Deliver one card. Returns True on success, False otherwise."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
