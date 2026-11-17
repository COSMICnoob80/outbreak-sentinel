"""Deploy truth: the Render blueprint must need exactly two pasted secrets."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "render.yaml"


def _blueprint() -> dict:
    return yaml.safe_load(BLUEPRINT.read_text(encoding="utf-8"))


def test_blueprint_parses_with_one_web_service():
    services = _blueprint()["services"]
    assert len(services) == 1
    service = services[0]
    assert service["type"] == "web"
    assert service["runtime"] == "python"


def test_health_check_points_at_the_real_endpoint():
    assert _blueprint()["services"][0]["healthCheckPath"] == "/health"


def test_both_secrets_are_prompted_and_never_committed():
    env = {var["key"]: var for var in _blueprint()["services"][0]["envVars"]}
    secrets = ["CMDC_API_KEY", "TELEGRAPH_EVM_PRIVATE_KEY"]
    for key in secrets:
        assert env[key]["sync"] is False, f"{key} must carry sync: false"
        assert "value" not in env[key], f"{key} must not carry a value"
    assert sum(1 for var in env.values() if "value" not in var) == len(secrets)
    assert "GROQ_API_KEY" not in env
