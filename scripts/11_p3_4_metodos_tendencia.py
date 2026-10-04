"""
Punto 3.4 — Métodos de tendencia y comparación de resultados (Rol C).

Tres aproximaciones, aplicadas a X, a y z, a escala global y mes a mes:

1. OLS (paramétrico, lineal): X_t = b0 + b1 t + e_t.
   * Global sobre X: además, ajuste con efectos fijos de mes calendario.
   * Inferencia: errores estándar clásicos y HAC de Newey-West (12 rezagos en la
     secuencia mensual; regla floor(4(n/100)^(2/9)) en subseries anuales).
   * Diagnóstico de residuos: autocorrelación de rezago 1, Durbin-Watson,
     Ljung-Box, Breusch-Pagan (heterocedasticidad frente a t) y Shapiro-Wilk.
2. Tendencia monotónica no paramétrica:
   * Global sobre X (con ciclo anual): Kendall estacional + pendiente de Sen
     estacional (Hirsch et al., 1982); valor p también por remuestreo de bloques
     de 3 años completos (conserva dependencia entre meses y persistencia corta).
   * Global sobre a y z (ciclo retirado): Mann-Kendall + Theil-Sen con la
     corrección de varianza de Hamed y Rao (1998).
   * Mes a mes: Mann-Kendall por mes calendario + Sen, con Hamed-Rao.
3. Evolución no lineal (exploratoria): LOESS robusto (Cleveland, 1979), ventana
   equivalente a ~10 años en la escala global (banda 95 % por remuestreo de
   residuos en bloques de 24 meses) y ~15 años en subseries mensuales.

Salidas:
  figuras/tabla_3_4_tendencias_globales.csv
  figuras/tabla_3_4_tendencias_mensuales.csv
  figuras/tabla_3_4_loess_intervalos.csv
  figuras/serie_3_4_loess_global.csv
  figuras/figura_3_4a_metodos_global.png
  figuras/figura_3_4b_loess_mes_anio.png
  figuras/figura_3_4c_diagnostico_residuos.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess
from statsmodels.tsa.stattools import acf

import rol_c_comun as rc

LOESS_WINDOW_YEARS_GLOBAL = 10
LOESS_WINDOW_YEARS_MONTHLY = 15
LOESS_ITER = 2            # iteraciones robustas (atenúan extremos)
BOOT_REPS = 300
BOOT_BLOCK = 24           # meses


def loess_fit(t: np.ndarray, y: np.ndarray, window_years: float) -> tuple[np.ndarray, float]:
    """LOESS local-lineal. frac = fracción de puntos equivalente a la ventana en años."""
    span_years = t.max() - t.min()
    frac = float(np.clip(window_years / span_years, 0.05, 1.0))
    fit = lowess(y, t, frac=frac, it=LOESS_ITER, return_sorted=False)
    return fit, frac


def loess_band(t: np.ndarray, y: np.ndarray, fit: np.ndarray, frac: float) -> tuple[np.ndarray, np.ndarray]:
    """Banda 95 % por remuestreo de bloques móviles de residuos (conserva persistencia corta)."""
    rng = np.random.default_rng(rc.RNG_SEED)
    resid = y - fit
    n = len(y)
    n_blocks = int(np.ceil(n / BOOT_BLOCK))
    sims = np.empty((BOOT_REPS, n))
    for b in range(BOOT_REPS):
        starts = rng.integers(0, n - BOOT_BLOCK + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + BOOT_BLOCK) for s in starts])[:n]
        sims[b] = lowess(fit + resid[idx], t, frac=frac, it=LOESS_ITER, return_sorted=False)
    return np.percentile(sims, 2.5, axis=0), np.percentile(sims, 97.5, axis=0)


def loess_intervals(dates: pd.Series, fit: np.ndarray) -> list[dict]:
    """Tramos de aumento/disminución de la curva LOESS (signo de la derivada)."""
    d = np.sign(np.gradient(fit))
    rows, start = [], 0
    for i in range(1, len(d) + 1):
        if i == len(d) or d[i] != d[start]:
            rows.append({"inicio": dates.iloc[start].strftime("%Y-%m"),
                         "fin": dates.iloc[i - 1].strftime("%Y-%m"),
                         "sentido": "aumento" if d[start] > 0 else "disminución",
                         "cambio_en_tramo": fit[i - 1] - fit[start]})
            start = i
    return rows


def global_analysis(data: pd.DataFrame):
    rows, loess_rows, interval_rows, curves = [], [], [], {}
    for col in rc.VARIABLES:
        anom = rc.add_anomalies(data, col)
        rec = anom.loc[anom["date"].between(*rc.valid_span(data, col))]
        period = f"{rec['date'].min():%Y-%m} a {rec['date'].max():%Y-%m}"
        for rep in rc.REPRESENTATIONS:
            valid = rec.loc[rec[rep].notna()]
            t, y = valid["t"].to_numpy(float), valid[rep].to_numpy(float)
            base = {"variable": col, "representacion": rep, "periodo": period}
            ols = rc.ols_trend(t, y, hac_lags=12)
            rows.append({**base, "metodo": "OLS", **ols})
            if rep == "X":
                ols_fe = rc.ols_trend(t, y, month=valid["month"].to_numpy(), hac_lags=12)
                rows.append({**base, "metodo": "OLS + efectos de mes", **ols_fe})
                sk = rc.seasonal_kendall(valid, rep)
                rows.append({**base, "metodo": "Kendall estacional + Sen estacional", **sk})
            else:
                mk = rc.mann_kendall(t, y, hamed_rao=True)
                rows.append({**base, "metodo": "Mann-Kendall (Hamed-Rao) + Theil-Sen", **mk})
            fit, frac = loess_fit(t, y, LOESS_WINDOW_YEARS_GLOBAL)
            lo, hi = (loess_band(t, y, fit, frac) if rep != "X" else (np.full_like(fit, np.nan),) * 2)
            curves[(col, rep)] = pd.DataFrame({"date": valid["date"].to_numpy(), "t": t, "y": y,
                                               "loess": fit, "lo": lo, "hi": hi})
            years = t.max() - t.min()
            loess_rows.append({**base, "metodo": "LOESS (exploratorio)", "n": len(y),
                               "frac": frac, "ventana_anios": frac * years,
                               "cambio_neto_loess": fit[-1] - fit[0],
                               "cambio_neto_por_dec": 10 * (fit[-1] - fit[0]) / years,
                               "loess_min": fit.min(), "fecha_min": valid["date"].iloc[int(np.argmin(fit))].strftime("%Y-%m"),
                               "loess_max": fit.max(), "fecha_max": valid["date"].iloc[int(np.argmax(fit))].strftime("%Y-%m")})
            if rep == "a":
                for r in loess_intervals(valid["date"], fit):
                    interval_rows.append({"variable": col, "representacion": rep, **r})
    table = pd.concat([pd.DataFrame(rows), pd.DataFrame(loess_rows)], ignore_index=True)
    return table, pd.DataFrame(interval_rows), curves


def monthly_analysis(data: pd.DataFrame):
    rows, loess_grid = [], {}
    for col in rc.VARIABLES:
        anom = rc.add_anomalies(data, col)
        grid = {}
        for month in range(1, 13):
            sub = anom.loc[(anom["month"] == month) & anom["X"].notna()]
            t = sub["t"].to_numpy(float)
            for rep in rc.REPRESENTATIONS:
                y = sub[rep].to_numpy(float)
                base = {"variable": col, "representacion": rep, "mes": month,
                        "periodo": f"{sub['year'].min()}-{sub['year'].max()}", "n": len(y)}
                ols = rc.ols_trend(t, y)
                mk = rc.mann_kendall(t, y, hamed_rao=True)
                rows.append({**base,
                             **{f"ols_{k}": v for k, v in ols.items() if k != "n"},
                             **{f"mk_{k}": v for k, v in mk.items() if k != "n"}})
            fit, frac = loess_fit(t, sub["z"].to_numpy(float), LOESS_WINDOW_YEARS_MONTHLY)
            grid[month] = pd.Series(fit, index=sub["year"].to_numpy())
        loess_grid[col] = pd.DataFrame(grid).T  # filas: mes, columnas: año
    return pd.DataFrame(rows), loess_grid


def plot_global(curves: dict, table: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(4, 3, figsize=(13, 11), sharex=True)
    for i, (col, meta) in enumerate(rc.VARIABLES.items()):
        for k, rep in enumerate(rc.REPRESENTATIONS):
            ax = axes[i, k]
            c = curves[(col, rep)]
            ax.plot(c["date"], c["y"], color=rc.COLOR_POINTS, lw=0.5, alpha=0.55)
            sel = table.loc[(table["variable"] == col) & (table["representacion"] == rep)]
            ols = sel.loc[sel["metodo"] == "OLS"].iloc[0]
            ax.plot(c["date"], ols["intercept_at_mean_t"] + ols["slope_dec"] / 10 * (c["t"] - ols["t_mean"]),
                    color=rc.COLOR_OLS, lw=2, label="OLS")
            if rep != "X":
                mk = sel.loc[sel["metodo"].str.startswith("Mann")].iloc[0]
                b = mk["sen_dec"] / 10
                intercept = np.median(c["y"] - b * c["t"])
                ax.plot(c["date"], intercept + b * c["t"], color=rc.COLOR_SEN, lw=2, ls="--", label="Theil-Sen")
                ax.fill_between(c["date"], c["lo"], c["hi"], color=rc.COLOR_LOESS, alpha=0.25, lw=0)
                ax.axhline(0, color="#0b0b0b", lw=0.6)
                txt = (f"OLS {ols['slope_dec']:+.2f} [{ols['ci_low_hac_dec']:+.2f}, {ols['ci_high_hac_dec']:+.2f}] p={ols['p_hac']:.3f}\n"
                       f"Sen {mk['sen_dec']:+.2f} [{mk['sen_low_hr_dec']:+.2f}, {mk['sen_high_hr_dec']:+.2f}] p$_{{HR}}$={mk['p_mk_hr']:.3f}")
            else:
                sk = sel.loc[sel["metodo"].str.startswith("Kendall")].iloc[0]
                fe = sel.loc[sel["metodo"] == "OLS + efectos de mes"].iloc[0]
                txt = (f"OLS+mes {fe['slope_dec']:+.2f} p={fe['p_hac']:.3f}\n"
                       f"Sen est. {sk['sen_dec']:+.2f} [{sk['sen_low_dec']:+.2f}, {sk['sen_high_dec']:+.2f}] p$_{{boot}}$={sk['p_sk_boot']:.3f}")
            ax.plot(c["date"], c["loess"], color=rc.COLOR_LOESS, lw=2.2, label="LOESS ~10 años")
            ax.text(0.01, 0.98, txt, transform=ax.transAxes, va="top", fontsize=6.5,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
            unit = meta["unit"] if rep != "z" else "adim."
            ax.set_ylabel(f"{meta['short']} [{unit}]")
            if i == 0:
                ax.set_title(rc.REPRESENTATIONS[rep])
    handles, labels = axes[0, 1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("Figura 3.4a. Comparación de métodos en la escala global (pendientes por década, IC 95 %)\n"
                 "OLS con IC HAC; Sen con IC de Hamed-Rao (a, z) o Kendall estacional (X); "
                 "banda verde: IC 95 % LOESS por bootstrap de bloques", fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(rc.FIGURES_DIR / "figura_3_4a_metodos_global.png")
    plt.close(fig)


def plot_loess_heatmaps(loess_grid: dict) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(4, 1, figsize=(11, 11))
    for ax, (col, meta) in zip(axes, rc.VARIABLES.items()):
        grid = loess_grid[col]
        cmap = "RdBu_r" if col == "Temp_C" else "BrBG"
        im = ax.pcolormesh(grid.columns, np.arange(1, 13), grid.to_numpy(float),
                           cmap=cmap, vmin=-1.5, vmax=1.5, shading="nearest")
        ax.set_yticks(range(1, 13), rc.MONTH_NAMES, fontsize=7)
        ax.invert_yaxis()
        ax.set_xlim(1979.5, 2020.5)  # mismo eje en las cuatro variables
        ax.grid(False)
        ax.set_title(f"{meta['label']}: LOESS de z por mes calendario", fontsize=9)
        fig.colorbar(im, ax=ax, pad=0.01, label="z suavizada")
    axes[-1].set_xlabel("Año")
    fig.suptitle("Figura 3.4b. Evolución no lineal mes a mes: LOESS (ventana ~15 años; ~todo el registro en "
                 "$P_I$ y $T$) de la anomalía estandarizada\nEscala recortada a ±1.5; exploratorio, sin inferencia",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_3_4b_loess_mes_anio.png")
    plt.close(fig)


def plot_diagnostics(data: pd.DataFrame, table: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(2, 4, figsize=(13, 5.5))
    for k, (col, meta) in enumerate(rc.VARIABLES.items()):
        anom = rc.add_anomalies(data, col)
        rec = anom.loc[anom["date"].between(*rc.valid_span(data, col)) & anom["a"].notna()]
        r = table.loc[(table["variable"] == col) & (table["representacion"] == "a")
                      & (table["metodo"] == "OLS")].iloc[0]
        resid = rec["a"] - (r["intercept_at_mean_t"] + r["slope_dec"] / 10 * (rec["t"] - r["t_mean"]))
        axes[0, k].plot(rec["date"], resid, color=rc.COLOR_POINTS, lw=0.6)
        axes[0, k].axhline(0, color="#0b0b0b", lw=0.6)
        axes[0, k].set_title(f"{meta['short']}: residuos OLS de a", fontsize=9)
        axes[0, k].set_ylabel(meta["unit"])
        # ACF calculada sobre la malla regular (los NaN se ignoran por pares).
        acf_vals = acf(resid.to_numpy(), nlags=36, missing="conservative")
        lags = np.arange(len(acf_vals))
        axes[1, k].bar(lags[1:], acf_vals[1:], color=rc.COLOR_OLS, width=0.7)
        bound = 1.96 / np.sqrt(len(resid))
        axes[1, k].axhspan(-bound, bound, color="#9a9994", alpha=0.25, lw=0)
        axes[1, k].set_xlabel("Rezago [meses]")
        axes[1, k].set_ylim(-0.4, 1)
        axes[1, k].text(0.97, 0.95, f"DW={r['durbin_watson']:.2f}\nLjung-Box(12) p={r['ljungbox_p']:.1e}\n"
                        f"Breusch-Pagan p={r['breusch_pagan_p']:.2f}", transform=axes[1, k].transAxes,
                        ha="right", va="top", fontsize=7, bbox=dict(fc="white", ec="none", alpha=0.85))
    axes[1, 0].set_ylabel("Autocorrelación")
    fig.suptitle("Figura 3.4c. Diagnóstico de residuos de la tendencia OLS global sobre anomalías "
                 "(banda gris: ±1.96/√n)", fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_3_4c_diagnostico_residuos.png")
    plt.close(fig)


def main() -> None:
    data = rc.load_master_data()
    glob, intervals, curves = global_analysis(data)
    glob.to_csv(rc.FIGURES_DIR / "tabla_3_4_tendencias_globales.csv", index=False)
    intervals.to_csv(rc.FIGURES_DIR / "tabla_3_4_loess_intervalos.csv", index=False)
    pd.concat([c.assign(variable=v, representacion=r) for (v, r), c in curves.items()]).to_csv(
        rc.FIGURES_DIR / "serie_3_4_loess_global.csv", index=False)
    monthly, loess_grid = monthly_analysis(data)
    monthly.to_csv(rc.FIGURES_DIR / "tabla_3_4_tendencias_mensuales.csv", index=False)
    plot_global(curves, glob)
    plot_loess_heatmaps(loess_grid)
    plot_diagnostics(data, glob)

    pd.set_option("display.width", 250)
    cols = ["variable", "representacion", "metodo", "n", "slope_dec", "ci_low_hac_dec", "ci_high_hac_dec",
            "p_hac", "sen_dec", "sen_low_dec", "sen_high_dec", "p_mk", "p_mk_hr", "hr_factor",
            "p_sk", "p_sk_boot", "resid_lag1", "ljungbox_p", "breusch_pagan_p", "cambio_neto_por_dec"]
    print(glob[[c for c in cols if c in glob]].round(3).to_string(index=False))
    print("\nTramos LOESS (anomalía a):")
    print(intervals.round(2).to_string(index=False))
    m = monthly.loc[monthly["representacion"] == "X"]
    print("\nMes a mes (X): pendiente OLS y Sen por década, p HAC y p MK-HR")
    print(m[["variable", "mes", "n", "ols_slope_dec", "ols_p_hac", "mk_sen_dec", "mk_p_mk", "mk_p_mk_hr"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
