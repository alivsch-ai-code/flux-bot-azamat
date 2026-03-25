"""Pytest-Konfiguration und gemeinsame Fixtures."""
import os
import sys
from pathlib import Path

# Projekt-Root in Python-Pfad (für GitHub Actions / CI, wo src nicht installiert ist)
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Env-Vars VOR dem Import von Modulen setzen, die config laden
os.environ.setdefault("TELEGRAM_TOKEN", "test_fake_token_for_ci_12345")
os.environ.setdefault("REPLICATE_API_TOKEN", "test_fake_replicate_for_ci_67890")


def pytest_configure(config):
    """Stellt sicher, dass Test-Env-Vars gesetzt sind."""
    for key, val in [
        ("TELEGRAM_TOKEN", "test_fake_token_for_ci_12345"),
        ("REPLICATE_API_TOKEN", "test_fake_replicate_for_ci_67890"),
    ]:
        if key not in os.environ or not os.environ[key]:
            os.environ[key] = val
