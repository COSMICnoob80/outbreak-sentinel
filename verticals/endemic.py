"""Endemic disease surveillance — persistent baseline monitoring.

Dengue/malaria baseline monitoring: lower-severity, continuous. Distinct from
pandemic (acute multi-region surge). Signals: news + weather.

Self-contained: adds no runtime dependency and touches no existing file.
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical

ENDEMIC = Vertical(
    slug="endemic",
    name="Endemic Disease Surveillance (dengue/malaria baseline)",
    description=(
        "Continuously monitor endemic diseases (dengue, malaria) against their "
        "seasonal baseline — lower-severity, persistent monitoring rather than "
        "acute surge detection."
    ),
    subjects=("dengue", "malaria"),
    subject_label="disease",
    signal_sources=("news", "weather"),
    risk_model=RiskModel(
        high_means=(
            "An endemic disease is exceeding its seasonal baseline in a "
            "monitored area."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) news of cases above the seasonal norm AND (b) vector-friendly "
            "weather (heavy rain >=50mm or sustained heat >=35C). Baseline "
            "monitoring stays MODERATE on a single signal."
        ),
        downgrade_rule=(
            "Drops to MODERATE when case reports return to seasonal baseline "
            "across two consecutive windows."
        ),
    ),
    keywords=(
        "dengue cases",
        "malaria cases",
        "endemic",
        "seasonal baseline",
        "vector breeding",
        "fever outbreak",
    ),
    example_queries=(
        "dengue cases pakistan when:72h",
        "malaria seasonal baseline when:72h",
    ),
    locations=(
        Location("Karachi", 24.8607, 67.0011, "PK"),
        Location("Lahore", 31.5204, 74.3587, "PK"),
        Location("Islamabad", 33.6844, 73.0479, "PK"),
        Location("Peshawar", 34.0151, 71.5249, "PK"),
        Location("Quetta", 30.1798, 66.9750, "PK"),
    ),
    forecast_vars=(
        "temperature_2m_max",
        "precipitation_sum",
        "weathercode",
    ),
    lookback_hours=72,
    fusion_role="endemic disease surveillance analyst",
)