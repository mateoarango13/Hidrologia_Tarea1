"""
Funciones comunes del Rol C (puntos 3 y 4: tendencias y Fourier).

Este módulo NO se ejecuta por sí solo: lo importan los scripts
09_p3_2 ... 14_p4_2. Centraliza:
  * lectura y validación del dataset maestro `datos/datos_mensuales_maipo.csv`;
  * periodos de análisis y de referencia climatológica;
  * anomalías (a) y anomalías estandarizadas (z) del punto 3.2;
  * pruebas de tendencia implementadas de forma explícita (sin cajas negras):
      - OLS con errores estándar clásicos y HAC (Newey y West, 1987);
      - Mann-Kendall (Mann, 1945; Kendall, 1975) con varianza corregida por
        autocorrelación (Hamed y Rao, 1998);
      - pendiente de Theil-Sen con intervalo de confianza (Sen, 1968);
      - Kendall estacional y pendiente de Sen estacional (Hirsch et al., 1982),
        con valor p por remuestreo de bloques de años (Kundzewicz y Robson, 2004);
      - prueba de Pettitt (1979) para un cambio de nivel;
      - control de falsos descubrimientos de Benjamini y Hochberg (1995).

Convenciones:
  * Variable temporal: año decimal calculado con las fechas reales
    (t = año + (mes - 0.5)/12). Las pendientes se reportan por DÉCADA (x10).
  * Los meses faltantes se dejan como NaN; nunca se rellenan con ceros.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import acf

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "datos" / "datos_mensuales_maipo.csv"
FIGURES_DIR = ROOT_DIR / "figuras"
FIGURES_DIR.mkdir(exist_ok=True)

DPI = 300
ALPHA = 0.05          # nivel de significancia fijado para todo el Rol C
RNG_SEED = 20261004   # semilla fija para remuestreos reproducibles

# Periodo de referencia climatológica: el mismo adoptado por los roles A y B
# (entradas #13, #15 y #16 de la bitácora) para que las anomalías sean comparables
# entre fuentes. Es la única ventana en la que coexisten las cuatro variables.
REFERENCE_START = pd.Timestamp("2000-06-01")
REFERENCE_END = pd.Timestamp("2020-03-01")

# Periodo común para comparar variables y productos (punto 3.1 de la guía).
COMMON_START = pd.Timestamp("2000-06-01")
COMMON_END = pd.Timestamp("2020-03-01")

# Variables analizadas. Se usa Caudal_m3s para el caudal; Q_lamina_mm es una
# transformación casi lineal (factor de días del mes) y no aporta evidencia
# independiente de tendencia.
VARIABLES = {
    "P_local_mm": {"label": "Precipitación de referencia $P_L$", "short": "P_L",
                    "unit": "mm/mes", "source": "CAMELS-CL (CR2MET)"},
    "P_IMERG_mm": {"label": "Precipitación IMERG $P_I$", "short": "P_I",
                    "unit": "mm/mes", "source": "GPM IMERG Final mensual (V06 según script 02)"},
    "Caudal_m3s": {"label": r"Caudal medio $\overline{Q}$", "short": "Q",
                    "unit": "m³/s", "source": "CAMELS-CL (DGA), estación 5710001"},
    "Temp_C": {"label": "Temperatura media ERA5-Land $T$", "short": "T",
               "unit": "°C", "source": "ERA5-Land mensual (reanálisis)"},
}
REPRESENTATIONS = {
    "X": "Serie original",
    "a": "Anomalía",
    "z": "Anomalía estandarizada",
}
MONTH_NAMES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Paleta (posiciones 1-3 de la paleta categórica de referencia, validadas
# para todos los pares). Se asignan a MÉTODOS, que son los que comparten panel.
COLOR_OLS = "#2a78d6"
COLOR_SEN = "#eb6834"
COLOR_LOESS = "#1baf7a"
COLOR_POINTS = "#52514e"
COLOR_GRID = "#d9d8d4"


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
def load_master_data() -> pd.DataFrame:
    """Lee el CSV maestro y valida que la malla mensual sea regular y única."""
    data = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    missing_cols = set(VARIABLES).difference(data.columns)
    if missing_cols:
        raise ValueError(f"Faltan columnas en el dataset maestro: {sorted(missing_cols)}")
    if data["date"].duplicated().any():
        raise ValueError("El dataset maestro tiene fechas duplicadas.")
    expected = pd.date_range(data["date"].min(), data["date"].max(), freq="MS")
    if not data["date"].reset_index(drop=True).equals(pd.Series(expected, name="date")):
        raise ValueError("La secuencia mensual no es regular; revisar el dataset maestro.")
    data["year"] = data["date"].dt.year
    data["month"] = data["date"].dt.month
    data["t"] = decimal_year(data["date"])
    # Año hidrológico chileno (abril-marzo), usado en agregados anuales.
    data["water_year"] = np.where(data["month"] >= 4, data["year"], data["year"] - 1)
    return data


def decimal_year(dates: pd.Series) -> np.ndarray:
    dates = pd.to_datetime(dates)
    return (dates.dt.year + (dates.dt.month - 0.5) / 12.0).to_numpy(dtype=float)


def valid_span(data: pd.DataFrame, column: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    valid = data.loc[data[column].notna(), "date"]
    return valid.min(), valid.max()


def full_record(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Registro completo disponible de una variable (sin recortar a IMERG).

    Se conservan los NaN internos para que las fechas reales se respeten.
    """
    start, end = valid_span(data, column)
    return data.loc[data["date"].between(start, end)].copy()


# ---------------------------------------------------------------------------
# Punto 3.2: climatología de referencia y anomalías
# ---------------------------------------------------------------------------
def reference_climatology(data: pd.DataFrame, column: str) -> pd.DataFrame:
    ref = data.loc[data["date"].between(REFERENCE_START, REFERENCE_END) & data[column].notna()]
    clim = ref.groupby("month")[column].agg(mu="mean", s="std", n_years="count")
    clim = clim.reindex(range(1, 13))
    return clim


def add_anomalies(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Devuelve columnas X, a, z para la variable, con la referencia fija."""
    clim = reference_climatology(data, column)
    mu = data["month"].map(clim["mu"])
    s = data["month"].map(clim["s"])
    out = pd.DataFrame({"date": data["date"], "t": data["t"], "month": data["month"],
                        "year": data["year"], "water_year": data["water_year"]})
    out["X"] = data[column]
    out["a"] = data[column] - mu
    # s_j > 0 en todos los meses (se verifica en 09_p3_2); si fuera 0 quedaría NaN.
    out["z"] = np.where(s > 0, out["a"] / s, np.nan)
    return out


# ---------------------------------------------------------------------------
# OLS con diagnóstico de residuos
# ---------------------------------------------------------------------------
def newey_west_lags(n: int) -> int:
    """Regla de Newey y West (1994): floor(4 (n/100)^(2/9))."""
    return int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0)))


def ols_trend(t: np.ndarray, y: np.ndarray, month: np.ndarray | None = None,
              hac_lags: int | None = None) -> dict:
    """Ajusta y = b0 + b1 t (+ efectos de mes calendario si `month` no es None).

    Devuelve pendiente por década, IC 95 % clásico y HAC, valores p y diagnóstico.
    """
    mask = np.isfinite(t) & np.isfinite(y)
    t, y = t[mask], y[mask]
    n = len(y)
    if n < 8:
        return {"n": n}
    tc = t - t.mean()
    if month is None:
        X = sm.add_constant(tc)
        slope_idx = 1
    else:
        m = month[mask]
        dummies = pd.get_dummies(pd.Categorical(m, categories=range(1, 13)), drop_first=False)
        dummies = dummies.loc[:, dummies.sum() > 0].to_numpy(dtype=float)
        X = np.column_stack([tc, dummies])
        slope_idx = 0
    if hac_lags is None:
        hac_lags = newey_west_lags(n)
    fit = sm.OLS(y, X).fit()
    fit_hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    resid = fit.resid
    ci = fit.conf_int(ALPHA)[slope_idx]
    ci_hac = fit_hac.conf_int(ALPHA)[slope_idx]
    lb_lag = 12 if n > 100 else max(2, min(10, n // 5))
    try:
        bp_p = het_breuschpagan(resid, sm.add_constant(tc))[1]
    except Exception:
        bp_p = np.nan
    return {
        "n": n,
        "slope_dec": 10 * fit.params[slope_idx],
        "ci_low_dec": 10 * ci[0], "ci_high_dec": 10 * ci[1],
        "p_ols": fit.pvalues[slope_idx],
        "ci_low_hac_dec": 10 * ci_hac[0], "ci_high_hac_dec": 10 * ci_hac[1],
        "p_hac": fit_hac.pvalues[slope_idx],
        "hac_lags": hac_lags,
        "r2": fit.rsquared,
        "resid_lag1": float(acf(resid, nlags=1, fft=False)[1]),
        "durbin_watson": float(durbin_watson(resid)),
        "ljungbox_lag": lb_lag,
        "ljungbox_p": float(acorr_ljungbox(resid, lags=[lb_lag])["lb_pvalue"].iloc[0]),
        "breusch_pagan_p": float(bp_p),
        "shapiro_p": float(stats.shapiro(resid)[1]) if n <= 5000 else np.nan,
        "intercept_at_mean_t": fit.params[0] if month is None else np.nan,
        "t_mean": t.mean(),
    }


# ---------------------------------------------------------------------------
# Mann-Kendall, Hamed-Rao y Theil-Sen
# ---------------------------------------------------------------------------
def _mk_s(y: np.ndarray) -> float:
    diff = np.sign(y[None, :] - y[:, None])
    return float(np.triu(diff, k=1).sum())


def _mk_var(y: np.ndarray) -> float:
    n = len(y)
    _, counts = np.unique(y, return_counts=True)
    ties = counts[counts > 1]
    return (n * (n - 1) * (2 * n + 5) - np.sum(ties * (ties - 1) * (2 * ties + 5))) / 18.0


def _z_from_s(s: float, var: float) -> float:
    if var <= 0:
        return 0.0
    if s > 0:
        return (s - 1) / np.sqrt(var)
    if s < 0:
        return (s + 1) / np.sqrt(var)
    return 0.0


def _pairwise_slopes(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    i, j = np.triu_indices(len(y), k=1)
    dt = t[j] - t[i]
    keep = dt != 0
    return (y[j][keep] - y[i][keep]) / dt[keep]


def sen_slope_ci(t: np.ndarray, y: np.ndarray, var_s: float) -> tuple[float, float, float]:
    """Pendiente de Theil-Sen e IC (Sen, 1968) usando Var(S) suministrada."""
    slopes = np.sort(_pairwise_slopes(t, y))
    n_prime = len(slopes)
    slope = float(np.median(slopes))
    c = stats.norm.ppf(1 - ALPHA / 2) * np.sqrt(var_s)
    m1 = int(np.floor((n_prime - c) / 2.0))
    m2 = int(np.ceil((n_prime + c) / 2.0))
    lo = slopes[max(m1 - 1, 0)]
    hi = slopes[min(m2, n_prime - 1)]
    return slope, float(lo), float(hi)


def hamed_rao_factor(t: np.ndarray, y: np.ndarray, slope: float) -> float:
    """Factor n/n* de Hamed y Rao (1998) con autocorrelaciones significativas
    de los rangos de la serie sin tendencia (Sen)."""
    n = len(y)
    detr = y - slope * t
    ranks = stats.rankdata(detr)
    r = acf(ranks, nlags=n - 1, fft=True)[1:]
    k = np.arange(1, n)
    bound = stats.norm.ppf(1 - ALPHA / 2) / np.sqrt(n)
    sig = np.abs(r) > bound
    factor = 1 + 2.0 / (n * (n - 1) * (n - 2)) * np.sum(
        ((n - k) * (n - k - 1) * (n - k - 2) * r)[sig])
    # Decisión conservadora: la corrección solo puede inflar Var(S). Un factor < 1
    # (autocorrelación negativa espuria de rangos) reduciría el valor p sin
    # justificación física, por lo que se acota inferiormente en 1.
    return float(max(factor, 1.0))


def mann_kendall(t: np.ndarray, y: np.ndarray, hamed_rao: bool = True) -> dict:
    """Mann-Kendall + Theil-Sen. Si hamed_rao, también la versión corregida."""
    mask = np.isfinite(t) & np.isfinite(y)
    t, y = t[mask], y[mask]
    order = np.argsort(t)
    t, y = t[order], y[order]
    n = len(y)
    if n < 8:
        return {"n": n}
    s = _mk_s(y)
    var = _mk_var(y)
    z = _z_from_s(s, var)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    tau = s / (0.5 * n * (n - 1))
    out = {"n": n, "S": s, "tau": tau, "z_mk": z, "p_mk": p}
    slope, lo, hi = sen_slope_ci(t, y, var)
    out.update({"sen_dec": 10 * slope, "sen_low_dec": 10 * lo, "sen_high_dec": 10 * hi})
    if hamed_rao:
        factor = hamed_rao_factor(t, y, slope)
        var_hr = var * factor
        z_hr = _z_from_s(s, var_hr)
        _, lo_hr, hi_hr = sen_slope_ci(t, y, var_hr)
        out.update({"hr_factor": factor, "z_mk_hr": z_hr,
                    "p_mk_hr": 2 * (1 - stats.norm.cdf(abs(z_hr))),
                    "sen_low_hr_dec": 10 * lo_hr, "sen_high_hr_dec": 10 * hi_hr})
    return out


# ---------------------------------------------------------------------------
# Kendall estacional (Hirsch et al., 1982) y remuestreo por bloques de años
# ---------------------------------------------------------------------------
def _year_month_matrix(frame: pd.DataFrame, col: str) -> pd.DataFrame:
    return frame.pivot_table(index="year", columns="month", values=col, aggfunc="first").reindex(
        columns=range(1, 13))


def _seasonal_s(matrix: np.ndarray) -> tuple[float, float]:
    s_tot, var_tot = 0.0, 0.0
    for j in range(matrix.shape[1]):
        col = matrix[:, j]
        col = col[np.isfinite(col)]
        if len(col) < 3:
            continue
        s_tot += _mk_s(col)
        var_tot += _mk_var(col)
    return s_tot, var_tot


def seasonal_kendall(frame: pd.DataFrame, col: str, n_boot: int = 2000,
                     block_years: int = 3) -> dict:
    """Kendall estacional con pendiente de Sen estacional.

    p_sk: varianza bajo independencia entre meses (Hirsch et al., 1982).
    p_boot: remuestreo de bloques móviles de `block_years` años completos, que
            conserva la correlación entre meses del mismo año y la persistencia
            interanual corta (Kundzewicz y Robson, 2004).
    """
    mat_df = _year_month_matrix(frame, col)
    years = mat_df.index.to_numpy(dtype=float)
    mat = mat_df.to_numpy(dtype=float)
    s, var = _seasonal_s(mat)
    z = _z_from_s(s, var)
    p = 2 * (1 - stats.norm.cdf(abs(z)))

    slopes = []
    for j in range(12):
        col_vals = mat[:, j]
        ok = np.isfinite(col_vals)
        if ok.sum() >= 3:
            slopes.append(_pairwise_slopes(years[ok], col_vals[ok]))
    slopes = np.sort(np.concatenate(slopes))
    n_prime = len(slopes)
    c = stats.norm.ppf(1 - ALPHA / 2) * np.sqrt(var)
    lo = slopes[max(int(np.floor((n_prime - c) / 2)) - 1, 0)]
    hi = slopes[min(int(np.ceil((n_prime + c) / 2)), n_prime - 1)]

    rng = np.random.default_rng(RNG_SEED)
    n_years = mat.shape[0]
    n_blocks = int(np.ceil(n_years / block_years))
    starts_max = n_years - block_years
    boot = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, starts_max + 1, size=n_blocks)
        idx = np.concatenate([np.arange(st, st + block_years) for st in starts])[:n_years]
        boot[b] = _seasonal_s(mat[idx])[0]
    p_boot = (np.sum(np.abs(boot) >= abs(s)) + 1) / (n_boot + 1)
    return {"n": int(np.isfinite(mat).sum()), "S": s, "z_sk": z, "p_sk": p,
            "p_sk_boot": p_boot, "block_years": block_years, "n_boot": n_boot,
            "sen_dec": 10 * float(np.median(slopes)),
            "sen_low_dec": 10 * float(lo), "sen_high_dec": 10 * float(hi)}


# ---------------------------------------------------------------------------
# Cambio de nivel (Pettitt, 1979)
# ---------------------------------------------------------------------------
def pettitt(y: np.ndarray) -> dict:
    y = np.asarray(y, dtype=float)
    n = len(y)
    sgn = np.sign(y[None, :] - y[:, None])  # sgn[i, j] = sign(y_j - y_i)
    u = np.array([sgn[: k + 1, k + 1:].sum() for k in range(n - 1)])
    k_idx = int(np.argmax(np.abs(u)))
    k_stat = float(np.abs(u[k_idx]))
    p = min(1.0, 2 * np.exp(-6 * k_stat ** 2 / (n ** 3 + n ** 2)))
    return {"k_last_before": k_idx, "K": k_stat, "p": p}


# ---------------------------------------------------------------------------
# Comparaciones múltiples
# ---------------------------------------------------------------------------
def bh_fdr(pvalues: pd.Series) -> pd.Series:
    p = pvalues.astype(float)
    ok = p.notna()
    q = pd.Series(np.nan, index=p.index)
    if ok.any():
        q[ok] = multipletests(p[ok], alpha=ALPHA, method="fdr_bh")[1]
    return q


# ---------------------------------------------------------------------------
# Estilo de figuras
# ---------------------------------------------------------------------------
def apply_style() -> None:
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": DPI, "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#8a8984", "axes.grid": True, "grid.color": COLOR_GRID,
        "grid.linewidth": 0.5, "lines.linewidth": 2.0, "savefig.bbox": "tight",
        "axes.titleweight": "bold",
    })
