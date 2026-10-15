"""Bio-surveillance — the first vertical.

This is the dengue / malaria / cholera setup Outbreak Sentinel shipped with,
expressed declaratively. It is derived from ``config.yaml`` so the definition
and the shipping config cannot drift. ``config.yaml`` is READ-ONLY here.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from verticals.base import Location, RiskModel, Vertical

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

_DEFAULT_CITIES = [
    {"name": "Karachi", "lat": 24.8607, "lon": 67.0011},
    {"name": "Lahore", "lat": 31.5204, "lon": 74.3587},
    {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479},
    {"name": "Peshawar", "lat": 34.0151, "lon": 71.5249},
    {"name": "Quetta", "lat": 30.1798, "lon": 66.9750},
]
_DEFAULT_DISEASES = ["dengue", "malaria", "cholera", "typhoid", "hepatitis"]
_DEFAULT_NEWS_KEYWORDS = [
    "dengue outbreak", "malaria cases", "cholera", "typhoid",
    "hepatitis", "fever outbreak", "hospital patients",
]


def _load_config() -> dict:
    """Read config.yaml if present; fall back to baked-in defaults on any error."""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


_CFG = _load_config()


def _locations() -> tuple[Location, ...]:
    cities = _CFG.get("cities") or _DEFAULT_CITIES
    return tuple(
        Location(name=c["name"], lat=c["lat"], lon=c["lon"], country="PK")
        for c in cities
    )


BIO_SURVEILLANCE = Vertical(
    slug="bio-surveillance",
    name="Bio-Surveillance (disease outbreak early warning)",
    description=(
        "Watch Pakistan cities for the digital exhaust of a brewing outbreak — "
        "news upticks, panic chatter, and vector-friendly weather — days before "
        "official confirmation. Surveillance only, never diagnosis."
    ),
    subjects=tuple(_CFG.get("diseases") or _DEFAULT_DISEASES),
    subject_label="disease",
    signal_sources=("news", "weather", "social"),
    risk_model=RiskModel(
        high_means=(
            "A city is likely to see an outbreak of the named disease within 7 days."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) a news uptick in a 24h window (>=10 articles) AND (b) vector-"
            "friendly weather (heavy rain >=50mm or sustained heat >=35C) or "
            "(c) panic sentiment >=0.6. Never HIGH on a single signal."
        ),
        downgrade_rule=(
            "Drops to MODERATE when the ministry confirms/denies within 24h, or "
            "when no news uptick recurs across two consecutive windows."
        ),
    ),
    keywords=tuple(_CFG.get("news_keywords") or _DEFAULT_NEWS_KEYWORDS),
    example_queries=(
        "dengue outbreak pakistan when:24h",
        "hospital patients fever pakistan when:24h",
        "cholera karachi when:24h",
    ),
    locations=_locations(),
    forecast_vars=("temperature_2m_max", "precipitation_sum", "weathercode"),
    lookback_hours=int(_CFG.get("lookback_hours", 24)),
    fusion_role="outbreak risk analyst for Pakistan",
)
