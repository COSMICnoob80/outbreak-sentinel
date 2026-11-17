"""Feed and card honesty: one row per story, real publish times, on-topic drivers."""
from datetime import datetime

import app as app_module

NOW = datetime(2026, 11, 17, 10, 29)

DENGUE_LAHORE = "Lahore struggles to shake off dengue - The Express Tribune"
TYPHOID_HEADLINE = "Dual antibiotics linked to longer pediatric typhoid hospital stays"
VACCINE_HEADLINE = "DRAP alert over fake children's vaccine in vial form"


def _karachi_dengue_news():
    """One genuine Karachi dengue story, so the geography gate lets drivers through."""
    return [{
        "title": "Karachi dengue cases rise sharply",
        "link": "https://e.com/karachi-dengue",
        "published": "2026-11-16",
        "city": "Karachi",
    }]


def _card(**overrides):
    card = {
        "city": "Karachi",
        "disease": "dengue",
        "risk_level": "MODERATE",
        "confidence": 0.83,
        "drivers": [{"kind": "news", "text": "Karachi dengue cases rise"}],
        "recommendation": "Monitor",
        "sources": [],
        "chart": [],
    }
    card.update(overrides)
    return card


def test_identical_headlines_render_once():
    twin = {
        "title": DENGUE_LAHORE,
        "url": "https://tribune.com.pk/a",
        "outlet": "The Express Tribune",
        "published": "2026-11-17",
    }
    same_story_other_url = {
        "title": DENGUE_LAHORE,
        "url": "https://tribune.com.pk/b",
        "outlet": "The Express Tribune",
        "published": "2026-11-17",
    }
    feed = app_module._build_feed(
        [_card(city="Lahore", sources=[twin, same_story_other_url])], NOW, "dengue"
    )
    assert [row["headline"] for row in feed] == [DENGUE_LAHORE]


def test_headline_differing_only_by_outlet_is_one_row():
    feed = app_module._build_feed(
        [
            _card(city="Karachi", sources=[{"title": "Dengue cases climb in Karachi - The News"}]),
            _card(city="Karachi", sources=[{"title": "Dengue cases climb in Karachi - Dawn"}]),
        ],
        NOW,
        "dengue",
    )
    assert len(feed) == 1


def test_every_feed_row_carries_a_publish_time_or_date_unknown():
    feed = app_module._build_feed(
        [
            _card(
                sources=[
                    {"title": "Karachi dengue cases rise", "published": "2026-11-12", "outlet": "A"},
                    {"title": "Karachi dengue ward full", "published": "", "outlet": "B"},
                    {"title": "Karachi dengue drive begins", "published": "2026-11-16", "outlet": "C"},
                ]
            )
        ],
        NOW,
        "dengue",
    )
    published = {row["headline"]: row["published"] for row in feed}
    assert published["Karachi dengue cases rise"] == "12 Nov"
    assert published["Karachi dengue drive begins"] == "Yesterday"
    assert published["Karachi dengue ward full"] == "date unknown"
    assert all(row["published"] != "10:29" for row in feed)


def test_dengue_card_drops_typhoid_and_vaccine_drivers():
    card = _card(
        drivers=[
            {"kind": "news", "text": TYPHOID_HEADLINE},
            {"kind": "news", "text": VACCINE_HEADLINE},
            {"kind": "news", "text": "Karachi dengue hospitalisations keep climbing"},
            {"kind": "weather", "text": "Heavy rain forecast: 61.0mm"},
        ]
    )
    out = app_module._attach_card_extras(
        [card], _karachi_dengue_news(), {"karachi": {"city": "Karachi"}}, "dengue"
    )[0]
    texts = " ".join(d["text"].lower() for d in out["drivers"])
    assert "typhoid" not in texts
    assert "vaccine" not in texts
    assert any("dengue" in d["text"].lower() for d in out["drivers"])
    assert len(out["drivers"]) <= 4


def test_card_with_only_off_topic_drivers_states_it_plainly():
    card = _card(drivers=[{"kind": "news", "text": TYPHOID_HEADLINE}])
    out = app_module._attach_card_extras(
        [card], _karachi_dengue_news(), {"karachi": {"city": "Karachi"}}, "dengue"
    )[0]
    assert [d["text"] for d in out["drivers"]] == [
        "no disease-specific drivers in the last 7 days"
    ]


def test_evidence_count_matches_sources_on_every_card():
    news = [
        {"title": "Lahore dengue cases rise", "link": "https://e.com/1",
         "published": "2026-11-17", "city": "Lahore"},
        {"title": "Lahore dengue ward full", "link": "https://e.com/2",
         "published": "2026-11-15", "city": "Lahore"},
        {"title": "Lahore dengue drive begins", "link": "https://e.com/3",
         "published": "2026-11-13", "city": "Lahore"},
        {"title": "Karachi typhoid cases rise", "link": "https://e.com/4",
         "published": "2026-11-16", "city": "Karachi"},
    ]
    cards = [_card(city="Lahore", sources=[]), _card(city="Karachi", sources=[])]
    out = app_module._attach_card_extras(cards, news, {}, "dengue")
    for card in out:
        sources = card["sources"]
        line = card["evidence_line"]
        assert line.startswith(f"{len(sources)} city-specific dengue report")
        if sources:
            newest = max(s["published"] for s in sources)
            assert datetime.strptime(newest, "%Y-%m-%d").strftime("%d %b") in line
