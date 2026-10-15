"""Supply-chain disruption — early warning from news + weather + social.

Trade chokepoints (ports, canals, straits) fail for boring, forecastable
reasons: a storm, a strike, a backlog. This vertical watches those hub nodes
for the leading indicators of a disruption, then resolves the receipt against
whether the disruption actually materialised.

Self-contained: adds no runtime dependency and touches no existing file.
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical

SUPPLY_CHAIN = Vertical(
    slug="supply-chain",
    name="Supply-Chain Disruption Early Warning (news + weather + social)",
    description=(
        "Watch global trade hubs for the leading indicators of a disruption — "
        "port closures, strikes, congestion, blocked routes — corroborated by "
        "severe weather at the hub and rising shipper chatter. Same loop, "
        "different blast radius."
    ),
    subjects=(
        "port congestion",
        "port closure",
        "shipping delay",
        "dockworkers strike",
        "canal blockage",
    ),
    subject_label="disruption",
    signal_sources=("news", "weather", "social"),
    risk_model=RiskModel(
        high_means=(
            "A monitored trade hub is likely to see a material disruption "
            "(closure, congestion, or route blockage) within 7 days."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) news of a closure / strike / congestion at the hub AND "
            "(b) severe weather at the hub (storm code, wind >=40 km/h, or heavy "
            "precip) OR a spike in shipper chatter about delays."
        ),
        downgrade_rule=(
            "Drops to MODERATE when the hub reports normal operations across one "
            "full window, or the reported blockage clears."
        ),
    ),
    keywords=(
        "port congestion",
        "port closure",
        "shipping delay",
        "supply chain disruption",
        "dockworkers strike",
        "container backlog",
        "canal blocked",
    ),
    example_queries=(
        "port congestion Shanghai when:72h",
        "dockworkers strike Rotterdam when:72h",
        "shipping delay Singapore when:72h",
    ),
    locations=(
        Location("Shanghai", 31.2304, 121.4737, "CN"),
        Location("Singapore", 1.3521, 103.8198, "SG"),
        Location("Rotterdam", 51.9244, 4.4777, "NL"),
        Location("Long Beach", 33.7405, -118.2775, "US"),
        Location("Jebel Ali", 25.0116, 55.0614, "AE"),
    ),
    forecast_vars=(
        "wind_speed_10m_max",
        "precipitation_sum",
        "weathercode",
    ),
    # Disruptions unfold over days, not hours.
    lookback_hours=72,
    fusion_role="supply-chain disruption analyst",
)
