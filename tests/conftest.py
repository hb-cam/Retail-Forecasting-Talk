"""Shared pytest fixtures for data_loader tests.

All FRED API tests use a real API key loaded from .env — no mocks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@pytest.fixture(scope="session")
def fred_api_key() -> str:
    """Load FRED_API_KEY from .env; skip entire session if missing."""
    import os

    key = os.environ.get("FRED_API_KEY", "")
    if not key:
        pytest.skip("FRED_API_KEY not set — skipping live API tests")
    return key


@pytest.fixture(scope="session")
def loader(fred_api_key: str):
    """Real FredMacroRetailLoader with live API key."""
    from data_loader import FredMacroRetailLoader

    return FredMacroRetailLoader(api_key=fred_api_key)


@pytest.fixture()
def sample_quarterly_macro_df() -> pd.DataFrame:
    """Small known-value quarterly DataFrame for alignment math tests."""
    idx = pd.to_datetime(["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"])
    return pd.DataFrame(
        {"real_gdp": [100.0, 200.0, 300.0, 400.0], "gdp_deflator": [1.0, 2.0, 3.0, 4.0]},
        index=idx,
    )
