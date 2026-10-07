"""Punto 5.3 (robustez frente al producto de SST): ERA5 frente a NOAA ERSST v5.

La guía sugiere explorar el catálogo de SST de NOAA PSL. Este script contrasta los
resultados del punto 5 que dependen de la SST con un producto independiente del
reanálisis: ERSST v5 (Huang et al., 2017; doi:10.7289/V5T72FNM), una reconstrucción
mensual de 2° basada en observaciones in situ (ICOADS).

  1. Descarga sst.mnmean.nc de NOAA PSL si no está y guarda el subconjunto usado
     (1979-01 a 2020-12) en datos/campos_ersst/ersst_v5_sst_mensual_1979_2020_2deg.nc.
  2. Calcula Niño 3.4 con ERSST y lo compara con el de ERA5 (correlación de anomalías).
  3. Repite los perfiles mensuales de P_L y Q frente a Niño 3.4 con ERSST.
  4. Correlación de patrón (Pacífico 60°S–60°N, 120°E–60°W) entre los mapas de
     correlación de ERA5 (remuestreados a la malla de 2°) y de ERSST, para P_L y Q
     en los doce meses.

Misma referencia climatológica (2000-06 a 2020-03), mismos años y mismas funciones
que los scripts 17-19 (p5_comun.py).

Salidas:
  figuras/tabla_5_5_contraste_ersst_indices.csv
  figuras/tabla_5_5_contraste_ersst_patrones.csv
  figuras/figura_5_5_contraste_ersst.png

Ejecutar desde la raíz (requiere conexión solo la primera vez):
  python scripts/24_p5_3_contraste_ersst.py
"""
from __future__ import annotations

import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

import p5_comun as c

URL = "https://downloads.psl.noaa.gov/Datasets/noaa.ersst.v5/sst.mnmean.nc"
RAW = c.ROOT / "datos_pesados_ignorados" / "ersst_v5_sst.mnmean.nc"
SUBSET = c.ROOT / "datos" / "campos_ersst" / "ersst_v5_sst_mensual_1979_2020_2deg.nc"


def ersst_subset() -> xr.DataArray:
    if not SUBSET.exists():
        if not RAW.exists():
            RAW.parent.mkdir(parents=True, exist_ok=True)
            print(f"Descargando {URL} ...")
            urllib.request.urlretrieve(URL, RAW)
        ds = xr.open_dataset(RAW)
        sst = ds["sst"].sel(time=slice("1979-01-01", "2020-12-01")).astype("float32")
        sst.attrs.update({"source": URL, "product": "NOAA ERSST v5 (Huang et al., 2017)", "units": "degC"})
        SUBSET.parent.mkdir(parents=True, exist_ok=True)
        sst.to_dataset(name="sst").to_netcdf(SUBSET, encoding={"sst": {"zlib": True, "complevel": 5}})
        ds.close()
    da = xr.open_dataset(SUBSET)["sst"].load()
    da = da.rename(lat="latitude", lon="longitude").sortby("latitude")
    da = da.assign_coords(time=pd.to_datetime(da["time"].values).to_period("M").to_timestamp())
    if da.sizes["time"] != 504:
        raise ValueError(f"ERSST: se esperaban 504 meses y hay {da.sizes['time']}")
    da = da.where(da > c.SEA_ICE_SST)  # misma máscara de hielo marino que ERA5
    return da.astype("float64")


def main() -> None:
    fields, f_anom, b_anom, lat, lon = c.load_all()
    ersst = ersst_subset()
    e_anom = c.field_anomalies(ersst)

    # (2) Índices Niño 3.4
    box = c.BOXES["nino34"]
    n34_era5 = c.box_index(f_anom["sst"], box)
    n34_ersst = c.box_index(e_anom, box)
    common = n34_era5.index.intersection(n34_ersst.index)
    r_idx = float(np.corrcoef(n34_era5[common], n34_ersst[common])[0, 1])
    rmsd_idx = float(np.sqrt(np.mean((n34_era5[common] - n34_ersst[common]) ** 2)))

    # (3) Perfiles mensuales con cada producto
    rows = []
    for var in ("P_local_mm", "Caudal_m3s"):
        x = b_anom[var]
        for month in range(1, 13):
            out = {"variable": var, "mes": month}
            for name, idx in [("era5", n34_era5), ("ersst", n34_ersst)]:
                s = x[x.index.month == month].dropna()
                s = s[s.index.isin(idx.index)]
                out[f"r_nino34_{name}"] = float(np.corrcoef(s.to_numpy(), idx[s.index].to_numpy())[0, 1])
                out["n"] = len(s)
            rows.append(out)
    prof = pd.DataFrame(rows)
    prof["dif_ersst_menos_era5"] = prof["r_nino34_ersst"] - prof["r_nino34_era5"]
    resumen = pd.DataFrame([
        {"indicador": "r de anomalías Niño 3.4 ERA5 vs ERSST (1979-2020)", "valor": r_idx},
        {"indicador": "RMSD de anomalías Niño 3.4 (°C)", "valor": rmsd_idx},
        {"indicador": "máx |Δr| perfiles P_L", "valor": prof.loc[prof.variable == "P_local_mm", "dif_ersst_menos_era5"].abs().max()},
        {"indicador": "máx |Δr| perfiles Q", "valor": prof.loc[prof.variable == "Caudal_m3s", "dif_ersst_menos_era5"].abs().max()},
    ])
    with open(c.FIGURES_DIR / "tabla_5_5_contraste_ersst_indices.csv", "w", encoding="utf-8", newline="") as fh:
        resumen.to_csv(fh, index=False)
        fh.write("\n")
        prof.round(4).to_csv(fh, index=False)

    # (4) Correlación de patrón mes a mes (ERA5 remuestreado a la malla de ERSST)
    era5_2deg = f_anom["sst"].interp(latitude=ersst["latitude"], longitude=ersst["longitude"])
    elat, elon = ersst["latitude"].values, ersst["longitude"].values
    pat_rows, maps = [], {}
    for var in ("P_local_mm", "Caudal_m3s"):
        m_era5 = c.monthly_maps(b_anom[var], era5_2deg)
        m_ersst = c.monthly_maps(b_anom[var], e_anom)
        for a, b in zip(m_era5, m_ersst):
            pat_rows.append({"variable": var, "mes": a["month"], "n_anios": a["n_pairs"],
                             "corr_patron_pacifico": c.pattern_correlation(a["r"], b["r"], elat, c.PACIFIC, elon),
                             "frac_area_sig_era5": c.area_fraction(a["sig"], np.isfinite(a["r"]), elat),
                             "frac_area_sig_ersst": c.area_fraction(b["sig"], np.isfinite(b["r"]), elat)})
        maps[var] = (m_era5, m_ersst)
    pat = pd.DataFrame(pat_rows)
    pat.round(4).to_csv(c.FIGURES_DIR / "tabla_5_5_contraste_ersst_patrones.csv", index=False)

    # Figura: Q septiembre y P_L octubre con cada producto + perfiles
    plt.rcParams.update({"font.size": 8, "savefig.dpi": c.DPI})
    fig = plt.figure(figsize=(13, 5.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 0.9])
    for row, (var, month, lab) in enumerate([("Caudal_m3s", 9, "Q, septiembre"), ("P_local_mm", 10, "P$_L$, octubre")]):
        m_era5, m_ersst = maps[var]
        for col, (res, name) in enumerate([(m_era5[month - 1], "ERA5 (a 2°)"), (m_ersst[month - 1], "ERSST v5")]):
            ax = fig.add_subplot(gs[row, col])
            mesh = c.draw_map(ax, elon, elat, res["r"], sig=res["sig"], lat_range=(-60, 60), lon_range=(100, 330),
                              title=f"{lab} · SST {name} · n={res['n_pairs']}")
        pc = pat.loc[(pat.variable == var) & (pat.mes == month), "corr_patron_pacifico"].iloc[0]
        ax.text(0.02, 0.04, f"corr. de patrón = {pc:.2f}", transform=ax.transAxes, fontsize=7,
                bbox=dict(fc="white", ec="none", alpha=0.8))
    cb = fig.colorbar(mesh, ax=fig.axes, orientation="horizontal", fraction=0.04, pad=0.06, shrink=0.55, anchor=(0.3, 0))
    cb.set_label("Correlación de Pearson r (anomalías del mismo mes a través de los años)")
    ax = fig.add_subplot(gs[:, 2])
    for var, color, lab in [("P_local_mm", "#2a78d6", "P$_L$"), ("Caudal_m3s", "#1baf7a", "Q")]:
        p = prof[prof.variable == var]
        ax.plot(p["mes"], p["r_nino34_era5"], "o-", color=color, label=f"{lab} · Niño 3.4 ERA5")
        ax.plot(p["mes"], p["r_nino34_ersst"], "s--", color=color, alpha=0.7, label=f"{lab} · Niño 3.4 ERSST")
    ax.axhline(0, color="#52514e", lw=0.8)
    ax.set_xticks(range(1, 13), c.MONTHS)
    ax.set_ylabel("r con Niño 3.4 (1980–2020, ℓ = 0)")
    ax.set_title(f"Perfiles mensuales; r(Niño 3.4 ERA5, ERSST) = {r_idx:.3f}", fontsize=8)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    ax.grid(True, color="#d9d8d4", lw=0.5)
    fig.suptitle("Figura 5.5. Sensibilidad al producto de SST: ERA5 frente a NOAA ERSST v5 (script 24)", fontsize=10)
    fig.savefig(c.FIGURES_DIR / "figura_5_5_contraste_ersst.png", bbox_inches="tight")
    plt.close(fig)

    print(resumen.round(3).to_string(index=False))
    print(pat.groupby("variable")["corr_patron_pacifico"].describe().round(3).to_string())


if __name__ == "__main__":
    main()
