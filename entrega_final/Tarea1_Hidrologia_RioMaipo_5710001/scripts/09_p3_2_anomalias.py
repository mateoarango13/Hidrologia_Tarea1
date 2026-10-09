"""
Punto 3.2 — Series originales, anomalías y anomalías estandarizadas (Rol C).

Para cada variable X_t con mes calendario j(t):
    a_t = X_t - mu_j(t)          (conserva unidades)
    z_t = (X_t - mu_j(t)) / s_j(t)  (adimensional)
mu_j y s_j: media y desviación estándar muestral (ddof=1) del mes j en el periodo
de referencia FIJO 2000-06 a 2020-03, el mismo de los roles A y B y el único en
que coexisten las cuatro variables (permite comparar fuentes con igual referencia).

Las anomalías se aplican a TODO el registro disponible de cada variable
(P_L y Q desde 1980), sin recortar al periodo satelital (punto 3.1).

Salidas:
  figuras/tabla_3_2_periodos_analisis.csv
  figuras/tabla_3_2_climatologia_referencia.csv
  figuras/serie_3_2_anomalias_rol_c.csv
  figuras/figura_3_2_representaciones.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import rol_c_comun as rc


def periods_table(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, meta in rc.VARIABLES.items():
        start, end = rc.valid_span(data, col)
        rec = rc.full_record(data, col)
        common = data.loc[data["date"].between(rc.COMMON_START, rc.COMMON_END), col]
        missing = rec.loc[rec[col].isna(), "date"].dt.strftime("%Y-%m").tolist()
        rows.append({
            "variable": col, "fuente": meta["source"], "unidad": meta["unit"],
            "inicio_registro": start.strftime("%Y-%m"), "fin_registro": end.strftime("%Y-%m"),
            "meses_en_registro": len(rec), "meses_validos_registro": int(rec[col].notna().sum()),
            "faltantes_internos": len(missing), "lista_faltantes": ";".join(missing),
            "meses_validos_periodo_comun": int(common.notna().sum()),
            "meses_periodo_comun": len(common),
        })
    return pd.DataFrame(rows)


def climatology_table(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, meta in rc.VARIABLES.items():
        clim = rc.reference_climatology(data, col)
        anom = rc.add_anomalies(data, col)
        in_ref = anom["date"].between(rc.REFERENCE_START, rc.REFERENCE_END)
        for month, row in clim.iterrows():
            sel = anom.loc[(anom["month"] == month) & anom["X"].notna()]
            sel_ref = anom.loc[in_ref & (anom["month"] == month) & anom["X"].notna()]
            rows.append({
                "variable": col, "unidad": meta["unit"], "mes": month,
                "referencia": f"{rc.REFERENCE_START:%Y-%m} a {rc.REFERENCE_END:%Y-%m}",
                "anios_validos_referencia": int(row["n_years"]),
                "mu_j": row["mu"], "s_j": row["s"],
                # Indicador de inestabilidad de z: s_j relativa a la media (solo P y Q;
                # en temperatura el cero es convencional y el cociente no tiene sentido).
                "s_j_sobre_mu_j": (row["s"] / row["mu"]) if col != "Temp_C" else np.nan,
                # Verificaciones: en la referencia, media(a)=0 y desv(z)=1 por construcción.
                "media_a_en_referencia": sel_ref["a"].mean(),
                "desv_z_en_referencia": sel_ref["z"].std(ddof=1),
                "max_abs_z_registro": sel["z"].abs().max(),
                "fecha_max_abs_z": sel.loc[sel["z"].abs().idxmax(), "date"].strftime("%Y-%m"),
            })
    table = pd.DataFrame(rows)
    if (table["s_j"] <= 0).any():
        raise ValueError("Algún s_j es 0: la anomalía estandarizada no está definida.")
    if not np.allclose(table["media_a_en_referencia"], 0, atol=1e-9):
        raise AssertionError("La media de las anomalías en la referencia no es 0.")
    if not np.allclose(table["desv_z_en_referencia"], 1, atol=1e-9):
        raise AssertionError("La desviación de z en la referencia no es 1.")
    return table


def export_anomalies(data: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"date": data["date"].dt.strftime("%Y-%m-%d")})
    for col in rc.VARIABLES:
        anom = rc.add_anomalies(data, col)
        for rep in rc.REPRESENTATIONS:
            out[f"{col}__{rep}"] = anom[rep].to_numpy()
    return out


def plot_representations(data: pd.DataFrame) -> None:
    rc.apply_style()
    fig, axes = plt.subplots(4, 3, figsize=(13, 10.5), sharex=True)
    for i, (col, meta) in enumerate(rc.VARIABLES.items()):
        anom = rc.add_anomalies(data, col)
        rec = anom.loc[anom["date"].between(*rc.valid_span(data, col))]
        for k, (rep, rep_name) in enumerate(rc.REPRESENTATIONS.items()):
            ax = axes[i, k]
            ax.plot(rec["date"], rec[rep], color=rc.COLOR_POINTS, lw=0.8)
            ax.axvspan(rc.REFERENCE_START, rc.REFERENCE_END, color=rc.COLOR_OLS, alpha=0.06, lw=0)
            if rep != "X":
                ax.axhline(0, color="#0b0b0b", lw=0.7)
            unit = meta["unit"] if rep != "z" else "adim."
            ax.set_ylabel(f"{meta['short']} [{unit}]")
            if i == 0:
                ax.set_title(rep_name)
            # Marcar faltantes internos (vacíos visibles, no rellenados).
            gaps = rec.loc[rec["X"].isna(), "date"]
            for g in gaps:
                ax.axvline(g, color="#e34948", lw=0.6, alpha=0.6)
        axes[i, 0].text(0.01, 0.97, meta["label"], transform=axes[i, 0].transAxes,
                        va="top", fontsize=8, color="#0b0b0b",
                        bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
    fig.suptitle("Figura 3.2. Series originales $X_t$, anomalías $a_t$ y anomalías estandarizadas $z_t$\n"
                 "Referencia climatológica fija 2000-06 a 2020-03 (banda azul); líneas rojas: meses faltantes",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(rc.FIGURES_DIR / "figura_3_2_representaciones.png")
    plt.close(fig)


def main() -> None:
    data = rc.load_master_data()
    periods = periods_table(data)
    periods.to_csv(rc.FIGURES_DIR / "tabla_3_2_periodos_analisis.csv", index=False)
    clim = climatology_table(data)
    clim.to_csv(rc.FIGURES_DIR / "tabla_3_2_climatologia_referencia.csv", index=False)
    export_anomalies(data).to_csv(rc.FIGURES_DIR / "serie_3_2_anomalias_rol_c.csv", index=False)
    plot_representations(data)

    print("Periodos de análisis:")
    print(periods.drop(columns="lista_faltantes").to_string(index=False))
    print("\nMeses con s_j/mu_j > 1 (z potencialmente inestable):")
    print(clim.loc[clim["s_j_sobre_mu_j"] > 1, ["variable", "mes", "anios_validos_referencia",
                                                 "mu_j", "s_j", "s_j_sobre_mu_j",
                                                 "max_abs_z_registro", "fecha_max_abs_z"]].round(2).to_string(index=False))
    print("\nMáximo |z| por variable:")
    print(clim.loc[clim.groupby("variable")["max_abs_z_registro"].idxmax(),
                   ["variable", "mes", "max_abs_z_registro", "fecha_max_abs_z"]].round(2).to_string(index=False))
    print("\nVerificación: media(a)=0 y desv(z)=1 en la referencia para los 48 pares variable-mes: OK")


if __name__ == "__main__":
    main()
