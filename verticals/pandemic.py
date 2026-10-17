"""Pandemic / epidemic early warning — the flagship health vertical.

Acute, multi-region surge detection: news + social + weather. HIGH means a
multi-region case surge is likely. Distinct from endemic (persistent baseline).

Self-contained: adds no runtime dependency and touches no existing file.
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical

PANDEMIC = Vertical(
    slug="pandemic",
    name="Pandemic / Epidemic Early Warning (news + social + weather)",
    description=(
        "Watch for the digital exhaust of an emerging pandemic or epidemic — "
        "multi-region case surges, WHO signals, transmission and variant chatter "
        "corroborated by weather. Surveillance only, never diagnosis."
    ),
    subjects=("influenza", "COVID-19", "respiratory virus", "novel pathogen"),
    subject_label="disease",
    signal_sources=("news", "social", "weather"),
    risk_model=RiskModel(
        high_means=(
            "A multi-region case surge of the named disease is likely within "
            "7-14 days."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) news of rising cases / WHO alert / variant detection across "
            "multiple regions AND (b) social chatter spike on symptoms or "
            "hospital load OR (c) weather favouring transmission. Never HIGH on "
            "a single signal."
        ),
        downgrade_rule=(
            "Drops to MODERATE when official sources report containment or no "
            "new-region spread across two consecutive windows."
        ),
    ),
    keywords=(
        "outbreak",
        "WHO",
        "cases",
        "transmission",
        "variant",
        "epidemic",
        "pandemic",
        "hospital surge",
    ),
    example_queries=(
        "outbreak WHO cases when:24h",
        "variant transmission surge when:24h",
        "hospital patients fever when:24h",
    ),
    locations=(
        Location("Karachi", 24.8607, 67.0011, "PK"),
        Location("Lahore", 31.5204, 74.3587, "PK"),
        Location("London", 51.5074, -0.1278, "GB"),
        Location("New York", 40.7128, -74.0060, "US"),
        Location("Singapore", 1.3521, 103.8198, "SG"),
    ),
    forecast_vars=(
        "temperature_2m_max",
        "precipitation_sum",
        "weathercode",
    ),
    lookback_hours=24,
    fusion_role="pandemic risk analyst",
)