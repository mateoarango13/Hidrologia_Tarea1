"""Punto 3.6: ¿responde el caudal de forma consistente con la lluvia? Balance por año hidrológico.

Para los años hidrológicos (abril–marzo) con los doce meses válidos de P_L y de Q:
  * totales anuales de P_L y R (mm/año) y cociente R/P;
  * medias antes (1980–2009) y después (2010–2019) del inicio de la megasequía, cambio
    relativo y elasticidad aparente ε = (ΔR/R) / (ΔP/P);
  * tendencia de R/P (Theil–Sen con Mann–Kendall de Hamed–Rao);
  * regresión anual R_t = b0 + b1 P_t + b2 P_{t-1} (memoria de un año) y residuo medio
    antes y después de 2010;
  * deriva entre fuentes: diferencia anual P_I − P_L y cociente P_I/P_L (2000–2019) con su
    tendencia (Theil–Sen, Mann–Kendall de Hamed–Rao).

Salidas:
  figuras/tabla_3_6_balance_anual.csv    (un año por fila)
  figuras/tabla_3_6_balance_resumen.csv  (indicadores)

Ejecutar desde la raíz:  python scripts/25_p3_6_balance_anual.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

import rol_c_comun as rc


def annual_totals(data: pd.DataFrame) -> pd.DataFrame:
    g = data.groupby("water_year")
    out = pd.DataFrame({
        "meses_P": g["P_local_mm"].count(), "meses_Q": g["Q_lamina_mm"].count(),
        "meses_PI": g["P_IMERG_mm"].count(),
        "P_anual_mm": g["P_local_mm"].sum(min_count=12), "R_anual_mm": g["Q_lamina_mm"].sum(min_count=12),
        "PI_anual_mm": g["P_IMERG_mm"].sum(min_count=12),
    })
    out.loc[out["meses_P"] < 12, "P_anual_mm"] = np.nan
    out.loc[out["meses_Q"] < 12, "R_anual_mm"] = np.nan
    out.loc[out["meses_PI"] < 12, "PI_anual_mm"] = np.nan
    out["R_sobre_P"] = out["R_anual_mm"] / out["P_anual_mm"]
    out["PI_menos_PL_mm"] = out["PI_anual_mm"] - out["P_anual_mm"]
    out["PI_sobre_PL"] = out["PI_anual_mm"] / out["P_anual_mm"]
    out.index.name = "anio_hidrologico"
    return out


def main() -> None:
    data = rc.load_master_data()
    data = data[(data["water_year"] >= 1980) & (data["water_year"] <= 2019)]
    ann = annual_totals(data)
    both = ann.dropna(subset=["P_anual_mm", "R_anual_mm"])

    pre, post = both.loc[both.index <= 2009], both.loc[both.index >= 2010]
    dP = post["P_anual_mm"].mean() / pre["P_anual_mm"].mean() - 1
    dR = post["R_anual_mm"].mean() / pre["R_anual_mm"].mean() - 1

    t = both.index.to_numpy(float) + 0.5
    mk_rp = rc.mann_kendall(t, both["R_sobre_P"].to_numpy(float))

    # Regresión con la lluvia del año previo (exige P del año anterior válido)
    reg = both.copy()
    reg["P_prev"] = ann["P_anual_mm"].shift(1).reindex(reg.index)
    reg = reg.dropna(subset=["P_prev"])
    X = sm.add_constant(reg[["P_anual_mm", "P_prev"]].to_numpy())
    fit = sm.OLS(reg["R_anual_mm"].to_numpy(), X).fit()
    reg["residuo_mm"] = fit.resid
    ann["residuo_regresion_mm"] = reg["residuo_mm"].reindex(ann.index)

    sat = ann.dropna(subset=["PI_anual_mm", "P_anual_mm"])
    ts = sat.index.to_numpy(float) + 0.5
    mk_dif = rc.mann_kendall(ts, sat["PI_menos_PL_mm"].to_numpy(float))
    ols_dif = rc.ols_trend(ts, sat["PI_menos_PL_mm"].to_numpy(float))

    rows = [
        ("años hidrológicos completos (P y R)", len(both)),
        ("años completos 1980-2009", len(pre)), ("años completos 2010-2019", len(post)),
        ("P media 1980-2009 (mm/año)", pre["P_anual_mm"].mean()), ("P media 2010-2019 (mm/año)", post["P_anual_mm"].mean()),
        ("R media 1980-2009 (mm/año)", pre["R_anual_mm"].mean()), ("R media 2010-2019 (mm/año)", post["R_anual_mm"].mean()),
        ("cambio relativo de P (%)", 100 * dP), ("cambio relativo de R (%)", 100 * dR),
        ("elasticidad aparente ΔR/R ÷ ΔP/P", dR / dP),
        ("R/P medio 1980-2009", pre["R_sobre_P"].mean()), ("R/P medio 2010-2019", post["R_sobre_P"].mean()),
        ("R/P mediana (todos)", both["R_sobre_P"].median()),
        ("Sen de R/P (por década)", mk_rp["sen_dec"]), ("p MK Hamed-Rao de R/P", mk_rp["p_mk_hr"]),
        ("regresión: n años", int(fit.nobs)), ("regresión: b0 (mm)", fit.params[0]),
        ("regresión: b1 (P del año)", fit.params[1]), ("regresión: b2 (P del año previo)", fit.params[2]),
        ("regresión: p de b2", fit.pvalues[2]), ("regresión: R²", fit.rsquared),
        ("residuo medio hasta 2009 (mm/año)", reg.loc[reg.index <= 2009, "residuo_mm"].mean()),
        ("residuo medio 2010-2019 (mm/año)", reg.loc[reg.index >= 2010, "residuo_mm"].mean()),
        ("años con IMERG completo", len(sat)),
        ("P_I - P_L: Sen (mm/año por década)", mk_dif["sen_dec"]), ("P_I - P_L: p MK Hamed-Rao", mk_dif["p_mk_hr"]),
        ("P_I - P_L: OLS (mm/año por década)", ols_dif["slope_dec"]), ("P_I - P_L: p HAC", ols_dif["p_hac"]),
        ("P_I/P_L mínimo", sat["PI_sobre_PL"].min()), ("P_I/P_L máximo", sat["PI_sobre_PL"].max()),
    ]
    summary = pd.DataFrame(rows, columns=["indicador", "valor"])
    ann.round(4).to_csv(rc.FIGURES_DIR / "tabla_3_6_balance_anual.csv")
    summary.to_csv(rc.FIGURES_DIR / "tabla_3_6_balance_resumen.csv", index=False)
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
