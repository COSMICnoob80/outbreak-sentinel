"""Network truth: the configured chain must be the settlement network."""
from telegraph.config import TELEGRAPH_CONFIG


def test_chain_id_is_base_sepolia():
    assert TELEGRAPH_CONFIG["chain_id"] == 84532
    assert TELEGRAPH_CONFIG["chain_caip"] == "eip155:84532"
    assert "Base Sepolia" in TELEGRAPH_CONFIG["network_label"]
