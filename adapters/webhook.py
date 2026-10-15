"""Webhook channel — POSTs the card as JSON to any URL.

Target comes from SENTINEL_WEBHOOK_URL. This is the surface that makes the
platform integrable with Slack/Discord/IFTTT/n8n-style endpoints without
touching the fusion core.
"""
from __future__ import annotations

import logging
import os

import aiohttp

from .base import Channel

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15


class WebhookChannel(Channel):
    name = "webhook"

    def __init__(self, url: str | None = None):
        self.url = (url or os.environ.get("SENTINEL_WEBHOOK_URL") or "").strip()

    async def send(self, card: dict) -> bool:
        if not self.url:
            log.warning("webhook: SENTINEL_WEBHOOK_URL is not set, skipping")
            return False
        try:
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.url, json=card) as resp:
                    if 200 <= resp.status < 300:
                        return True
                    log.warning("webhook: HTTP %s from %s", resp.status, self.url)
                    return False
        except Exception as exc:  # a failed channel is not a failed run
            log.warning("webhook: delivery to %s failed: %s", self.url, exc)
            return False
