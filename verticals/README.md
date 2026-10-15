# Verticals — add your domain in under 50 lines

Outbreak Sentinel is a **platform**, not a dengue app. The engine is fixed:

```
fetch signals ─→ fuse (LLM) ─→ calibrated risk card ─→ signed receipt ─→ resolve vs reality
```

Everything domain-specific lives in a **Vertical**. A vertical is a declarative
config: what to watch, which signals to pull, how to read the weather, and what
`HIGH` means. Adding one changes *no engine code*.

## What ships today

| Slug | Domain | Signals | Subject axis |
|---|---|---|---|
| `bio-surveillance` | Disease outbreak | news, weather, social | disease |
| `wildfire` | Fire ignition/spread | news, weather (wind, humidity) | hazard |
| `supply-chain` | Trade-hub disruption | news, weather, social | disruption |

```python
from verticals import all_verticals
for v in all_verticals():
    print(v.describe().splitlines()[0])
```

## The seam

A `Vertical.to_config()` compiles down to the exact dict the shipping engine
already reads (`cities`, `diseases`, `news_keywords`, `social_keywords`,
`lookback_hours` — see `outbreak_sentinel.py` -> `load_config`). So the engine is
reused untouched; only the vertical changes.

```python
from verticals import WILDFIRE
cfg = WILDFIRE.to_config()   # drop-in config for the existing engine
```

## Add a vertical (≤50 lines)

1. Copy the template below into `verticals/<slug>.py`.
2. Fill in the fields. The two you must think hardest about are
   `risk_model.high_means` (what a HIGH card claims) and `escalation_rule`
   (the ≥2-signal-agree rule that keeps the false-positive budget honest).
3. Register it in `verticals/__init__.py` (two lines).

```python
from verticals.base import Location, RiskModel, Vertical

MY_VERTICAL = Vertical(
    slug="traffic",
    name="Urban Traffic Congestion Early Warning",
    description="Watch metro corridors for jams before they gridlock.",
    subjects=("gridlock", "road closure", "transit outage"),
    subject_label="incident",
    signal_sources=("news", "social"),          # source *kinds*
    risk_model=RiskModel(
        high_means="A corridor is likely to gridlock within 6h.",
        escalation_rule=(
            "HIGH only when >=2 families agree: (a) news of a crash/closure "
            "AND (b) social chatter spike on the same corridor."
        ),
        downgrade_rule="Drops to MODERATE when the closure clears.",
    ),
    keywords=("road closure", "traffic accident", "transit outage"),
    example_queries=(
        "road closure downtown when:6h",
        "traffic accident highway when:6h",
    ),
    locations=(
        Location("Downtown", 24.8607, 67.0011, "PK"),
    ),
    forecast_vars=("precipitation_sum",),       # optional
    lookback_hours=6,
    fusion_role="traffic incident analyst",
)
```

Then in `verticals/__init__.py`:

```python
from verticals.traffic import MY_VERTICAL
VERTICALS[MY_VERTICAL.slug] = MY_VERTICAL
```

That's it — the fusion, receipt ledger, and resolution loop come for free.

## Fields

| Field | Meaning |
|---|---|
| `slug` | Stable id used by the registry |
| `name` / `description` | Human-facing identity |
| `subjects` | The list of things a card can be *about* |
| `subject_label` | Word used in cards ("disease", "hazard", "disruption") |
| `signal_sources` | Source kinds the engine must fetch (`news`, `weather`, `social`) |
| `risk_model` | `high_means` + `escalation_rule` + `downgrade_rule` + `levels` |
| `keywords` | Search terms for news/social fetchers |
| `example_queries` | Ready-to-run queries for the demo |
| `locations` | `Location(name, lat, lon, country)` the vertical monitors |
| `forecast_vars` | Which weather variables matter for this domain |
| `lookback_hours` | Signal window |
| `fusion_role` | The LLM's persona for this domain |

## Calibration is the contract

A vertical is not just a keyword list — it is a **promise about what HIGH
means**. The `RiskModel` forces you to write down the escalation and downgrade
rules, so "cries wolf once" stays a bug you can point at, not a vibe. An
alarmist vertical that cannot resolve its own receipts is worse than no vertical.
