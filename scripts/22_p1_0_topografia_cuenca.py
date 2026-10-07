"""Introducción (ficha de la cuenca): mapa topográfico y curva hipsométrica.

Genera los dos paneles de relieve del informe a partir del modelo digital de
elevación ASTER GDEM v3 (30 m; NASA/METI/AIST/Japan Spacesystems, 2019,
doi:10.5067/ASTER/ASTGTM.003), descargado en cuatro teselas de 1° x 1° desde
NASA Earthdata Search, y de la delimitación oficial CAMELS-CL de la cuenca.

El panel (a) de la Figura 1 del informe (ubicación en Chile central) NO se genera
aquí: es una captura del visor de NASA Earthdata Search tomada durante la
descarga de estas teselas.

Entradas:
  datos/ASTGTM_003-20261004_142607/ASTGTMV003_S3{4,5}W07{0,1}_dem.tif  teselas ASTER GDEM v3
  datos/camels_cl_5710001/polygon/polygon.shp                          delimitación CAMELS-CL
  datos/camels_cl_5710001/catchment_attributes.csv                     salida de la estación

Salidas (figuras/):
  mapa_topografico_Maipo.png        relieve sombreado, curvas de nivel, salida y punto más alto
  curva_hipsometrica_Maipo.png      curva hipsométrica y área por franjas de 250 m
  tabla_1_12_hipsometria.csv        área por franja de 250 m y fracción acumulada

Las áreas se calculan con el tamaño real de cada píxel (1" x 1", corregido por
cos(latitud)); la elevación de cada píxel es la del DEM sin suavizar.

Ejecutar desde la raíz del repositorio:  python scripts/22_p1_0_topografia_cuenca.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LightSource, LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter, MultipleLocator
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEM_DIR = ROOT / "datos" / "ASTGTM_003-20261004_142607"
CAMELS = ROOT / "datos" / "camels_cl_5710001"
OUT = ROOT / "figuras"

RES = 1.0 / 3600.0          # paso de la grilla ASTER GDEM v3 (1 segundo de arco)
RADIUS_KM = 6371.0088       # radio medio terrestre
MARGIN = 0.03               # margen del mapa alrededor de la cuenca (grados)
BAND = 250                  # ancho de las franjas de elevación (m)
PLOT_STEP = 2               # submuestreo solo para dibujar el mapa (60 m)

Image.MAX_IMAGE_PIXELS = None

# Lector de polígonos .shp ya usado en la auditoría diaria (script 20).
_spec = importlib.util.spec_from_file_location("auditoria", Path(__file__).with_name("20_p1_4_auditoria_diaria.py"))
_auditoria = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_auditoria)
read_polygon = _auditoria.read_polygon


def thousands(value: float) -> str:
    """Formato con punto de miles, como en el resto de figuras del informe."""
    return f"{value:,.0f}".replace(",", ".")


def read_mosaic() -> tuple[np.ndarray, float, float]:
    """Une las cuatro teselas. Devuelve el DEM y la lon/lat del centro del píxel superior izquierdo."""
    lat_tops, lon_lefts = (-33, -34), (-71, -70)
    n = 3600  # cada tesela tiene 3601 píxeles; la última fila/columna se repite en la vecina
    mosaic = np.zeros((2 * n + 1, 2 * n + 1), dtype=np.float32)
    for i, lat_top in enumerate(lat_tops):
        for j, lon_left in enumerate(lon_lefts):
            name = f"ASTGTMV003_S{-lat_top + 1:02d}W{-lon_left:03d}_dem.tif"
            tile = np.asarray(Image.open(DEM_DIR / name), dtype=np.float32)
            mosaic[i * n:i * n + n + 1, j * n:j * n + n + 1] = tile
    return mosaic, float(lon_lefts[0]), float(lat_tops[0])


def basin_mask(ring: np.ndarray, lon0: float, lat0: float, shape: tuple[int, int]) -> np.ndarray:
    """Rasteriza el polígono sobre la grilla del recorte (centro de píxel dentro del polígono)."""
    cols = (ring[:, 0] - lon0) / RES + 0.5
    rows = (lat0 - ring[:, 1]) / RES + 0.5
    img = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(img).polygon(list(zip(cols, rows)), fill=1)
    return np.asarray(img, dtype=bool)


def load_basin() -> dict:
    rings = read_polygon(CAMELS / "polygon" / "polygon.shp")
    ring = max(rings, key=len)
    attrs = pd.read_csv(CAMELS / "catchment_attributes.csv", header=None, index_col=0)[1]
    outlet = float(attrs["outlet_camels_lon"]), float(attrs["outlet_camels_lat"])

    mosaic, lon_ul, lat_ul = read_mosaic()
    west, east = ring[:, 0].min() - MARGIN, ring[:, 0].max() + MARGIN
    south, north = ring[:, 1].min() - MARGIN, ring[:, 1].max() + MARGIN
    c0, c1 = int(np.floor((west - lon_ul) / RES)), int(np.ceil((east - lon_ul) / RES)) + 1
    r0, r1 = int(np.floor((lat_ul - north) / RES)), int(np.ceil((lat_ul - south) / RES)) + 1
    dem = mosaic[r0:r1, c0:c1]
    lon0, lat0 = lon_ul + c0 * RES, lat_ul - r0 * RES  # centro del píxel [0, 0]

    inside = basin_mask(ring, lon0, lat0, dem.shape)
    lats = lat0 - np.arange(dem.shape[0]) * RES
    cell_km2 = (np.deg2rad(RES) * RADIUS_KM) ** 2 * np.cos(np.deg2rad(lats))
    area = np.broadcast_to(cell_km2[:, None], dem.shape)
    return {"ring": ring, "outlet": outlet, "dem": dem, "inside": inside, "area": area,
            "lon0": lon0, "lat0": lat0}


def hypsometry(basin: dict) -> tuple[pd.DataFrame, dict]:
    z = basin["dem"][basin["inside"]].astype(float)
    a = basin["area"][basin["inside"]]
    order = np.argsort(z)
    z_sorted, a_sorted = z[order], a[order]
    cum = np.cumsum(a_sorted)
    total = cum[-1]
    stats = {"area_km2": total, "z_min": z_sorted[0], "z_max": z_sorted[-1],
             "z_mean": float(np.sum(z * a) / total),
             "z_median": float(np.interp(0.5 * total, cum, z_sorted)),
             "frac_sobre_3000": float(a[z >= 3000].sum() / total),
             "frac_sobre_4000": float(a[z >= 4000].sum() / total)}
    edges = np.arange(np.floor(z.min() / BAND) * BAND, np.ceil(z.max() / BAND) * BAND + BAND, BAND)
    band_area, _ = np.histogram(z, bins=edges, weights=a)
    table = pd.DataFrame({"z_inf_m": edges[:-1], "z_sup_m": edges[1:], "area_km2": band_area})
    table["fraccion_area"] = table["area_km2"] / total
    table["fraccion_area_sobre_z_inf"] = table["fraccion_area"][::-1].cumsum()[::-1]
    # Curva: % del área por encima de cada elevación (submuestreada para graficar).
    pct_above = 100.0 * (1.0 - cum / total)
    idx = np.linspace(0, len(z_sorted) - 1, 2000).astype(int)
    stats["curve"] = (pct_above[idx], z_sorted[idx])
    return table, stats


def topo_cmap() -> LinearSegmentedColormap:
    stops = [(0.00, "#2f6b3a"), (0.12, "#6f9a5a"), (0.25, "#b9bf86"), (0.38, "#dcbf7c"),
             (0.52, "#c9a06a"), (0.68, "#9c7354"), (0.82, "#8f7a72"), (1.00, "#fbfbfb")]
    return LinearSegmentedColormap.from_list("topo_maipo", stops)


def plot_map(basin: dict, stats: dict) -> None:
    s = PLOT_STEP
    dem = basin["dem"][::s, ::s]
    inside = basin["inside"][::s, ::s]
    lon = basin["lon0"] + np.arange(basin["dem"].shape[1])[::s] * RES
    lat = basin["lat0"] - np.arange(basin["dem"].shape[0])[::s] * RES
    lat_mid = np.deg2rad(lat.mean())
    dx = np.deg2rad(RES * s) * RADIUS_KM * 1000 * np.cos(lat_mid)
    dy = np.deg2rad(RES * s) * RADIUS_KM * 1000

    vmin, vmax = 850.0, 6550.0
    cmap = topo_cmap()
    ls = LightSource(azdeg=315, altdeg=40)
    rgb = ls.shade(dem, cmap=cmap, vmin=vmin, vmax=vmax, blend_mode="soft", vert_exag=1.6, dx=dx, dy=dy)[..., :3]
    # Fuera de la cuenca el relieve se aclara para resaltar la delimitación.
    rgb[~inside] = 0.70 * rgb[~inside] + 0.30

    extent = (lon[0] - RES * s / 2, lon[-1] + RES * s / 2, lat[-1] - RES * s / 2, lat[0] + RES * s / 2)
    fig = plt.figure(figsize=(7.6, 10.2), dpi=200)
    ax = fig.add_axes([0.13, 0.07, 0.57, 0.83])
    ax.imshow(rgb, extent=extent, origin="upper", interpolation="bilinear")
    ax.set_aspect(1.0 / np.cos(lat_mid))

    z_in = np.where(inside, dem, np.nan)
    ax.contour(lon, lat, z_in, levels=np.arange(1000, 6501, BAND), colors="k", linewidths=0.18, alpha=0.55)
    ax.contour(lon, lat, z_in, levels=np.arange(1000, 6001, 1000), colors="k", linewidths=0.55, alpha=0.8)
    ring = basin["ring"]
    ax.plot(ring[:, 0], ring[:, 1], color="k", lw=1.3)

    # Punto más alto y más bajo dentro de la cuenca (DEM a resolución completa).
    full, mask = basin["dem"], basin["inside"]
    z_masked = np.where(mask, full, np.nan)
    r_hi, c_hi = np.unravel_index(np.nanargmax(z_masked), full.shape)
    hi = (basin["lon0"] + c_hi * RES, basin["lat0"] - r_hi * RES)
    ax.plot(*hi, marker="*", ms=14, mfc="#f5c518", mec="k", mew=0.8, zorder=5)
    ax.annotate(f"Punto más alto\n{thousands(stats['z_max'])} m", xy=hi, xytext=(hi[0] + 0.12, hi[1] + 0.22),
                fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7, color="k"), annotation_clip=False)
    out = basin["outlet"]
    ax.plot(*out, marker="^", ms=10, mfc="#d62728", mec="k", mew=0.8, zorder=5)
    ax.annotate(f"Punto más bajo\n{thousands(stats['z_min'])} m (≈ salida,\nEl Manzano)", xy=out,
                xytext=(out[0] - 0.065, -34.10), fontsize=8.5,
                arrowprops=dict(arrowstyle="-", lw=0.7, color="k"),
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none", alpha=0.85))

    # Flecha del norte y barra de escala de 20 km.
    x_n, y_n = extent[1] - 0.06, extent[3] - 0.08
    ax.annotate("N", xy=(x_n, y_n), xytext=(x_n, y_n - 0.07), ha="center", va="center", fontsize=11,
                fontweight="bold", arrowprops=dict(arrowstyle="-|>", lw=1.3, color="k"))
    km_per_deg = np.deg2rad(1.0) * RADIUS_KM * np.cos(np.deg2rad(extent[2] + 0.05))
    x0, y0 = extent[0] + 0.04, extent[2] + 0.05
    ax.plot([x0, x0 + 20 / km_per_deg], [y0, y0], color="k", lw=3.5, solid_capstyle="butt")
    ax.text(x0 + 10 / km_per_deg, y0 + 0.015, "20 km", ha="center", va="bottom", fontsize=8.5)

    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.xaxis.set_major_locator(MultipleLocator(0.2))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{abs(v):.1f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{abs(v):.1f}"))
    ax.set_xlabel("Longitud (°O)", fontsize=9)
    ax.set_ylabel("Latitud (°S)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(color="k", alpha=0.08, lw=0.5)

    cax = fig.add_axes([0.80, 0.25, 0.025, 0.50])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin, vmax))
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("Elevación (m s. n. m.)", fontsize=9)
    cb.ax.tick_params(labelsize=8)

    fig.text(0.07, 0.965, "Cuenca Río Maipo en El Manzano — Topografía", fontsize=14, fontweight="bold")
    fig.text(0.07, 0.935, "ASTER GDEM v3 (30 m) · sombreado 315°/40° · curvas cada 250 m (gruesas cada "
             "1.000 m) · gauge 5710001", fontsize=7.5, color="#444")
    fig.savefig(OUT / "mapa_topografico_Maipo.png", dpi=200)
    plt.close(fig)


def plot_hypsometry(table: pd.DataFrame, stats: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 4.3), dpi=200)
    x, z = stats["curve"]
    ax1.fill_betweenx(z, 0, x, color="#d9b779", alpha=0.45, lw=0)
    ax1.plot(x, z, color="#8b4a1c", lw=2)
    for level, frac, dx, dy in ((4000, stats["frac_sobre_4000"], 3, 100), (3000, stats["frac_sobre_3000"], 3, -300)):
        ax1.plot(100 * frac, level, "o", color="#d62728", ms=5, zorder=4)
        ax1.text(100 * frac + dx, level + dy, f"{100 * frac:.0f} % sobre {thousands(level)} m", fontsize=7.5)
    ax1.axhline(stats["z_mean"], color="k", ls="--", lw=0.9)
    ax1.axhline(stats["z_median"], color="k", ls=":", lw=0.9)
    ax1.text(98, stats["z_median"] + 330, f"media {thousands(stats['z_mean'])} m · mediana "
             f"{thousands(stats['z_median'])} m", fontsize=7.5, ha="right")
    ax1.set_xlim(0, 100)
    ax1.set_ylim(stats["z_min"] - 280, stats["z_max"] + 250)
    ax1.set_xlabel("Área de la cuenca por encima de esa altura (%)")
    ax1.set_ylabel("Elevación (m s. n. m.)")
    ax1.set_title("Curva hipsométrica", fontweight="bold", fontsize=10)
    ax1.grid(alpha=0.3)

    ax2.barh(table["z_inf_m"], table["area_km2"], height=BAND * 0.85, align="edge", color="#b5895c")
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_xlabel(f"Área por franja de {BAND} m (km²)")
    ax2.set_title("Distribución del área por altura", fontweight="bold", fontsize=10)
    ax2.grid(axis="x", alpha=0.3)
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=9)
    fig.suptitle("Río Maipo en El Manzano — ASTER GDEM v3 (30 m)", fontsize=9.5, color="#444")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / "curva_hipsometrica_Maipo.png", dpi=200)
    plt.close(fig)


def main() -> None:
    basin = load_basin()
    table, stats = hypsometry(basin)
    table.to_csv(OUT / "tabla_1_12_hipsometria.csv", index=False, float_format="%.4f")
    plot_map(basin, stats)
    plot_hypsometry(table, stats)
    print(f"Área DEM dentro del polígono: {stats['area_km2']:.1f} km²")
    print(f"Elevación mín/máx: {stats['z_min']:.0f} / {stats['z_max']:.0f} m; media {stats['z_mean']:.0f} m; "
          f"mediana {stats['z_median']:.0f} m")
    print(f"Fracción sobre 3000 m: {stats['frac_sobre_3000']:.3f}; sobre 4000 m: {stats['frac_sobre_4000']:.3f}")
    peak = table.loc[table["area_km2"].idxmax()]
    print(f"Franja con más área: {peak['z_inf_m']:.0f}-{peak['z_sup_m']:.0f} m ({peak['area_km2']:.0f} km²)")


if __name__ == "__main__":
    main()
