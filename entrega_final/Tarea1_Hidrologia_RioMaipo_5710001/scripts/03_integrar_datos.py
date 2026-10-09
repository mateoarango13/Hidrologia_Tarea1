"""
03_integrar_datos.py — Construye el CSV maestro datos/datos_mensuales_maipo.csv.

Une con un OUTER JOIN (la menor duración de IMERG no recorta los registros locales):
  datos/datos_mensuales_procesados.csv   (script 01: P_local_mm, Caudal_m3s, Q_lamina_mm, Temp_C)
  datos/datos_satelitales_imerg_era5.csv (script 02: P_IMERG_mm, Temp_ERA5L_C)

Columnas del maestro:
  P_local_mm    precipitación de referencia CR2MET [mm/mes]
  P_IMERG_mm    precipitación GPM IMERG Final mensual V06 [mm/mes]
  Caudal_m3s    caudal medio mensual observado [m³/s]
  Q_lamina_mm   escorrentía en lámina [mm/mes]
  Temp_C        temperatura media mensual CR2MET de la base CAMELS-CL [°C] (principal)
  Temp_ERA5L_C  temperatura a 2 m ERA5-Land [°C] (contraste, 2000-06 a 2020-03)
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "datos" / "datos_mensuales_procesados.csv"
SATELITE = ROOT / "datos" / "datos_satelitales_imerg_era5.csv"
SALIDA = ROOT / "datos" / "datos_mensuales_maipo.csv"
COLUMNAS = ["P_local_mm", "P_IMERG_mm", "Caudal_m3s", "Q_lamina_mm", "Temp_C", "Temp_ERA5L_C"]


def main():
    for f, script in [(LOCAL, "01_preparar_datos.py"), (SATELITE, "02_descargar_satelite.py")]:
        if not f.exists():
            raise SystemExit(f"ERROR: falta {f.relative_to(ROOT)}; ejecutar antes scripts/{script}")

    local = pd.read_csv(LOCAL, index_col="date", parse_dates=True)
    sat = pd.read_csv(SATELITE, index_col="date", parse_dates=True)
    for df in (local, sat):
        df.index = df.index.to_period("M").to_timestamp()

    maestro = local.join(sat, how="outer")[COLUMNAS]
    esperado = pd.date_range(maestro.index.min(), maestro.index.max(), freq="MS")
    if not maestro.index.equals(esperado):
        raise ValueError("La malla mensual del maestro no es regular")

    maestro.index.name = "date"
    maestro.to_csv(SALIDA, float_format="%.6f")
    print(f"Maestro: {SALIDA.relative_to(ROOT)} | {maestro.index.min():%Y-%m} a "
          f"{maestro.index.max():%Y-%m} | {len(maestro)} meses")
    print("Meses válidos por columna:")
    print(maestro.notna().sum().to_string())


if __name__ == "__main__":
    main()
