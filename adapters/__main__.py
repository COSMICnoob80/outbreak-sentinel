"""Send one risk card through every configured channel.

    python -m adapters --card '{"city":"Karachi","disease":"dengue",...}'

Exits 0 when every channel delivered, 1 when any channel failed or none is
configured, 2 on a bad argument.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from . import REGISTRY, build_channels, fan_out, parse_channels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m adapters",
        description="Fan a risk card out through the configured channels.",
    )
    parser.add_argument("--card", required=True, help="risk card as a JSON object")
    parser.add_argument(
        "--channels",
        default=None,
        help="comma-separated channel list (overrides SENTINEL_CHANNELS)",
    )
    return parser


def parse_card(raw: str) -> dict:
    card = json.loads(raw)
    if not isinstance(card, dict):
        raise ValueError("card must be a JSON object")
    return card


async def dispatch(args: argparse.Namespace) -> int:
    try:
        card = parse_card(args.card)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"invalid --card: {exc}", file=sys.stderr)
        return 2

    channels = build_channels(args.channels)
    if not channels:
        print(
            f"no usable channels in {parse_channels(args.channels)!r} "
            f"(known: {', '.join(sorted(REGISTRY))})",
            file=sys.stderr,
        )
        return 1

    results = await fan_out(card, channels)
    for name, ok in results.items():
        print(f"{name}: {'ok' if ok else 'FAILED'}")
    return 0 if all(results.values()) else 1


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    args = build_parser().parse_args()
    return asyncio.run(dispatch(args))


if __name__ == "__main__":
    sys.exit(main())
