"""
Punto 5.1 — Seleccionar y documentar los campos climáticos.

Lee los campos descargados por 15_p5_1_descargar_campos_era5.py y documenta fuente,
versión, resolución, periodo, máscaras y transformaciones. Comprueba cobertura y unidades
y dibuja la climatología invernal (mayo-agosto, estación lluviosa de la cuenca) y la
variabilidad interanual de cada campo, que es la que se correlacionará en 5.2.

Justificación física de los campos (ver informe):
  * SST: fuente de las teleconexiones tropicales (ENSO) y del Pacífico extratropical.
  * PNM: posición e intensidad del anticiclón subtropical del Pacífico Sur, que bloquea o
    deja pasar los sistemas frontales que traen la lluvia invernal a Chile central.
  * Z500: vaguadas y bajas segregadas en la troposfera media, y bloqueos; complementa
    la PNM en la vertical (circulación equivalente barotrópica de latitudes medias).

Salidas:
  figuras/tabla_5_1_metadatos_campos.csv
  figuras/tabla_5_1_muestras_cuenca.csv
  figuras/figura_5_1_climatologia_campos.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import p5_comun as c


def metadata(fields: dict) -> pd.DataFrame:
    rows = []
    origin = {
        "sst": ("reanalysis-era5-single-levels-monthly-means", "sea_surface_temperature", "superficie", "K", "°C (T - 273.15)"),
        "msl": ("reanalysis-era5-single-levels-monthly-means", "mean_sea_level_pressure", "superficie (reducida al nivel del mar)", "Pa", "hPa (/100)"),
        "z500": ("reanalysis-era5-pressure-levels-monthly-means", "geopotential", "500 hPa", "m² s⁻²", "altura geopotencial en m (/g0, g0 = 9.80665 m s⁻²)"),
    }
    for name, da in fields.items():
        ds_name, var, level, unit_in, unit_out = origin[name]
        vals = da.values
        nan_frac = float(np.isnan(vals).mean())
        always_nan = float(np.all(np.isnan(vals), axis=0).mean())
        rows.append({
            "campo": name, "descripcion": c.FIELDS[name]["long"], "producto": "ERA5 (ECMWF/Copernicus C3S)",
            "dataset_cds": ds_name, "tipo": "monthly_averaged_reanalysis", "variable": var, "nivel": level,
            "unidad_original": unit_in, "unidad_usada": unit_out,
            "resolucion_nativa": "0.25° x 0.25°", "resolucion_usada": "1° x 1° (interpolada por CDS al descargar)",
            "dominio": "global, lat -90 a 90, lon 0 a 359",
            "periodo": f"{pd.Timestamp(da.time.values[0]):%Y-%m} a {pd.Timestamp(da.time.values[-1]):%Y-%m}",
            "meses": da.sizes["time"], "fraccion_nan": round(nan_frac, 3),
            "fraccion_celdas_siempre_nan": round(always_nan, 3),
            "mascara": "tierra (sin dato en ERA5) y hielo marino (SST <= -1.6 °C, punto de congelación); celdas con algún año enmascarado se excluyen de la correlación" if name == "sst" else "ninguna",
            "minimo": round(float(np.nanmin(vals)), 1), "maximo": round(float(np.nanmax(vals)), 1),
            "media_global_ponderada": round(float(da.weighted(np.cos(np.deg2rad(da.latitude))).mean()), 2),
            "transformacion_posterior": "anomalía por mes calendario y celda, referencia 2000-06 a 2020-03",
            "doi_cds": "10.24381/cds.f17050d7" if "single" in ds_name else "10.24381/cds.6860a573",
        })
    return pd.DataFrame(rows)


def basin_samples(basin: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, meta in c.BASIN_VARS.items():
        s = basin[col].dropna()
        for m in range(1, 13):
            sm = s[s.index.month == m]
            rows.append({"variable": col, "mes": m, "anios_validos": len(sm),
                         "primer_anio": int(sm.index.year.min()), "ultimo_anio": int(sm.index.year.max())})
    return pd.DataFrame(rows)


def plot_climatology(fields: dict) -> None:
    plt.rcParams.update({"font.size": 8, "savefig.dpi": c.DPI, "savefig.bbox": "tight"})
    fig, axes = plt.subplots(3, 2, figsize=(12, 9.2))
    lat = fields["sst"].latitude.values
    lon = fields["sst"].longitude.values
    specs = {"sst": ("RdYlBu_r", (-2, 30)), "msl": ("viridis", (990, 1030)), "z500": ("viridis", (5000, 5900))}
    for i, (name, da) in enumerate(fields.items()):
        winter = da.sel(time=da["time.month"].isin([5, 6, 7, 8]))
        mean = winter.mean("time").values
        anom = c.field_anomalies(da)
        sd = anom.sel(time=anom["time.month"].isin([5, 6, 7, 8])).std("time").values
        cmap, (lo, hi) = specs[name]
        m1 = c.draw_map(axes[i, 0], lon, lat, mean, vmin=lo, vmax=hi, cmap=cmap,
                        title=f"{c.FIELDS[name]['long']}: media may–ago 1979–2020")
        fig.colorbar(m1, ax=axes[i, 0], shrink=0.75, label=c.FIELDS[name]["unit"])
        m2 = c.draw_map(axes[i, 1], lon, lat, sd, vmin=0, vmax=np.nanpercentile(sd, 98), cmap="magma_r",
                        title=f"{c.FIELDS[name]['label']}: desviación interanual de la anomalía (may–ago)")
        fig.colorbar(m2, ax=axes[i, 1], shrink=0.75, label=c.FIELDS[name]["unit"])
    fig.suptitle("Figura 5.1. Campos ERA5 mensuales (1°): climatología invernal y variabilidad interanual\n"
                 "Estrella: cuenca del Maipo. Meridiano central 180° para centrar el Pacífico", fontsize=10)
    fig.tight_layout()
    fig.savefig(c.FIGURES_DIR / "figura_5_1_climatologia_campos.png")
    plt.close(fig)


def main() -> None:
    fields = c.load_fields()
    meta = metadata(fields)
    meta.to_csv(c.FIGURES_DIR / "tabla_5_1_metadatos_campos.csv", index=False)
    samples = basin_samples(c.load_basin())
    samples.to_csv(c.FIGURES_DIR / "tabla_5_1_muestras_cuenca.csv", index=False)
    plot_climatology(fields)
    pd.set_option("display.width", 250)
    print(meta[["campo", "variable", "nivel", "unidad_usada", "periodo", "meses", "fraccion_nan",
                "fraccion_celdas_siempre_nan", "minimo", "maximo", "media_global_ponderada"]].to_string(index=False))
    print("\nAños válidos por mes (mín-máx):")
    print(samples.groupby("variable")["anios_validos"].agg(["min", "max"]))


if __name__ == "__main__":
    main()
