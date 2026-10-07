"""
Punto 5.4 — Interpretación física e integración.

Para no elegir regiones a partir de los propios mapas (sesgo de selección), se usan tres
índices definidos A PRIORI por mecanismo (cajas en p5_comun.BOXES), calculados de las
anomalías ERA5 ponderadas por cos(lat):
  * Niño 3.4 (SST, 5°S-5°N, 170°W-120°W): estado de ENSO (Trenberth, 1997).
  * PNM Pacífico SE (30-40°S, 75-90°W): intensidad del anticiclón/paso de sistemas frontales.
  * Z500 Chile central (30-40°S, 70-85°W): vaguadas y bajas segregadas en altura.

Preguntas que se responden:
  1. ¿Coinciden los meses de mayor asociación para P_L y Q? -> perfiles mensuales (ℓ = 0)
     con IC 95 % de Fisher usando n_eff.
  2. ¿Los patrones atmosféricos apoyan la explicación de la SST? -> correlación entre
     índices y correlación parcial de P_L con Niño 3.4 controlando la PNM local.
  3. ¿El rezago es compatible con los procesos? -> matriz de rezagos ℓ = 0..12 de Q y P_L
     frente a Niño 3.4, y Q de deshielo frente a la lluvia invernal previa.
  4. Estabilidad regional -> perfiles por subperiodo (1980-1999 vs 2000-2019).
  5. Relación con el punto 4 -> coherencia espectral (Welch, 120 meses) entre anomalías
     de la cuenca y Niño 3.4 en la banda interanual de 2-7 años.

Salidas:
  figuras/figura_5_4a_perfiles_indices.png
  figuras/figura_5_4b_rezagos_nino34.png
  figuras/figura_5_4c_subperiodos_parcial.png
  figuras/figura_5_4d_coherencia.png
  figuras/tabla_5_4_perfiles_indices.csv
  figuras/tabla_5_4_rezagos.csv
  figuras/tabla_5_4_dependencia_indices.csv
  figuras/tabla_5_4_coherencia.csv
  figuras/tabla_5_4_memoria_nival.csv
  figuras/serie_5_4_indices_climaticos.csv
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal, stats

import p5_comun as c

INDEX_COLORS = {"nino34": "#d97853", "pnm_sepac": "#2a78d6", "z500_chile": "#1baf7a"}
VAR_STYLE = {"P_local_mm": "-", "Caudal_m3s": "--"}


def corr_neff(x: np.ndarray, y: np.ndarray) -> dict:
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    r = float(np.corrcoef(x, y)[0, 1])
    r1x = float(np.corrcoef(x[1:], x[:-1])[0, 1])
    r1y = float(np.corrcoef(y[1:], y[:-1])[0, 1])
    prod = np.clip(r1x * r1y, -0.9, 0.9)
    ne = float(np.clip(n * (1 - prod) / (1 + prod), 4, n))
    t = r * np.sqrt((ne - 2) / max(1 - r ** 2, 1e-12))
    p = float(2 * stats.t.sf(abs(t), ne - 2))
    z, se = np.arctanh(r), 1 / np.sqrt(ne - 3)
    return {"r": r, "p": p, "n": n, "n_eff": ne, "ic_inf": float(np.tanh(z - 1.96 * se)),
            "ic_sup": float(np.tanh(z + 1.96 * se))}


def month_pairs(x: pd.Series, idx: pd.Series, month: int, lag: int = 0, years=None):
    s = x[x.index.month == month].dropna()
    if years:
        s = s[(s.index.year >= years[0]) & (s.index.year <= years[1])]
    d = s.index - pd.DateOffset(months=lag)
    keep = d.isin(idx.index)
    return s[keep].to_numpy(float), idx.loc[d[keep]].to_numpy(float)


def partial_corr(x, y, z):
    rxy, rxz, ryz = np.corrcoef(x, y)[0, 1], np.corrcoef(x, z)[0, 1], np.corrcoef(y, z)[0, 1]
    return (rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def main() -> None:
    fields, f_anom, b_anom, lat, lon = c.load_all()
    idx = {k: c.box_index(f_anom[b["field"]], b) for k, b in c.BOXES.items()}
    pd.DataFrame(idx).rename_axis("date").to_csv(c.FIGURES_DIR / "serie_5_4_indices_climaticos.csv")

    # 1. Perfiles mensuales y 4. subperiodos
    prof = []
    for var in ["P_local_mm", "Caudal_m3s"]:
        for k in idx:
            for period, yrs in [("1980-2020", None), ("1980-1999", (1980, 1999)), ("2000-2019", (2000, 2019))]:
                for m in range(1, 13):
                    x, y = month_pairs(b_anom[var], idx[k], m, years=yrs)
                    prof.append({"variable_cuenca": var, "indice": k, "periodo": period, "mes": m, **corr_neff(x, y)})
    prof = pd.DataFrame(prof)
    prof["q_fdr"] = np.nan
    full = prof["periodo"] == "1980-2020"
    from statsmodels.stats.multitest import multipletests
    prof.loc[full, "q_fdr"] = multipletests(prof.loc[full, "p"], method="fdr_bh")[1]
    prof.to_csv(c.FIGURES_DIR / "tabla_5_4_perfiles_indices.csv", index=False)

    # 3. Rezagos frente a Niño 3.4 y memoria nival
    lag_rows = []
    for var in ["P_local_mm", "Caudal_m3s"]:
        for m in range(1, 13):
            for lag in range(0, 13):
                x, y = month_pairs(b_anom[var], idx["nino34"], m, lag=lag)
                res = corr_neff(x, y)
                lag_rows.append({"variable_cuenca": var, "mes": m, "rezago": lag, "r": res["r"], "p": res["p"], "n": res["n"]})
    lags = pd.DataFrame(lag_rows)
    lags.to_csv(c.FIGURES_DIR / "tabla_5_4_rezagos.csv", index=False)

    # Q de deshielo frente a lluvia invernal (may-ago) del mismo año hidrológico
    pl = b_anom["P_local_mm"]
    winter = pl[pl.index.month.isin([5, 6, 7, 8])].groupby(pl[pl.index.month.isin([5, 6, 7, 8])].index.year).mean()
    nino_w = idx["nino34"][idx["nino34"].index.month.isin([5, 6, 7, 8])]
    nino_w = nino_w.groupby(nino_w.index.year).mean()
    memory = []
    for m in [10, 11, 12, 1, 2, 3]:
        q = b_anom["Caudal_m3s"][b_anom["Caudal_m3s"].index.month == m].dropna()
        yr = q.index.year - (1 if m <= 3 else 0)
        qq = pd.Series(q.to_numpy(), index=yr)
        common = qq.index.intersection(winter.index)
        rp = corr_neff(qq.loc[common].to_numpy(), winter.loc[common].to_numpy())
        common_n = qq.index.intersection(nino_w.index)
        rn = corr_neff(qq.loc[common_n].to_numpy(), nino_w.loc[common_n].to_numpy())
        memory.append({"mes_Q": m, "r_Q_vs_PL_may_ago": rp["r"], "p_PL": rp["p"],
                       "r_Q_vs_Nino34_may_ago": rn["r"], "p_Nino": rn["p"], "n": rp["n"]})
    memory = pd.DataFrame(memory)
    memory.to_csv(c.FIGURES_DIR / "tabla_5_4_memoria_nival.csv", index=False)

    # 2. Dependencia entre índices y correlación parcial
    dep = []
    for m in range(1, 13):
        sel = lambda s: s[s.index.month == m]
        a, b_, z = sel(idx["nino34"]), sel(idx["pnm_sepac"]), sel(idx["z500_chile"])
        x, n34 = month_pairs(b_anom["P_local_mm"], idx["nino34"], m)
        _, pnm = month_pairs(b_anom["P_local_mm"], idx["pnm_sepac"], m)
        dep.append({"mes": m,
                    "r_nino34_pnm": float(np.corrcoef(a, b_)[0, 1]),
                    "r_nino34_z500": float(np.corrcoef(a, z)[0, 1]),
                    "r_pnm_z500": float(np.corrcoef(b_, z)[0, 1]),
                    "r_PL_nino34": float(np.corrcoef(x, n34)[0, 1]),
                    "r_parcial_PL_nino34_dado_pnm": float(partial_corr(x, n34, pnm)),
                    "r_PL_pnm": float(np.corrcoef(x, pnm)[0, 1]),
                    "r_parcial_PL_pnm_dado_nino34": float(partial_corr(x, pnm, n34))})
    dep = pd.DataFrame(dep)
    dep.to_csv(c.FIGURES_DIR / "tabla_5_4_dependencia_indices.csv", index=False)

    # 5. Coherencia espectral con Niño 3.4 (anomalías mensuales, 1980-04 a 2020-03)
    coh_rows, coh_curves = [], {}
    span = slice("1980-04-01", "2020-03-01")
    n34_series = idx["nino34"].loc[span]
    for var in ["P_local_mm", "Caudal_m3s"]:
        s = b_anom[var].loc[span]
        s = s.interpolate(limit=8) if s.isna().any() else s   # mismos 14 vacíos de Q que en el punto 4
        f, cxy = signal.coherence(s.to_numpy(), n34_series.to_numpy(), fs=1.0, window="hann",
                                  nperseg=120, noverlap=60)
        coh_curves[var] = (f, cxy)
        band = (f >= 1 / 84) & (f <= 1 / 24)
        k = 480 // 60 - 1   # número de segmentos Welch con 50 % de solapamiento
        thr = 1 - 0.05 ** (1 / (k - 1))  # umbral 95 % de coherencia nula (aprox., segmentos independientes)
        coh_rows.append({"variable_cuenca": var, "coherencia_media_2_7_anios": float(cxy[band].mean()),
                         "coherencia_max_2_7_anios": float(cxy[band].max()),
                         "periodo_max_anios": float(1 / f[band][np.argmax(cxy[band])] / 12),
                         "umbral_95_aprox": thr, "segmentos": k})
    coh = pd.DataFrame(coh_rows)
    coh.to_csv(c.FIGURES_DIR / "tabla_5_4_coherencia.csv", index=False)

    # ----------------------------- Figuras -----------------------------
    plt.rcParams.update({"font.size": 9, "savefig.dpi": c.DPI, "savefig.bbox": "tight",
                         "axes.spines.top": False, "axes.spines.right": False})
    # (a) Perfiles mensuales
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, k in zip(axes, idx):
        for j, var in enumerate(["P_local_mm", "Caudal_m3s"]):
            d = prof[(prof["variable_cuenca"] == var) & (prof["indice"] == k) & full]
            x = np.arange(1, 13) + (-0.12 if j == 0 else 0.12)
            ax.vlines(x, d["ic_inf"], d["ic_sup"], color=INDEX_COLORS[k], alpha=0.5, lw=2)
            sig = d["q_fdr"].to_numpy() < 0.05
            ax.plot(x, d["r"], VAR_STYLE[var], color=INDEX_COLORS[k], lw=1.6)
            ax.plot(x[sig], d["r"].to_numpy()[sig], "o", color=INDEX_COLORS[k], ms=7, mec="white")
            ax.plot(x[~sig], d["r"].to_numpy()[~sig], "o", mfc="white", mec=INDEX_COLORS[k], ms=7, mew=1.5)
        ax.axhline(0, color="#111111", lw=0.7)
        ax.set_xticks(range(1, 13), [m[0] for m in c.MONTHS])
        ax.set_title(c.BOXES[k]["label"], fontsize=9)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("r (mismo mes calendario, ℓ = 0) · IC 95 % con n_eff")
    axes[0].plot([], [], "-", color="#555", label="P_L (línea continua)")
    axes[0].plot([], [], "--", color="#555", label="Q (línea discontinua)")
    axes[0].plot([], [], "o", color="#555", label="q_FDR < 0.05")
    axes[0].plot([], [], "o", mfc="white", mec="#555", label="q_FDR ≥ 0.05")
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("Figura 5.4a. Correlación mensual de la cuenca con índices definidos a priori (1980–2020). "
                 "FDR sobre 72 pruebas (2 variables × 3 índices × 12 meses)", fontsize=10)
    fig.tight_layout()
    fig.savefig(c.FIGURES_DIR / "figura_5_4a_perfiles_indices.png")
    plt.close(fig)

    # (b) Matriz de rezagos con Niño 3.4 + memoria nival
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), gridspec_kw={"width_ratios": [1, 1, 0.8]})
    for ax, var in zip(axes[:2], ["P_local_mm", "Caudal_m3s"]):
        piv = lags[lags["variable_cuenca"] == var].pivot(index="rezago", columns="mes", values="r")
        im = ax.imshow(piv.to_numpy(), cmap="RdBu_r", vmin=-0.7, vmax=0.7, aspect="auto", origin="lower")
        for (yy, xx), v in np.ndenumerate(piv.to_numpy()):
            ax.text(xx, yy, f"{v:.2f}", ha="center", va="center", fontsize=5.5)
        ax.set_xticks(range(12), [m[0] for m in c.MONTHS])
        ax.set_yticks(range(13))
        ax.set_xlabel(f"Mes calendario de {c.BASIN_VARS[var]['plain']}")
        ax.set_ylabel("Rezago ℓ (meses que Niño 3.4 antecede)")
        ax.set_title(f"{c.BASIN_VARS[var]['long']} vs Niño 3.4", fontsize=9)
        ax.grid(False)
    fig.colorbar(im, ax=axes[:2], shrink=0.8, label="r")
    labels = [c.MONTHS[m - 1] for m in memory["mes_Q"]]
    xx = np.arange(len(labels))
    axes[2].bar(xx - 0.2, memory["r_Q_vs_PL_may_ago"], 0.4, color="#56a9ba", label="P_L may–ago previo")
    axes[2].bar(xx + 0.2, memory["r_Q_vs_Nino34_may_ago"], 0.4, color="#d97853", label="Niño 3.4 may–ago previo")
    axes[2].set_xticks(xx, labels)
    axes[2].set_ylim(0, 1)
    axes[2].set_ylabel("r con Q del mes")
    axes[2].set_title("Q de deshielo frente al invierno previo", fontsize=9)
    axes[2].legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1)
    fig.suptitle("Figura 5.4b. Rezagos: ℓ > 0 = el índice antecede a la cuenca (enero con ℓ = 1 usa diciembre del año anterior)",
                 fontsize=10)
    fig.savefig(c.FIGURES_DIR / "figura_5_4b_rezagos_nino34.png")
    plt.close(fig)

    # (c) Subperiodos y correlación parcial
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.0))
    for ax, (var, k) in zip(axes[:2], [("P_local_mm", "pnm_sepac"), ("Caudal_m3s", "nino34")]):
        for period, style in [("1980-1999", "o-"), ("2000-2019", "s--"), ("1980-2020", "-")]:
            d = prof[(prof["variable_cuenca"] == var) & (prof["indice"] == k) & (prof["periodo"] == period)]
            ax.plot(d["mes"], d["r"], style, color="#111111" if period == "1980-2020" else INDEX_COLORS[k],
                    alpha=1 if period != "1980-2020" else 0.5, lw=1.4, ms=5, label=period)
        ax.axhline(0, color="#111111", lw=0.6)
        ax.set_xticks(range(1, 13), [m[0] for m in c.MONTHS])
        ax.set_title(f"{c.BASIN_VARS[var]['plain']} vs {c.BOXES[k]['label']}", fontsize=9)
        ax.set_ylabel("r")
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=0.3)
    ax = axes[2]
    ax.plot(dep["mes"], dep["r_PL_nino34"], "o-", color="#d97853", label="r(P_L, Niño 3.4)")
    ax.plot(dep["mes"], dep["r_parcial_PL_nino34_dado_pnm"], "o--", color="#d97853", mfc="white",
            label="parcial dado PNM SE")
    ax.plot(dep["mes"], dep["r_PL_pnm"], "s-", color="#2a78d6", label="r(P_L, PNM SE)")
    ax.plot(dep["mes"], dep["r_parcial_PL_pnm_dado_nino34"], "s--", color="#2a78d6", mfc="white",
            label="parcial dado Niño 3.4")
    ax.axhline(0, color="#111111", lw=0.6)
    ax.set_xticks(range(1, 13), [m[0] for m in c.MONTHS])
    ax.set_title("Dependencia entre campos: correlación parcial de P_L", fontsize=9)
    ax.legend(frameon=False, fontsize=7)
    ax.grid(alpha=0.3)
    fig.suptitle("Figura 5.4c. Estabilidad regional por subperiodo y dependencia entre SST y circulación local",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(c.FIGURES_DIR / "figura_5_4c_subperiodos_parcial.png")
    plt.close(fig)

    # (d) Coherencia con Niño 3.4
    fig, ax = plt.subplots(figsize=(8, 4))
    for var, color in [("P_local_mm", "#56a9ba"), ("Caudal_m3s", "#d97853")]:
        f, cxy = coh_curves[var]
        ax.plot(f[1:], cxy[1:], color=color, lw=2, label=c.BASIN_VARS[var]["plain"])
    ax.axhline(coh["umbral_95_aprox"].iloc[0], color="#555", ls=":", label="umbral 95 % aprox. (coherencia nula)")
    ax.axvspan(1 / 84, 1 / 24, color="#9a9994", alpha=0.15, lw=0, label="banda 2–7 años")
    ax.set_xlim(0, 0.2)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Frecuencia [ciclos/mes]")
    ax.set_ylabel("Coherencia cuadrática")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_title("Figura 5.4d. Coherencia de las anomalías de la cuenca con Niño 3.4 (Welch, Hann 120 meses, 1980–2020)",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(c.FIGURES_DIR / "figura_5_4d_coherencia.png")
    plt.close(fig)

    pd.set_option("display.width", 250)
    print(prof[full].pivot_table(index="mes", columns=["variable_cuenca", "indice"], values="r").round(2).to_string())
    print("\nq FDR < 0.05:")
    print(prof[full & (prof["q_fdr"] < 0.05)][["variable_cuenca", "indice", "mes", "r", "ic_inf", "ic_sup", "q_fdr"]].round(3).to_string(index=False))
    print("\nSubperiodos (P_L-PNM y Q-Niño34):")
    sub = prof[((prof["variable_cuenca"] == "P_local_mm") & (prof["indice"] == "pnm_sepac")) |
               ((prof["variable_cuenca"] == "Caudal_m3s") & (prof["indice"] == "nino34"))]
    print(sub.pivot_table(index="mes", columns=["variable_cuenca", "periodo"], values="r").round(2).to_string())
    print("\nMemoria nival:"); print(memory.round(3).to_string(index=False))
    print("\nDependencia:"); print(dep.round(2).to_string(index=False))
    print("\nCoherencia:"); print(coh.round(3).to_string(index=False))
    best = lags.loc[lags.groupby(["variable_cuenca", "mes"])["r"].idxmax()]
    print("\nRezago de máxima r por mes:"); print(best.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
