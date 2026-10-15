"""Wildfire — early warning from news + weather.

Same engine, different signal set. Fire risk is driven by *weather physics*
(hot, dry, windy) more than by chatter, so this vertical leans on weather
forecast fields the bio-surveillance vertical does not need: wind and humidity.

Self-contained: adds no runtime dependency and touches no existing file.
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical

WILDFIRE = Vertical(
    slug="wildfire",
    name="Wildfire Early Warning (news + weather)",
    description=(
        "Watch fire-prone regions for the conditions that precede a fast-spreading "
        "fire — news of ignitions or evacuations, plus a hot / dry / windy forecast. "
        "The same fuse -> card -> receipt -> resolve loop, pointed at a hazard."
    ),
    subjects=("wildfire", "brush fire", "bushfire", "forest fire"),
    subject_label="hazard",
    signal_sources=("news", "weather"),
    risk_model=RiskModel(
        high_means=(
            "An active or fast-spreading fire is likely at a monitored location "
            "within 48h."
        ),
        escalation_rule=(
            "Escalate to HIGH only when >=2 independent signal families agree: "
            "(a) news of an active fire / evacuation / red-flag warning AND "
            "(b) a dangerous forecast — temp >=35C OR humidity <=20% — with "
            "sustained wind >=25 km/h. Wind and humidity are mandatory inputs."
        ),
        downgrade_rule=(
            "Drops to MODERATE when the fire is reported contained, or when the "
            "48h forecast window passes with no ignition reports."
        ),
    ),
    keywords=(
        "wildfire",
        "brush fire",
        "bushfire",
        "forest fire",
        "fire evacuation",
        "red flag warning",
        "wildfire smoke",
    ),
    example_queries=(
        "wildfire near Los Angeles when:24h",
        "bushfire Sydney when:24h",
        "fire evacuation Athens when:24h",
    ),
    locations=(
        Location("Los Angeles", 34.0522, -118.2437, "US"),
        Location("Sacramento", 38.5816, -121.4944, "US"),
        Location("San Diego", 32.7157, -117.1611, "US"),
        Location("Athens", 37.9838, 23.7275, "GR"),
        Location("Sydney", -33.8688, 151.2093, "AU"),
    ),
    # Wind + humidity are the wildfire drivers; the engine requests these per the
    # vertical's forecast_vars when wired to the weather adapter.
    forecast_vars=(
        "temperature_2m_max",
        "relative_humidity_2m_min",
        "wind_speed_10m_max",
        "precipitation_sum",
    ),
    lookback_hours=24,
    fusion_role="wildfire risk analyst",
)
