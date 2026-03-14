"""Tests for the FRED data loader.

Design: No mocked HTTP. All FRED API tests hit the live API so that real
behavior is validated — mocks can hide breaking changes. Pure-logic tests
(config checks, static methods) don't need HTTP at all.

Requires FRED_API_KEY in .env (loaded via conftest).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_loader import (
    FredMacroRetailLoader,
    _fetch_fred_series,
    _fetch_series_metadata,
)

# ---------------------------------------------------------------------------
# Config-only tests (no HTTP)
# ---------------------------------------------------------------------------


class TestDefaultSeriesConfig:
    """Validate default series IDs without touching the network."""

    def test_retail_mrts_series_end_in_usn(self) -> None:
        """All MRTS retail series must use NSA (USN suffix)."""
        defaults = FredMacroRetailLoader.__dataclass_fields__["retail_series"].default_factory()
        mrts = {k: v for k, v in defaults.items() if k.startswith("mrts_")}
        for name, fred_id in mrts.items():
            assert fred_id.endswith("USN"), f"{name} ({fred_id}) should end with USN (NSA)"

    def test_macro_series_present(self) -> None:
        defaults = FredMacroRetailLoader.__dataclass_fields__["macro_series"].default_factory()
        assert "real_gdp" in defaults
        assert "gdp_deflator" in defaults

    def test_gas_series_present(self) -> None:
        defaults = FredMacroRetailLoader.__dataclass_fields__["retail_series"].default_factory()
        assert "pump_price_gas_all_grades" in defaults
        assert defaults["pump_price_gas_all_grades"] == "GASALLM"

    def test_crisis_sa_series_end_in_uss(self) -> None:
        """All crisis SA series must use SA (USS suffix)."""
        defaults = FredMacroRetailLoader.__dataclass_fields__[
            "crisis_sa_series"
        ].default_factory()
        for name, fred_id in defaults.items():
            assert fred_id.endswith("USS"), f"{name} ({fred_id}) should end with USS (SA)"

    def test_crisis_sa_series_has_expected_keys(self) -> None:
        defaults = FredMacroRetailLoader.__dataclass_fields__[
            "crisis_sa_series"
        ].default_factory()
        expected = {"grocery_sa", "online_nonstore_sa", "big_box_warehouse_sa", "food_services_sa"}
        assert set(defaults.keys()) == expected


class TestLoaderInit:
    """Constructor validation — no HTTP."""

    def test_raises_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        with pytest.raises(ValueError, match="FRED API key required"):
            FredMacroRetailLoader(api_key="")

    def test_accepts_explicit_key(self) -> None:
        loader = FredMacroRetailLoader(api_key="test-key-abc")
        assert loader.api_key == "test-key-abc"


class TestQuarterlyToMonthlyFill:
    """Static method — pure logic, no HTTP."""

    def test_values_replicate_to_three_months(
        self, sample_quarterly_macro_df: pd.DataFrame
    ) -> None:
        months = pd.date_range("2023-01-31", "2023-12-31", freq="ME")
        result = FredMacroRetailLoader._to_monthly_quarter_fill(sample_quarterly_macro_df, months)

        # Q1 (Jan, Feb, Mar) should all have 100.0
        q1 = result.loc["2023-01":"2023-03", "real_gdp"]
        assert len(q1) == 3
        assert (q1 == 100.0).all(), f"Q1 values: {q1.tolist()}"

        # Q3 (Jul, Aug, Sep) should all have 300.0
        q3 = result.loc["2023-07":"2023-09", "real_gdp"]
        assert (q3 == 300.0).all()

    def test_within_quarter_uniformity(self, sample_quarterly_macro_df: pd.DataFrame) -> None:
        months = pd.date_range("2023-01-31", "2023-12-31", freq="ME")
        result = FredMacroRetailLoader._to_monthly_quarter_fill(sample_quarterly_macro_df, months)

        # Group by quarter — each group should have 0 variance
        for col in result.columns:
            quarterly_groups = result[col].groupby(result.index.to_period("Q"))
            for _, group in quarterly_groups:
                assert group.std() == 0.0, f"Non-uniform values in quarter: {group.tolist()}"

    def test_empty_input(self) -> None:
        empty = pd.DataFrame()
        months = pd.date_range("2023-01-31", "2023-03-31", freq="ME")
        result = FredMacroRetailLoader._to_monthly_quarter_fill(empty, months)
        assert len(result) == 3
        assert result.isna().all().all()


# ---------------------------------------------------------------------------
# Live FRED API tests
# ---------------------------------------------------------------------------


class TestSeriesMetadata:
    """Verify SA/NSA status via live FRED metadata API."""

    def test_retail_mrts_series_are_nsa(self, fred_api_key: str) -> None:
        defaults = FredMacroRetailLoader.__dataclass_fields__["retail_series"].default_factory()
        mrts = {k: v for k, v in defaults.items() if k.startswith("mrts_")}

        for name, fred_id in mrts.items():
            meta = _fetch_series_metadata(fred_id, fred_api_key)
            assert meta.seasonal_adjustment_short == "NSA", (
                f"{name} ({fred_id}): expected NSA, got {meta.seasonal_adjustment_short}"
            )

    def test_macro_series_are_sa(self, fred_api_key: str) -> None:
        defaults = FredMacroRetailLoader.__dataclass_fields__["macro_series"].default_factory()

        for name, fred_id in defaults.items():
            meta = _fetch_series_metadata(fred_id, fred_api_key)
            assert meta.seasonal_adjustment_short in ("SA", "SAAR"), (
                f"{name} ({fred_id}): expected SA/SAAR, got {meta.seasonal_adjustment_short}"
            )

    def test_gas_series_is_nsa(self, fred_api_key: str) -> None:
        meta = _fetch_series_metadata("GASALLM", fred_api_key)
        assert meta.seasonal_adjustment_short == "NSA"


class TestSeasonalAdjustmentVerification:
    """Integration test for the verify_seasonal_adjustment method."""

    def test_all_series_match(self, loader: FredMacroRetailLoader) -> None:
        result = loader.verify_seasonal_adjustment()
        assert isinstance(result, pd.DataFrame)
        assert result["match"].all(), f"Mismatches found:\n{result[~result['match']]}"

    def test_result_has_expected_columns(self, loader: FredMacroRetailLoader) -> None:
        result = loader.verify_seasonal_adjustment()
        expected_cols = {
            "group",
            "friendly_name",
            "series_id",
            "expected_sa",
            "actual_sa",
            "title",
            "match",
        }
        assert set(result.columns) == expected_cols

    def test_result_row_count(self, loader: FredMacroRetailLoader) -> None:
        result = loader.verify_seasonal_adjustment()
        defaults_macro = FredMacroRetailLoader.__dataclass_fields__[
            "macro_series"
        ].default_factory()
        defaults_retail = FredMacroRetailLoader.__dataclass_fields__[
            "retail_series"
        ].default_factory()
        assert len(result) == len(defaults_macro) + len(defaults_retail)


class TestCrisisSAVerification:
    """Integration test for the verify_crisis_sa method."""

    def test_all_crisis_sa_series_match(self, loader: FredMacroRetailLoader) -> None:
        result = loader.verify_crisis_sa()
        assert isinstance(result, pd.DataFrame)
        assert result["match"].all(), f"Mismatches found:\n{result[~result['match']]}"

    def test_crisis_sa_result_row_count(self, loader: FredMacroRetailLoader) -> None:
        result = loader.verify_crisis_sa()
        defaults = FredMacroRetailLoader.__dataclass_fields__[
            "crisis_sa_series"
        ].default_factory()
        assert len(result) == len(defaults)


class TestCrisisSALoad:
    """Integration test for load_crisis_sa method."""

    def test_returns_dataframe_with_sa_columns(self, loader: FredMacroRetailLoader) -> None:
        df = loader.load_crisis_sa(start="2020-01-01", end="2020-12-31")
        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.index, pd.DatetimeIndex)
        expected_cols = {
            "grocery_sa", "online_nonstore_sa",
            "big_box_warehouse_sa", "food_services_sa",
        }
        assert set(df.columns) == expected_cols

    def test_crisis_sa_data_has_no_all_nan_rows(self, loader: FredMacroRetailLoader) -> None:
        df = loader.load_crisis_sa(start="2020-01-01", end="2020-12-31")
        assert not df.isna().all(axis=1).any(), "Unexpected all-NaN rows in crisis SA data"


class TestDataFetch:
    """Live FRED data fetch tests."""

    def test_returns_series_with_datetime_index(self, fred_api_key: str) -> None:
        s = _fetch_fred_series("GDPC1", fred_api_key, start="2020-01-01", end="2020-12-31")
        assert isinstance(s, pd.Series)
        assert isinstance(s.index, pd.DatetimeIndex)
        assert s.name == "GDPC1"

    def test_correct_name(self, fred_api_key: str) -> None:
        s = _fetch_fred_series("GASALLM", fred_api_key, start="2023-01-01", end="2023-03-31")
        assert s.name == "GASALLM"

    def test_missing_values_are_nan(self, fred_api_key: str) -> None:
        # FRED returns "." for missing values — verify they become NaN
        s = _fetch_fred_series("GDPC1", fred_api_key, start="2020-01-01", end="2020-12-31")
        # Quarterly series with monthly start/end — we just verify NaN handling is correct
        # (all values should be numeric or NaN, never strings)
        assert s.dtype == np.float64

    def test_known_series_has_expected_range(self, fred_api_key: str) -> None:
        """GDPC1 (Real GDP) has data back to at least 1947."""
        s = _fetch_fred_series("GDPC1", fred_api_key, start="1947-01-01", end="1948-12-31")
        assert s.index.min().year == 1947


class TestPanelAlignment:
    """Verify quarterly→monthly fill in a real loaded panel."""

    def test_months_in_quarter_have_same_gdp(self, loader: FredMacroRetailLoader) -> None:
        _, _, panel_m = loader.load(start="2022-01-01", end="2023-12-31")

        # Group by quarter, check GDP is uniform within each quarter
        gdp = panel_m["real_gdp"].dropna()
        quarters = gdp.groupby(gdp.index.to_period("Q"))
        for q, group in quarters:
            assert group.std() == pytest.approx(0.0, abs=1e-8), (
                f"GDP not uniform in {q}: {group.tolist()}"
            )

    def test_no_cross_quarter_leakage(self, loader: FredMacroRetailLoader) -> None:
        _, _, panel_m = loader.load(start="2022-01-01", end="2023-12-31")

        gdp = panel_m["real_gdp"].dropna()
        quarters = gdp.groupby(gdp.index.to_period("Q"))
        q_values = {q: group.iloc[0] for q, group in quarters}

        # Adjacent quarters should have different values (GDP changes each quarter)
        q_list = sorted(q_values.keys())
        changes = [q_values[q_list[i]] != q_values[q_list[i + 1]] for i in range(len(q_list) - 1)]
        # At least some quarters should differ (GDP doesn't stay perfectly flat)
        assert any(changes), "All quarters have identical GDP — possible leakage or fill error"
