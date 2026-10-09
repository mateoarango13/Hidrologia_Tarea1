"""Punto 3.1: temperatura de la base CAMELS-CL (CR2MET) frente a ERA5-Land.

La guía pide usar la temperatura disponible en la base de la cuenca y, si se usa
ERA5-Land, contrastarla con los registros existentes sin unirlos en una sola serie.
Desde la versión final, la temperatura principal del CSV maestro (Temp_C) es la media
mensual CR2MET de CAMELS-CL (1980-01 a 2020-04, script 01) y ERA5-Land queda como
contraste (Temp_ERA5L_C, 2000-06 a 2020-03). Este script:

  1. recalcula T CR2MET desde los archivos diarios (media de (Tmax + Tmin)/2, >= 80 %
     de días válidos) y verifica que coincide con Temp_C del maestro;
  2. compara CR2MET con ERA5-Land en los meses comunes (sesgo, correlación, ciclo anual);
  3. estima la tendencia (OLS sobre anomalías con IC HAC y Theil-Sen con Mann-Kendall
     de Hamed-Rao, mismas funciones del punto 3) en 1980-2020 y en 2000-06 a 2020-03.

Salidas:
  figuras/tabla_3_1_temperatura_cr2met_vs_era5.csv
  figuras/tabla_3_1_tendencia_temperatura_cr2met.csv

Ejecutar desde la raíz:  python scripts/21_p3_1_temperatura_cr2met.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import rol_c_comun as rc

RAW = Path(__file__).resolve().parents[1] / "datos" / "camels_cl_5710001"


def monthly_cr2met() -> pd.Series:
    read = lambda name: pd.read_csv(RAW / name, parse_dates=["date"], index_col="date")["5710001"]
    tmean = ((read("tmax_cr2met_day.csv") + read("tmin_cr2met_day.csv")) / 2).loc["1980-01-01":"2020-04-30"]
    count = tmean.resample("MS").count()
    days = tmean.index.to_series().resample("MS").size()
    return tmean.resample("MS").mean().where(count / days >= 0.8)


def trend_rows(data: pd.DataFrame, column: str, label: str, start, end) -> dict:
    sub = data.loc[data["date"].between(start, end)].copy()
    anom = rc.add_anomalies(sub, column)
    ols = rc.ols_trend(anom["t"].to_numpy(), anom["a"].to_numpy())
    mk = rc.mann_kendall(anom["t"].to_numpy(), anom["a"].to_numpy())
    return {"serie": label, "periodo": f"{pd.Timestamp(start):%Y-%m} a {pd.Timestamp(end):%Y-%m}", "n": ols["n"],
            "ols_C_dec": ols["slope_dec"], "ols_ic_inf": ols["ci_low_hac_dec"], "ols_ic_sup": ols["ci_high_hac_dec"],
            "ols_p_hac": ols["p_hac"], "sen_C_dec": mk["sen_dec"], "sen_ic_inf": mk["sen_low_hr_dec"],
            "sen_ic_sup": mk["sen_high_hr_dec"], "mk_hr_p": mk["p_mk_hr"]}


def main() -> None:
    data = rc.load_master_data()
    recalc = monthly_cr2met().reindex(data["date"]).to_numpy()
    max_dif = np.nanmax(np.abs(recalc - data["Temp_C"].to_numpy(float)))
    if max_dif > 1e-4:
        raise ValueError(f"Temp_C del maestro no coincide con CR2MET recalculado (máx. dif. {max_dif})")
    print(f"Verificación: Temp_C del maestro = CR2MET recalculado (máx. dif. {max_dif:.1e} °C)")
    data["T_cr2met"] = data["Temp_C"]
    data["T_era5l"] = data["Temp_ERA5L_C"]

    common = data.dropna(subset=["T_cr2met", "T_era5l"])
    diff = common["T_era5l"] - common["T_cr2met"]
    clim = common.groupby("month")[["T_cr2met", "T_era5l"]].mean()
    anom_c = common["T_cr2met"] - common["month"].map(clim["T_cr2met"])
    anom_e = common["T_era5l"] - common["month"].map(clim["T_era5l"])
    rows = [{"metrica": "meses comunes", "valor": len(common)},
            {"metrica": "media T CR2MET [°C]", "valor": common["T_cr2met"].mean()},
            {"metrica": "media T ERA5-Land [°C]", "valor": common["T_era5l"].mean()},
            {"metrica": "sesgo medio ERA5-Land - CR2MET [°C]", "valor": diff.mean()},
            {"metrica": "correlación de las series", "valor": common["T_cr2met"].corr(common["T_era5l"])},
            {"metrica": "correlación de las anomalías mensuales", "valor": anom_c.corr(anom_e)},
            {"metrica": "amplitud ciclo anual CR2MET [°C]", "valor": clim["T_cr2met"].max() - clim["T_cr2met"].min()},
            {"metrica": "amplitud ciclo anual ERA5-Land [°C]", "valor": clim["T_era5l"].max() - clim["T_era5l"].min()},
            {"metrica": "meses con T CR2MET < 0 °C en la climatología", "valor": int((clim["T_cr2met"] < 0).sum())},
            {"metrica": "meses con T ERA5-Land < 0 °C en la climatología", "valor": int((clim["T_era5l"] < 0).sum())}]
    out = pd.DataFrame(rows)
    out.to_csv(rc.FIGURES_DIR / "tabla_3_1_temperatura_cr2met_vs_era5.csv", index=False)

    trends = pd.DataFrame([
        trend_rows(data, "T_cr2met", "T CR2MET (CAMELS-CL)", "1980-01-01", "2020-04-01"),
        trend_rows(data, "T_cr2met", "T CR2MET (CAMELS-CL)", rc.COMMON_START, rc.COMMON_END),
        trend_rows(data, "T_era5l", "T ERA5-Land (contraste)", rc.COMMON_START, rc.COMMON_END),
    ])
    trends.to_csv(rc.FIGURES_DIR / "tabla_3_1_tendencia_temperatura_cr2met.csv", index=False)
    print(out.round(3).to_string(index=False))
    print(trends.round(3).to_string(index=False))
    print(clim.round(2).T.to_string())


if __name__ == "__main__":
    main()
