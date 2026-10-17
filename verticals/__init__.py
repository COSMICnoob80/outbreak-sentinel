"""Vertical registry — the platform's domain seam.

Bio-surveillance is the *first* vertical, not the only one. Import a vertical
and call ``.to_config()`` to run the same engine on a different problem.

    from verticals import WILDFIRE
    cfg = WILDFIRE.to_config()   # -> dict the shipping engine already reads
"""
from __future__ import annotations

from verticals.base import Location, RiskModel, Vertical
from verticals.bio_surveillance import BIO_SURVEILLANCE
from verticals.commodity_disruption import COMMODITY_DISRUPTION
from verticals.endemic import ENDEMIC
from verticals.financial_stress import FINANCIAL_STRESS
from verticals.pandemic import PANDEMIC
from verticals.supply_chain import SUPPLY_CHAIN
from verticals.wildfire import WILDFIRE

VERTICALS: dict[str, Vertical] = {
    BIO_SURVEILLANCE.slug: BIO_SURVEILLANCE,
    WILDFIRE.slug: WILDFIRE,
    SUPPLY_CHAIN.slug: SUPPLY_CHAIN,
    PANDEMIC.slug: PANDEMIC,
    ENDEMIC.slug: ENDEMIC,
    COMMODITY_DISRUPTION.slug: COMMODITY_DISRUPTION,
    FINANCIAL_STRESS.slug: FINANCIAL_STRESS,
}


def get_vertical(slug: str) -> Vertical:
    """Look up a registered vertical by slug."""
    return VERTICALS[slug]


def all_verticals() -> list[Vertical]:
    """All registered verticals, in registration order."""
    return list(VERTICALS.values())


__all__ = [
    "Vertical",
    "Location",
    "RiskModel",
    "VERTICALS",
    "get_vertical",
    "all_verticals",
    "BIO_SURVEILLANCE",
    "WILDFIRE",
    "SUPPLY_CHAIN",
    "PANDEMIC",
    "ENDEMIC",
    "COMMODITY_DISRUPTION",
    "FINANCIAL_STRESS",
]
