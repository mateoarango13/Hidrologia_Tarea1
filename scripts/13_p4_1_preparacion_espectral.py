"""
Punto 4.1 — Preparar las series y documentar el cálculo espectral (Rol C).

Decisiones (justificadas en el informe):
* Secuencia mensual cronológica (no las 12 medias climatológicas), Delta t = 1 mes.
* Tramos de AÑOS HIDROLÓGICOS COMPLETOS (abril-marzo) para que el ciclo anual
  quepa un número entero de veces en el registro (reduce la fuga del pico anual):
    - "completo": 1980-04 a 2020-03, N = 480 (40 ciclos anuales) -> P_L, Q y T (CR2MET).
    - "comun":    2001-04 a 2020-03, N = 228 (19 ciclos anuales) -> P_L, P_I, Q, T.
  Sensibilidad (en 14_p4_2): Q en el tramo continuo más largo sin vacíos (detectado automáticamente),
  mitades 1980-04/2000-03 y 2000-04/2020-03, y Lomb-Scargle sin rellenar.
* Vacíos de caudal (21 meses en el tramo completo tras el criterio de >= 80 % de días; 10 en el común):
  NO se eliminan ni se rellenan con ceros. Se rellenan interpolando
  linealmente la ANOMALÍA entre los meses válidos vecinos y sumando la
  climatología del mes (X = mu_j + a_interp). Cada valor rellenado queda marcado.
  Su efecto se evalúa en 14_p4_2 (tramo continuo y Lomb-Scargle).
* Transformaciones de cada serie:
    C  : original centrada, X - media del tramo (conserva el ciclo anual).
    A  : anomalía respecto a la climatología mensual fija 2000-06/2020-03,
         centrada en su media del tramo (la referencia no coincide con el
         tramo completo y su media residual contaminaría las bajas frecuencias).
    AD : A sin la tendencia lineal OLS del tramo (sensibilidad pedida en 4.1:
         la tendencia del punto 3 puede dominar las bajas frecuencias).

Salidas:
  figuras/serie_4_1_series_espectrales.csv
  figuras/tabla_4_1_documentacion_espectral.csv
  figuras/figura_4_1_series_preparadas.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import rol_c_comun as rc

SEGMENTS = {
    "completo": (pd.Timestamp("1980-04-01"), pd.Timestamp("2020-03-01"), ["P_local_mm", "Caudal_m3s", "Temp_C"]),
    "comun": (pd.Timestamp("2001-04-01"), pd.Timestamp("2020-03-01"), list(rc.VARIABLES)),
}
TRANSFORMS = {"C": "Original centrada", "A": "Anomalía (centrada)", "AD": "Anomalía sin tendencia lineal"}


def fill_gaps(seg: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Rellena vacíos interpolando la anomalía; devuelve (X_rellena, bandera)."""
    filled_flag = seg["X"].isna()
    if filled_flag.iloc[0] or filled_flag.iloc[-1]:
        raise ValueError("El tramo empieza o termina en un vacío; elegir otro tramo.")
    a_interp = seg["a"].interpolate(method="linear")
    mu = seg["X"] - seg["a"]                                  # mu_j donde hay dato
    mu = mu.fillna(seg["X_mu"])
    return (mu + a_interp).where(filled_flag, seg["X"]), filled_flag


def prepare(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    series_rows, doc_rows = [], []
    for seg_name, (start, end, variables) in SEGMENTS.items():
        for col in variables:
            anom = rc.add_anomalies(data, col)
            clim = rc.reference_climatology(data, col)
            seg = anom.loc[anom["date"].between(start, end)].copy().reset_index(drop=True)
            seg["X_mu"] = seg["month"].map(clim["mu"])
            x_full, flag = fill_gaps(seg)
            a_full = x_full - seg["X_mu"]
            n = len(seg)
            idx = np.arange(n, dtype=float)
            out = {"C": x_full - x_full.mean(), "A": a_full - a_full.mean()}
            coef = np.polyfit(idx, out["A"], 1)
            out["AD"] = out["A"] - np.polyval(coef, idx)
            for tr, values in out.items():
                series_rows.append(pd.DataFrame({
                    "tramo": seg_name, "variable": col, "transformacion": tr,
                    "date": seg["date"].dt.strftime("%Y-%m-%d"), "valor": values.to_numpy(),
                    "rellenado": flag.to_numpy()}))
            unit = rc.VARIABLES[col]["unit"]
            doc_rows.append({
                "tramo": seg_name, "variable": col, "unidad": unit,
                "inicio": start.strftime("%Y-%m"), "fin": end.strftime("%Y-%m"), "N_meses": n,
                "ciclos_anuales_en_tramo": n / 12, "dt_meses": 1, "delta_f_ciclos_mes": 1 / n,
                "f_min_ciclos_mes": 1 / n, "periodo_max_meses": n, "f_nyquist_ciclos_mes": 0.5,
                "periodo_min_meses": 2,
                "meses_rellenados": int(flag.sum()),
                "fechas_rellenadas": ";".join(seg.loc[flag, "date"].dt.strftime("%Y-%m")),
                "tendencia_retirada_AD_por_decada": coef[0] * 120,
                "varianza_C": out["C"].var(ddof=0), "varianza_A": out["A"].var(ddof=0),
                "fraccion_varianza_ciclo_anual": 1 - out["A"].var(ddof=0) / out["C"].var(ddof=0),
                "estimadores": "periodograma boxcar; periodograma Hann; Welch Hann 120 meses 50 %",
                "normalizacion": f"DEP unilateral [{unit}]^2/(ciclo/mes); sum(P)*df = varianza",
            })
    return pd.concat(series_rows, ignore_index=True), pd.DataFrame(doc_rows)


def plot_series(series: pd.DataFrame) -> None:
    rc.apply_style()
    combos = [("completo", "P_local_mm"), ("completo", "Caudal_m3s"),
              ("comun", "P_IMERG_mm"), ("completo", "Temp_C")]
    fig, axes = plt.subplots(4, 3, figsize=(13, 10), sharex="row")
    for i, (seg, col) in enumerate(combos):
        meta = rc.VARIABLES[col]
        for k, tr in enumerate(TRANSFORMS):
            ax = axes[i, k]
            s = series.loc[(series["tramo"] == seg) & (series["variable"] == col) & (series["transformacion"] == tr)]
            dates = pd.to_datetime(s["date"])
            ax.plot(dates, s["valor"], color=rc.COLOR_POINTS, lw=0.7)
            fl = s["rellenado"].to_numpy(bool)
            if fl.any():
                ax.plot(dates[fl], s["valor"][fl], "o", ms=3.5, color="#e34948", label="Rellenado (anomalía interpolada)")
                ax.legend(loc="upper right", frameon=False, fontsize=7)
            ax.axhline(0, color="#0b0b0b", lw=0.6)
            ax.set_ylabel(f"{meta['short']} [{meta['unit']}]")
            ax.set_title(f"{TRANSFORMS[tr]} — tramo {seg} (N={len(s)})", fontsize=8.5)
    fig.suptitle("Figura 4.1. Series preparadas para el análisis espectral (Δt = 1 mes, años hidrológicos completos)\n"
                 "C: original centrada; A: anomalía centrada; AD: anomalía sin tendencia lineal", fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_4_1_series_preparadas.png")
    plt.close(fig)


def main() -> None:
    data = rc.load_master_data()
    series, doc = prepare(data)
    series.to_csv(rc.FIGURES_DIR / "serie_4_1_series_espectrales.csv", index=False)
    doc.to_csv(rc.FIGURES_DIR / "tabla_4_1_documentacion_espectral.csv", index=False)
    plot_series(series)
    pd.set_option("display.width", 250)
    print(doc[["tramo", "variable", "inicio", "fin", "N_meses", "delta_f_ciclos_mes", "meses_rellenados",
               "fechas_rellenadas", "tendencia_retirada_AD_por_decada", "fraccion_varianza_ciclo_anual"]]
          .round(4).to_string(index=False))


if __name__ == "__main__":
    main()
