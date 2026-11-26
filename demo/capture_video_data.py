"""Capture every string the demo video may render, into one JSON bundle.

Two sources of truth only:

1. LIVE HTTP responses already written to ``state/video-capture/*.json`` by
   ``demo/capture_video_data.sh`` (curl against the Render deployment).
2. A FORCED-FALLBACK weather run: the shipped ``app.fetch_weather`` executed
   with ``_fetch_open_meteo`` replaced by the exact 429 the deployment really
   returned on 2026-11-25, so real MET Norway data flows through the real
   fallback branch. Nothing is hand-written; every number below comes out of a
   call.

Output: ``state/video-capture/snapshot.json``. The builder reads ONLY this file.
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAP = ROOT / "state" / "video-capture"
sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402

import app  # noqa: E402


def _load(name: str) -> dict:
    path = CAP / name
    if not path.exists():
        raise SystemExit(f"missing live capture: {path} — run capture_video_data.sh first")
    return json.loads(path.read_text())


async def _forced_met_fallback() -> dict:
    """Run the real fetch_weather with Open-Meteo replaying its real 429."""
    real_open_meteo = app._fetch_open_meteo

    async def quota_dead(session, city):
        # The verbatim condition the deployment returned on 2026-11-25.
        return {
            "city": city["name"],
            "error": "HTTP 429",
            "http_status": 429,
            "retry_after": 33776,
            "detail": '{"reason":"Daily API request limit exceeded. '
                      'Please try again tomorrow.","error":true}',
        }

    app._fetch_open_meteo = quota_dead
    cities = app._unique_cities(
        list(app.CONFIG.get("cities") or []) + list(app.CONFIG.get("wildfire_cities") or [])
    )
    try:
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                *[app.fetch_weather(session, city) for city in cities]
            )
    finally:
        app._fetch_open_meteo = real_open_meteo

    rows = [
        {
            "city": r.get("city"),
            "provider": r.get("provider"),
            "ok": bool(r.get("forecast")),
            "forecast_days": len(r.get("forecast") or []),
            "error": r.get("error"),
        }
        for r in results
    ]
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "condition_replayed": "Open-Meteo HTTP 429 daily-quota (verbatim 2026-11-25 reply)",
        "configured_cities": len(cities),
        "attempted_cities": len(rows),
        "ok": sum(1 for r in rows if r["ok"]),
        "failed": sum(1 for r in rows if not r["ok"]),
        "served_by": sorted({r["provider"] for r in rows if r["provider"]}),
        "cities": rows,
    }


async def _onchain_receipt(tx_hash: str, rpc_url: str) -> dict:
    """Read-only eth_getTransactionReceipt — proves the tx really settled.

    No wallet, no signing, no spend: a single JSON-RPC read so the video's
    block number is a captured fact, not a number copied from a markdown file.
    """
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "eth_getTransactionReceipt", "params": [tx_hash],
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(rpc_url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as r:
            body = await r.json(content_type=None)
    result = body.get("result") or {}
    block = result.get("blockNumber")
    return {
        "rpc_url": rpc_url,
        "tx_hash": tx_hash,
        "status": result.get("status"),
        "block_number": int(block, 16) if isinstance(block, str) else None,
        "to": result.get("to"),
        "from": result.get("from"),
        "log_count": len(result.get("logs") or []),
        "found": bool(result),
    }


def main() -> None:
    risk = _load("risk.json")
    cards = risk.get("risk_cards") or []
    by_city_vertical = {(c.get("city"), c.get("vertical")): c for c in cards}

    def pick(city, vertical):
        c = by_city_vertical.get((city, vertical))
        if not c:
            raise SystemExit(f"card missing from live /risk: {city}/{vertical}")
        return c

    def card_brief(c):
        srcs = c.get("sources") or []
        return {
            "city": c.get("city"),
            "vertical": c.get("vertical"),
            "disease": c.get("disease"),
            "risk_level": c.get("risk_level"),
            "risk_score": c.get("risk_score"),
            "confidence": c.get("confidence"),
            "drivers": c.get("drivers") or [],
            "evidence_line": c.get("evidence_line"),
            "evidence_count": c.get("evidence_count"),
            "summary": c.get("summary"),
            "recommendation": c.get("recommendation"),
            "sources": [
                {
                    "title": s.get("title"),
                    "outlet": s.get("outlet"),
                    "published": s.get("published"),
                    "url": s.get("url"),
                }
                for s in srcs
            ],
            "source_count": len(srcs),
            "chart": c.get("chart") or [],
        }

    levels = Counter(c.get("risk_level") for c in cards)
    verticals = Counter(c.get("vertical") for c in cards)

    fallback = asyncio.run(_forced_met_fallback())
    status = _load("telegraph_status.json")
    settlement = status.get("last_settlement") or {}
    onchain = asyncio.run(
        _onchain_receipt(settlement.get("tx_hash"), status.get("rpc_url"))
    )

    bundle = {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "live_base": "https://outbreak-sentinel.onrender.com",
        "health": _load("health.json"),
        "telegraph_status": _load("telegraph_status.json"),
        "telegraph_stats": _load("telegraph_stats.json"),
        "debug_weather": _load("debug_weather.json"),
        "receipts": _load("receipts.json"),
        "scoreboard": _load("scoreboard.json"),
        "cities": _load("cities.json"),
        "grid": {
            "card_count": len(cards),
            "city_count": len({c.get("city") for c in cards}),
            "levels": dict(levels),
            "verticals": dict(verticals),
            "engine": risk.get("engine"),
            "timestamp": risk.get("timestamp"),
            "signals": risk.get("signals") or {},
        },
        "hero_la_wildfire": card_brief(pick("Los Angeles", "wildfire")),
        "london_dengue": card_brief(pick("London", "bio-surveillance")),
        "cape_town_wildfire": card_brief(pick("Cape Town", "wildfire")),
        "empty_bio": card_brief(pick("Karachi", "bio-surveillance")),
        "weather_forces_fallback": fallback,
        "onchain_settlement": onchain,
    }

    out = CAP / "snapshot.json"
    out.write_text(json.dumps(bundle, indent=1, ensure_ascii=False))
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    print(
        f"grid: {bundle['grid']['card_count']} cards, "
        f"{bundle['grid']['city_count']} cities, levels={bundle['grid']['levels']}"
    )
    print(
        f"fallback: {fallback['ok']}/{fallback['attempted_cities']} "
        f"via {fallback['served_by']}"
    )
    print(
        f"onchain: status={onchain['status']} block={onchain['block_number']} "
        f"to={onchain['to']}"
    )


if __name__ == "__main__":
    main()
