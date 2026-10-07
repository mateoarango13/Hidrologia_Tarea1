"""
Funciones comunes del punto 5 (mapas de correlación con el clima global).

No se ejecuta solo: lo importan 16_p5_1 ... 19_p5_4 y 08_build_dashboard_data.

Contiene:
  * lectura de los campos ERA5 (datos/campos_era5/) con conversión de unidades:
      SST  K -> °C;  MSL  Pa -> hPa;  Z500 geopotencial (m²/s²) -> ALTURA geopotencial (m)
      dividiendo por g0 = 9.80665 m/s² (se distinguen ambas magnitudes);
  * series de la cuenca desde el CSV maestro;
  * anomalías por mes calendario y por celda con la referencia fija 2000-06 a 2020-03
    (la misma de la cuenca en los puntos 1-4);
  * correlación de Pearson/Spearman por celda a través de los años de un mes calendario,
    con rezago ℓ (ℓ > 0: el campo antecede a la respuesta; enero con ℓ = 1 usa diciembre
    del año anterior);
  * tamaño de muestra efectivo (Bretherton et al., 1999), prueba t y FDR
    (Benjamini y Hochberg, 1995; α_FDR = 0.10 según Wilks, 2016);
  * mapa base con costas Natural Earth 110 m (dominio público), sin cartopy.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FIELDS_DIR = ROOT / "datos" / "campos_era5"
DATA_PATH = ROOT / "datos" / "datos_mensuales_maipo.csv"
FIGURES_DIR = ROOT / "figuras"
COAST_PATH = FIELDS_DIR / "ne_110m_coastline.geojson"
FILE_SINGLE = FIELDS_DIR / "era5_msl_sst_mensual_1979_2020_1deg.nc"
FILE_Z500 = FIELDS_DIR / "era5_z500_mensual_1979_2020_1deg.nc"

G0 = 9.80665
SEA_ICE_SST = -1.6        # °C; SST <= umbral se trata como hielo marino
REF_START, REF_END = pd.Timestamp("2000-06-01"), pd.Timestamp("2020-03-01")
ALPHA_FDR = 0.10          # Wilks (2016): α_FDR = 2 α_global para campos espacialmente correlacionados
MIN_YEARS = 15            # mínimo de pares (años) por celda para reportar una correlación
DPI = 300
# Ubicación aproximada de la cuenca (centroide ~; estación El Manzano ~33.6°S, 70.4°W). VERIFICAR con CAMELS-CL.
BASIN_LAT, BASIN_LON = -33.8, 360 - 70.1

FIELDS = {
    "sst": {"label": "SST", "long": "Temperatura superficial del mar", "unit": "°C"},
    "msl": {"label": "PNM", "long": "Presión al nivel del mar", "unit": "hPa"},
    "z500": {"label": "Z500", "long": "Altura geopotencial en 500 hPa", "unit": "m"},
}
BASIN_VARS = {
    "P_local_mm": {"label": "P$_L$", "plain": "P_L", "long": "Precipitación de referencia", "unit": "mm/mes"},
    "Caudal_m3s": {"label": "Q", "plain": "Q", "long": "Caudal medio", "unit": "m³/s"},
    "P_IMERG_mm": {"label": "P$_I$", "plain": "P_I", "long": "Precipitación IMERG", "unit": "mm/mes"},
    "Temp_C": {"label": "T", "plain": "T", "long": "Temperatura ERA5-Land", "unit": "°C"},
}
MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Cajas predefinidas por mecanismo (no elegidas a partir de los mapas), en lon 0-360.
BOXES = {
    "nino34": {"label": "Niño 3.4 (SST)", "field": "sst", "lat": (-5, 5), "lon": (190, 240)},
    "pnm_sepac": {"label": "PNM Pacífico SE (30–40°S, 75–90°W)", "field": "msl", "lat": (-40, -30), "lon": (270, 285)},
    "z500_chile": {"label": "Z500 Chile central (30–40°S, 70–85°W)", "field": "z500", "lat": (-40, -30), "lon": (275, 290)},
}


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
def _standardize(da: xr.DataArray) -> xr.DataArray:
    if "valid_time" in da.dims:
        da = da.rename(valid_time="time")
    if "pressure_level" in da.dims:
        da = da.squeeze("pressure_level", drop=True)
    for coord in ("number", "expver", "pressure_level"):
        if coord in da.coords:
            da = da.drop_vars(coord)
    da = da.assign_coords(time=pd.to_datetime(da["time"].values).to_period("M").to_timestamp())
    return da.sortby("latitude")


def load_fields() -> dict[str, xr.DataArray]:
    """Devuelve {sst, msl, z500} en °C, hPa y m, dims (time, latitude, longitude)."""
    single = xr.open_dataset(FILE_SINGLE)
    z500 = xr.open_dataset(FILE_Z500)
    fields = {
        "sst": _standardize(single["sst"]) - 273.15,
        "msl": _standardize(single["msl"]) / 100.0,
        "z500": _standardize(z500["z"]) / G0,
    }
    # ERA5 fija la SST bajo hielo marino en el punto de congelación (~ -1.69 °C): no es una
    # SST oceánica libre y se enmascara como hielo (valor inválido para la correlación).
    fields["sst"] = fields["sst"].where(fields["sst"] > SEA_ICE_SST)
    for name, da in fields.items():
        da.name = name
        da.attrs["units"] = FIELDS[name]["unit"]
    # float64: xarray acumula en float32 y pierde precisión en medias globales.
    return {k: v.load().astype("float64") for k, v in fields.items()}


def load_basin() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, parse_dates=["date"]).set_index("date")
    return data[list(BASIN_VARS)]


def basin_anomalies(basin: pd.DataFrame) -> pd.DataFrame:
    ref = basin.loc[REF_START:REF_END]
    clim = ref.groupby(ref.index.month).mean()
    return basin - clim.reindex(basin.index.month).set_index(basin.index)


def field_anomalies(da: xr.DataArray) -> xr.DataArray:
    ref = da.sel(time=slice(REF_START, REF_END))
    clim = ref.groupby("time.month").mean("time")
    return (da.groupby("time.month") - clim).drop_vars("month")


# ---------------------------------------------------------------------------
# Correlaciones por mes calendario
# ---------------------------------------------------------------------------
def paired_samples(x_anom: pd.Series, f_anom: xr.DataArray, month: int, lag: int = 0,
                   years: tuple[int, int] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """x (n,), Y (n, lat, lon) y años para el mes calendario `month` de la cuenca.

    El campo se toma en t - lag meses (ℓ > 0: el campo antecede a la cuenca)."""
    s = x_anom[(x_anom.index.month == month)].dropna()
    if years:
        s = s[(s.index.year >= years[0]) & (s.index.year <= years[1])]
    field_dates = s.index - pd.DateOffset(months=lag)
    available = pd.DatetimeIndex(f_anom["time"].values)
    keep = field_dates.isin(available)
    s, field_dates = s[keep], field_dates[keep]
    Y = f_anom.sel(time=field_dates).values
    return s.to_numpy(float), Y, s.index.year.to_numpy()


def detrend_years(values: np.ndarray, years: np.ndarray) -> np.ndarray:
    """Retira la tendencia lineal en el año (a lo largo del eje 0), ignorando NaN."""
    t = (years - years.mean()).astype(float)
    shape = values.shape
    v = values.reshape(len(t), -1)
    out = np.full_like(v, np.nan, dtype=float)
    ok_cols = np.all(np.isfinite(v), axis=0)
    if ok_cols.any():
        coef = np.polyfit(t, v[:, ok_cols], 1)
        out[:, ok_cols] = v[:, ok_cols] - (np.outer(t, coef[0]) + coef[1])
    return out.reshape(shape)


def _lag1(v: np.ndarray) -> np.ndarray:
    a = v - v.mean(axis=0)
    num = np.sum(a[1:] * a[:-1], axis=0)
    den = np.sum(a * a, axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / den


def correlation_map(x: np.ndarray, Y: np.ndarray, method: str = "pearson") -> dict[str, np.ndarray]:
    """Correlación por celda con prueba t y tamaño efectivo (Bretherton et al., 1999).

    Las celdas con algún año faltante (p. ej., hielo marino variable) o con menos de
    MIN_YEARS pares se enmascaran."""
    n = len(x)
    flat = Y.reshape(n, -1)
    valid = np.all(np.isfinite(flat), axis=0) & (n >= MIN_YEARS)
    r = np.full(flat.shape[1], np.nan)
    p = np.full(flat.shape[1], np.nan)
    n_eff = np.full(flat.shape[1], np.nan)
    if valid.any():
        yv = flat[:, valid]
        xv = x
        if method == "spearman":
            xv = stats.rankdata(x)
            yv = np.apply_along_axis(stats.rankdata, 0, yv)
        xa = xv - xv.mean()
        ya = yv - yv.mean(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            rv = (xa @ ya) / np.sqrt(np.sum(xa ** 2) * np.sum(ya ** 2, axis=0))
        r1x = _lag1(xv[:, None])[0]
        r1y = _lag1(yv)
        prod = np.clip(r1x * r1y, -0.9, 0.9)
        ne = np.clip(n * (1 - prod) / (1 + prod), 3, n)
        with np.errstate(invalid="ignore", divide="ignore"):
            tval = rv * np.sqrt((ne - 2) / np.clip(1 - rv ** 2, 1e-12, None))
        pv = 2 * stats.t.sf(np.abs(tval), ne - 2)
        r[valid], p[valid], n_eff[valid] = rv, pv, ne
    shape = Y.shape[1:]
    return {"r": r.reshape(shape), "p": p.reshape(shape), "n_eff": n_eff.reshape(shape),
            "n": np.where(valid, n, 0).reshape(shape)}


def fdr_mask(p: np.ndarray, alpha: float = ALPHA_FDR) -> np.ndarray:
    """Benjamini-Hochberg sobre las celdas válidas de un mapa (familia = un mapa)."""
    flat = p.ravel()
    ok = np.isfinite(flat)
    sig = np.zeros_like(flat, dtype=bool)
    m = ok.sum()
    if m == 0:
        return sig.reshape(p.shape)
    order = np.argsort(flat[ok])
    ranked = flat[ok][order]
    below = ranked <= alpha * np.arange(1, m + 1) / m
    if below.any():
        cutoff = ranked[np.max(np.nonzero(below))]
        sig[ok] = flat[ok] <= cutoff
    return sig.reshape(p.shape)


def area_weights(lat: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    return np.broadcast_to(np.cos(np.deg2rad(lat))[:, None], shape)


def area_fraction(mask: np.ndarray, valid: np.ndarray, lat: np.ndarray) -> float:
    w = area_weights(lat, mask.shape)
    den = np.sum(w[valid])
    return float(np.sum(w[mask & valid]) / den) if den > 0 else np.nan


def pattern_correlation(a: np.ndarray, b: np.ndarray, lat: np.ndarray, region: dict | None = None,
                        lon: np.ndarray | None = None) -> float:
    """Correlación espacial centrada, ponderada por cos(lat), entre dos mapas."""
    w = area_weights(lat, a.shape).copy()
    if region is not None:
        la = (lat >= region["lat"][0]) & (lat <= region["lat"][1])
        lo = (lon >= region["lon"][0]) & (lon <= region["lon"][1])
        w = w * np.outer(la, lo)
    ok = np.isfinite(a) & np.isfinite(b) & (w > 0)
    if ok.sum() < 10:
        return np.nan
    wa, aa, bb = w[ok], a[ok], b[ok]
    am, bm = np.average(aa, weights=wa), np.average(bb, weights=wa)
    cov = np.average((aa - am) * (bb - bm), weights=wa)
    return float(cov / np.sqrt(np.average((aa - am) ** 2, weights=wa) * np.average((bb - bm) ** 2, weights=wa)))


PACIFIC = {"lat": (-60, 60), "lon": (120, 300)}


def box_index(f_anom: xr.DataArray, box: dict) -> pd.Series:
    sub = f_anom.sel(latitude=slice(*box["lat"]), longitude=slice(*box["lon"]))
    w = np.cos(np.deg2rad(sub["latitude"]))
    series = sub.weighted(w).mean(("latitude", "longitude"))
    return pd.Series(series.values, index=pd.DatetimeIndex(series["time"].values))


# ---------------------------------------------------------------------------
# Mapas
# ---------------------------------------------------------------------------
def coastline_segments() -> list[np.ndarray]:
    """Segmentos de costa en longitudes 0-360, cortados en el salto 360/0."""
    gj = json.loads(COAST_PATH.read_text())
    segs = []
    for feat in gj["features"]:
        coords = np.asarray(feat["geometry"]["coordinates"], float)
        lon = np.mod(coords[:, 0], 360)
        lat = coords[:, 1]
        breaks = np.nonzero(np.abs(np.diff(lon)) > 180)[0] + 1
        for part_lon, part_lat in zip(np.split(lon, breaks), np.split(lat, breaks)):
            if len(part_lon) > 1:
                segs.append(np.column_stack([part_lon, part_lat]))
    return segs


_COAST = None


def draw_map(ax, lon, lat, values, sig=None, vmin=-1, vmax=1, cmap="RdBu_r", lat_range=(-80, 80),
             lon_range=(0, 360), title=None, basin=True):
    global _COAST
    if _COAST is None:
        _COAST = coastline_segments()
    mesh = ax.pcolormesh(lon, lat, values, cmap=cmap, vmin=vmin, vmax=vmax, shading="nearest", rasterized=True)
    for seg in _COAST:
        ax.plot(seg[:, 0], seg[:, 1], color="#2b2b2b", lw=0.4)
    if sig is not None and sig.any():
        jj, ii = np.nonzero(sig)
        step = 3  # puntear cada 3 celdas para legibilidad
        keep = (jj % step == 0) & (ii % step == 0)
        ax.plot(lon[ii[keep]], lat[jj[keep]], ".", ms=0.9, color="#111111")
    if basin:
        ax.plot(BASIN_LON, BASIN_LAT, marker="*", ms=7, color="#ffd400", mec="#111111", mew=0.6)
    ax.set_xlim(*lon_range)
    ax.set_ylim(*lat_range)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_linewidth(0.4)
    if title:
        ax.set_title(title, fontsize=8, pad=2)
    return mesh


# ---------------------------------------------------------------------------
# Lote de 12 mapas (uno por mes calendario de la respuesta de la cuenca)
# ---------------------------------------------------------------------------
def monthly_maps(x_anom: pd.Series, f_anom: xr.DataArray, lag: int = 0, years=None,
                 detrend: bool = False, method: str = "pearson", exclude_years=()) -> list[dict]:
    out = []
    for month in range(1, 13):
        x, Y, yrs = paired_samples(x_anom, f_anom, month, lag=lag, years=years)
        if exclude_years:
            keep = ~np.isin(yrs, list(exclude_years))
            x, Y, yrs = x[keep], Y[keep], yrs[keep]
        if detrend:
            x = detrend_years(x[:, None], yrs)[:, 0]
            Y = detrend_years(Y, yrs)
        res = correlation_map(x, Y, method=method)
        res["sig"] = fdr_mask(res["p"])
        res.update({"month": month, "n_pairs": len(x), "years": (int(yrs.min()), int(yrs.max()))})
        out.append(res)
    return out


def load_all():
    """Campos, anomalías de campos, anomalías de la cuenca, lat y lon."""
    fields = load_fields()
    f_anom = {k: field_anomalies(v) for k, v in fields.items()}
    b_anom = basin_anomalies(load_basin())
    lat = fields["sst"].latitude.values
    lon = fields["sst"].longitude.values
    return fields, f_anom, b_anom, lat, lon
