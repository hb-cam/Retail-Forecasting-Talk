from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.graphics.regressionplots import influence_plot
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import (
    acorr_ljungbox,
    het_breuschpagan,
    het_white,
    linear_reset,
)
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson


@dataclass
class RegressionDiagnostics:
    """
    OLS + diagnostics wrapper with:
      - HAC (Newey–West) robust standard errors
      - Metrics: RMSE, MAE, MAPE
      - Influence/outliers: leverage, studentized residuals, Cook's D, influence plot
      - Heteroskedasticity: Breusch–Pagan, White
      - Autocorrelation: Durbin–Watson, Ljung–Box
      - Collinearity: Variance Inflation Factor (VIF)
      - Specification test: Ramsey RESET
      - OVB test (optional): auxiliary regression of residuals on candidate omitted vars Z
    """

    X: Any
    y: Any
    add_const: bool = True

    # Optional candidate omitted variables for OVB check
    Z_ovb: Any | None = None
    add_const_Z: bool = True
    ovb_use_hac: bool = False

    # HAC / NW
    hac_maxlags: int | None = None
    hac_kernel: str = "bartlett"

    # Outliers / influence
    leverage_thresh: float | None = None  # default: 2p/n
    student_resid_thresh: float = 3.0
    cooks_thresh: float | None = None  # default: 4/n
    top_cooks: int = 10

    # Autocorr tests
    ljungbox_lags: int = 20

    # Spec test
    reset_power: int = 2
    reset_use_f: bool = True

    # Collinearity
    vif_threshold: float = 5.0

    model_: sm.OLS | None = None
    fit_: Any | None = None
    results_: dict[str, Any] | None = None

    def _to_numpy_2d(self, X: Any) -> np.ndarray:
        if X is None:
            raise ValueError("X is None.")
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

    def _prepare_Z(self, n: int) -> np.ndarray | None:
        if self.Z_ovb is None:
            return None
        Z = self._to_numpy_2d(self.Z_ovb)
        if Z.shape[0] != n:
            raise ValueError(f"Row mismatch: Z has {Z.shape[0]} rows; expected {n}.")
        if self.add_const_Z:
            Z = sm.add_constant(Z, has_constant="add")
        return Z

    # ---- NEW: safe lag caps to prevent PACF ValueError ----
    def _cap_acf_lags(self, requested: int, n: int) -> int:
        # ACF is safe up to n-1; cap defensively and ensure >= 1
        return int(max(1, min(int(requested), n - 1)))

    def _cap_pacf_lags(self, requested: int, n: int) -> int:
        # statsmodels requirement: nlags must be < 0.5*n
        max_allowed = int(np.floor(n / 2) - 1)
        return int(max(1, min(int(requested), max_allowed)))

    # -----------------------------------------------

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
        influence_plot_size: tuple[int, int] = (7, 5),
    ) -> dict[str, Any]:
        if self.fit_ is None:
            raise RuntimeError("Call .fit() before .diagnose(), or call .run().")

        Xn, y = self._prepare_Xy()
        yhat = self.fit_.fittedvalues
        resid = self.fit_.resid

        n, p = Xn.shape

        # ---------- Metrics ----------
        rmse = float(np.sqrt(np.mean((y - yhat) ** 2)))
        mae = float(np.mean(np.abs(y - yhat)))
        mape = self._safe_mape(y, yhat)

        # ---------- Influence / outliers ----------
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

        # statsmodels native leverage/outlier plot: influence_plot
        fig_infl = None
        if make_plots:
            fig_infl = plt.figure(figsize=influence_plot_size)
            ax = fig_infl.gca()
            influence_plot(self.fit_, ax=ax, criterion="cooks")
            ax.set_title("Influence Plot (Leverage vs. Studentized Residuals; Cook’s D contours)")

        # ---------- Orthogonality checks ----------
        Xc = Xn - Xn.mean(axis=0, keepdims=True)
        ec = resid - resid.mean()
        cov_X_e = (Xc.T @ ec) / (n - 1)
        cov_X_e_norm = float(np.linalg.norm(cov_X_e))

        xte = Xn.T @ resid
        xte_norm = float(np.linalg.norm(xte))
        denom = float(np.linalg.norm(Xn, ord="fro") * np.linalg.norm(resid) + 1e-12)
        xte_rel = float(xte_norm / denom)

        # ---------- Heteroskedasticity tests ----------
        # Ensure BP exog includes a constant (required by statsmodels)
        if np.allclose(Xn[:, 0], 1.0):
            X_bp = Xn
        else:
            X_bp = sm.add_constant(Xn, has_constant="add")
        bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(resid, X_bp)

        # White test
        w_lm, w_lm_p, w_f, w_f_p = het_white(resid, X_bp)

        # ---------- Collinearity (VIF) ----------
        has_const = np.allclose(Xn[:, 0], 1.0)
        vif_start = 1 if has_const else 0
        vif_values = np.array([variance_inflation_factor(Xn, i) for i in range(vif_start, p)])
        high_vif_mask = vif_values > self.vif_threshold
        high_vif_indices = np.where(high_vif_mask)[0]

        # ---------- Autocorrelation tests ----------
        dw = float(durbin_watson(resid))
        lb = acorr_ljungbox(resid, lags=self.ljungbox_lags, return_df=True)

        # ---------- Specification test (Ramsey RESET) ----------
        reset_res = linear_reset(self.fit_, power=self.reset_power, use_f=self.reset_use_f)
        spec_test = {
            "test": "Ramsey RESET",
            "power": int(self.reset_power),
            "statistic": float(reset_res.statistic),
            "pvalue": float(reset_res.pvalue),
        }

        # ---------- OVB test (optional): residuals ~ Z ----------
        ovb_test = None
        Z = self._prepare_Z(n)
        if Z is not None:
            aux = sm.OLS(resid, Z).fit(
                cov_type="HAC" if self.ovb_use_hac else "nonrobust",
                cov_kwds={
                    "maxlags": int(self.hac_maxlags or self._infer_hac_lags(n)),
                    "kernel": self.hac_kernel,
                }
                if self.ovb_use_hac
                else None,
            )
            if self.add_const_Z and Z.shape[1] > 1:
                R = np.zeros((Z.shape[1] - 1, Z.shape[1]))
                R[:, 1:] = np.eye(Z.shape[1] - 1)
                wald = aux.wald_test(R)
            else:
                wald = aux.wald_test(np.eye(Z.shape[1]))

            ovb_test = {
                "test": "Auxiliary residual regression (OVB candidate test)",
                "n": int(n),
                "k_z": int(Z.shape[1]),
                "r2": float(aux.rsquared),
                "adj_r2": float(aux.rsquared_adj),
                "joint_statistic": float(np.asarray(wald.statistic).squeeze()),
                "joint_pvalue": float(np.asarray(wald.pvalue).squeeze()),
                "cov_type": ("HAC" if self.ovb_use_hac else "nonrobust"),
            }

        # ---------- ACF/PACF plots (SAFE LAGGING) ----------
        fig_acf = fig_pacf = None
        acf_lags_eff = self._cap_acf_lags(acf_lags, n)
        pacf_lags_eff = self._cap_pacf_lags(pacf_lags, n)

        if make_plots:
            fig_acf = plt.figure()
            plot_acf(resid, lags=acf_lags_eff, ax=plt.gca())
            plt.title(f"Residual ACF (lags={acf_lags_eff})")

            fig_pacf = plt.figure()
            plot_pacf(resid, lags=pacf_lags_eff, ax=plt.gca(), method="ywm")
            plt.title(f"Residual PACF (lags={pacf_lags_eff})")

        out = {
            "n": int(n),
            "p": int(p),
            # Fit/inference (HAC)
            "model_summary": self.fit_.summary().as_text(),
            "coef": np.asarray(self.fit_.params),
            "stderr_hac": np.asarray(self.fit_.bse),
            "tvalues_hac": np.asarray(self.fit_.tvalues),
            "pvalues_hac": np.asarray(self.fit_.pvalues),
            "hac": {
                "maxlags": int(self.fit_.cov_kwds.get("maxlags", -1)),
                "kernel": self.hac_kernel,
            },
            # Predictions
            "fitted": np.asarray(yhat),
            "residuals": np.asarray(resid),
            # Metrics
            "rmse": rmse,
            "mae": mae,
            "mape": mape,
            # Leverage/studentized
            "leverage": np.asarray(hat),
            "studentized_residuals": np.asarray(rstudent),
            "leverage_threshold": float(leverage_thr),
            "student_resid_threshold": float(self.student_resid_thresh),
            "leveraged_outlier_indices": leveraged_outliers,
            # Cook's distance
            "cooks_distance": np.asarray(cooks_d),
            "cooks_threshold": float(cooks_thr),
            "cooks_flag_indices": cooks_flag,
            "cooks_ranking": cooks_ranking,
            # Specification + OVB
            "specification_test": spec_test,
            "ovb_test": ovb_test,
            # Orthogonality checks
            "cov_X_error": np.asarray(cov_X_e),
            "cov_X_error_norm": cov_X_e_norm,
            "XTe": np.asarray(xte),
            "XTe_rel_norm": xte_rel,
            # Heteroskedasticity tests
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
            # Collinearity
            "vif": {
                "vif_values": vif_values,
                "high_vif_indices": high_vif_indices,
                "high_vif_threshold": float(self.vif_threshold),
            },
            # Autocorr tests
            "durbin_watson": dw,
            "ljung_box": lb,
            # Plot handles
            "acf_fig": fig_acf,
            "pacf_fig": fig_pacf,
            "influence_fig": fig_infl,
            # NEW: effective lag values actually used
            "acf_lags_effective": int(acf_lags_eff),
            "pacf_lags_effective": int(pacf_lags_eff),
        }

        self.results_ = out
        return out

    def run(
        self, make_plots: bool = True, acf_lags: int = 40, pacf_lags: int = 40
    ) -> dict[str, Any]:
        self.fit()
        return self.diagnose(make_plots=make_plots, acf_lags=acf_lags, pacf_lags=pacf_lags)

    def report(
        self,
        alpha: float = 0.05,
        ljungbox_focus_lags: list[int] | None = None,
        max_outliers_to_print: int = 5,
    ) -> str:
        if self.results_ is None:
            raise RuntimeError("No diagnostics available. Call .run() before .report().")

        r = self.results_
        n, p = r["n"], r["p"]

        lb: pd.DataFrame = r["ljung_box"]
        if ljungbox_focus_lags is None:
            candidate = [1, 5, 10, min(20, int(lb.index.max()) if len(lb) else self.ljungbox_lags)]
            ljungbox_focus_lags = sorted(
                set([lag for lag in candidate if lag >= 1 and (lag in lb.index or lag <= len(lb))])
            )

        def fmt(x: float, digits: int = 4) -> str:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return "NA"
            if abs(x) < 1e-4 and x != 0:
                return f"{x:.2e}"
            return f"{x:.{digits}f}"

        rmse, mae, mape = r["rmse"], r["mae"], r["mape"]
        dw = r["durbin_watson"]
        bp_p = r["breusch_pagan"]["lm_pvalue"]
        w_p = r["white"]["lm_pvalue"]
        xte_rel = r["XTe_rel_norm"]

        reset_p = r["specification_test"]["pvalue"]
        ovb = r["ovb_test"]
        ovb_p = ovb["joint_pvalue"] if ovb is not None else None

        cooks_ranking = r["cooks_ranking"][
            : int(min(max_outliers_to_print, len(r["cooks_ranking"])))
        ]
        leveraged_idx = r["leveraged_outlier_indices"][
            : int(min(max_outliers_to_print, len(r["leveraged_outlier_indices"])))
        ]

        lb_lines = []
        for lag in ljungbox_focus_lags:
            row = lb.loc[lag] if lag in lb.index else lb.iloc[lag - 1]
            lb_lines.append(f"  - Lag {int(lag):>2}: p={fmt(float(row['lb_pvalue']), 4)}")

        vif_data = r["vif"]
        vif_flag = len(vif_data["high_vif_indices"]) > 0

        hetero_flag = (bp_p < alpha) or (w_p < alpha)
        autocorr_flag = any(
            float((lb.loc[lag] if lag in lb.index else lb.iloc[lag - 1])["lb_pvalue"]) < alpha
            for lag in ljungbox_focus_lags
        )
        spec_flag = reset_p < alpha
        ovb_flag = ovb_p is not None and ovb_p < alpha
        influence_flag = (len(r["cooks_flag_indices"]) > 0) or (
            len(r["leveraged_outlier_indices"]) > 0
        )

        actions: list[str] = []
        if spec_flag:
            actions.append(
                "Specification risk (RESET rejected): consider nonlinear terms, interactions, piecewise effects, or missing lags/seasonality; validate with domain constraints."
            )
        else:
            actions.append(
                "No strong RESET evidence of functional-form misspecification at the chosen alpha; proceed, but continue residual review."
            )

        if ovb is not None:
            if ovb_flag:
                actions.append(
                    "Candidate OVB signal (residuals explained by Z): add/transform Z, or revisit identification; check whether Z is correlated with included regressors."
                )
            else:
                actions.append(
                    "No strong evidence that provided Z explains residual structure at the chosen alpha."
                )
        else:
            actions.append("OVB test not run (no candidate omitted variables Z provided).")

        if hetero_flag:
            actions.append(
                "Heteroskedasticity detected: consider transforms, WLS/GLS, feature re-specification; HAC supports inference but not efficiency."
            )
        else:
            actions.append("No strong evidence of heteroskedasticity at the chosen alpha.")

        if autocorr_flag or (dw < 1.6 or dw > 2.4):
            actions.append(
                "Autocorrelation indicated: consider lags/AR errors, differencing, seasonal terms, or GLS; confirm with ACF/PACF and holdout behavior."
            )
        else:
            actions.append(
                "Residual autocorrelation not strongly indicated in the highlighted lags."
            )

        if influence_flag:
            actions.append(
                "Influential points present: review top Cook’s distance cases; confirm data quality/regimes; consider mitigation strategies."
            )
        else:
            actions.append("No major influence/outlier signals using current thresholds.")

        if vif_flag:
            actions.append(
                "Collinearity detected (VIF > threshold): consider dropping or combining correlated predictors, PCA, or ridge regression."
            )
        else:
            actions.append("No strong collinearity indicated by VIF at the chosen threshold.")

        if xte_rel > 1e-6:
            actions.append(
                "OLS orthogonality (X′e) higher than expected: verify intercept handling, scaling/conditioning, and that diagnostics used the same X as the fit."
            )

        lines = []
        lines.append("MODEL DIAGNOSTICS SUMMARY")
        lines.append(
            f"Sample size (n)={n}, parameters (p)={p}  |  HAC: maxlags={r['hac']['maxlags']}, kernel={r['hac']['kernel']}"
        )
        lines.append("")
        lines.append("Performance (in-sample)")
        lines.append(f"  RMSE={fmt(rmse, 6)}  |  MAE={fmt(mae, 6)}  |  MAPE={fmt(mape, 3)}%")
        lines.append("")
        lines.append("Model Risk Tests")
        lines.append(
            f"  Specification (Ramsey RESET, power={r['specification_test']['power']}): p={fmt(reset_p, 4)} (alpha={alpha})"
        )
        if ovb is not None:
            lines.append(
                f"  OVB candidate test (residuals ~ Z, joint): p={fmt(ovb_p, 4)} | R²={fmt(ovb['r2'], 4)} | cov_type={ovb['cov_type']}"
            )
        else:
            lines.append("  OVB candidate test: not run (provide Z_ovb to enable).")
        lines.append("")
        lines.append("Error Structure Tests")
        lines.append(
            f"  Heteroskedasticity: Breusch–Pagan p={fmt(bp_p, 4)}; White p={fmt(w_p, 4)} (alpha={alpha})"
        )
        lines.append(f"  Autocorrelation: Durbin–Watson={fmt(dw, 3)}; Ljung–Box p-values:")
        lines.extend(lb_lines)
        lines.append("")
        lines.append("Collinearity (VIF)")
        lines.append(
            f"  Threshold={fmt(vif_data['high_vif_threshold'], 1)}; "
            f"flagged={len(vif_data['high_vif_indices'])}"
        )
        for i, v in enumerate(vif_data["vif_values"]):
            flag = " ***" if v > vif_data["high_vif_threshold"] else ""
            lines.append(f"  - Predictor {i + 1}: VIF={fmt(float(v), 2)}{flag}")
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
            f"  X′e relative norm={fmt(xte_rel, 6)} (near zero expected for OLS with an intercept)"
        )
        lines.append("")
        lines.append("ACF/PACF Settings Used")
        lines.append(
            f"  ACF lags used: {r.get('acf_lags_effective', 'NA')}, PACF lags used: {r.get('pacf_lags_effective', 'NA')}"
        )
        lines.append("")
        lines.append("Recommended Next Actions")
        for a in actions:
            lines.append(f"  - {a}")

        return "\n".join(lines)
