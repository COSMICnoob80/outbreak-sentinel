import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HTML = Path(__file__).resolve().parents[1] / "dashboard" / "index.html"


def _score_functions() -> str:
    src = HTML.read_text(encoding="utf-8")
    sev = re.search(r"var SEV=\{.*?\};", src, re.S).group(0)
    fn = re.search(r"function scoreFor\([^)]*\)\{.*?\n\}", src, re.S).group(0)
    return sev + "\n" + fn


def _score(card: dict):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required to execute the dashboard's score function")
    args = ", ".join(json.dumps(v) for v in
                     (card, card.get("risk_level") or card.get("level"),
                      card.get("confidence")))
    script = (
        _score_functions()
        + "\nconst v=scoreFor(" + args + ");"
        + 'console.log(JSON.stringify({v:v===undefined?null:v,undef:v===undefined}));'
    )
    out = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, timeout=30
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_live_card_uses_risk_score_from_the_api():
    # The shape GET /risk actually returns for Karachi.
    card = {
        "city": "Karachi",
        "disease": "dengue",
        "risk_level": "MODERATE",
        "confidence": 0.7,
        "risk_score": 30,
    }
    result = _score(card)
    assert result["v"] == 30


def test_card_without_any_score_renders_no_number():
    card = {
        "city": "Karachi",
        "disease": "dengue",
        "risk_level": "MODERATE",
        "confidence": 0.7,
    }
    result = _score(card)
    assert result["undef"] is False
    assert result["v"] is None


def test_demo_score_field_is_still_accepted():
    assert _score({"city": "Karachi", "level": "CRITICAL", "score": 87})["v"] == 87


def test_dashboard_carries_no_fabricated_timeline_or_stale_provider():
    src = HTML.read_text(encoding="utf-8")
    assert "var TL=" not in src
    assert "Groq (free tier)" not in src
