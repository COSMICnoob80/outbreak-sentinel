"""Console channel — the default surface, for humans and for logs."""
from __future__ import annotations

from .base import Channel


def format_card(card: dict) -> str:
    level = str(card.get("risk_level", "UNKNOWN")).upper()
    lines = [f"[{level}] {card.get('city', 'Unknown')} — {card.get('disease', 'unknown')}"]
    confidence = card.get("confidence")
    if isinstance(confidence, (int, float)):
        lines.append(f"  confidence: {confidence:.0%}")
    for driver in card.get("drivers") or []:
        lines.append(f"  - {driver}")
    if card.get("recommendation"):
        lines.append(f"  recommendation: {card['recommendation']}")
    if card.get("receipt_id"):
        lines.append(f"  receipt: {card['receipt_id']}")
    return "\n".join(lines)


class ConsoleChannel(Channel):
    name = "console"

    async def send(self, card: dict) -> bool:
        print(format_card(card), flush=True)
        return True
