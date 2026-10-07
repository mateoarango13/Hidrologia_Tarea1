"""
Punto 4.2 — Construir e interpretar los espectros (Rol C).

Requiere 13_p4_1_preparacion_espectral.py (lee serie_4_1_series_espectrales.csv).

Convención espectral:
  Densidad espectral de potencia (DEP) UNILATERAL, scipy.signal.periodogram/welch
  con fs = 1 ciclo/mes y scaling='density':
      P(f_k) = 2 Δt |sum_n w_n x_n e^{-i 2π k n / N}|^2 / sum_n w_n^2   (0 < f < 0.5)
  Unidades: [unidad de la variable]^2 / (ciclo/mes). Se verifica Parseval:
  sum_k P(f_k) Δf ≈ varianza de la serie (boxcar).
  Frecuencias f_k = k/(N Δt); Δf = 1/N; Nyquist 0.5 ciclos/mes; f = 0 (media) se omite.

Estimadores (para controlar fuga y varianza):
  * boxcar: periodograma sin ventana (máxima resolución, mayor fuga);
  * Hann:   periodograma con ventana Hann (estimador principal: reduce la fuga a
            costa de ensanchar el lóbulo principal a ~2Δf);
  * Welch:  segmentos Hann de 120 meses con 50 % de solapamiento (reduce la
            varianza; resolución 1/120 ciclos/mes, periodos > 10 años no resueltos).

Significancia (solo para anomalías A y AD, que no tienen el ciclo anual
determinista): fondo de ruido rojo AR(1) con el r1 y la varianza de la serie.
Umbrales al 95 % por Monte Carlo (1000 series AR(1) procesadas con el MISMO
estimador): puntual (percentil 95 por frecuencia) y GLOBAL (percentil 95 del
máximo cociente P/fondo sobre todas las frecuencias), que trata la búsqueda
entre frecuencias.

Salidas:
  figuras/tabla_4_2_picos_espectrales.csv
  figuras/tabla_4_2_fracciones_banda.csv
  figuras/tabla_4_2_persistencia.csv
  figuras/tabla_4_2_estabilidad_picos.csv
  figuras/figura_4_2a_espectros_originales.png
  figuras/figura_4_2b_espectros_anomalias_ar1.png
  figuras/figura_4_2c_espectros_normalizados.png
  figuras/figura_4_2d_estabilidad.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal

import rol_c_comun as rc

N_SIM = 1000
WELCH_SEG = 120
BANDS = {  # en ciclos/mes
    "interanual (T > 18 meses)": (0.0, 1 / 18),
    "anual (10.5-14 meses)": (1 / 14, 1 / 10.5),
    "semianual (5.25-7 meses)": (1 / 7, 1 / 5.25),
}
SERIES_PATH = rc.FIGURES_DIR / "serie_4_1_series_espectrales.csv"


# ---------------------------------------------------------------------------
# Estimadores
# ---------------------------------------------------------------------------
def spectrum(x: np.ndarray, method: str) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, float)
    if method == "boxcar":
        f, p = signal.periodogram(x, fs=1.0, window="boxcar", scaling="density", detrend=False)
    elif method == "hann":
        f, p = signal.periodogram(x, fs=1.0, window="hann", scaling="density", detrend=False)
    elif method == "welch":
        f, p = signal.welch(x, fs=1.0, window="hann", nperseg=min(WELCH_SEG, len(x)),
                            noverlap=min(WELCH_SEG, len(x)) // 2, scaling="density", detrend=False)
    else:
        raise ValueError(method)
    return f[1:], p[1:]  # sin f = 0


def lag1(x: np.ndarray) -> float:
    x = x - x.mean()
    return float(np.sum(x[1:] * x[:-1]) / np.sum(x * x))


def ar1_series(n: int, r: float, var: float, rng: np.random.Generator, n_sim: int) -> np.ndarray:
    e = rng.normal(0, np.sqrt(var * (1 - r ** 2)), size=(n_sim, n + 200))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0] / np.sqrt(1 - r ** 2)
    for t in range(1, n + 200):
        x[:, t] = r * x[:, t - 1] + e[:, t]
    x = x[:, 200:]
    return x - x.mean(axis=1, keepdims=True)


def ar1_thresholds(x: np.ndarray, method: str) -> dict:
    """Fondo AR(1) teórico y umbrales 95 % puntual y global por Monte Carlo."""
    rng = np.random.default_rng(rc.RNG_SEED)
    r, var, n = lag1(x), np.var(x), len(x)
    f, _ = spectrum(x, method)
    theory = 2 * var * (1 - r ** 2) / (1 - 2 * r * np.cos(2 * np.pi * f) + r ** 2)
    sims = np.array([spectrum(s, method)[1] for s in ar1_series(n, r, var, rng, N_SIM)])
    point95 = np.percentile(sims, 95, axis=0)
    ratio_max = np.max(sims / theory, axis=1)
    global95 = theory * np.percentile(ratio_max, 95)
    return {"r1": r, "theory": theory, "point95": point95, "global95": global95}


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------
def band_fractions(f: np.ndarray, p: np.ndarray) -> dict:
    df = f[1] - f[0]
    total = np.sum(p) * df
    out = {}
    for name, (lo, hi) in BANDS.items():
        sel = (f > lo) & (f <= hi)
        out[name] = np.sum(p[sel]) * df / total
    out["resto (intraanual no armónico)"] = 1 - sum(out.values())
    return out


def find_peaks_table(f, p, n, meta: dict, thr: dict | None, top: int = 5) -> list[dict]:
    idx, _ = signal.find_peaks(p)
    idx = idx[np.argsort(p[idx])[::-1]][:top]
    df = 1 / n
    rows = []
    for i in sorted(idx, key=lambda k: f[k]):
        fk = f[i]
        rows.append({**meta, "f_ciclos_mes": fk, "periodo_meses": 1 / fk, "periodo_anios": 1 / fk / 12,
                     "delta_f": df,
                     "periodo_min_meses": 1 / (fk + df), "periodo_max_meses": (1 / (fk - df)) if fk > df else np.inf,
                     "ciclos_observados": n * fk, "dep": p[i],
                     "fraccion_varianza_bin": p[i] * df / (np.sum(p) * df),
                     "supera_AR1_95_puntual": (bool(p[i] > thr["point95"][i]) if thr else None),
                     "supera_AR1_95_global": (bool(p[i] > thr["global95"][i]) if thr else None)})
    return rows


def spectral_slope(f: np.ndarray, p: np.ndarray) -> float:
    sel = f < 1 / 12
    return float(np.polyfit(np.log10(f[sel]), np.log10(p[sel]), 1)[0])


def dominant_interannual(f, p) -> float:
    sel = f < 1 / 18
    return float(1 / f[sel][np.argmax(p[sel])] / 12)


# ---------------------------------------------------------------------------
def get(series: pd.DataFrame, seg: str, col: str, tr: str) -> pd.DataFrame:
    return series.loc[(series["tramo"] == seg) & (series["variable"] == col)
                      & (series["transformacion"] == tr)].reset_index(drop=True)


def add_period_axis(ax) -> None:
    sec = ax.secondary_xaxis("top", functions=(lambda f: 1 / np.maximum(f, 1e-6) / 12,
                                               lambda T: 1 / np.maximum(T, 1e-6) / 12))
    sec.set_xticks([10, 2, 1, 0.5, 0.25])
    sec.set_xticklabels(["10", "2", "1", "0.5", "0.25"], fontsize=7)
    sec.set_xlabel("Periodo [años]", fontsize=8)


def mark_bands(ax) -> None:
    for T in (12, 6, 4, 3):
        ax.axvline(1 / T, color="#9a9994", lw=0.7, ls=":")
    ax.axvspan(0, 1 / 18, color="#9a9994", alpha=0.08, lw=0)


def analyse(series: pd.DataFrame):
    peaks, bands, persist = [], [], []
    thr_store = {}
    combos = [(seg, col) for seg, col in series[["tramo", "variable"]].drop_duplicates().itertuples(index=False)]
    for seg, col in combos:
        for tr in ("C", "A", "AD"):
            s = get(series, seg, col, tr)
            x = s["valor"].to_numpy(float)
            n = len(x)
            for method in ("boxcar", "hann", "welch"):
                f, p = spectrum(x, method)
                if method == "boxcar":
                    parseval = np.sum(p) * (f[1] - f[0]) / np.var(x)
                thr = ar1_thresholds(x, method) if (tr != "C" and method != "boxcar") else None
                if thr is not None:
                    thr_store[(seg, col, tr, method)] = thr
                meta = {"tramo": seg, "variable": col, "transformacion": tr, "estimador": method, "N": n}
                if method in ("hann", "welch"):
                    n_eff = n if method == "hann" else WELCH_SEG
                    peaks += find_peaks_table(f, p, n_eff, meta, thr)
                bands.append({**meta, **band_fractions(f, p), "varianza": np.var(x)})
            if tr in ("A", "AD"):
                f, p = spectrum(x, "hann")
                persist.append({"tramo": seg, "variable": col, "transformacion": tr, "N": n,
                                "r1": lag1(x), "pendiente_espectral_loglog_f<1/12": spectral_slope(f, p),
                                "periodo_interanual_dominante_anios": dominant_interannual(f, p),
                                "parseval_boxcar_C": parseval if tr == "A" else np.nan})
    return pd.DataFrame(peaks), pd.DataFrame(bands), pd.DataFrame(persist), thr_store


def stability(series: pd.DataFrame, data: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows, curves = [], {}

    def record(var, config, x, f=None, p=None, n_res=None):
        if f is None:
            f, p = spectrum(x, "hann")
        fr = band_fractions(f, p) if np.allclose(np.diff(f), f[1] - f[0]) else {}
        rows.append({"variable": var, "configuracion": config, "N": len(x) if x is not None else n_res,
                     "periodo_interanual_dominante_anios": dominant_interannual(f, p),
                     **{f"frac_{k}": v for k, v in fr.items()}})
        curves[(var, config)] = (f, p)

    for col in ("P_local_mm", "Caudal_m3s"):
        a = get(series, "completo", col, "A")
        x = a["valor"].to_numpy(float)
        ad = get(series, "completo", col, "AD")["valor"].to_numpy(float)
        record(col, "A Hann 1980-2020", x)
        record(col, "A boxcar 1980-2020", None, *spectrum(x, "boxcar"), n_res=len(x))
        rows[-1]["N"] = len(x)
        record(col, "A Welch 120 m 1980-2020", None, *spectrum(x, "welch"), n_res=len(x))
        rows[-1]["N"] = len(x)
        record(col, "AD (sin tendencia) Hann", ad)
        lo, hi = np.percentile(x, [1, 99])
        record(col, "A winsorizada p1-p99", np.clip(x, lo, hi) - np.clip(x, lo, hi).mean())
        first, second = x[:240], x[240:]
        record(col, "A 1980-04/2000-03", first - first.mean())
        record(col, "A 2000-04/2020-03", second - second.mean())
    # Efecto del relleno de vacíos en Q
    anom = rc.add_anomalies(data, "Caudal_m3s")
    cont = anom.loc[anom["date"].between("1990-12-01", "2014-11-01"), "a"].to_numpy(float)
    record("Caudal_m3s", "A continua sin relleno 1990-12/2014-11", cont - cont.mean())
    raw = anom.loc[anom["date"].between("1980-04-01", "2020-03-01")]
    raw = raw.loc[raw["a"].notna()]
    t = raw["t"].to_numpy(float) * 12  # meses
    y = raw["a"].to_numpy(float) - raw["a"].mean()
    f_ls = np.arange(1, 240) / 480.0
    pgram = signal.lombscargle(t, y, 2 * np.pi * f_ls)
    p_ls = pgram / np.sum(pgram) * np.var(y) / (f_ls[1] - f_ls[0])  # escalada a varianza total
    record("Caudal_m3s", "A Lomb-Scargle sin relleno 1980-2020", None, f_ls, p_ls, n_res=len(y))
    return pd.DataFrame(rows), curves


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------
def plot_original(series: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (col, meta) in zip(axes.ravel(), rc.VARIABLES.items()):
        for seg, color, lab in [("completo", rc.COLOR_OLS, "1980-04/2020-03 (N=480)"),
                                ("comun", rc.COLOR_SEN, "2001-04/2020-03 (N=228)")]:
            s = get(series, seg, col, "C")
            if s.empty:
                continue
            f, p = spectrum(s["valor"].to_numpy(float), "hann")
            ax.semilogy(f, p, color=color, lw=1.4, label=lab)
        mark_bands(ax)
        ax.set_xlim(0, 0.5)
        ax.set_xlabel("Frecuencia [ciclos/mes]")
        ax.set_ylabel(f"DEP [({meta['unit']})²/(ciclo/mes)]")
        ax.set_title(meta["label"], fontsize=9, pad=24)
        add_period_axis(ax)
        ax.legend(frameon=False, loc="upper right")
    fig.suptitle("Figura 4.2a. Espectros de las series originales centradas (C), periodograma con ventana Hann, "
                 "DEP unilateral\nLíneas punteadas: 12, 6, 4 y 3 meses; sombreado: banda interanual (T > 18 meses)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_4_2a_espectros_originales.png")
    plt.close(fig)


def plot_anomalies(series: pd.DataFrame, thr: dict) -> None:
    rc.apply_style()
    combos = [("completo", "P_local_mm"), ("completo", "Caudal_m3s"), ("comun", "P_local_mm"),
              ("comun", "P_IMERG_mm"), ("comun", "Caudal_m3s"), ("comun", "Temp_C")]
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    for ax, (seg, col) in zip(axes.ravel(), combos):
        meta = rc.VARIABLES[col]
        a = get(series, seg, col, "A")["valor"].to_numpy(float)
        ad = get(series, seg, col, "AD")["valor"].to_numpy(float)
        f, p = spectrum(a, "hann")
        ax.semilogy(f, p, color=rc.COLOR_OLS, lw=1.3, label="A (Hann)")
        f2, p2 = spectrum(ad, "hann")
        ax.semilogy(f2, p2, color=rc.COLOR_SEN, lw=1.0, ls="--", label="AD sin tendencia (Hann)")
        fw, pw = spectrum(a, "welch")
        ax.semilogy(fw, pw, color=rc.COLOR_LOESS, lw=2.2, label="A (Welch 120 m)")
        t = thr[(seg, col, "A", "hann")]
        ax.semilogy(f, t["theory"], color="#52514e", lw=1.0, label="AR(1) teórico (r1 de cada serie)")
        ax.semilogy(f, t["point95"], color="#52514e", lw=0.9, ls="--", label="AR(1) 95 % puntual")
        ax.semilogy(f, t["global95"], color="#52514e", lw=0.9, ls=":", label="AR(1) 95 % global")
        mark_bands(ax)
        ax.set_xlim(0, 0.5)
        ax.set_xlabel("Frecuencia [ciclos/mes]")
        ax.set_ylabel(f"DEP [({meta['unit']})²/(ciclo/mes)]")
        ax.set_title(f"{meta['label']} — tramo {seg} (N={len(a)}, r1={t['r1']:.2f})", fontsize=9, pad=24)
        add_period_axis(ax)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False)
    fig.suptitle("Figura 4.2b. Espectros de anomalías (A) y anomalías sin tendencia (AD) frente a un fondo de ruido rojo AR(1)\n"
                 "Umbrales 95 % por Monte Carlo (1000 series AR(1), mismo estimador Hann); global = corrige la búsqueda entre frecuencias",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(rc.FIGURES_DIR / "figura_4_2b_espectros_anomalias_ar1.png")
    plt.close(fig)


def plot_normalized(series: pd.DataFrame) -> None:
    rc.apply_style()
    colors = {"P_local_mm": rc.COLOR_OLS, "P_IMERG_mm": rc.COLOR_SEN, "Caudal_m3s": rc.COLOR_LOESS,
              "Temp_C": "#9a6b00"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, tr, title in [(axes[0], "C", "Original centrada (C)"), (axes[1], "A", "Anomalía (A)")]:
        for col, meta in rc.VARIABLES.items():
            x = get(series, "comun", col, tr)["valor"].to_numpy(float)
            f, p = spectrum(x, "welch")
            ax.semilogy(f, p / np.var(x), color=colors[col], lw=1.8, label=meta["short"])
        mark_bands(ax)
        ax.set_xlim(0, 0.5)
        ax.set_xlabel("Frecuencia [ciclos/mes]")
        ax.set_ylabel("DEP / varianza [1/(ciclo/mes)]")
        ax.set_title(title, fontsize=9, pad=24)
        add_period_axis(ax)
        ax.legend(frameon=False, loc="upper right")
    fig.suptitle("Figura 4.2c. Forma espectral comparada en el periodo común 2001-04/2020-03 (Welch, Hann 120 meses, 50 %)\n"
                 "DEP normalizada por la varianza de cada serie: compara FORMAS, no variabilidad absoluta", fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_4_2c_espectros_normalizados.png")
    plt.close(fig)


def plot_stability(curves: dict) -> None:
    rc.apply_style()
    panels = [
        ("P_local_mm", ["A Hann 1980-2020", "A boxcar 1980-2020", "A Welch 120 m 1980-2020"], "P_L: estimador/ventana"),
        ("P_local_mm", ["A Hann 1980-2020", "A 1980-04/2000-03", "A 2000-04/2020-03"], "P_L: periodo de análisis"),
        ("Caudal_m3s", ["A Hann 1980-2020", "A continua sin relleno 1990-12/2014-11", "A Lomb-Scargle sin relleno 1980-2020"], "Q: tratamiento de vacíos"),
        ("Caudal_m3s", ["A Hann 1980-2020", "AD (sin tendencia) Hann", "A winsorizada p1-p99"], "Q: tendencia y extremos"),
    ]
    colors = [rc.COLOR_OLS, rc.COLOR_SEN, rc.COLOR_LOESS]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5))
    for ax, (col, configs, title) in zip(axes.ravel(), panels):
        for c, cfg in zip(colors, configs):
            f, p = curves[(col, cfg)]
            ax.semilogy(f, p, color=c, lw=1.3 if c != rc.COLOR_OLS else 1.0, label=cfg)
        mark_bands(ax)
        ax.set_xlim(0, 0.2)
        ax.set_xlabel("Frecuencia [ciclos/mes] (zoom f < 0.2)")
        ax.set_ylabel(f"DEP [({rc.VARIABLES[col]['unit']})²/(ciclo/mes)]")
        ax.set_title(title, fontsize=9, pad=24)
        add_period_axis(ax)
        ax.legend(frameon=False, fontsize=7, loc="upper right")
    fig.suptitle("Figura 4.2d. Estabilidad de los espectros de anomalías frente a ventana, periodo, vacíos, tendencia y extremos",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_4_2d_estabilidad.png")
    plt.close(fig)


def main() -> None:
    data = rc.load_master_data()
    series = pd.read_csv(SERIES_PATH)
    peaks, bands, persist, thr = analyse(series)
    peaks.to_csv(rc.FIGURES_DIR / "tabla_4_2_picos_espectrales.csv", index=False)
    bands.to_csv(rc.FIGURES_DIR / "tabla_4_2_fracciones_banda.csv", index=False)
    persist.to_csv(rc.FIGURES_DIR / "tabla_4_2_persistencia.csv", index=False)
    stab, curves = stability(series, data)
    stab.to_csv(rc.FIGURES_DIR / "tabla_4_2_estabilidad_picos.csv", index=False)
    plot_original(series)
    plot_anomalies(series, thr)
    plot_normalized(series)
    plot_stability(curves)

    pd.set_option("display.width", 250)
    print("Fracciones de varianza por banda (Hann):")
    print(bands.loc[bands["estimador"] == "hann"].drop(columns="estimador").round(3).to_string(index=False))
    print("\nPersistencia:")
    print(persist.round(3).to_string(index=False))
    print("\nPicos (Hann) en anomalías que superan el AR(1) 95 % puntual o global:")
    sel = peaks.loc[(peaks["estimador"] == "hann") & (peaks["transformacion"] != "C")
                    & (peaks["supera_AR1_95_puntual"] == True)]
    print(sel[["tramo", "variable", "transformacion", "periodo_meses", "periodo_min_meses", "periodo_max_meses",
               "ciclos_observados", "supera_AR1_95_puntual", "supera_AR1_95_global"]].round(2).to_string(index=False))
    print("\nPicos principales de C (Hann):")
    selc = peaks.loc[(peaks["estimador"] == "hann") & (peaks["transformacion"] == "C")]
    print(selc[["tramo", "variable", "periodo_meses", "ciclos_observados", "fraccion_varianza_bin"]].round(3).to_string(index=False))
    print("\nEstabilidad:")
    print(stab.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
