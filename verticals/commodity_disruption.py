"""Commodity disruption early warning — supply-chain/commodity angle.

Supply-chain/commodity disruption: drought/frost hits agriculture. HIGH = commodity
price-shock risk. Signals: news + weather. Maps to Telegraph Mission 08
(Commodities) and Mission 06 (Resources & Agriculture).

Self-contained: adds no runtime dependency and touches no existing file.
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical

COMMODITY_DISRUPTION = Vertical(
    slug="commodity-disruption",
    name="Commodity Disruption Early Warning (news + weather)",
    description=(
        "Watch agricultural commodity supply for price-shock risk — harvest "
        "failures, drought, frost, export bans and port/logistics disruption "
        "corroborated by weather at producing regions."
    ),
    subjects=("wheat", "corn", "soybeans", "rice", "coffee"),
    subject_label="commodity",
    signal_sources=("news", "weather"),
    risk_model=RiskModel(
        high_means=(
            "A monitored agricultural commodity faces price-shock risk from "
            "supply disruption within 14 days."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) news of a harvest failure / drought / export ban / port or "
            "logistics disruption AND (b) adverse weather at a producing region "
            "(drought, frost, or heavy precip). Never HIGH on a single signal."
        ),
        downgrade_rule=(
            "Drops to MODERATE when supply reports normalize or the weather "
            "window passes without further disruption reports."
        ),
    ),
    keywords=(
        "harvest",
        "drought",
        "export ban",
        "port",
        "logistics",
        "crop failure",
        "frost",
        "commodity price",
    ),
    example_queries=(
        "harvest drought export ban when:72h",
        "crop failure frost when:72h",
        "commodity supply disruption when:72h",
    ),
    locations=(
        Location("US Midwest", 41.8781, -93.0977, "US"),
        Location("Brazil", -14.2350, -51.9253, "BR"),
        Location("Ukraine", 48.3794, 31.1656, "UA"),
        Location("Argentina", -38.4161, -63.6167, "AR"),
        Location("India", 20.5937, 78.9629, "IN"),
    ),
    forecast_vars=(
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "weathercode",
    ),
    lookback_hours=72,
    fusion_role="commodity disruption analyst",
)