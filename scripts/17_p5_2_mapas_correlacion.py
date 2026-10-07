"""
Punto 5.2 — Definir y calcular los mapas mensuales de correlación.

r_j(λ, φ; ℓ) = corr_{t: j(t) = j}[ a_X(t), a_Y(λ, φ, t - ℓ) ]
  * j: mes calendario de la RESPUESTA de la cuenca; la correlación es a través de los años
    (todos los eneros de la cuenca con todos los eneros del campo en esa celda).
  * a_X, a_Y: anomalías por mes calendario y celda con la referencia fija 2000-06/2020-03.
    Para un mes fijo y la misma muestra, centrar no cambia Pearson (los mapas de X y de
    a son idénticos), por lo que se presenta una sola versión.
  * Base: P_L y Q frente a SST, PNM y Z500, sin rezago (ℓ = 0) -> 6 juegos de 12 mapas.
  * Rezago justificado: Q frente a SST con ℓ = 6 meses (el caudal de deshielo responde a la
    nieve acumulada en el invierno anterior; puntos 1 y 2: desfase de 6-7 meses).
    Con esta convención ℓ > 0 = el campo antecede; enero con ℓ = 6 usa julio del año anterior.
  * Pearson como referencia; Spearman para P_L-SST y Q-SST (asimetría de la lluvia).

Salidas:
  figuras/figura_5_2a ... 5_2f  (12 mapas por combinación, ℓ = 0)
  figuras/figura_5_2g_q_sst_rezago6.png
  figuras/figura_5_2h_pearson_vs_spearman.png
  figuras/tabla_5_2_resumen_mapas.csv
  figuras/tabla_5_2_pearson_vs_spearman.csv
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import p5_comun as c

COMBOS = [("P_local_mm", "sst"), ("P_local_mm", "msl"), ("P_local_mm", "z500"),
          ("Caudal_m3s", "sst"), ("Caudal_m3s", "msl"), ("Caudal_m3s", "z500")]
LETTERS = "abcdef"


def box_mean(r, lat, lon, box):
    la = (lat >= box["lat"][0]) & (lat <= box["lat"][1])
    lo = (lon >= box["lon"][0]) & (lon <= box["lon"][1])
    w = np.cos(np.deg2rad(lat[la]))[:, None] * np.ones(lo.sum())
    sub = r[np.ix_(la, lo)]
    ok = np.isfinite(sub)
    return float(np.sum(sub[ok] * w[ok]) / np.sum(w[ok])) if ok.any() else np.nan


def summarize(maps, var, field, lag, lat, lon, method="pearson"):
    rows = []
    pac = c.PACIFIC
    la = (lat >= pac["lat"][0]) & (lat <= pac["lat"][1])
    lo = (lon >= pac["lon"][0]) & (lon <= pac["lon"][1])
    for res in maps:
        r = res["r"]
        sub = np.where(np.outer(la, lo), r, np.nan)
        j, i = np.unravel_index(np.nanargmax(np.abs(sub)), r.shape)
        valid = np.isfinite(r)
        rows.append({
            "variable_cuenca": var, "campo": field, "rezago_meses": lag, "metodo": method, "mes": res["month"],
            "anios": f"{res['years'][0]}-{res['years'][1]}", "n_pares": res["n_pairs"],
            "r_max_abs_pacifico": round(float(r[j, i]), 3), "lat_max": float(lat[j]), "lon_max_0_360": float(lon[i]),
            "fraccion_area_abs_r_mayor_0.4": round(c.area_fraction(np.abs(np.nan_to_num(r)) > 0.4, valid, lat), 3),
            "fraccion_area_signif_fdr": round(c.area_fraction(res["sig"], valid, lat), 4),
            **{f"r_media_{k}": round(box_mean(r, lat, lon, b), 3) for k, b in c.BOXES.items() if b["field"] == field},
        })
    return rows


def plot_twelve(maps, lat, lon, title, path, note=""):
    plt.rcParams.update({"font.size": 8, "savefig.dpi": c.DPI, "savefig.bbox": "tight"})
    fig, axes = plt.subplots(4, 3, figsize=(12, 7.2))
    for ax, res in zip(axes.ravel(), maps):
        mesh = c.draw_map(ax, lon, lat, res["r"], vmin=-1, vmax=1,
                          title=f"{c.MONTHS[res['month'] - 1]} · n={res['n_pairs']} ({res['years'][0]}–{res['years'][1]})")
    cbar = fig.colorbar(mesh, ax=axes, orientation="horizontal", shrink=0.5, pad=0.03, aspect=40)
    cbar.set_label("Correlación de Pearson r (anomalías del mismo mes calendario a través de los años)")
    fig.suptitle(title + ("\n" + note if note else ""), fontsize=10, y=0.995)
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    fields, f_anom, b_anom, lat, lon = c.load_all()
    rows = []
    for letter, (var, field) in zip(LETTERS, COMBOS):
        maps = c.monthly_maps(b_anom[var], f_anom[field], lag=0)
        rows += summarize(maps, var, field, 0, lat, lon)
        meta_v, meta_f = c.BASIN_VARS[var], c.FIELDS[field]
        plot_twelve(maps, lat, lon,
                    f"Figura 5.2{letter}. {meta_v['long']} ({meta_v['plain']}) frente a {meta_f['long'].lower()} "
                    f"({meta_f['label']}) · rezago ℓ = 0 · ERA5 1°",
                    c.FIGURES_DIR / f"figura_5_2{letter}_{meta_v['plain'].lower()}_{field}.png",
                    "Mes = mes calendario de la cuenca; escala común −1 a 1; blanco: tierra o hielo marino (SST) o pares insuficientes; estrella: cuenca")

    # Rezago justificado: caudal frente a SST seis meses antes.
    maps_lag = c.monthly_maps(b_anom["Caudal_m3s"], f_anom["sst"], lag=6)
    rows += summarize(maps_lag, "Caudal_m3s", "sst", 6, lat, lon)
    plot_twelve(maps_lag, lat, lon,
                "Figura 5.2g. Caudal (Q) del mes indicado frente a la SST seis meses antes · rezago ℓ = 6",
                c.FIGURES_DIR / "figura_5_2g_q_sst_rezago6.png",
                "ℓ > 0: el campo antecede a la cuenca (diciembre de Q con junio de SST; enero con julio del año anterior)")

    # Pearson frente a Spearman.
    comp_rows = []
    fig, axes = plt.subplots(2, 3, figsize=(12, 4.6))
    for k, (var, month) in enumerate([("P_local_mm", 7), ("Caudal_m3s", 12)]):
        mp = c.monthly_maps(b_anom[var], f_anom["sst"])
        ms = c.monthly_maps(b_anom[var], f_anom["sst"], method="spearman")
        rows += summarize(ms, var, "sst", 0, lat, lon, method="spearman")
        for a, b in zip(mp, ms):
            d = b["r"] - a["r"]
            comp_rows.append({"variable_cuenca": var, "mes": a["month"],
                              "mediana_abs_dif": round(float(np.nanmedian(np.abs(d))), 3),
                              "p95_abs_dif": round(float(np.nanpercentile(np.abs(d), 95)), 3),
                              "corr_patron_pacifico": round(c.pattern_correlation(a["r"], b["r"], lat, c.PACIFIC, lon), 3)})
        a, b = mp[month - 1], ms[month - 1]
        name = c.BASIN_VARS[var]["plain"]
        c.draw_map(axes[k, 0], lon, lat, a["r"], title=f"{name} · {c.MONTHS[month - 1]} · Pearson")
        m2 = c.draw_map(axes[k, 1], lon, lat, b["r"], title=f"{name} · {c.MONTHS[month - 1]} · Spearman")
        m3 = c.draw_map(axes[k, 2], lon, lat, b["r"] - a["r"], vmin=-0.3, vmax=0.3, cmap="PuOr_r",
                        title="Spearman − Pearson")
    fig.colorbar(m2, ax=axes[:, :2], orientation="horizontal", shrink=0.6, pad=0.04, label="r")
    fig.colorbar(m3, ax=axes[:, 2], orientation="horizontal", shrink=0.9, pad=0.04, label="Δr")
    fig.suptitle("Figura 5.2h. Sensibilidad al coeficiente: Pearson frente a Spearman (SST, ℓ = 0)", fontsize=10)
    fig.savefig(c.FIGURES_DIR / "figura_5_2h_pearson_vs_spearman.png", dpi=c.DPI, bbox_inches="tight")
    plt.close(fig)

    summary = pd.DataFrame(rows)
    summary.to_csv(c.FIGURES_DIR / "tabla_5_2_resumen_mapas.csv", index=False)
    comp = pd.DataFrame(comp_rows)
    comp.to_csv(c.FIGURES_DIR / "tabla_5_2_pearson_vs_spearman.csv", index=False)

    pd.set_option("display.width", 250)
    base = summary[summary["metodo"] == "pearson"]
    print(base.drop(columns=["metodo"]).to_string(index=False))
    print("\nPearson vs Spearman:")
    print(comp.to_string(index=False))


if __name__ == "__main__":
    main()
