"""Macro financial-stress early warning — Wall Street angle.

Macro financial-stress: news + social. HIGH = escalation. Keywords: default,
sanction, volatility, central bank. Maps to Telegraph Mission 05 (Conflict
Intelligence — "an escalation score that traces to a specific input").

Self-contained: adds no runtime dependency and touches no existing file.
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical

FINANCIAL_STRESS = Vertical(
    slug="financial-stress",
    name="Macro Financial-Stress Early Warning (news + social)",
    description=(
        "Watch macro financial stress — sovereign default risk, sanctions, "
        "volatility spikes and central-bank shocks — from news and social "
        "chatter, producing an escalation score traceable to a specific input."
    ),
    subjects=(
        "sovereign default",
        "sanctions",
        "volatility spike",
        "central bank shock",
    ),
    subject_label="stressor",
    signal_sources=("news", "social"),
    risk_model=RiskModel(
        high_means=(
            "A macro financial-stress escalation (default, sanction, or "
            "volatility shock) is likely within 7 days."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) news of a default / sanction / volatility event AND (b) social "
            "chatter spike on the same stressor. Never HIGH on a single signal."
        ),
        downgrade_rule=(
            "Drops to MODERATE when markets stabilize or official sources "
            "clarify across two consecutive windows."
        ),
    ),
    keywords=(
        "default",
        "sanction",
        "volatility",
        "central bank",
        "market crash",
        "credit downgrade",
        "capital flight",
    ),
    example_queries=(
        "sovereign default sanction when:24h",
        "market volatility central bank when:24h",
    ),
    locations=(
        Location("New York", 40.7128, -74.0060, "US"),
        Location("London", 51.5074, -0.1278, "GB"),
        Location("Tokyo", 35.6762, 139.6503, "JP"),
        Location("Hong Kong", 22.3193, 114.1694, "HK"),
        Location("Frankfurt", 50.1109, 8.6821, "DE"),
    ),
    forecast_vars=(
        "temperature_2m_max",
        "weathercode",
    ),
    lookback_hours=24,
    fusion_role="financial stress analyst",
)