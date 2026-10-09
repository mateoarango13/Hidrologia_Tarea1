from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm
from scipy.stats import pearsonr, spearmanr


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "datos" / "datos_mensuales_maipo.csv"
FIGURES_DIR = ROOT_DIR / "figuras"
FIGURE_PATH = FIGURES_DIR / "figura_2_1_relaciones_scatter.png"
METRICS_PATH = FIGURES_DIR / "tabla_2_1_metricas_relaciones.csv"
GROUP_DIAGNOSTICS_PATH = FIGURES_DIR / "tabla_2_1_errores_por_grupo.csv"
INFLUENTIAL_MONTHS_PATH = FIGURES_DIR / "tabla_2_1_meses_influyentes.csv"
OUTLIER_SENSITIVITY_PATH = FIGURES_DIR / "tabla_2_1_sensibilidad_extremos.csv"

MONTH_LABELS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MONTH_CMAP = plt.get_cmap("twilight", 12)
MONTH_NORM = BoundaryNorm(np.arange(0.5, 13.5, 1), MONTH_CMAP.N)
SEASON_BY_MONTH = {
    12: "Verano",
    1: "Verano",
    2: "Verano",
    3: "Otono",
    4: "Otono",
    5: "Otono",
    6: "Invierno",
    7: "Invierno",
    8: "Invierno",
    9: "Primavera",
    10: "Primavera",
    11: "Primavera",
}
SEASON_ORDER = ["Verano", "Otono", "Invierno", "Primavera"]

PAIR_CONFIGS = [
    {
        "x": "P_IMERG_mm",
        "y": "P_local_mm",
        "title": "IMERG vs. precipitación de referencia",
        "x_label": "Precipitación IMERG (mm/mes)",
        "y_label": "Precipitación de referencia (mm/mes)",
        "identity_line": True,
    },
    {
        "x": "P_local_mm",
        "y": "Caudal_m3s",
        "title": "Precipitación de referencia vs. caudal",
        "x_label": "Precipitación de referencia (mm/mes)",
        "y_label": "Caudal medio mensual (m³/s)",
    },
    {
        "x": "P_IMERG_mm",
        "y": "Caudal_m3s",
        "title": "IMERG vs. caudal",
        "x_label": "Precipitación IMERG (mm/mes)",
        "y_label": "Caudal medio mensual (m³/s)",
    },
    {
        "x": "P_local_mm",
        "y": "Q_lamina_mm",
        "title": "Precipitación de referencia vs. escorrentía equivalente",
        "x_label": "Precipitación de referencia (mm/mes)",
        "y_label": "Escorrentía equivalente (mm/mes)",
    },
    {
        "x": "P_IMERG_mm",
        "y": "Q_lamina_mm",
        "title": "IMERG vs. escorrentía equivalente",
        "x_label": "Precipitación IMERG (mm/mes)",
        "y_label": "Escorrentía equivalente (mm/mes)",
    },
]


def load_master_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, parse_dates=["date"])
    required_columns = {
        "date",
        "P_local_mm",
        "P_IMERG_mm",
        "Caudal_m3s",
        "Q_lamina_mm",
    }
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas en el dataset maestro: {sorted(missing_columns)}")
    return data


def summarize_pair(data: pd.DataFrame, x_column: str, y_column: str) -> dict[str, object]:
    paired = data[["date", x_column, y_column]].dropna().copy()
    if len(paired) < 2:
        raise ValueError(f"No hay suficientes pares válidos para {x_column} vs. {y_column}.")

    return {
        "x": x_column,
        "y": y_column,
        "n": len(paired),
        "period_start": paired["date"].min().strftime("%Y-%m"),
        "period_end": paired["date"].max().strftime("%Y-%m"),
        "pearson_r": pearsonr(paired[x_column], paired[y_column]).statistic,
        "spearman_rho": spearmanr(paired[x_column], paired[y_column]).statistic,
    }


def plot_pair(axis, data: pd.DataFrame, config: dict[str, object]):
    x_column = config["x"]
    y_column = config["y"]
    paired = data[["date", x_column, y_column]].dropna().copy()
    paired["month"] = paired["date"].dt.month
    start = paired["date"].min().strftime("%Y-%m")
    end = paired["date"].max().strftime("%Y-%m")

    points = axis.scatter(
        paired[x_column],
        paired[y_column],
        c=paired["month"],
        cmap=MONTH_CMAP,
        norm=MONTH_NORM,
        s=24,
        alpha=0.78,
        linewidths=0,
    )
    axis.set_title(f"{config['title']}\nn = {len(paired)} | {start} a {end}")
    axis.set_xlabel(config["x_label"])
    axis.set_ylabel(config["y_label"])
    axis.grid(True, color="#D9DEE5", linewidth=0.7, alpha=0.8)
    axis.set_axisbelow(True)

    if config.get("identity_line"):
        lower = min(paired[x_column].min(), paired[y_column].min())
        upper = max(paired[x_column].max(), paired[y_column].max())
        axis.plot([lower, upper], [lower, upper], color="#202A35", linestyle="--", linewidth=1.2, label="1:1")
        axis.set_xlim(lower, upper)
        axis.set_ylim(lower, upper)
        axis.set_aspect("equal", adjustable="box")
        axis.legend(loc="upper left", frameon=False)

    return points


def summarize_precipitation_group(label: str, group_type: str, group: pd.DataFrame) -> dict[str, object]:
    errors = group["P_IMERG_mm"] - group["P_local_mm"]
    return {
        "group_type": group_type,
        "group": label,
        "n": len(group),
        "mean_P_local_mm_month": group["P_local_mm"].mean(),
        "mean_P_IMERG_mm_month": group["P_IMERG_mm"].mean(),
        "mean_bias_PI_minus_PL_mm_month": errors.mean(),
        "mae_mm_month": errors.abs().mean(),
        "rmse_mm_month": np.sqrt(errors.pow(2).mean()),
        "pearson_r": pearsonr(group["P_IMERG_mm"], group["P_local_mm"]).statistic
        if group["P_IMERG_mm"].nunique() > 1 and group["P_local_mm"].nunique() > 1
        else np.nan,
    }


def build_precipitation_group_diagnostics(data: pd.DataFrame) -> pd.DataFrame:
    paired = data[["date", "P_local_mm", "P_IMERG_mm"]].dropna().copy()
    paired["season"] = paired["date"].dt.month.map(SEASON_BY_MONTH)
    paired["intensity_quartile"] = pd.qcut(paired["P_local_mm"], q=4, duplicates="drop")

    summaries = []
    for season in SEASON_ORDER:
        season_group = paired.loc[paired["season"] == season]
        if not season_group.empty:
            summaries.append(summarize_precipitation_group(season, "estacion_austral", season_group))

    for intensity, intensity_group in paired.groupby("intensity_quartile", observed=True):
        summaries.append(summarize_precipitation_group(str(intensity), "cuartil_P_local", intensity_group))

    return pd.DataFrame(summaries)


def build_influential_months(data: pd.DataFrame) -> pd.DataFrame:
    paired = data[["date", "P_local_mm", "P_IMERG_mm"]].dropna().copy()
    paired["error_PI_minus_PL_mm_month"] = paired["P_IMERG_mm"] - paired["P_local_mm"]
    paired["absolute_error_mm_month"] = paired["error_PI_minus_PL_mm_month"].abs()
    paired["season"] = paired["date"].dt.month.map(SEASON_BY_MONTH)

    return paired.nlargest(10, "absolute_error_mm_month").assign(
        date=lambda frame: frame["date"].dt.strftime("%Y-%m")
    )


def build_outlier_sensitivity(data: pd.DataFrame) -> pd.DataFrame:
    paired = data[["date", "P_local_mm", "P_IMERG_mm"]].dropna().copy()
    paired["error"] = paired["P_IMERG_mm"] - paired["P_local_mm"]
    ranked_dates = paired.assign(absolute_error=paired["error"].abs()).nlargest(10, "absolute_error")["date"]

    summaries = []
    for excluded_count in [0, 1, 3, 5, 10]:
        excluded_dates = ranked_dates.iloc[:excluded_count]
        remaining = paired.loc[~paired["date"].isin(excluded_dates)]
        errors = remaining["error"]
        summaries.append(
            {
                "excluded_largest_absolute_errors": excluded_count,
                "excluded_dates": ", ".join(date.strftime("%Y-%m") for date in excluded_dates),
                "n_remaining": len(remaining),
                "pearson_r": pearsonr(remaining["P_IMERG_mm"], remaining["P_local_mm"]).statistic,
                "mean_bias_PI_minus_PL_mm_month": errors.mean(),
                "mae_mm_month": errors.abs().mean(),
                "rmse_mm_month": np.sqrt(errors.pow(2).mean()),
            }
        )

    return pd.DataFrame(summaries)


def main() -> None:
    data = load_master_data()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    metrics = [summarize_pair(data, config["x"], config["y"]) for config in PAIR_CONFIGS]
    precipitation_pairs = data[["P_local_mm", "P_IMERG_mm"]].dropna()
    precipitation_error = precipitation_pairs["P_IMERG_mm"] - precipitation_pairs["P_local_mm"]
    metrics[0].update(
        {
            "mean_bias_PI_minus_PL_mm_month": precipitation_error.mean(),
            "mae_mm_month": precipitation_error.abs().mean(),
            "rmse_mm_month": np.sqrt(precipitation_error.pow(2).mean()),
            "pbias_PI_minus_PL_percent": 100 * precipitation_error.sum() / precipitation_pairs["P_local_mm"].sum(),
        }
    )

    figure, axes = plt.subplots(2, 3, figsize=(17, 10), constrained_layout=True)
    flat_axes = axes.ravel()
    for axis, config in zip(flat_axes, PAIR_CONFIGS):
        color_mappable = plot_pair(axis, data, config)
    flat_axes[-1].set_visible(False)

    colorbar = figure.colorbar(color_mappable, ax=flat_axes[:-1], ticks=np.arange(1, 13), shrink=0.88, pad=0.025)
    colorbar.ax.set_yticklabels(MONTH_LABELS)
    colorbar.set_label("Mes calendario")
    figure.suptitle("Relaciones mensuales entre precipitación y respuesta de la cuenca", fontsize=15)
    figure.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight")
    plt.close(figure)

    metrics_table = pd.DataFrame(metrics)
    metrics_table.to_csv(METRICS_PATH, index=False, float_format="%.6f")
    build_precipitation_group_diagnostics(data).to_csv(GROUP_DIAGNOSTICS_PATH, index=False, float_format="%.6f")
    build_influential_months(data).to_csv(INFLUENTIAL_MONTHS_PATH, index=False, float_format="%.6f")
    build_outlier_sensitivity(data).to_csv(OUTLIER_SENSITIVITY_PATH, index=False, float_format="%.6f")

    print(f"Figura guardada: {FIGURE_PATH.relative_to(ROOT_DIR)}")
    print(f"Tabla guardada: {METRICS_PATH.relative_to(ROOT_DIR)}")
    print(f"Errores por estación e intensidad: {GROUP_DIAGNOSTICS_PATH.relative_to(ROOT_DIR)}")
    print(f"Meses influyentes: {INFLUENTIAL_MONTHS_PATH.relative_to(ROOT_DIR)}")
    print(f"Sensibilidad a extremos: {OUTLIER_SENSITIVITY_PATH.relative_to(ROOT_DIR)}")
    print("Métricas calculadas con pares completos de datos mensuales:")
    print(metrics_table.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print("\nNota: las correlaciones usan series mensuales originales; aún conservan el ciclo anual compartido.")


if __name__ == "__main__":
    main()