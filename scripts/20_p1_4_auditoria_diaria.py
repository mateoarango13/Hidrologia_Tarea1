"""Punto 1.4 (complemento): auditoría de completitud diaria y de la agregación mensual.

La guía exige: (i) como máximo 10 % de días faltantes por variable en el periodo
común, calculado sobre los días esperados y antes de cualquier relleno; (ii) una
tabla de disponibilidad por año y mes con días válidos y meses retenidos o
excluidos, y (iii) no presentar agregados parciales como mensuales completos.

El CSV maestro (scripts 01-03) se construyó con la suma mensual de P exigiendo
>= 20 días y con la media mensual de Q SIN mínimo de días. Este script, que no
modifica el CSV maestro, cuantifica qué meses de Q son medias parciales y cuánto
cambian los resultados principales si se aplica un criterio de completitud del
80 % de los días del mes.

Entradas (subconjunto CAMELS-CL efectivamente usado; Alvarez-Garreton et al., 2018):
  datos/camels_cl_5710001/q_m3s_day.csv          caudal medio diario DGA [m3/s]
  datos/camels_cl_5710001/precip_cr2met_day.csv  precipitación diaria CR2MET [mm/día]
  datos/camels_cl_5710001/catchment_attributes.csv
  datos/camels_cl_5710001/polygon/polygon.shp     delimitación CAMELS-CL
  datos/datos_mensuales_maipo.csv                 CSV maestro

Salidas (figuras/):
  tabla_1_7_disponibilidad_diaria_mensual.csv   días válidos por año-mes y decisión
  tabla_1_8_resumen_faltantes_diarios.csv       % faltante diario y vacíos más largos
  tabla_1_9_sensibilidad_completitud_Q.csv      resultados de Q con y sin criterio
  tabla_1_10_ficha_cuenca.csv                   atributos CAMELS-CL usados en la ficha
  figura_1_8_disponibilidad_diaria.png          mapa año-mes de días válidos de Q

Ejecutar desde la raíz del repositorio:  python scripts/20_p1_4_auditoria_diaria.py
"""
from __future__ import annotations

import struct
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import rol_c_comun as rc

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "datos" / "camels_cl_5710001"
OUT = ROOT / "figuras"
START, END = pd.Timestamp("1980-01-01"), pd.Timestamp("2020-04-30")
MIN_FRACTION = 0.80  # criterio propuesto: >= 80 % de los días del mes con dato


def read_daily(name: str) -> pd.Series:
    frame = pd.read_csv(RAW / name, parse_dates=["date"], index_col="date")
    return frame["5710001"].reindex(pd.date_range(START, END, freq="D"))


def gaps(series: pd.Series) -> pd.DataFrame:
    missing = series.isna()
    run_id = (missing != missing.shift()).cumsum()
    rows = []
    for _, block in series[missing].groupby(run_id[missing]):
        rows.append({"inicio": block.index.min().date(), "fin": block.index.max().date(), "dias": len(block)})
    return pd.DataFrame(rows, columns=["inicio", "fin", "dias"])


def read_polygon(path: Path) -> list[np.ndarray]:
    """Lector mínimo de un .shp de polígonos (tipo 5), sin dependencias externas."""
    raw = path.read_bytes()
    pos, rings = 100, []
    while pos < len(raw):
        _, length = struct.unpack(">2i", raw[pos:pos + 8])
        rec = raw[pos + 8: pos + 8 + 2 * length]
        if struct.unpack("<i", rec[:4])[0] == 5:
            n_parts, n_points = struct.unpack("<2i", rec[36:44])
            parts = list(struct.unpack(f"<{n_parts}i", rec[44:44 + 4 * n_parts])) + [n_points]
            pts = np.frombuffer(rec[44 + 4 * n_parts: 44 + 4 * n_parts + 16 * n_points], dtype="<f8").reshape(-1, 2)
            rings += [pts[parts[i]:parts[i + 1]] for i in range(n_parts)]
        pos += 8 + 2 * length
    return rings


def polygon_summary(rings: list[np.ndarray]) -> dict:
    """Área (proyección equivalente local) y centroide del anillo exterior."""
    ring = max(rings, key=len)
    lon, lat = ring[:, 0], ring[:, 1]
    lat0 = np.deg2rad(lat.mean())
    radius = 6371.0088  # km, radio medio terrestre
    x = np.deg2rad(lon) * radius * np.cos(lat0)
    y = np.deg2rad(lat) * radius
    area = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
    return {"area_poligono_km2": area, "centroide_lon": lon.mean(), "centroide_lat": lat.mean(),
            "lon_min": lon.min(), "lon_max": lon.max(), "lat_min": lat.min(), "lat_max": lat.max()}


def q_results(monthly_q: pd.Series, label: str) -> dict:
    """Resultados principales de Q con una serie mensual dada (misma lógica del Rol C)."""
    data = rc.load_master_data()
    data["Caudal_m3s"] = monthly_q.reindex(data["date"]).to_numpy()
    anom = rc.add_anomalies(data, "Caudal_m3s")
    ols = rc.ols_trend(anom["t"].to_numpy(), anom["a"].to_numpy())
    mk = rc.mann_kendall(anom["t"].to_numpy(), anom["a"].to_numpy())
    annual = anom.groupby("water_year")["a"].agg(["mean", "count"])
    annual = annual[annual["count"] >= 10]  # misma regla que el script 12
    pet = rc.pettitt(annual["mean"].to_numpy())
    valid = data.dropna(subset=["Caudal_m3s"])
    top = valid.loc[valid["Caudal_m3s"].idxmax()]
    clim = valid.groupby("month")["Caudal_m3s"].mean()
    return {"serie": label, "meses_validos": int(valid.shape[0]),
            "media_m3s": valid["Caudal_m3s"].mean(), "maximo_m3s": top["Caudal_m3s"],
            "fecha_maximo": top["date"].strftime("%Y-%m"),
            "mes_climatologico_max": int(clim.idxmax()), "mes_climatologico_min": int(clim.idxmin()),
            "ols_hac_m3s_dec": ols["slope_dec"], "ols_ic_inf": ols["ci_low_hac_dec"],
            "ols_ic_sup": ols["ci_high_hac_dec"], "ols_p_hac": ols["p_hac"],
            "sen_m3s_dec": mk["sen_dec"], "mk_hr_p": mk["p_mk_hr"],
            "pettitt_anio": int(annual.index[pet["k_last_before"] + 1]), "pettitt_p": pet["p"]}


def main() -> None:
    q = read_daily("q_m3s_day.csv")
    p = read_daily("precip_cr2met_day.csv")
    master = pd.read_csv(ROOT / "datos" / "datos_mensuales_maipo.csv", parse_dates=["date"], index_col="date")

    # (1) Disponibilidad por año-mes y decisión de retención.
    table = pd.DataFrame({
        "dias_mes": q.resample("MS").size(),
        "dias_validos_Q": q.resample("MS").count(),
        "dias_validos_P": p.resample("MS").count(),
        "Q_media_dias_validos": q.resample("MS").mean(),
    })
    table["fraccion_Q"] = table["dias_validos_Q"] / table["dias_mes"]
    table["Q_csv_maestro"] = master["Caudal_m3s"].reindex(table.index)
    table["retenido_en_csv"] = table["Q_csv_maestro"].notna()
    table["retenido_criterio_80"] = table["fraccion_Q"] >= MIN_FRACTION
    table["nota"] = ""
    table.loc[table["retenido_en_csv"] & ~table["retenido_criterio_80"], "nota"] = "media parcial en el CSV"
    diff = (table["Q_csv_maestro"] - table["Q_media_dias_validos"]).abs()
    table.loc[diff > 1e-6, "nota"] = "CSV usa solo el 1 de abril (corte del script 01)"
    table.index = table.index.strftime("%Y-%m")
    table.index.name = "mes"
    table.round(4).to_csv(OUT / "tabla_1_7_disponibilidad_diaria_mensual.csv")

    # (2) Resumen diario por variable.
    rows = []
    for name, series in [("Caudal_m3s (DGA)", q), ("P_local_mm (CR2MET)", p)]:
        g = gaps(series)
        longest = g.sort_values("dias", ascending=False).head(3)
        rows.append({"variable": name, "periodo": f"{START.date()} a {END.date()}",
                     "dias_esperados": len(series), "dias_faltantes": int(series.isna().sum()),
                     "pct_faltante": 100 * series.isna().mean(), "n_vacios": len(g),
                     "vacios_mas_largos": "; ".join(f"{r.inicio} a {r.fin} ({r.dias} d)" for r in longest.itertuples()),
                     "meses_sin_ningun_dia": int((series.resample("MS").count() == 0).sum()),
                     "meses_con_menos_80pct": int(((series.resample("MS").count() / series.resample("MS").size()) < MIN_FRACTION).sum())})
    pd.DataFrame(rows).round(3).to_csv(OUT / "tabla_1_8_resumen_faltantes_diarios.csv", index=False)

    # (3) Sensibilidad de los resultados de Q al criterio de completitud.
    q80 = q.resample("MS").mean().where(q.resample("MS").count() / q.resample("MS").size() >= MIN_FRACTION)
    sens = pd.DataFrame([q_results(master["Caudal_m3s"], "CSV maestro (sin mínimo de días)"),
                         q_results(q80, f"criterio >= {int(100 * MIN_FRACTION)} % de días")])
    sens.round(4).to_csv(OUT / "tabla_1_9_sensibilidad_completitud_Q.csv", index=False)

    # (4) Ficha de la cuenca con atributos CAMELS-CL y verificación del área.
    attrs = pd.read_csv(RAW / "catchment_attributes.csv", header=None, names=["atributo", "valor", "descripcion"])
    keep = ["gauge_name", "gauge_lat", "gauge_lon", "outlet_camels_elev", "area_km2", "mean_elev", "med_elev",
            "max_elev", "min_elev", "mean_slope_perc", "geol_class_1st", "geol_class_1st_frac", "geol_class_2nd",
            "geol_class_2nd_frac", "lc_barren", "lc_grass", "lc_shrub", "lc_glacier", "lc_snow", "lc_wet",
            "lc_forest", "lc_imp", "p_mean_cr2met_1979_2010", "pet_mean_1979_2010", "aridity_cr2met_1979_2010",
            "frac_snow_cr2met_1979_2010", "p_seasonality_cr2met_1979_2010", "runoff_ratio_cr2met_1979_2010",
            "stream_elas_cr2met_1979_2010", "baseflow_index_1979_2010", "hfd_mean", "q_mean_1979_2010",
            "sur_rights_flow_m3s", "IAI_Q", "dam_index", "record_period_start", "record_period_end"]
    ficha = attrs.set_index("atributo").loc[keep].reset_index()
    poly = polygon_summary(read_polygon(RAW / "polygon" / "polygon.shp"))
    implied = (master["Caudal_m3s"] * 86.4 * master.index.days_in_month / master["Q_lamina_mm"]).dropna()
    extra = pd.DataFrame([
        {"atributo": "area_poligono_calculada_km2", "valor": round(poly["area_poligono_km2"], 1),
         "descripcion": "área del polígono CAMELS-CL (proyección equivalente local, este script)"},
        {"atributo": "area_implicita_en_Q_lamina_mm_km2", "valor": round(float(implied.median()), 3),
         "descripcion": "área con la que el script 01 convirtió Q a lámina (R = 86.4 n Q / A)"},
        {"atributo": "centroide_poligono_lat_lon", "valor": f"{poly['centroide_lat']:.3f}, {poly['centroide_lon']:.3f}",
         "descripcion": "promedio de los vértices del anillo exterior (aproximado)"},
        {"atributo": "extension_poligono", "valor": f"lat {poly['lat_min']:.2f} a {poly['lat_max']:.2f}; lon {poly['lon_min']:.2f} a {poly['lon_max']:.2f}",
         "descripcion": "caja envolvente de la delimitación"},
    ])
    pd.concat([ficha, extra], ignore_index=True).to_csv(OUT / "tabla_1_10_ficha_cuenca.csv", index=False)

    # (5) Figura: fracción de días válidos de Q por año y mes.
    frac = (q.resample("MS").count() / q.resample("MS").size())
    grid = frac.groupby([frac.index.year, frac.index.month]).first().unstack()
    rc.apply_style()
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    im = ax.imshow(grid.to_numpy(), aspect="auto", cmap="viridis", vmin=0, vmax=1, origin="upper")
    ax.set_xticks(range(12), rc.MONTH_NAMES)
    ax.set_yticks(range(0, len(grid), 4), grid.index[::4])
    partial = (grid < MIN_FRACTION) & (grid > 0)
    for (i, j), flag in np.ndenumerate(partial.to_numpy()):
        if flag:
            ax.text(j, i, "×", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Fracción de días con caudal válido")
    ax.set_title("Figura 1.8. Días válidos de caudal diario por año y mes (1980–2020)\n"
                 "× = mes con datos pero < 80 % de días (media parcial en el CSV maestro)", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "figura_1_8_disponibilidad_diaria.png", dpi=rc.DPI)
    plt.close(fig)

    # (6) Punto 1.5.b: ¿aparecen los picos del ciclo medio en la mayoría de los años?
    #     Mes del máximo por año hidrológico (abr-mar, solo años completos) y totales anuales.
    data = rc.load_master_data()
    years = []
    for wy, g in data.groupby("water_year"):
        if g["P_local_mm"].notna().sum() < 12 or g["Caudal_m3s"].notna().sum() < 12:
            continue
        years.append({"anio_hidrologico": wy,
                      "P_anual_mm": g["P_local_mm"].sum(), "R_anual_mm": g["Q_lamina_mm"].sum(),
                      "mes_max_P": int(g.loc[g["P_local_mm"].idxmax(), "month"]),
                      "mes_max_Q": int(g.loc[g["Caudal_m3s"].idxmax(), "month"]),
                      "mes_min_Q": int(g.loc[g["Caudal_m3s"].idxmin(), "month"])})
    peaks = pd.DataFrame(years)
    peaks["R_sobre_P"] = peaks["R_anual_mm"] / peaks["P_anual_mm"]
    peaks.round(3).to_csv(OUT / "tabla_1_11_picos_y_totales_por_anio.csv", index=False)
    print(f"Años hidrológicos completos: {len(peaks)}")
    print("Pico de P en may-ago:", round(100 * peaks["mes_max_P"].between(5, 8).mean(), 1), "%")
    print("Pico de Q en nov-ene:", round(100 * peaks["mes_max_Q"].isin([11, 12, 1]).mean(), 1), "%")
    print("Mínimo de Q en may-ago:", round(100 * peaks["mes_min_Q"].between(5, 8).mean(), 1), "%")
    print(peaks.sort_values("P_anual_mm").iloc[[0, 1, 2, -3, -2, -1]].round(2).to_string(index=False))

    print(pd.DataFrame(rows).to_string(index=False))
    print(sens.round(3).T.to_string())
    print(pd.concat([ficha, extra]).tail(6).to_string(index=False))


if __name__ == "__main__":
    main()
