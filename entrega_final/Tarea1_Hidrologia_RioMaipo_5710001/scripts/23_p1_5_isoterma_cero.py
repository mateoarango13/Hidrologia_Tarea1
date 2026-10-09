"""Punto 1.5.c (y 3.6): isoterma de 0 °C y área de la cuenca bajo cero.

Pregunta física: ¿qué parte de la cuenca está bajo 0 °C en cada mes y qué fracción
de la precipitación cae sobre esa parte? Es la base cuantitativa del régimen nival.

Método (explícito y reproducible):
  * T(z) = T_cuenca + Γ (z_media − z): la temperatura media mensual CR2MET de la cuenca
    (Temp_C del CSV maestro) se asigna a la elevación media de la hipsometría y se
    extrapola con un gradiente vertical Γ. Γ = 6.5 °C/km (atmósfera estándar) es el
    valor central; 5.5 y 7.5 °C/km acotan la sensibilidad.
  * Isoterma de 0 °C: z0 = z_media + 1000 · T_cuenca / Γ  [m s.n.m.].
  * Fracción del área bajo cero: área sobre z0, interpolada linealmente dentro de cada
    franja de 250 m de la curva hipsométrica (script 22, ASTER GDEM v3).
  * Fracción de la precipitación sobre área bajo cero: Σ P_m f_m / Σ P_m, suponiendo P
    uniforme en la cuenca (supuesto conservador: el realce orográfico concentra más
    lluvia en altura, de modo que la fracción real sería mayor).
  * Contraste: la misma cuenta con ERA5-Land (Temp_ERA5L_C, 2000-06 a 2020-03) y la
    fracción de precipitación diaria con T CR2MET < 0 °C (sin hipsometría).
  * Tendencia de la isoterma invernal (media mayo–septiembre por año, 1980–2019):
    OLS con IC HAC y Theil–Sen con Mann–Kendall de Hamed–Rao (funciones de rol_c_comun).

Entradas: datos/datos_mensuales_maipo.csv, figuras/tabla_1_12_hipsometria.csv (script 22),
          datos/camels_cl_5710001/{precip,tmax,tmin}_cr2met_day.csv
Salidas:  figuras/tabla_1_13_isoterma_cero_climatologia.csv
          figuras/tabla_1_14_isoterma_cero_resumen.csv
          figuras/figura_1_9_isoterma_cero.png

Ejecutar desde la raíz (después del script 22):  python scripts/23_p1_5_isoterma_cero.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import rol_c_comun as rc

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "datos" / "camels_cl_5710001"
GAMMAS = {"central": 6.5, "bajo": 5.5, "alto": 7.5}  # °C/km
WINTER = [5, 6, 7, 8, 9]


def load_hypsometry() -> tuple[np.ndarray, np.ndarray, float]:
    h = pd.read_csv(rc.FIGURES_DIR / "tabla_1_12_hipsometria.csv")
    edges = np.append(h["z_inf_m"].to_numpy(float), h["z_sup_m"].iloc[-1])
    above = np.append(h["fraccion_area_sobre_z_inf"].to_numpy(float), 0.0)
    z_mean = float(np.sum(0.5 * (h["z_inf_m"] + h["z_sup_m"]) * h["fraccion_area"]) / h["fraccion_area"].sum())
    return edges, above, z_mean


def area_above(z0: np.ndarray, edges: np.ndarray, above: np.ndarray) -> np.ndarray:
    """Fracción del área de la cuenca por encima de z0 (interpolación lineal por franja)."""
    return np.interp(z0, edges, above, left=1.0, right=0.0)


def daily_snow_fraction() -> float:
    read = lambda n: pd.read_csv(RAW / n, parse_dates=["date"], index_col="date")["5710001"].loc["1980-01-01":"2020-04-30"]
    p = read("precip_cr2met_day.csv")
    t = (read("tmax_cr2met_day.csv") + read("tmin_cr2met_day.csv")) / 2
    return float(p[t < 0].sum() / p.sum())


def main() -> None:
    data = rc.load_master_data()
    edges, above, z_mean = load_hypsometry()

    for name, g in GAMMAS.items():
        data[f"z0_{name}"] = z_mean + 1000 * data["Temp_C"] / g
        data[f"f_{name}"] = area_above(data[f"z0_{name}"].to_numpy(float), edges, above)
    data["z0_era5l"] = z_mean + 1000 * data["Temp_ERA5L_C"] / GAMMAS["central"]
    data["f_era5l"] = np.where(data["Temp_ERA5L_C"].notna(),
                               area_above(data["z0_era5l"].to_numpy(float), edges, above), np.nan)

    # Climatología mensual 1980-2020 (CR2MET) y 2000-06/2020-03 (ERA5-Land)
    clim = data.groupby("month").agg(
        T_CR2MET_C=("Temp_C", "mean"), T_ERA5L_C=("Temp_ERA5L_C", "mean"),
        P_local_mm=("P_local_mm", "mean"),
        z0_m=("z0_central", "mean"), z0_m_gamma55=("z0_bajo", "mean"), z0_m_gamma75=("z0_alto", "mean"),
        frac_area_bajo_cero=("f_central", "mean"), frac_area_bajo_cero_gamma55=("f_bajo", "mean"),
        frac_area_bajo_cero_gamma75=("f_alto", "mean"),
        z0_m_era5l=("z0_era5l", "mean"), frac_area_bajo_cero_era5l=("f_era5l", "mean"))
    clim.index.name = "mes"
    clim.round(4).to_csv(rc.FIGURES_DIR / "tabla_1_13_isoterma_cero_climatologia.csv")

    # Fracción de la precipitación que cae sobre área bajo cero (P uniforme)
    def p_weighted(col, sub=None):
        d = data if sub is None else sub
        d = d.dropna(subset=["P_local_mm", col])
        return float((d["P_local_mm"] * d[col]).sum() / d["P_local_mm"].sum())

    common = data.dropna(subset=["Temp_ERA5L_C"])
    rows = [
        {"indicador": "elevación media de la hipsometría (m)", "valor": z_mean},
        {"indicador": "fracción de P sobre área bajo cero, CR2MET Γ=6.5, 1980-2020", "valor": p_weighted("f_central")},
        {"indicador": "fracción de P sobre área bajo cero, CR2MET Γ=5.5, 1980-2020", "valor": p_weighted("f_bajo")},
        {"indicador": "fracción de P sobre área bajo cero, CR2MET Γ=7.5, 1980-2020", "valor": p_weighted("f_alto")},
        {"indicador": "fracción de P sobre área bajo cero, CR2MET Γ=6.5, 2000-06/2020-03", "valor": p_weighted("f_central", common)},
        {"indicador": "fracción de P sobre área bajo cero, ERA5-Land Γ=6.5, 2000-06/2020-03", "valor": p_weighted("f_era5l", common)},
        {"indicador": "fracción de P diaria con T media CR2MET de la cuenca < 0 °C, 1980-2020", "valor": daily_snow_fraction()},
        {"indicador": "frac_snow_cr2met_1979_2010 (atributo CAMELS-CL)", "valor": 0.7091864},
    ]

    # Isoterma invernal (mayo-septiembre) por año y su tendencia
    win = data[data["month"].isin(WINTER)].groupby("year").agg(z0=("z0_central", "mean"), n=("z0_central", "count"))
    win = win[win["n"] == len(WINTER)]
    t = win.index.to_numpy(float) + 0.5
    ols = rc.ols_trend(t, win["z0"].to_numpy(float))
    mk = rc.mann_kendall(t, win["z0"].to_numpy(float))
    rows += [
        {"indicador": "isoterma invernal (may-sep) media 1980-2019 (m)", "valor": win["z0"].mean()},
        {"indicador": "años con isoterma invernal completa", "valor": len(win)},
        {"indicador": "tendencia OLS isoterma invernal (m/década)", "valor": ols["slope_dec"]},
        {"indicador": "IC 95 % HAC inferior (m/década)", "valor": ols["ci_low_hac_dec"]},
        {"indicador": "IC 95 % HAC superior (m/década)", "valor": ols["ci_high_hac_dec"]},
        {"indicador": "p HAC", "valor": ols["p_hac"]},
        {"indicador": "Theil-Sen (m/década)", "valor": mk["sen_dec"]},
        {"indicador": "p Mann-Kendall Hamed-Rao", "valor": mk["p_mk_hr"]},
    ]
    summary = pd.DataFrame(rows)
    summary.to_csv(rc.FIGURES_DIR / "tabla_1_14_isoterma_cero_resumen.csv", index=False)

    # Figura
    rc.apply_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.15, 1]})
    m = np.arange(1, 13)
    ax1.fill_between(m, clim["z0_m_gamma75"], clim["z0_m_gamma55"], color=rc.COLOR_OLS, alpha=0.18,
                     label="CR2MET, Γ = 5.5–7.5 °C/km")
    ax1.plot(m, clim["z0_m"], "o-", color=rc.COLOR_OLS, label="CR2MET 1980–2020, Γ = 6.5 °C/km")
    ax1.plot(m, clim["z0_m_era5l"], "s--", color=rc.COLOR_SEN, lw=1.4, label="ERA5-Land 2000–2020, Γ = 6.5 °C/km")
    for q, ls in [(0.25, ":"), (0.5, "--"), (0.75, ":")]:
        zq = float(np.interp(q, above[::-1], edges[::-1]))  # altura con una fracción q del área por encima
        ax1.axhline(zq, color="#52514e", lw=0.8, ls=ls)
        ax1.text(0.7, zq + 40, f"{int(q * 100)} % del área sobre {zq:.0f} m", fontsize=7, va="bottom", color="#52514e")
    ax1.set_xticks(m, rc.MONTH_NAMES)
    ax1.set_xlim(0.6, 12.4)
    ax1.set_ylabel("Altura de la isoterma de 0 °C [m s.n.m.]")
    ax1.set_title("a) Ciclo anual de la isoterma de 0 °C frente a la hipsometría")
    ax1.legend(frameon=False, loc="upper center", fontsize=7.5)
    ax1b = ax1.twinx()
    ax1b.bar(m, clim["P_local_mm"], color="#9aa0a6", alpha=0.25, width=0.6)
    ax1b.set_ylabel("P_L media [mm/mes] (barras)")
    ax1b.grid(False)
    ax1.set_zorder(ax1b.get_zorder() + 1)
    ax1.patch.set_visible(False)

    ax2.plot(win.index, win["z0"], "o-", color=rc.COLOR_POINTS, lw=1.2, ms=3.5, label="Media may–sep (CR2MET, Γ = 6.5)")
    fit_line = win["z0"].mean() + ols["slope_dec"] / 10 * (t - t.mean())
    ax2.plot(win.index, fit_line, color=rc.COLOR_OLS,
             label=f"OLS {ols['slope_dec']:+.0f} m/década [IC HAC {ols['ci_low_hac_dec']:+.0f}, {ols['ci_high_hac_dec']:+.0f}], p = {ols['p_hac']:.3f}")
    ax2.set_ylabel("Isoterma de 0 °C invernal [m s.n.m.]")
    ax2.set_title("b) Isoterma invernal por año (estación de acumulación)")
    ax2.legend(frameon=False, loc="upper left", fontsize=7.5)
    fig.suptitle("Figura 1.9. Isoterma de 0 °C estimada con T CR2MET, gradiente vertical Γ e hipsometría ASTER GDEM "
                 "(script 23)", fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_1_9_isoterma_cero.png", dpi=rc.DPI)
    plt.close(fig)

    print(clim[["T_CR2MET_C", "z0_m", "frac_area_bajo_cero", "T_ERA5L_C", "frac_area_bajo_cero_era5l"]].round(2).to_string())
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
