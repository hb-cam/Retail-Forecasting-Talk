"""FRED macro + retail data loader.

Fetches macroeconomic and retail time series from the FRED API and assembles
a monthly panel with quarterly macro values replicated to each month within
the quarter.

Requires a FRED API key — set via FRED_API_KEY environment variable or pass
directly to the constructor.  Free keys are available at:
https://fred.stlouisfed.org/docs/api/api_key.html
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import requests

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES_URL = "https://api.stlouisfed.org/fred/series"


@dataclass(frozen=True)
class SeriesMetadata:
    """Metadata for a single FRED series, from the /fred/series endpoint."""

    series_id: str
    title: str
    frequency_short: str
    seasonal_adjustment_short: str
    units_short: str
    last_updated: str


def _fetch_series_metadata(series_id: str, api_key: str) -> SeriesMetadata:
    """Fetch metadata for a FRED series (title, frequency, SA status, etc.)."""
    resp = requests.get(
        FRED_SERIES_URL,
        params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if "seriess" not in data or not data["seriess"]:
        raise ValueError(f"No metadata returned for {series_id}: {data}")

    s = data["seriess"][0]
    return SeriesMetadata(
        series_id=s["id"],
        title=s["title"],
        frequency_short=s["frequency_short"],
        seasonal_adjustment_short=s["seasonal_adjustment_short"],
        units_short=s["units_short"],
        last_updated=s["last_updated"],
    )


def _fetch_fred_series(
    series_id: str,
    api_key: str,
    start: str | None = None,
    end: str | None = None,
) -> pd.Series:
    """Fetch a single FRED series as a pandas Series with a DatetimeIndex."""
    params: dict[str, str] = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end

    resp = requests.get(FRED_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "observations" not in data:
        raise ValueError(f"FRED API error for {series_id}: {data}")

    obs = data["observations"]
    dates = pd.to_datetime([o["date"] for o in obs])
    values = [float(o["value"]) if o["value"] != "." else np.nan for o in obs]

    # FRED returns first-of-month dates (e.g. 2005-01-01); snap to month-end
    # so they align with the ME-frequency index used in load().
    dates = dates + pd.offsets.MonthEnd(0)

    return pd.Series(values, index=dates, name=series_id)


@dataclass
class FredMacroRetailLoader:
    """Load macro + retail time series from FRED and build a monthly panel.

    Returns three DataFrames from ``.load()``:

    1. ``macro_q``  — quarterly macro frame (quarter-end index)
    2. ``retail_m`` — monthly retail/pump-price frame (month-end index)
    3. ``panel_m``  — monthly-joined panel where each month in a quarter is
       filled with that quarter's macro values

    Notes
    -----
    - Macros are expected to be quarterly (Real GDP, GDP Deflator).
    - Retail series and pump prices are expected to be monthly.
    - ``panel_m`` replicates quarterly values to every month in the quarter
      via PeriodIndex mapping (not forward-fill).
    """

    api_key: str | None = None

    macro_series: dict[str, str] = field(
        default_factory=lambda: {
            "real_gdp": "GDPC1",
            "gdp_deflator": "GDPDEF",
        }
    )

    retail_series: dict[str, str] = field(
        default_factory=lambda: {
            "pump_price_gas_all_grades": "GASALLM",
            "mrts_grocery_sales": "MRTSSM4451USN",
            "mrts_online_sales_nonstore": "MRTSSM454USN",
            "mrts_full_service_restaurants": "MRTSSM7221USN",
            "mrts_quick_service_limited": "SM72251XUSN",
            "mrts_big_box_warehouse_supercenters": "SM452311USN",
        }
    )

    crisis_sa_series: dict[str, str] = field(
        default_factory=lambda: {
            "grocery_sa": "MRTSSM4451USS",
            "online_nonstore_sa": "MRTSSM454USS",
            "big_box_warehouse_sa": "SM452311USS",
            "food_services_sa": "MRTSSM722USS",
        }
    )

    monthly_freq: str = "ME"
    quarterly_freq: str = "QE"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("FRED_API_KEY", "")
        if not self.api_key:
            raise ValueError("FRED API key required. Set FRED_API_KEY env var or pass api_key=.")

    def verify_seasonal_adjustment(self) -> pd.DataFrame:
        """Verify that retail series are NSA and macro series are SA via FRED metadata.

        Returns a DataFrame with columns:
            group, friendly_name, series_id, expected_sa, actual_sa, title, match

        Raises ValueError if any series has unexpected seasonal adjustment.
        """
        rows: list[dict[str, str | bool]] = []

        for friendly, fred_id in self.macro_series.items():
            meta = _fetch_series_metadata(fred_id, self.api_key)
            expected = "SA"
            actual = meta.seasonal_adjustment_short
            # SA variants: "SA", "SAAR" (Seasonally Adjusted Annual Rate)
            is_sa = actual in ("SA", "SAAR")
            rows.append(
                {
                    "group": "macro",
                    "friendly_name": friendly,
                    "series_id": fred_id,
                    "expected_sa": expected,
                    "actual_sa": actual,
                    "title": meta.title,
                    "match": is_sa,
                }
            )

        for friendly, fred_id in self.retail_series.items():
            meta = _fetch_series_metadata(fred_id, self.api_key)
            expected = "NSA"
            actual = meta.seasonal_adjustment_short
            rows.append(
                {
                    "group": "retail",
                    "friendly_name": friendly,
                    "series_id": fred_id,
                    "expected_sa": expected,
                    "actual_sa": actual,
                    "title": meta.title,
                    "match": actual == "NSA",
                }
            )

        result = pd.DataFrame(rows)
        mismatches = result[~result["match"]]
        if not mismatches.empty:
            bad = mismatches[["series_id", "expected_sa", "actual_sa"]].to_string(index=False)
            raise ValueError(f"Seasonal adjustment mismatch:\n{bad}")

        return result

    def verify_crisis_sa(self) -> pd.DataFrame:
        """Verify that crisis SA series are seasonally adjusted via FRED metadata.

        Returns a DataFrame with columns:
            friendly_name, series_id, expected_sa, actual_sa, title, match

        Raises ValueError if any series is not SA.
        """
        rows: list[dict[str, str | bool]] = []

        for friendly, fred_id in self.crisis_sa_series.items():
            meta = _fetch_series_metadata(fred_id, self.api_key)
            actual = meta.seasonal_adjustment_short
            rows.append(
                {
                    "friendly_name": friendly,
                    "series_id": fred_id,
                    "expected_sa": "SA",
                    "actual_sa": actual,
                    "title": meta.title,
                    "match": actual in ("SA", "SAAR"),
                }
            )

        result = pd.DataFrame(rows)
        mismatches = result[~result["match"]]
        if not mismatches.empty:
            bad = mismatches[["series_id", "expected_sa", "actual_sa"]].to_string(index=False)
            raise ValueError(f"Crisis SA series mismatch:\n{bad}")

        return result

    def load_crisis_sa(
        self,
        start: str = "2005-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        """Fetch seasonally adjusted retail series for crisis comparison charts.

        Returns a monthly DataFrame with SA series (separate from the main NSA
        retail_series used for STL decomposition).
        """
        return self._fetch_frame(self.crisis_sa_series, start=start, end=end)

    def _fetch_frame(
        self,
        series_map: dict[str, str],
        start: str,
        end: str | None,
    ) -> pd.DataFrame:
        frames: list[pd.Series] = []
        for col, fred_id in series_map.items():
            s = _fetch_fred_series(fred_id, self.api_key, start=start, end=end)
            s.name = col
            frames.append(s)
        return pd.concat(frames, axis=1).sort_index()

    @staticmethod
    def _to_monthly_quarter_fill(
        macro_q: pd.DataFrame,
        month_index: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        """Replicate each quarter's macro values to every month in that quarter.

        Uses PeriodIndex mapping so that Jan–Mar all get the Q1 value, etc.
        """
        if macro_q.empty:
            return macro_q.reindex(month_index)

        q_period = month_index.to_period("Q")
        macro_q_period = macro_q.copy()
        macro_q_period.index = macro_q_period.index.to_period("Q")

        macro_m = pd.DataFrame(index=month_index)
        for col in macro_q_period.columns:
            macro_m[col] = q_period.map(macro_q_period[col])

        return macro_m

    def load(
        self,
        start: str = "1992-01-01",
        end: str | None = None,
        macro_cols: Iterable[str] | None = None,
        retail_cols: Iterable[str] | None = None,
        drop_all_na_panel: bool = True,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Fetch data and return ``(macro_q, retail_m, panel_m)``.

        Parameters
        ----------
        start : str
            Earliest observation date (ISO format).
        end : str | None
            Latest observation date.  ``None`` for latest available.
        macro_cols, retail_cols : Iterable[str] | None
            Subset of series to fetch.  ``None`` fetches all configured series.
        drop_all_na_panel : bool
            Drop rows where *all* columns are NaN from the panel.
        """
        macro_map = (
            self.macro_series
            if macro_cols is None
            else {k: self.macro_series[k] for k in macro_cols}
        )
        retail_map = (
            self.retail_series
            if retail_cols is None
            else {k: self.retail_series[k] for k in retail_cols}
        )

        macro_q_raw = self._fetch_frame(macro_map, start=start, end=end)
        retail_m_raw = self._fetch_frame(retail_map, start=start, end=end)

        macro_q = macro_q_raw.copy()
        retail_m = retail_m_raw.copy()

        min_dt = min(
            (d for d in [macro_q.index.min(), retail_m.index.min()] if pd.notna(d)),
            default=pd.to_datetime(start),
        )
        max_dt = max(
            (d for d in [macro_q.index.max(), retail_m.index.max()] if pd.notna(d)),
            default=pd.to_datetime(end) if end else pd.Timestamp.today(),
        )

        month_index = pd.date_range(min_dt, max_dt, freq=self.monthly_freq)

        retail_m = retail_m.reindex(month_index)
        macro_m = self._to_monthly_quarter_fill(macro_q, month_index)
        panel_m = macro_m.join(retail_m, how="outer")

        if drop_all_na_panel:
            panel_m = panel_m.dropna(how="all")

        return macro_q, retail_m, panel_m
