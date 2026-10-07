"""
01_preparar_datos.py — Agregación mensual de los registros diarios de CAMELS-CL (punto 1.1 y 1.4).

Entradas (datos/camels_cl_5710001/):
  q_m3s_day.csv          caudal medio diario observado (DGA) [m³/s]
  precip_cr2met_day.csv  precipitación diaria CR2MET [mm/día]
  tmax_cr2met_day.csv    temperatura máxima diaria CR2MET [°C]
  tmin_cr2met_day.csv    temperatura mínima diaria CR2MET [°C]
  catchment_attributes.csv  área de drenaje de la estación (area_km2)

Salida:
  datos/datos_mensuales_procesados.csv  series mensuales y días válidos por mes

Criterio de completitud (aplicado de forma explícita, punto 1.4 de la guía):
  * Precipitación: el acumulado mensual exige el 100 % de los días válidos; un mes con
    algún día faltante queda como NaN (no se presentan sumas parciales como acumulados).
  * Caudal y temperatura: la media mensual exige al menos el 80 % de los días del mes.
  * Lámina de escorrentía: R_m = 86.4 · n_m · Q_m / A, con Q_m la media de los días válidos.
Los faltantes nunca se rellenan.

Periodo: 1980-01-01 a 2020-04-30 (último día de la serie CR2MET de CAMELS-CL).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CAMELS_DIR = ROOT / "datos" / "camels_cl_5710001"
SALIDA = ROOT / "datos" / "datos_mensuales_procesados.csv"
GAUGE = "5710001"
INICIO, FIN = "1980-01-01", "2020-04-30"
UMBRAL_MEDIAS = 0.80  # fracción mínima de días válidos para Q y T


def leer_diaria(nombre: str) -> pd.Series:
    df = pd.read_csv(CAMELS_DIR / nombre, usecols=["date", GAUGE], parse_dates=["date"])
    serie = df.set_index("date")[GAUGE].astype(float)
    if serie.index.duplicated().any():
        raise ValueError(f"{nombre}: fechas duplicadas")
    return serie


def area_cuenca_km2() -> float:
    attrs = pd.read_csv(CAMELS_DIR / "catchment_attributes.csv", header=None, index_col=0)
    return float(attrs.loc["area_km2", 1])


def main():
    dias = pd.date_range(INICIO, FIN, freq="D")
    diaria = pd.DataFrame({
        "P": leer_diaria("precip_cr2met_day.csv"),
        "Q": leer_diaria("q_m3s_day.csv"),
        "Tmax": leer_diaria("tmax_cr2met_day.csv"),
        "Tmin": leer_diaria("tmin_cr2met_day.csv"),
    }).reindex(dias)
    diaria["T"] = (diaria["Tmax"] + diaria["Tmin"]) / 2.0

    print(f"Periodo {INICIO} a {FIN}: {len(dias)} días esperados")
    for col in ["P", "Q", "T"]:
        falt = diaria[col].isna().sum()
        print(f"  {col}: {falt} días faltantes ({100 * falt / len(dias):.2f} %)")
    if (diaria[["P", "Q", "T"]].isna().mean() > 0.10).any():
        print("¡ALERTA! Alguna variable supera el 10 % de días faltantes.")

    meses = diaria.resample("MS")
    n_dias = meses["P"].size()
    n_p, n_q, n_t = meses["P"].count(), meses["Q"].count(), meses["T"].count()

    mensual = pd.DataFrame(index=n_dias.index)
    mensual.index.name = "date"
    mensual["P_local_mm"] = meses["P"].sum().where(n_p == n_dias)
    mensual["Caudal_m3s"] = meses["Q"].mean().where(n_q >= UMBRAL_MEDIAS * n_dias)
    area = area_cuenca_km2()
    mensual["Q_lamina_mm"] = 86.4 * n_dias * mensual["Caudal_m3s"] / area
    mensual["Temp_C"] = meses["T"].mean().where(n_t >= UMBRAL_MEDIAS * n_dias)
    mensual["dias_mes"] = n_dias
    mensual["dias_validos_P"] = n_p
    mensual["dias_validos_Q"] = n_q
    mensual["dias_validos_T"] = n_t

    excluidos_q = mensual.index[(n_q > 0) & mensual["Caudal_m3s"].isna()]
    print(f"Área de drenaje (CAMELS-CL): {area} km²")
    print(f"Meses de caudal excluidos por tener datos pero < 80 % de días: "
          f"{[d.strftime('%Y-%m') for d in excluidos_q]}")
    print(f"Meses válidos: P={mensual['P_local_mm'].notna().sum()}, "
          f"Q={mensual['Caudal_m3s'].notna().sum()}, T={mensual['Temp_C'].notna().sum()} "
          f"de {len(mensual)}")

    # Comprobación manual de una conversión (mayo de 1980)
    m = mensual.loc["1980-05-01"]
    print(f"Control mayo 1980: Q={m['Caudal_m3s']:.3f} m³/s -> "
          f"R = 86.4·31·Q/A = {86.4 * 31 * m['Caudal_m3s'] / area:.3f} mm (CSV: {m['Q_lamina_mm']:.3f})")

    mensual.to_csv(SALIDA, float_format="%.6f")
    print(f"Guardado: {SALIDA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
