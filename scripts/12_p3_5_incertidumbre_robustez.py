"""
Punto 3.5 — Incertidumbre, robustez y presentación (Rol C).

Requiere haber ejecutado 11_p3_4_metodos_tendencia.py (lee sus tablas).

1. Tabla comparativa por método con pendientes por DÉCADA y unidades explícitas.
   En precipitación es el cambio del ACUMULADO MENSUAL (mm/mes por década), no
   del total anual.
2. Nivel de significancia fijado: alpha = 0.05. Comparaciones múltiples con
   Benjamini-Hochberg (FDR), definiendo dos familias:
     F1 (mes a mes): 12 meses x 4 variables = 48 pruebas, por método
         (OLS-HAC y Mann-Kendall con Hamed-Rao). Solo se usa la serie original:
         a y z dan el MISMO valor p mes a mes (invarianza verificada en 3.3), así
         que no son pruebas independientes.
     F2 (global): 4 variables x 3 pruebas (OLS-HAC sobre a, MK-HR sobre a,
         Kendall estacional con bootstrap sobre X) = 12 pruebas.
3. Gráfico de pendientes e IC para los doce meses.
4. Sensibilidad con series de años hidrológicos (abril-marzo) de anomalías:
     - fecha inicial y final (todas las ventanas de >= 15 años; >= 10 en P_I y T);
     - años extremos (retirar los 3 años hidrológicos más húmedos);
     - periodo completo vs periodo común 2000-2020;
     - salto vs tendencia gradual: prueba de Pettitt y comparación AIC de
       modelos (nivel constante, tendencia lineal, escalón, escalón + tendencia);
     - ancho de ventana LOESS (6, 10 y 20 años).

Salidas:
  figuras/tabla_3_5_comparacion_metodos.csv
  figuras/tabla_3_5_fdr_mensual.csv
  figuras/tabla_3_5_fdr_global.csv
  figuras/tabla_3_5_sensibilidad.csv
  figuras/tabla_3_5_salto_vs_tendencia.csv
  figuras/figura_3_5a_pendientes_mensuales_ic.png
  figuras/figura_3_5b_sensibilidad_inicio_fin.png
  figuras/figura_3_5c_salto_vs_tendencia.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess

import rol_c_comun as rc

MIN_MONTHS_PER_WATER_YEAR = 10
UNITS_DEC = {"P_local_mm": "mm/mes por década", "P_IMERG_mm": "mm/mes por década",
             "Caudal_m3s": "m³/s por década", "Temp_C": "°C por década"}


# ---------------------------------------------------------------------------
# 1-2. Tabla comparativa y FDR
# ---------------------------------------------------------------------------
def comparison_table(glob: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in rc.VARIABLES:
        g = glob.loc[glob["variable"] == col]

        def pick(rep, metodo):
            return g.loc[(g["representacion"] == rep) & (g["metodo"] == metodo)].iloc[0]

        for rep in ["X", "a", "z"]:
            unit = UNITS_DEC[col] if rep != "z" else "unidades estandarizadas por década"
            ols = pick(rep, "OLS")
            rows.append({"variable": col, "representacion": rep, "unidad": unit, "periodo": ols["periodo"],
                         "metodo": "OLS (IC HAC)", "n": ols["n"], "pendiente": ols["slope_dec"],
                         "ic_inf": ols["ci_low_hac_dec"], "ic_sup": ols["ci_high_hac_dec"],
                         "p": ols["p_hac"], "p_sin_corregir_dependencia": ols["p_ols"]})
            if rep == "X":
                fe = pick(rep, "OLS + efectos de mes")
                rows.append({"variable": col, "representacion": rep, "unidad": unit, "periodo": fe["periodo"],
                             "metodo": "OLS + efectos de mes (IC HAC)", "n": fe["n"], "pendiente": fe["slope_dec"],
                             "ic_inf": fe["ci_low_hac_dec"], "ic_sup": fe["ci_high_hac_dec"],
                             "p": fe["p_hac"], "p_sin_corregir_dependencia": fe["p_ols"]})
                sk = pick(rep, "Kendall estacional + Sen estacional")
                rows.append({"variable": col, "representacion": rep, "unidad": unit, "periodo": sk["periodo"],
                             "metodo": "Kendall estacional + Sen estacional (p bootstrap bloques 3 años)",
                             "n": sk["n"], "pendiente": sk["sen_dec"], "ic_inf": sk["sen_low_dec"],
                             "ic_sup": sk["sen_high_dec"], "p": sk["p_sk_boot"],
                             "p_sin_corregir_dependencia": sk["p_sk"]})
            else:
                mk = pick(rep, "Mann-Kendall (Hamed-Rao) + Theil-Sen")
                rows.append({"variable": col, "representacion": rep, "unidad": unit, "periodo": mk["periodo"],
                             "metodo": "Mann-Kendall Hamed-Rao + Theil-Sen", "n": mk["n"], "pendiente": mk["sen_dec"],
                             "ic_inf": mk["sen_low_hr_dec"], "ic_sup": mk["sen_high_hr_dec"],
                             "p": mk["p_mk_hr"], "p_sin_corregir_dependencia": mk["p_mk"]})
            lo = pick(rep, "LOESS (exploratorio)")
            rows.append({"variable": col, "representacion": rep, "unidad": unit, "periodo": lo["periodo"],
                         "metodo": f"LOESS ~10 años: cambio neto/década (sin inferencia)", "n": lo["n"],
                         "pendiente": lo["cambio_neto_por_dec"], "ic_inf": np.nan, "ic_sup": np.nan,
                         "p": np.nan, "p_sin_corregir_dependencia": np.nan})
    return pd.DataFrame(rows)


def fdr_tables(glob: pd.DataFrame, monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = monthly.loc[monthly["representacion"] == "X"].copy()
    m["q_ols_hac"] = rc.bh_fdr(m["ols_p_hac"])
    m["q_mk_hr"] = rc.bh_fdr(m["mk_p_mk_hr"])
    m["signif_ols_sin_fdr"] = m["ols_p_hac"] < rc.ALPHA
    m["signif_ols_fdr"] = m["q_ols_hac"] < rc.ALPHA
    m["signif_mk_sin_fdr"] = m["mk_p_mk_hr"] < rc.ALPHA
    m["signif_mk_fdr"] = m["q_mk_hr"] < rc.ALPHA
    keep = ["variable", "mes", "periodo", "n", "ols_slope_dec", "ols_ci_low_hac_dec", "ols_ci_high_hac_dec",
            "ols_p_hac", "q_ols_hac", "mk_sen_dec", "mk_sen_low_hr_dec", "mk_sen_high_hr_dec", "mk_p_mk_hr",
            "q_mk_hr", "signif_ols_sin_fdr", "signif_ols_fdr", "signif_mk_sin_fdr", "signif_mk_fdr"]
    m = m[keep]

    g_rows = []
    for col in rc.VARIABLES:
        g = glob.loc[glob["variable"] == col]
        g_rows.append({"variable": col, "prueba": "OLS-HAC sobre a",
                       "p": g.loc[(g["representacion"] == "a") & (g["metodo"] == "OLS"), "p_hac"].iloc[0]})
        g_rows.append({"variable": col, "prueba": "MK Hamed-Rao sobre a",
                       "p": g.loc[(g["representacion"] == "a") & g["metodo"].str.startswith("Mann"), "p_mk_hr"].iloc[0]})
        g_rows.append({"variable": col, "prueba": "Kendall estacional bootstrap sobre X",
                       "p": g.loc[(g["representacion"] == "X") & g["metodo"].str.startswith("Kendall"), "p_sk_boot"].iloc[0]})
    gf = pd.DataFrame(g_rows)
    gf["q_fdr"] = rc.bh_fdr(gf["p"])
    gf["signif_fdr"] = gf["q_fdr"] < rc.ALPHA
    return m, gf


def plot_monthly_slopes(mf: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (col, meta) in zip(axes.ravel(), rc.VARIABLES.items()):
        d = mf.loc[mf["variable"] == col]
        x = d["mes"].to_numpy()
        for off, slope, lo, hi, q, color, name in [
            (-0.15, "ols_slope_dec", "ols_ci_low_hac_dec", "ols_ci_high_hac_dec", "q_ols_hac", rc.COLOR_OLS, "OLS (IC HAC)"),
            (0.15, "mk_sen_dec", "mk_sen_low_hr_dec", "mk_sen_high_hr_dec", "q_mk_hr", rc.COLOR_SEN, "Sen (IC Hamed-Rao)")]:
            ax.vlines(x + off, d[lo], d[hi], color=color, lw=2)
            sig = d[q] < rc.ALPHA
            ax.plot(x[sig] + off, d.loc[sig, slope], "o", ms=8, color=color, mec="white", mew=1.5,
                    label=f"{name}, q$_{{FDR}}$<0.05")
            ax.plot(x[~sig] + off, d.loc[~sig, slope], "o", ms=8, mfc="white", mec=color, mew=1.8,
                    label=f"{name}, q$_{{FDR}}$≥0.05")
        ax.axhline(0, color="#0b0b0b", lw=0.8)
        ax.set_xticks(range(1, 13), rc.MONTH_NAMES)
        ax.set_ylabel(UNITS_DEC[col])
        ax.set_title(f"{meta['label']} ({d['periodo'].iloc[0]}, n≈{int(d['n'].median())} años)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle("Figura 3.5a. Pendientes por década e IC 95 % para los doce meses calendario (serie original)\n"
                 "Relleno: significativo tras FDR (Benjamini-Hochberg, familia de 48 pruebas por método); "
                 "hueco: no significativo", fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(rc.FIGURES_DIR / "figura_3_5a_pendientes_mensuales_ic.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. Sensibilidad con años hidrológicos
# ---------------------------------------------------------------------------
def water_year_anomalies(data: pd.DataFrame, col: str) -> pd.DataFrame:
    anom = rc.add_anomalies(data, col)
    g = anom.groupby("water_year").agg(a=("a", "mean"), n=("a", "count"))
    g = g.loc[g["n"] >= MIN_MONTHS_PER_WATER_YEAR]
    return g.reset_index().rename(columns={"water_year": "wy"})


def window_matrix(wy: pd.DataFrame, min_len: int) -> pd.DataFrame:
    rows = []
    years = wy["wy"].to_numpy()
    for s in years:
        for e in years:
            if e - s + 1 < min_len:
                continue
            sel = wy.loc[wy["wy"].between(s, e)]
            mk = rc.mann_kendall(sel["wy"].to_numpy(float), sel["a"].to_numpy(float), hamed_rao=False)
            rows.append({"inicio": s, "fin": e, "sen_dec": mk["sen_dec"], "p_mk": mk["p_mk"], "n": mk["n"]})
    return pd.DataFrame(rows)


def plot_start_end(data: pd.DataFrame) -> pd.DataFrame:
    rc.apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    out = []
    for ax, (col, meta) in zip(axes.ravel(), rc.VARIABLES.items()):
        wy = water_year_anomalies(data, col)
        min_len = 15 if col in ("P_local_mm", "Caudal_m3s") else 10
        mat = window_matrix(wy, min_len)
        out.append(mat.assign(variable=col))
        piv = mat.pivot(index="fin", columns="inicio", values="sen_dec")
        vmax = np.nanmax(np.abs(piv.to_numpy()))
        cmap = "RdBu_r" if col == "Temp_C" else "BrBG"
        im = ax.pcolormesh(piv.columns, piv.index, piv.to_numpy(), cmap=cmap, vmin=-vmax, vmax=vmax,
                           shading="nearest")
        sig = mat.loc[mat["p_mk"] < rc.ALPHA]
        ax.plot(sig["inicio"], sig["fin"], ".", ms=2.5, color="#0b0b0b")
        ax.set_xlabel("Año hidrológico inicial")
        ax.set_ylabel("Año hidrológico final")
        ax.set_title(f"{meta['label']}\nventanas ≥ {min_len} años", fontsize=9)
        ax.grid(False)
        fig.colorbar(im, ax=ax, label=f"Sen de anomalía anual [{UNITS_DEC[col]}]")
    fig.suptitle("Figura 3.5b. Sensibilidad de la pendiente de Sen a los años inicial y final "
                 "(media de anomalías por año hidrológico abr-mar)\nPuntos negros: Mann-Kendall p<0.05 "
                 "sin corregir (exploración de muchas ventanas solapadas; no son pruebas independientes)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_3_5b_sensibilidad_inicio_fin.png")
    plt.close(fig)
    return pd.concat(out)


def step_vs_trend(wy: pd.DataFrame) -> tuple[dict, dict]:
    y = wy["a"].to_numpy(float)
    t = wy["wy"].to_numpy(float)
    pet = rc.pettitt(y)
    k = pet["k_last_before"]
    step = (np.arange(len(y)) > k).astype(float)
    tc = t - t.mean()
    designs = {"nivel constante": np.ones((len(y), 1)),
               "tendencia lineal": sm.add_constant(tc),
               "escalón (Pettitt)": sm.add_constant(step),
               "escalón + tendencia": sm.add_constant(np.column_stack([step, tc]))}
    fits = {name: sm.OLS(y, X).fit() for name, X in designs.items()}
    aic = {name: f.aic for name, f in fits.items()}
    best = min(aic, key=aic.get)
    row = {"anio_cambio_pettitt": int(t[k + 1]), "K_pettitt": pet["K"], "p_pettitt": pet["p"],
           "media_antes": y[: k + 1].mean(), "media_despues": y[k + 1:].mean(),
           **{f"AIC_{n}": v for n, v in aic.items()}, "modelo_menor_AIC": best,
           "delta_AIC_tendencia_menos_escalon": aic["tendencia lineal"] - aic["escalón (Pettitt)"]}
    curves = {"t": t, "y": y, "k": k,
              "trend": fits["tendencia lineal"].fittedvalues,
              "step": fits["escalón (Pettitt)"].fittedvalues}
    return row, curves


def sensitivity(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rows, step_rows, curves_all = [], [], {}
    p_local_wy = water_year_anomalies(data, "P_local_mm")
    wettest = p_local_wy.nlargest(3, "a")["wy"].tolist()
    for col in rc.VARIABLES:
        wy = water_year_anomalies(data, col)
        t, y = wy["wy"].to_numpy(float), wy["a"].to_numpy(float)

        def add(test, config, tt, yy):
            ols = rc.ols_trend(tt, yy)
            mk = rc.mann_kendall(tt, yy, hamed_rao=True)
            rows.append({"variable": col, "unidad": UNITS_DEC[col], "prueba": test, "configuracion": config,
                         "periodo": f"{int(tt.min())}-{int(tt.max())}", "n_anios": len(yy),
                         "ols_dec": ols["slope_dec"], "ols_ic_inf": ols["ci_low_hac_dec"],
                         "ols_ic_sup": ols["ci_high_hac_dec"], "ols_p_hac": ols["p_hac"],
                         "sen_dec": mk["sen_dec"], "sen_ic_inf": mk["sen_low_hr_dec"],
                         "sen_ic_sup": mk["sen_high_hr_dec"], "mk_p_hr": mk["p_mk_hr"]})

        add("base", "años hidrológicos completos del registro", t, y)
        keep = ~np.isin(wy["wy"], wettest)
        add("años extremos", f"sin los 3 años más húmedos de P_L {wettest}", t[keep], y[keep])
        own_wettest = wy.nlargest(3, "a")["wy"].tolist()
        keep2 = ~np.isin(wy["wy"], own_wettest)
        add("años extremos", f"sin los 3 años de mayor anomalía propia {own_wettest}", t[keep2], y[keep2])
        common = wy["wy"].between(2000, 2019).to_numpy()
        add("periodo", "periodo común (años hidrológicos 2000-2019)", t[common], y[common])
        if col in ("P_local_mm", "Caudal_m3s"):
            early = wy["wy"].between(1980, 2009).to_numpy()
            add("fecha final", "hasta 2009 (antes de la megasequía 2010+)", t[early], y[early])
            late = wy["wy"].between(1990, 2019).to_numpy()
            add("fecha inicial", "desde 1990 (sin la década húmeda de 1980)", t[late], y[late])
        # LOESS: ancho de ventana sobre anomalías mensuales
        anom = rc.add_anomalies(data, col)
        rec = anom.loc[anom["a"].notna()]
        span = rec["t"].max() - rec["t"].min()
        for wyears in (6, 10, 20):
            frac = min(1.0, wyears / span)
            fit = lowess(rec["a"], rec["t"], frac=frac, it=2, return_sorted=False)
            fit_nr = lowess(rec["a"], rec["t"], frac=frac, it=0, return_sorted=False)
            rows.append({"variable": col, "unidad": UNITS_DEC[col], "prueba": "suavización LOESS",
                         "configuracion": f"ventana {wyears} años (robusto / no robusto)",
                         "periodo": f"{rec['date'].min():%Y-%m} a {rec['date'].max():%Y-%m}",
                         "n_anios": round(span, 1),
                         "ols_dec": np.nan, "sen_dec": 10 * (fit[-1] - fit[0]) / span,
                         "sen_ic_inf": np.nan, "sen_ic_sup": np.nan, "ols_p_hac": np.nan, "mk_p_hr": np.nan,
                         "loess_no_robusto_dec": 10 * (fit_nr[-1] - fit_nr[0]) / span,
                         "loess_rango_robusto": fit.max() - fit.min()})
        srow, curves = step_vs_trend(wy)
        step_rows.append({"variable": col, "unidad": UNITS_DEC[col].replace(" por década", ""), **srow})
        curves_all[col] = curves
    # Sensibilidad mensual al mes extremo de caudal (mayo 1993, z=16.5)
    anom_q = rc.add_anomalies(data, "Caudal_m3s")
    sub = anom_q.loc[(anom_q["month"] == 5) & anom_q["X"].notna()]
    for label, s in [("mayo, con 1993", sub), ("mayo, sin 1993", sub.loc[sub["year"] != 1993])]:
        ols = rc.ols_trend(s["t"].to_numpy(float), s["X"].to_numpy(float))
        mk = rc.mann_kendall(s["t"].to_numpy(float), s["X"].to_numpy(float))
        rows.append({"variable": "Caudal_m3s", "unidad": UNITS_DEC["Caudal_m3s"], "prueba": "mes extremo",
                     "configuracion": label, "periodo": f"{s['year'].min()}-{s['year'].max()}", "n_anios": len(s),
                     "ols_dec": ols["slope_dec"], "ols_ic_inf": ols["ci_low_hac_dec"], "ols_ic_sup": ols["ci_high_hac_dec"],
                     "ols_p_hac": ols["p_hac"], "sen_dec": mk["sen_dec"], "sen_ic_inf": mk["sen_low_hr_dec"],
                     "sen_ic_sup": mk["sen_high_hr_dec"], "mk_p_hr": mk["p_mk_hr"]})
    return pd.DataFrame(rows), pd.DataFrame(step_rows), curves_all


def plot_step_vs_trend(data: pd.DataFrame, steps: pd.DataFrame, curves: dict) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (col, meta) in zip(axes.ravel(), rc.VARIABLES.items()):
        c = curves[col]
        ax.bar(c["t"], c["y"], color=np.where(c["y"] >= 0, "#9fc7c0", "#d9b98c"), width=0.8)
        ax.plot(c["t"], c["trend"], color=rc.COLOR_OLS, lw=2, label="Tendencia lineal (OLS)")
        ax.step(c["t"], c["step"], where="mid", color=rc.COLOR_SEN, lw=2, label="Escalón en el cambio de Pettitt")
        for w, ls in [(6, ":"), (10, "-"), (20, "--")]:
            anom = rc.add_anomalies(data, col)
            rec = anom.loc[anom["a"].notna()]
            span = rec["t"].max() - rec["t"].min()
            fit = lowess(rec["a"], rec["t"], frac=min(1.0, w / span), it=2, return_sorted=False)
            ax.plot(rec["t"], fit, color=rc.COLOR_LOESS, lw=1.6, ls=ls, label=f"LOESS {w} años (mensual)")
        ax.axhline(0, color="#0b0b0b", lw=0.6)
        s = steps.loc[steps["variable"] == col].iloc[0]
        ax.set_title(f"{meta['label']}\nPettitt: cambio en {s['anio_cambio_pettitt']} (p={s['p_pettitt']:.3f}); "
                     f"menor AIC: {s['modelo_menor_AIC']}", fontsize=9)
        ax.set_ylabel(f"Anomalía [{meta['unit']}]")
        ax.set_xlim(1979, 2021)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False)
    fig.suptitle("Figura 3.5c. Tendencia gradual frente a salto de nivel: anomalía media por año hidrológico "
                 "(abr-mar, ≥10 meses válidos)\ny sensibilidad del LOESS al ancho de ventana", fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(rc.FIGURES_DIR / "figura_3_5c_salto_vs_tendencia.png")
    plt.close(fig)


def main() -> None:
    data = rc.load_master_data()
    glob = pd.read_csv(rc.FIGURES_DIR / "tabla_3_4_tendencias_globales.csv")
    monthly = pd.read_csv(rc.FIGURES_DIR / "tabla_3_4_tendencias_mensuales.csv")

    comp = comparison_table(glob)
    comp.to_csv(rc.FIGURES_DIR / "tabla_3_5_comparacion_metodos.csv", index=False)
    mf, gf = fdr_tables(glob, monthly)
    mf.to_csv(rc.FIGURES_DIR / "tabla_3_5_fdr_mensual.csv", index=False)
    gf.to_csv(rc.FIGURES_DIR / "tabla_3_5_fdr_global.csv", index=False)
    plot_monthly_slopes(mf)
    windows = plot_start_end(data)
    sens, steps, curves = sensitivity(data)
    sens.to_csv(rc.FIGURES_DIR / "tabla_3_5_sensibilidad.csv", index=False)
    steps.to_csv(rc.FIGURES_DIR / "tabla_3_5_salto_vs_tendencia.csv", index=False)
    plot_step_vs_trend(data, steps, curves)

    pd.set_option("display.width", 250)
    print("Comparación de métodos (por década):")
    print(comp[["variable", "representacion", "metodo", "n", "pendiente", "ic_inf", "ic_sup", "p"]].round(3).to_string(index=False))
    print("\nFDR global:")
    print(gf.round(4).to_string(index=False))
    print("\nFDR mensual: meses significativos (q<0.05)")
    print(mf.loc[mf["signif_ols_fdr"] | mf["signif_mk_fdr"],
                 ["variable", "mes", "ols_slope_dec", "q_ols_hac", "mk_sen_dec", "q_mk_hr"]].round(3).to_string(index=False))
    print("\nConteo por variable (sin FDR -> con FDR):")
    print(mf.groupby("variable")[["signif_ols_sin_fdr", "signif_ols_fdr", "signif_mk_sin_fdr", "signif_mk_fdr"]].sum())
    print("\nSensibilidad:")
    print(sens.drop(columns=["unidad"]).round(3).to_string(index=False))
    print("\nSalto vs tendencia:")
    print(steps.round(3).T.to_string())
    for col in ("P_local_mm", "Caudal_m3s"):
        w = windows.loc[windows["variable"] == col]
        print(f"\n{col}: ventanas={len(w)}, Sen<0 en {100 * (w['sen_dec'] < 0).mean():.0f} %, "
              f"rango Sen [{w['sen_dec'].min():.2f}, {w['sen_dec'].max():.2f}]")


if __name__ == "__main__":
    main()
