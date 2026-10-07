"""
Punto 3.3 — Dos escalas de evaluación temporal (Rol C).

1) TODOS LOS DATOS: secuencia cronológica de meses, en X, a y z.
   En la serie original se considera explícitamente la estacionalidad con un
   ajuste OLS con efectos fijos de mes calendario: X_t = b1 t + sum_j g_j D_j(t).
2) MES A MES: doce subseries (todos los eneros, todos los febreros, ...), en X, a, z.

Variable temporal: año decimal de la fecha real (los vacíos se respetan).
Verificación pedida por la guía: dentro de un mismo mes calendario y con la
misma muestra, b1(a) = b1(X) y b1(z) = b1(X)/s_j. Se comprueba numéricamente.

Las pendientes OLS de este script son la base; la inferencia completa
(HAC, Mann-Kendall, Sen, LOESS) está en 11_p3_4_metodos_tendencia.py.

Salidas:
  figuras/tabla_3_3_pendientes_ols_dos_escalas.csv
  figuras/tabla_3_3_verificacion_invarianza.csv
  figuras/figura_3_3a_todos_los_datos.png
  figuras/figura_3_3b_subseries_mensuales.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import rol_c_comun as rc


def global_slopes(data: pd.DataFrame) -> list[dict]:
    rows = []
    for col in rc.VARIABLES:
        anom = rc.add_anomalies(data, col)
        rec = anom.loc[anom["date"].between(*rc.valid_span(data, col))]
        for rep in rc.REPRESENTATIONS:
            y = rec[rep].to_numpy(float)
            t = rec["t"].to_numpy(float)
            res = rc.ols_trend(t, y, hac_lags=12)
            rows.append({"escala": "todos_los_datos", "modelo": "OLS simple",
                         "variable": col, "representacion": rep, "mes": 0, **res})
            # Ajuste con efectos estacionales (pedido para X; se reporta en las 3).
            res_fe = rc.ols_trend(t, y, month=rec["month"].to_numpy(), hac_lags=12)
            rows.append({"escala": "todos_los_datos", "modelo": "OLS + efectos de mes",
                         "variable": col, "representacion": rep, "mes": 0, **res_fe})
    return rows


def monthly_slopes(data: pd.DataFrame) -> list[dict]:
    rows = []
    for col in rc.VARIABLES:
        anom = rc.add_anomalies(data, col)
        for month in range(1, 13):
            sub = anom.loc[(anom["month"] == month) & anom["X"].notna()]
            for rep in rc.REPRESENTATIONS:
                res = rc.ols_trend(sub["t"].to_numpy(float), sub[rep].to_numpy(float))
                rows.append({"escala": "mes_a_mes", "modelo": "OLS simple",
                             "variable": col, "representacion": rep, "mes": month,
                             "periodo": f"{sub['year'].min()}-{sub['year'].max()}", **res})
    return rows


def invariance_check(table: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    monthly = table.loc[table["escala"] == "mes_a_mes"].pivot_table(
        index=["variable", "mes"], columns="representacion", values="slope_dec")
    rows = []
    for col in rc.VARIABLES:
        clim = rc.reference_climatology(data, col)
        for month in range(1, 13):
            sx, sa, sz = monthly.loc[(col, month), ["X", "a", "z"]]
            s_j = clim.loc[month, "s"]
            rows.append({"variable": col, "mes": month, "pend_X_dec": sx, "pend_a_dec": sa,
                         "pend_z_dec": sz, "s_j": s_j,
                         "dif_a_menos_X": sa - sx, "dif_z_por_sj_menos_X": sz * s_j - sx})
    check = pd.DataFrame(rows)
    if not (np.allclose(check["dif_a_menos_X"], 0, atol=1e-8)
            and np.allclose(check["dif_z_por_sj_menos_X"], 0, atol=1e-8)):
        raise AssertionError("La invarianza de la pendiente OLS mensual no se cumple.")
    return check


def plot_global(data: pd.DataFrame, table: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(4, 3, figsize=(13, 10.5), sharex=True)
    glob = table.loc[table["escala"] == "todos_los_datos"]
    for i, (col, meta) in enumerate(rc.VARIABLES.items()):
        anom = rc.add_anomalies(data, col)
        rec = anom.loc[anom["date"].between(*rc.valid_span(data, col))]
        for k, rep in enumerate(rc.REPRESENTATIONS):
            ax = axes[i, k]
            ax.plot(rec["date"], rec[rep], color=rc.COLOR_POINTS, lw=0.6, alpha=0.8)
            r = glob.loc[(glob["variable"] == col) & (glob["representacion"] == rep)
                         & (glob["modelo"] == "OLS simple")].iloc[0]
            tt = rec["t"].to_numpy()
            line = r["intercept_at_mean_t"] + r["slope_dec"] / 10 * (tt - r["t_mean"])
            ax.plot(rec["date"], line, color=rc.COLOR_OLS, lw=2)
            r_fe = glob.loc[(glob["variable"] == col) & (glob["representacion"] == rep)
                            & (glob["modelo"] == "OLS + efectos de mes")].iloc[0]
            unit = meta["unit"] if rep != "z" else "adim."
            txt = (f"OLS: {r['slope_dec']:+.2f} {unit}/déc (p$_{{HAC}}$={r['p_hac']:.2f})\n"
                   f"OLS+mes: {r_fe['slope_dec']:+.2f} (p$_{{HAC}}$={r_fe['p_hac']:.2f})")
            ax.text(0.01, 0.97, txt, transform=ax.transAxes, va="top", fontsize=7,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
            ax.set_ylabel(f"{meta['short']} [{unit}]")
            if i == 0:
                ax.set_title(rc.REPRESENTATIONS[rep])
    fig.suptitle("Figura 3.3a. Escala 'todos los datos': tendencia OLS sobre la secuencia cronológica "
                 "(línea azul)\nOLS+mes: ajuste con efectos fijos de mes calendario; IC/p con errores HAC "
                 "(Newey-West, 12 rezagos)", fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_3_3a_todos_los_datos.png")
    plt.close(fig)


def plot_monthly(data: pd.DataFrame, table: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(12, 4, figsize=(12, 19), sharex=True)
    mon = table.loc[(table["escala"] == "mes_a_mes") & (table["representacion"] == "X")]
    for k, (col, meta) in enumerate(rc.VARIABLES.items()):
        anom = rc.add_anomalies(data, col)
        for month in range(1, 13):
            ax = axes[month - 1, k]
            sub = anom.loc[(anom["month"] == month) & anom["X"].notna()]
            ax.plot(sub["year"], sub["X"], "o", ms=3, color=rc.COLOR_POINTS)
            r = mon.loc[(mon["variable"] == col) & (mon["mes"] == month)].iloc[0]
            line = r["intercept_at_mean_t"] + r["slope_dec"] / 10 * (sub["t"] - r["t_mean"])
            ax.plot(sub["year"], line, color=rc.COLOR_OLS, lw=1.8,
                    ls="-" if r["p_hac"] < rc.ALPHA else "--")
            ax.text(0.98, 0.95, f"{r['slope_dec']:+.2f}/déc\np$_{{HAC}}$={r['p_hac']:.2f}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=6.5,
                    bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
            if k == 0:
                ax.set_ylabel(rc.MONTH_NAMES[month - 1], fontsize=9, fontweight="bold")
            if month == 1:
                ax.set_title(f"{meta['short']} [{meta['unit']}]")
            ax.tick_params(labelsize=7)
    fig.suptitle("Figura 3.3b. Escala 'mes a mes': doce subseries por mes calendario (serie original)\n"
                 "Línea continua: p$_{HAC}$ < 0.05 sin corregir por comparaciones múltiples; discontinua: p ≥ 0.05",
                 fontsize=10, y=0.995)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_3_3b_subseries_mensuales.png")
    plt.close(fig)


def main() -> None:
    data = rc.load_master_data()
    table = pd.DataFrame(global_slopes(data) + monthly_slopes(data))
    table.to_csv(rc.FIGURES_DIR / "tabla_3_3_pendientes_ols_dos_escalas.csv", index=False)
    check = invariance_check(table, data)
    check.to_csv(rc.FIGURES_DIR / "tabla_3_3_verificacion_invarianza.csv", index=False)
    plot_global(data, table)
    plot_monthly(data, table)

    cols = ["variable", "representacion", "modelo", "n", "slope_dec",
            "ci_low_hac_dec", "ci_high_hac_dec", "p_ols", "p_hac", "resid_lag1"]
    print("Escala 'todos los datos' (pendiente por década):")
    print(table.loc[table["escala"] == "todos_los_datos", cols].round(3).to_string(index=False))
    print("\nVerificación de invarianza mensual: máx |b(a)-b(X)| = "
          f"{check['dif_a_menos_X'].abs().max():.2e}; máx |b(z)*s_j-b(X)| = "
          f"{check['dif_z_por_sj_menos_X'].abs().max():.2e}  -> OK")


if __name__ == "__main__":
    main()
