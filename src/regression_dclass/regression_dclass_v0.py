from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import (
    acorr_ljungbox,
    het_breuschpagan,
    het_white,
)
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.stats.stattools import durbin_watson


@dataclass
class RegressionDiagnostics:
    """
    OLS + diagnostics wrapper with a compact executive-style report.

    Fit:
      - OLS with HAC (Newey-West) robust covariance for inference.

    Diagnostics:
      - RMSE, MAE, MAPE
      - leverage + studentized residual leveraged-outliers
      - Cook's distance ranking + threshold flags
      - Breusch–Pagan and White heteroskedasticity tests
      - Durbin–Watson and Ljung–Box autocorrelation tests
      - X vs residual covariance + X'e inner-product sanity check
      - Optional ACF/PACF plots

    Usage:
      diag = RegressionDiagnostics(X, y, hac_maxlags=8)
      diag.run(make_plots=False)
      print(diag.report())
    """

    X: Any
    y: Any
    add_const: bool = True

    # HAC / NW
    hac_maxlags: int | None = None
    hac_kernel: str = "bartlett"

    # Outliers
    leverage_thresh: float | None = None  # default: 2p/n
    student_resid_thresh: float = 3.0
    cooks_thresh: float | None = None  # default: 4/n
    top_cooks: int = 10

    # Autocorr tests
    ljungbox_lags: int = 20

    model_: sm.OLS | None = None
    fit_: Any | None = None
    results_: dict[str, Any] | None = None

    def _to_numpy_2d(self, X: Any) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            return X.values
        X = np.asarray(X)
        if X.ndim != 2:
            raise ValueError(f"X must be 2D; got shape {X.shape}.")
        return X

    def _to_numpy_1d(self, y: Any) -> np.ndarray:
        if isinstance(y, (pd.Series, pd.DataFrame)):
            y = np.asarray(y).squeeze()
        y = np.asarray(y).squeeze()
        if y.ndim != 1:
            raise ValueError(f"y must be 1D; got shape {y.shape}.")
        return y

    def _infer_hac_lags(self, n: int) -> int:
        return int(np.floor(4 * (n / 100) ** (2 / 9))) if n > 0 else 0

    def _safe_mape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        denom = np.where(np.abs(y_true) < 1e-12, np.nan, np.abs(y_true))
        return float(np.nanmean(np.abs((y_true - y_pred) / denom)) * 100.0)

    def _prepare_Xy(self) -> tuple[np.ndarray, np.ndarray]:
        Xn = self._to_numpy_2d(self.X)
        yn = self._to_numpy_1d(self.y)

        if Xn.shape[0] != yn.shape[0]:
            raise ValueError(f"Row mismatch: X has {Xn.shape[0]} rows; y has {yn.shape[0]} rows.")

        if self.add_const:
            Xn = sm.add_constant(Xn, has_constant="add")

        return Xn, yn

    def fit(self) -> RegressionDiagnostics:
        Xn, yn = self._prepare_Xy()
        self.model_ = sm.OLS(yn, Xn)

        maxlags = self.hac_maxlags
        if maxlags is None:
            maxlags = self._infer_hac_lags(n=Xn.shape[0])

        self.fit_ = self.model_.fit(
            cov_type="HAC",
            cov_kwds={"maxlags": int(maxlags), "kernel": self.hac_kernel},
        )
        return self

    def diagnose(
        self,
        make_plots: bool = True,
        acf_lags: int = 40,
        pacf_lags: int = 40,
    ) -> dict[str, Any]:
        if self.fit_ is None:
            raise RuntimeError("Call .fit() before .diagnose(), or call .run().")

        Xn, y = self._prepare_Xy()
        yhat = self.fit_.fittedvalues
        resid = self.fit_.resid

        n, p = Xn.shape

        # Metrics
        rmse = float(np.sqrt(np.mean((y - yhat) ** 2)))
        mae = float(np.mean(np.abs(y - yhat)))
        mape = self._safe_mape(y, yhat)

        # Influence / outliers
        infl = OLSInfluence(self.fit_)
        hat = infl.hat_matrix_diag
        rstudent = infl.resid_studentized_external

        leverage_thr = self.leverage_thresh if self.leverage_thresh is not None else (2.0 * p / n)
        leveraged_outlier_mask = (hat > leverage_thr) & (
            np.abs(rstudent) > self.student_resid_thresh
        )
        leveraged_outliers = np.where(leveraged_outlier_mask)[0]

        cooks_d, _ = infl.cooks_distance
        cooks_thr = self.cooks_thresh if self.cooks_thresh is not None else (4.0 / n)
        cooks_flag = np.where(cooks_d > cooks_thr)[0]

        top_k = int(min(max(self.top_cooks, 1), n))
        cooks_rank_idx = np.argsort(cooks_d)[::-1][:top_k]
        cooks_ranking = [
            {
                "index": int(i),
                "cooks_d": float(cooks_d[i]),
                "leverage": float(hat[i]),
                "rstudent": float(rstudent[i]),
            }
            for i in cooks_rank_idx
        ]

        # Orthogonality checks
        Xc = Xn - Xn.mean(axis=0, keepdims=True)
        ec = resid - resid.mean()
        cov_X_e = (Xc.T @ ec) / (n - 1)
        cov_X_e_norm = float(np.linalg.norm(cov_X_e))

        xte = Xn.T @ resid
        xte_norm = float(np.linalg.norm(xte))
        denom = float(np.linalg.norm(Xn, ord="fro") * np.linalg.norm(resid) + 1e-12)
        xte_rel = float(xte_norm / denom)

        # Heteroskedasticity tests
        bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(resid, Xn)
        w_lm, w_lm_p, w_f, w_f_p = het_white(resid, Xn)

        # Autocorrelation tests
        dw = float(durbin_watson(resid))
        lb = acorr_ljungbox(resid, lags=self.ljungbox_lags, return_df=True)

        # ACF/PACF plots
        fig_acf = fig_pacf = None
        if make_plots:
            fig_acf = plt.figure()
            plot_acf(resid, lags=acf_lags, ax=plt.gca())
            plt.title("Residual ACF")

            fig_pacf = plt.figure()
            plot_pacf(resid, lags=pacf_lags, ax=plt.gca(), method="ywm")
            plt.title("Residual PACF")

        out = {
            "n": int(n),
            "p": int(p),
            "model_summary": self.fit_.summary().as_text(),
            "coef": np.asarray(self.fit_.params),
            "stderr_hac": np.asarray(self.fit_.bse),
            "tvalues_hac": np.asarray(self.fit_.tvalues),
            "pvalues_hac": np.asarray(self.fit_.pvalues),
            "hac": {
                "maxlags": int(self.fit_.cov_kwds.get("maxlags", -1)),
                "kernel": self.hac_kernel,
            },
            "fitted": np.asarray(yhat),
            "residuals": np.asarray(resid),
            "rmse": rmse,
            "mae": mae,
            "mape": mape,
            "leverage": np.asarray(hat),
            "studentized_residuals": np.asarray(rstudent),
            "leverage_threshold": float(leverage_thr),
            "student_resid_threshold": float(self.student_resid_thresh),
            "leveraged_outlier_indices": leveraged_outliers,
            "cooks_distance": np.asarray(cooks_d),
            "cooks_threshold": float(cooks_thr),
            "cooks_flag_indices": cooks_flag,
            "cooks_ranking": cooks_ranking,
            "cov_X_error": np.asarray(cov_X_e),
            "cov_X_error_norm": cov_X_e_norm,
            "XTe": np.asarray(xte),
            "XTe_rel_norm": xte_rel,
            "breusch_pagan": {
                "lm_stat": float(bp_lm),
                "lm_pvalue": float(bp_lm_p),
                "f_stat": float(bp_f),
                "f_pvalue": float(bp_f_p),
            },
            "white": {
                "lm_stat": float(w_lm),
                "lm_pvalue": float(w_lm_p),
                "f_stat": float(w_f),
                "f_pvalue": float(w_f_p),
            },
            "durbin_watson": dw,
            "ljung_box": lb,
            "acf_fig": fig_acf,
            "pacf_fig": fig_pacf,
        }

        self.results_ = out
        return out

    def run(
        self,
        make_plots: bool = True,
        acf_lags: int = 40,
        pacf_lags: int = 40,
    ) -> dict[str, Any]:
        self.fit()
        return self.diagnose(make_plots=make_plots, acf_lags=acf_lags, pacf_lags=pacf_lags)

    def report(
        self,
        alpha: float = 0.05,
        ljungbox_focus_lags: list[int] | None = None,
        max_outliers_to_print: int = 5,
    ) -> str:
        """
        Returns a compact, executive-style text block.

        Includes:
          - Fit overview and error metrics
          - Key p-values (BP/White; Ljung–Box at selected lags)
          - Autocorrelation summary (Durbin–Watson)
          - Top influential points (Cook's distance) and leveraged-outliers
          - Recommended next actions

        Call .run() first (or at least .fit() + .diagnose()).
        """
        if self.results_ is None:
            raise RuntimeError("No diagnostics available. Call .run() before .report().")

        r = self.results_
        n, p = r["n"], r["p"]

        # Determine which Ljung–Box lags to highlight
        lb: pd.DataFrame = r["ljung_box"]
        if ljungbox_focus_lags is None:
            # Pick a few representative lags, bounded by computed lags
            candidate = [1, 5, 10, min(20, self.ljungbox_lags)]
            ljungbox_focus_lags = sorted(
                set([lag for lag in candidate if lag >= 1 and lag <= len(lb)])
            )

        def fmt(x: float, digits: int = 4) -> str:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return "NA"
            # Scientific formatting for very small values
            if abs(x) < 1e-4 and x != 0:
                return f"{x:.2e}"
            return f"{x:.{digits}f}"

        # Key stats
        rmse, mae, mape = r["rmse"], r["mae"], r["mape"]
        dw = r["durbin_watson"]
        bp_p = r["breusch_pagan"]["lm_pvalue"]
        w_p = r["white"]["lm_pvalue"]
        xte_rel = r["XTe_rel_norm"]

        # Outliers
        cooks_ranking = r["cooks_ranking"][
            : int(min(max_outliers_to_print, len(r["cooks_ranking"])))
        ]
        leveraged_idx = r["leveraged_outlier_indices"][
            : int(min(max_outliers_to_print, len(r["leveraged_outlier_indices"])))
        ]

        # Ljung–Box focus
        lb_lines = []
        for lag in ljungbox_focus_lags:
            # lb index is 1..L in statsmodels return_df; guard anyway
            row = lb.loc[lag] if lag in lb.index else lb.iloc[lag - 1]
            lb_lines.append(f"  - Lag {int(lag):>2}: p={fmt(float(row['lb_pvalue']), 4)}")

        # Simple decision logic for recommendations
        hetero_flag = (bp_p < alpha) or (w_p < alpha)
        autocorr_flag = any(
            float((lb.loc[lag] if lag in lb.index else lb.iloc[lag - 1])["lb_pvalue"]) < alpha
            for lag in ljungbox_focus_lags
        )
        influence_flag = (len(r["cooks_flag_indices"]) > 0) or (
            len(r["leveraged_outlier_indices"]) > 0
        )

        # Recommendations (compact and actionable)
        actions = []
        if hetero_flag:
            actions.append(
                "Heteroskedasticity detected: consider variance-stabilizing transforms, WLS/GLS, or re-specifying features; HAC helps inference but not efficiency."
            )
        else:
            actions.append(
                "No strong evidence of heteroskedasticity at the chosen alpha; proceed with current variance assumptions."
            )

        if autocorr_flag or (dw < 1.6 or dw > 2.4):
            actions.append(
                "Autocorrelation indicated: consider adding lagged terms/AR structure, differencing, seasonal terms, or switching to GLS/ARIMA-style error models; validate with residual ACF/PACF."
            )
        else:
            actions.append(
                "Residual autocorrelation not strongly indicated in the highlighted lags; current dynamic specification may be adequate."
            )

        if influence_flag:
            actions.append(
                "Influential points present: review top Cook’s distance cases; confirm data quality, assess regime changes, and consider robust regression or segmented models if points are legitimate."
            )
        else:
            actions.append(
                "No major influence/outlier signals using current thresholds; model appears stable to individual observations."
            )

        if xte_rel > 1e-6:
            actions.append(
                "OLS orthogonality check is higher than expected (X′e): verify intercept handling, consistent X used for fit vs diagnostics, and potential numerical conditioning issues."
            )

        # Assemble report
        lines = []
        lines.append("MODEL DIAGNOSTICS SUMMARY")
        lines.append(
            f"Sample size (n)={n}, parameters (p)={p}  |  HAC: maxlags={r['hac']['maxlags']}, kernel={r['hac']['kernel']}"
        )
        lines.append("")
        lines.append("Performance (in-sample)")
        lines.append(f"  RMSE={fmt(rmse, 6)}  |  MAE={fmt(mae, 6)}  |  MAPE={fmt(mape, 3)}%")
        lines.append("")
        lines.append("Error Structure Tests")
        lines.append(
            f"  Heteroskedasticity: Breusch–Pagan p={fmt(bp_p, 4)}; White p={fmt(w_p, 4)} (alpha={alpha})"
        )
        lines.append(f"  Autocorrelation: Durbin–Watson={fmt(dw, 3)}; Ljung–Box p-values:")
        lines.extend(lb_lines)
        lines.append("")
        lines.append("Stability / Influence")
        lines.append(
            f"  Cook’s distance: threshold={fmt(r['cooks_threshold'], 6)}; flagged={len(r['cooks_flag_indices'])}"
        )
        if cooks_ranking:
            lines.append("  Top Cook’s distance observations (index, D, leverage, rstudent):")
            for row in cooks_ranking:
                lines.append(
                    f"    - {row['index']}: D={fmt(row['cooks_d'], 6)}, h={fmt(row['leverage'], 6)}, r={fmt(row['rstudent'], 3)}"
                )
        lines.append(
            f"  Leveraged-outliers (h>{fmt(r['leverage_threshold'], 6)} and |rstudent|>{fmt(r['student_resid_threshold'], 2)}): "
            f"count={len(r['leveraged_outlier_indices'])}"
        )
        if len(leveraged_idx) > 0:
            lines.append(
                f"    - First {len(leveraged_idx)} indices: {', '.join(map(str, map(int, leveraged_idx)))}"
            )
        lines.append("")
        lines.append("Specification Sanity Checks")
        lines.append(
            f"  X′e relative norm={fmt(xte_rel, 6)} (near zero is expected for OLS with an intercept)"
        )
        lines.append("")
        lines.append("Recommended Next Actions")
        for a in actions:
            lines.append(f"  - {a}")

        return "\n".join(lines)
