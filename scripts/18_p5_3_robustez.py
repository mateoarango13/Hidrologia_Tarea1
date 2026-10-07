"""
Punto 5.3 — Robustez y presentación de los patrones.

1. Significancia: prueba t con tamaño de muestra efectivo por celda
   n_eff = n (1 - r1x r1y)/(1 + r1x r1y) (Bretherton et al., 1999), con r1 la
   autocorrelación entre años consecutivos de la subserie del mes (dependencia relevante
   para un mapa de un mes calendario). Familia de pruebas = las celdas válidas de UN mapa;
   control FDR de Benjamini-Hochberg con α_FDR = 0.10 (Wilks, 2016). Punteado = celdas
   significativas tras FDR. Mínimo de años por celda: 15; celdas con algún año
   enmascarado (tierra/hielo) se excluyen.
2. Tendencias: se comparan los mapas de anomalías con los de anomalías sin tendencia lineal
   (en el año, por mes calendario y por celda, en ambas series).
3. Estabilidad: (a) subperiodos 1980-1999 vs 2000-2019; (b) P_L vs IMERG con los mismos
   meses (2000-2020); (c) sin los 3 años de mayor |anomalía| de la cuenca en cada mes.
   Métrica: correlación espacial de patrones en el Pacífico (60°S-60°N, 120°E-60°W),
   ponderada por cos(lat).
4. Complemento: mapa con todos los meses juntos usando anomalías (n ≈ 480), con n_eff
   a partir de la autocorrelación mensual de rezago 1.

Salidas:
  figuras/figura_5_3a_significancia_fdr.png
  figuras/figura_5_3b_tendencia.png
  figuras/figura_5_3c_estabilidad.png
  figuras/figura_5_3d_todos_los_meses.png
  figuras/tabla_5_3_robustez.csv
  figuras/tabla_5_3_tamano_muestra.csv
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import p5_comun as c

COMBOS = [("P_local_mm", "sst"), ("P_local_mm", "msl"), ("P_local_mm", "z500"),
          ("Caudal_m3s", "sst"), ("Caudal_m3s", "msl"), ("Caudal_m3s", "z500")]
KEY = [("P_local_mm", 7), ("P_local_mm", 10), ("Caudal_m3s", 9), ("Caudal_m3s", 12)]


def without_extremes(x_anom, f_anom, n_drop=3):
    out = []
    for month in range(1, 13):
        x, Y, yrs = c.paired_samples(x_anom, f_anom, month)
        drop = np.argsort(np.abs(x))[-n_drop:]
        keep = np.setdiff1d(np.arange(len(x)), drop)
        res = c.correlation_map(x[keep], Y[keep])
        res.update({"month": month, "dropped": sorted(yrs[drop].tolist())})
        out.append(res)
    return out


def all_months_map(x_anom, f_anom):
    s = x_anom.dropna()
    dates = s.index[s.index.isin(pd.DatetimeIndex(f_anom["time"].values))]
    x = s.loc[dates].to_numpy(float)
    Y = f_anom.sel(time=dates).values
    return c.correlation_map(x, Y), len(x)


def main() -> None:
    fields, f_anom, b_anom, lat, lon = c.load_all()
    b_pl_common = b_anom["P_local_mm"].where(b_anom["P_IMERG_mm"].notna())
    base, rows, size_rows = {}, [], []

    for var, field in COMBOS:
        raw = c.monthly_maps(b_anom[var], f_anom[field])
        det = c.monthly_maps(b_anom[var], f_anom[field], detrend=True)
        p1 = c.monthly_maps(b_anom[var], f_anom[field], years=(1980, 1999))
        p2 = c.monthly_maps(b_anom[var], f_anom[field], years=(2000, 2019))
        ext = without_extremes(b_anom[var], f_anom[field])
        if var == "P_local_mm":
            pl_c = c.monthly_maps(b_pl_common, f_anom[field])
            pi_c = c.monthly_maps(b_anom["P_IMERG_mm"], f_anom[field])
        base[(var, field)] = {"raw": raw, "det": det}
        for k in range(12):
            valid = np.isfinite(raw[k]["r"])
            pc = lambda a, b: round(c.pattern_correlation(a, b, lat, c.PACIFIC, lon), 3)
            row = {
                "variable_cuenca": var, "campo": field, "mes": k + 1, "n_pares": raw[k]["n_pairs"],
                "area_signif_fdr": round(c.area_fraction(raw[k]["sig"], valid, lat), 4),
                "area_signif_fdr_sin_tendencia": round(c.area_fraction(det[k]["sig"], np.isfinite(det[k]["r"]), lat), 4),
                "patron_anomalia_vs_sin_tendencia": pc(raw[k]["r"], det[k]["r"]),
                "patron_1980_1999_vs_2000_2019": pc(p1[k]["r"], p2[k]["r"]),
                "patron_completo_vs_sin_3_extremos": pc(raw[k]["r"], ext[k]["r"]),
                "anios_extremos_retirados": ";".join(map(str, ext[k]["dropped"])),
            }
            if var == "P_local_mm":
                row["patron_PL_vs_IMERG_2000_2020"] = pc(pl_c[k]["r"], pi_c[k]["r"])
                row["n_pares_IMERG"] = pi_c[k]["n_pairs"]
            for key, box in c.BOXES.items():
                if box["field"] == field:
                    la = (lat >= box["lat"][0]) & (lat <= box["lat"][1])
                    lo = (lon >= box["lon"][0]) & (lon <= box["lon"][1])
                    row[f"r_{key}_anomalia"] = round(float(np.nanmean(raw[k]["r"][np.ix_(la, lo)])), 3)
                    row[f"r_{key}_sin_tendencia"] = round(float(np.nanmean(det[k]["r"][np.ix_(la, lo)])), 3)
            rows.append(row)
            ne = raw[k]["n_eff"][valid]
            size_rows.append({"variable_cuenca": var, "campo": field, "mes": k + 1, "n_pares": raw[k]["n_pairs"],
                              "celdas_validas": int(valid.sum()),
                              "n_eff_mediana": round(float(np.median(ne)), 1),
                              "n_eff_p10": round(float(np.percentile(ne, 10)), 1),
                              "n_eff_min": round(float(ne.min()), 1)})
    table = pd.DataFrame(rows)
    table.to_csv(c.FIGURES_DIR / "tabla_5_3_robustez.csv", index=False)
    pd.DataFrame(size_rows).to_csv(c.FIGURES_DIR / "tabla_5_3_tamano_muestra.csv", index=False)

    plt.rcParams.update({"font.size": 8, "savefig.dpi": c.DPI, "savefig.bbox": "tight"})
    # (a) Significancia FDR en meses clave
    fig, axes = plt.subplots(4, 3, figsize=(12, 7.4))
    for i, (var, month) in enumerate(KEY):
        for j, field in enumerate(["sst", "msl", "z500"]):
            res = base[(var, field)]["raw"][month - 1]
            frac = c.area_fraction(res["sig"], np.isfinite(res["r"]), lat)
            mesh = c.draw_map(axes[i, j], lon, lat, res["r"], sig=res["sig"],
                              title=f"{c.BASIN_VARS[var]['plain']} {c.MONTHS[month - 1]} vs {c.FIELDS[field]['label']} · área FDR {100 * frac:.0f} %")
    fig.colorbar(mesh, ax=axes, orientation="horizontal", shrink=0.5, pad=0.03, aspect=40, label="r de Pearson")
    fig.suptitle("Figura 5.3a. Meses clave con significancia: punteado = celdas significativas tras FDR (α_FDR = 0.10, "
                 "familia = celdas de cada mapa;\nprueba t con n_eff por persistencia interanual). Un píxel aislado no constituye un patrón",
                 fontsize=10, y=0.995)
    fig.savefig(c.FIGURES_DIR / "figura_5_3a_significancia_fdr.png")
    plt.close(fig)

    # (b) Con y sin tendencia
    fig, axes = plt.subplots(3, 3, figsize=(12, 5.8))
    for i, (var, field, month) in enumerate([("Caudal_m3s", "sst", 9), ("Caudal_m3s", "sst", 12), ("P_local_mm", "msl", 7)]):
        a = base[(var, field)]["raw"][month - 1]
        d = base[(var, field)]["det"][month - 1]
        name = f"{c.BASIN_VARS[var]['plain']} {c.MONTHS[month - 1]} vs {c.FIELDS[field]['label']}"
        c.draw_map(axes[i, 0], lon, lat, a["r"], sig=a["sig"], title=f"{name}: anomalías")
        m1 = c.draw_map(axes[i, 1], lon, lat, d["r"], sig=d["sig"], title=f"{name}: sin tendencia")
        m2 = c.draw_map(axes[i, 2], lon, lat, d["r"] - a["r"], vmin=-0.4, vmax=0.4, cmap="PuOr_r",
                        title="Diferencia (sin tendencia − anomalías)")
    fig.colorbar(m1, ax=axes[:, :2], orientation="horizontal", shrink=0.6, pad=0.04, label="r")
    fig.colorbar(m2, ax=axes[:, 2], orientation="horizontal", shrink=0.9, pad=0.04, label="Δr")
    fig.suptitle("Figura 5.3b. Sensibilidad a la tendencia: se retira la tendencia lineal (por mes calendario y celda) "
                 "de la cuenca y del campo", fontsize=10)
    fig.savefig(c.FIGURES_DIR / "figura_5_3b_tendencia.png")
    plt.close(fig)

    # (c) Estabilidad de patrones: mapas de calor combinación x mes
    tests = [("patron_anomalia_vs_sin_tendencia", "Anomalías vs sin tendencia"),
             ("patron_1980_1999_vs_2000_2019", "1980–1999 vs 2000–2019"),
             ("patron_completo_vs_sin_3_extremos", "Completo vs sin 3 años extremos"),
             ("patron_PL_vs_IMERG_2000_2020", "P_L vs IMERG (2000–2020)")]
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8))
    full_index = pd.MultiIndex.from_tuples(COMBOS, names=["variable_cuenca", "campo"])
    labels = [f"{c.BASIN_VARS[v]['plain']}–{c.FIELDS[f]['label']}" for v, f in COMBOS]
    for k, (ax, (col, title)) in enumerate(zip(axes, tests)):
        piv = table.pivot_table(index=["variable_cuenca", "campo"], columns="mes", values=col).reindex(full_index)
        vals = piv.to_numpy(dtype=float)
        im = ax.imshow(np.ma.masked_invalid(vals), cmap="viridis", vmin=-0.2, vmax=1, aspect="auto")
        ax.set_xticks(range(12), [m[0] for m in c.MONTHS])
        ax.set_yticks(range(len(labels)), labels if k == 0 else [""] * len(labels))
        for (yy, xx), v in np.ndenumerate(vals):
            if np.isfinite(v):
                ax.text(xx, yy, f"{v:.1f}", ha="center", va="center", fontsize=6,
                        color="white" if v < 0.5 else "#111111")
            elif xx == 5:
                ax.text(xx, yy, "no aplica", ha="center", va="center", fontsize=6, color="#777777")
        ax.set_title(title, fontsize=9)
        ax.grid(False)
    fig.colorbar(im, ax=axes, shrink=0.8, label="Correlación espacial de patrones (Pacífico)")
    fig.suptitle("Figura 5.3c. Estabilidad de los patrones de correlación: 1 = mismo patrón; ≤ 0.3 = patrón no reproducible",
                 fontsize=10)
    fig.savefig(c.FIGURES_DIR / "figura_5_3c_estabilidad.png")
    plt.close(fig)

    # (d) Todos los meses juntos con anomalías
    fig, axes = plt.subplots(2, 3, figsize=(12, 4.6))
    for i, var in enumerate(["P_local_mm", "Caudal_m3s"]):
        for j, field in enumerate(["sst", "msl", "z500"]):
            res, n = all_months_map(b_anom[var], f_anom[field])
            sig = c.fdr_mask(res["p"])
            mesh = c.draw_map(axes[i, j], lon, lat, res["r"], sig=sig, vmin=-0.6, vmax=0.6,
                              title=f"{c.BASIN_VARS[var]['plain']} vs {c.FIELDS[field]['label']} · todos los meses (n={n})")
    fig.colorbar(mesh, ax=axes, orientation="horizontal", shrink=0.5, pad=0.04, label="r (escala ±0.6)")
    fig.suptitle("Figura 5.3d. Complemento: anomalías de todos los meses juntos (evita la asociación por ciclo anual); "
                 "n_eff por autocorrelación mensual; punteado FDR", fontsize=10)
    fig.savefig(c.FIGURES_DIR / "figura_5_3d_todos_los_meses.png")
    plt.close(fig)

    pd.set_option("display.width", 250)
    agg = table.groupby(["variable_cuenca", "campo"]).agg(
        area_fdr_media=("area_signif_fdr", "mean"), area_fdr_max=("area_signif_fdr", "max"),
        area_fdr_sin_tend=("area_signif_fdr_sin_tendencia", "mean"),
        patron_tend=("patron_anomalia_vs_sin_tendencia", "median"),
        patron_subper=("patron_1980_1999_vs_2000_2019", "median"),
        patron_extremos=("patron_completo_vs_sin_3_extremos", "median"),
        patron_imerg=("patron_PL_vs_IMERG_2000_2020", "median"))
    print(agg.round(3).to_string())
    cols = [c_ for c_ in table.columns if c_.startswith("r_")]
    print(table[["variable_cuenca", "campo", "mes"] + cols].round(2).to_string(index=False))
    print(pd.DataFrame(size_rows).groupby(["variable_cuenca"])[["n_eff_mediana", "n_eff_p10"]].median())


if __name__ == "__main__":
    main()
