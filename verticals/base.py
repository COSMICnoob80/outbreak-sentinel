"""Vertical abstraction — the seam that makes the engine universal.

Outbreak Sentinel is not a dengue app. The engine
(fetch signals -> fuse with an LLM -> emit a risk card -> persist a receipt ->
resolve against reality) is domain-agnostic. A :class:`Vertical` is the *only*
thing that differs between domains: what to watch, which signals to pull, how
to read the weather, and what "HIGH" means.

No new dependencies — stdlib dataclasses only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Location:
    """A place a vertical monitors."""

    name: str
    lat: float
    lon: float
    country: str = ""


@dataclass(frozen=True)
class RiskModel:
    """Calibration contract.

    Every vertical must state, in words, what HIGH means and what moves a card
    up or down. Writing it down is what keeps the false-positive budget honest.
    """

    high_means: str
    escalation_rule: str
    downgrade_rule: str
    levels: tuple[str, ...] = ("LOW", "MODERATE", "HIGH", "CRITICAL")

    def as_dict(self) -> dict[str, Any]:
        return {
            "high_means": self.high_means,
            "escalation_rule": self.escalation_rule,
            "downgrade_rule": self.downgrade_rule,
            "levels": list(self.levels),
        }


@dataclass(frozen=True)
class Vertical:
    """A declarative early-warning domain.

    Adding a vertical means filling this in. Nothing in the engine changes.
    """

    slug: str
    name: str
    description: str
    subjects: tuple[str, ...]
    subject_label: str
    signal_sources: tuple[str, ...]
    risk_model: RiskModel
    keywords: tuple[str, ...]
    example_queries: tuple[str, ...]
    locations: tuple[Location, ...] = ()
    forecast_vars: tuple[str, ...] = (
        "temperature_2m_max",
        "precipitation_sum",
        "weathercode",
    )
    lookback_hours: int = 24
    fusion_role: str = "risk analyst"

    def to_config(self) -> dict[str, Any]:
        """Compile this Vertical into the dict the shipping engine already reads.

        This is the adapter seam: the existing loader (``load_config`` in
        ``outbreak_sentinel.py``) consumes ``cities`` / ``diseases`` /
        ``news_keywords`` / ``social_keywords`` / ``lookback_hours``. A Vertical
        compiles down to exactly that, so the engine is reused untouched.
        """
        return {
            "cities": [
                {"name": loc.name, "lat": loc.lat, "lon": loc.lon}
                for loc in self.locations
            ],
            # The engine names its subject axis "diseases"; a Vertical is agnostic
            # (a disease, a hazard, a chokepoint). Map subjects -> that key.
            "diseases": list(self.subjects),
            "news_keywords": list(self.keywords),
            "social_keywords": list(self.keywords),
            "lookback_hours": self.lookback_hours,
            "_vertical": {
                "slug": self.slug,
                "name": self.name,
                "subject_label": self.subject_label,
                "signal_sources": list(self.signal_sources),
                "forecast_vars": list(self.forecast_vars),
                "fusion_role": self.fusion_role,
                "risk_model": self.risk_model.as_dict(),
            },
        }

    def describe(self) -> str:
        """One-block human summary — used by docs and the demo script."""
        lines = [
            f"{self.name}  [{self.slug}]",
            f"  {self.description}",
            f"  watches:   {', '.join(self.subjects)}  ({self.subject_label})",
            f"  signals:   {', '.join(self.signal_sources)}",
            f"  weather:   {', '.join(self.forecast_vars)}",
            f"  lookback:  {self.lookback_hours}h",
            f"  HIGH means: {self.risk_model.high_means}",
        ]
        if self.locations:
            lines.append(
                f"  locations: {', '.join(loc.name for loc in self.locations)}"
            )
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
