"""Delivery-adapter layer: one card, many surfaces.

The universality unlock — the fusion core stays domain-agnostic and each new
delivery surface is a new module plus one registry entry.

Channel selection is env-driven:

    SENTINEL_CHANNELS=console,webhook,file   # default: console

Channel configuration:
    SENTINEL_WEBHOOK_URL   target for the webhook channel
    SENTINEL_ALERT_FILE    JSONL destination for the file channel
"""
from __future__ import annotations

import logging
import os
from typing import Iterable

from .base import CARD_FIELDS, Channel
from .console import ConsoleChannel
from .file import FileChannel
from .webhook import WebhookChannel

log = logging.getLogger(__name__)

REGISTRY: dict[str, type[Channel]] = {
    "console": ConsoleChannel,
    "webhook": WebhookChannel,
    "file": FileChannel,
}

DEFAULT_CHANNELS = "console"

__all__ = [
    "CARD_FIELDS",
    "DEFAULT_CHANNELS",
    "REGISTRY",
    "Channel",
    "ConsoleChannel",
    "FileChannel",
    "WebhookChannel",
    "build_channels",
    "fan_out",
    "parse_channels",
]


def parse_channels(spec: str | None = None) -> list[str]:
    """Resolve the channel list from an explicit spec or the environment."""
    raw = spec if spec is not None else os.environ.get("SENTINEL_CHANNELS", "")
    names = [name.strip().lower() for name in raw.split(",") if name.strip()]
    return names or [DEFAULT_CHANNELS]


def build_channels(spec: str | None = None) -> list[Channel]:
    channels: list[Channel] = []
    for name in parse_channels(spec):
        cls = REGISTRY.get(name)
        if cls is None:
            log.warning(
                "adapters: unknown channel %r (known: %s)",
                name,
                ", ".join(sorted(REGISTRY)),
            )
            continue
        channels.append(cls())
    return channels


async def fan_out(
    card: dict, channels: Iterable[Channel] | None = None
) -> dict[str, bool]:
    """Send one card through every configured channel. Never raises."""
    chans = list(channels) if channels is not None else build_channels()
    results: dict[str, bool] = {}
    for channel in chans:
        try:
            results[channel.name] = bool(await channel.send(card))
        except Exception as exc:  # defensive: keep the boundary honest
            log.warning("adapters: channel %s raised: %s", channel.name, exc)
            results[channel.name] = False
    return results
