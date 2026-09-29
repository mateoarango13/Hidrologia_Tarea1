from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "datos" / "datos_mensuales_maipo.csv"
FIGURES_DIR = ROOT_DIR / "figuras"

REFERENCE_START = pd.Timestamp("2000-06-01")
REFERENCE_END = pd.Timestamp("2020-03-01")
MAX_LAG_MONTHS = 12

VARIABLES = {
    "P_local_mm": "mm/mes",
    "P_IMERG_mm": "mm/mes",
    "Caudal_m3s": "m3/s",
    "Q_lamina_mm": "mm/mes",
    "Temp_C": "°C",
}
RAIN_COLUMNS = ["P_local_mm", "P_IMERG_mm"]
FLOW_COLUMNS = ["Caudal_m3s", "Q_lamina_mm"]
SOURCE_LABELS = {"P_local_mm": "Precipitación local", "P_IMERG_mm": "IMERG"}
FLOW_LABELS = {"Caudal_m3s": "Caudal (m3/s)", "Q_lamina_mm": "Lámina de escorrentía (mm/mes)"}
SOURCE_COLORS = {"P_local_mm": "#237A68", "P_IMERG_mm": "#C45D35"}


def load_master_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    required_columns = {"date", *VARIABLES}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas en el dataset maestro: {sorted(missing_columns)}")
    if data["date"].duplicated().any():
        raise ValueError("El dataset maestro contiene fechas mensuales duplicadas.")

    expected_dates = pd.date_range(data["date"].min(), data["date"].max(), freq="MS")
    if not data["date"].equals(pd.Series(expected_dates, name="date")):
        raise ValueError("La secuencia mensual tiene vacíos o fechas fuera del inicio de mes; no se deben inferir rezagos por fila.")
    return data


def calculate_climatology(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    in_reference = data["date"].between(REFERENCE_START, REFERENCE_END)
    reference = data.loc[in_reference].copy()
    if reference.empty:
        raise ValueError("No hay registros en el periodo fijo de referencia.")

    rows = []
    anomaly_series = pd.DataFrame({"date": data["date"]})
    month_numbers = data["date"].dt.month

    for variable, unit in VARIABLES.items():
        monthly_reference = reference.groupby(reference["date"].dt.month)[variable].agg(
            mean="mean",
            median="median",
            standard_deviation="std",
            valid_values="count",
        )
        valid_years = (
            reference.loc[reference[variable].notna()]
            .assign(month=lambda frame: frame["date"].dt.month, year=lambda frame: frame["date"].dt.year)
            .groupby("month")["year"]
            .nunique()
        )

        for month in range(1, 13):
            stats = monthly_reference.loc[month]
            rows.append(
                {
                    "variable": variable,
                    "unit": unit,
                    "calendar_month": month,
                    "reference_start": REFERENCE_START.strftime("%Y-%m"),
                    "reference_end": REFERENCE_END.strftime("%Y-%m"),
                    "valid_values": int(stats["valid_values"]),
                    "valid_years": int(valid_years.get(month, 0)),
                    "climatology_mean": stats["mean"],
                    "climatology_median": stats["median"],
                    "climatology_standard_deviation": stats["standard_deviation"],
                }
            )

        month_means = month_numbers.map(monthly_reference["mean"])
        month_standard_deviations = month_numbers.map(monthly_reference["standard_deviation"])
        anomaly_series[f"{variable}_anomaly"] = data[variable] - month_means
        valid_standard_deviation = month_standard_deviations.notna() & month_standard_deviations.ne(0)
        standardized = pd.Series(np.nan, index=data.index, dtype=float)
        standardized.loc[valid_standard_deviation] = (
            anomaly_series.loc[valid_standard_deviation, f"{variable}_anomaly"]
            / month_standard_deviations.loc[valid_standard_deviation]
        )
        anomaly_series[f"{variable}_z"] = standardized
        year_count_by_month = month_numbers.map(valid_years.to_dict())
        anomaly_series[f"{variable}_reference_years"] = year_count_by_month.astype("Int64")

    return pd.DataFrame(rows), anomaly_series


def calculate_lag_correlations(anomalies: pd.DataFrame) -> pd.DataFrame:
    indexed = anomalies.set_index("date")
    rows = []

    for rain_column in RAIN_COLUMNS:
        rain_anomaly = indexed[f"{rain_column}_anomaly"]
        for flow_column in FLOW_COLUMNS:
            flow_anomaly = indexed[f"{flow_column}_anomaly"]
            for lag in range(MAX_LAG_MONTHS + 1):
                paired = pd.DataFrame(
                    {
                        "rain_anomaly_t_minus_k": rain_anomaly.shift(lag),
                        "flow_anomaly_t": flow_anomaly,
                    }
                ).dropna()
                if len(paired) < 3:
                    pearson_value = np.nan
                    spearman_value = np.nan
                else:
                    pearson_value = pearsonr(
                        paired["rain_anomaly_t_minus_k"], paired["flow_anomaly_t"]
                    ).statistic
                    spearman_value = spearmanr(
                        paired["rain_anomaly_t_minus_k"], paired["flow_anomaly_t"]
                    ).statistic

                rows.append(
                    {
                        "rain_variable": rain_column,
                        "flow_variable": flow_column,
                        "lag_months": lag,
                        "lag_definition": "precipitación en t-k frente a caudal en t",
                        "n_valid_pairs": len(paired),
                        "flow_period_start": paired.index.min().strftime("%Y-%m") if len(paired) else "",
                        "flow_period_end": paired.index.max().strftime("%Y-%m") if len(paired) else "",
                        "pearson_r_anomalies": pearson_value,
                        "spearman_rho_anomalies": spearman_value,
                    }
                )

    return pd.DataFrame(rows)


def plot_lag_correlations(lag_table: pd.DataFrame, figure_path: Path) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(11, 9), sharex=True, constrained_layout=True)
    correlation_types = [
        ("pearson_r_anomalies", "Pearson r", "-"),
        ("spearman_rho_anomalies", "Spearman rho", "--"),
    ]

    for axis, flow_column in zip(axes, FLOW_COLUMNS):
        flow_rows = lag_table.loc[lag_table["flow_variable"] == flow_column]
        for rain_column in RAIN_COLUMNS:
            rain_rows = flow_rows.loc[flow_rows["rain_variable"] == rain_column]
            for statistic, statistic_label, line_style in correlation_types:
                axis.plot(
                    rain_rows["lag_months"],
                    rain_rows[statistic],
                    color=SOURCE_COLORS[rain_column],
                    linestyle=line_style,
                    marker="o",
                    markersize=4,
                    label=f"{SOURCE_LABELS[rain_column]} — {statistic_label}",
                )
        axis.axhline(0, color="#4A5360", linewidth=0.9)
        axis.set_ylabel("Correlación de anomalías")
        axis.set_title(f"Respuesta: {FLOW_LABELS[flow_column]}")
        axis.grid(True, color="#D9DEE5", linewidth=0.7, alpha=0.8)
        axis.set_axisbelow(True)
        axis.legend(frameon=False, ncol=2, fontsize=9)

    axes[-1].set_xlabel("Rezago: precipitación en t-k y caudal en t (meses)")
    figure.suptitle("Asociación exploratoria entre anomalías mensuales", fontsize=14)
    figure.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    data = load_master_data()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    climatology, anomalies = calculate_climatology(data)
    lag_table = calculate_lag_correlations(anomalies)
    climatology_path = FIGURES_DIR / "tabla_2_2_climatologia_referencia.csv"
    anomalies_path = FIGURES_DIR / "serie_2_2_anomalias_estandarizadas.csv"
    lag_table_path = FIGURES_DIR / "tabla_2_2_correlaciones_rezagos.csv"
    lag_figure_path = FIGURES_DIR / "figura_2_2_correlaciones_rezagos.png"

    climatology.to_csv(climatology_path, index=False, float_format="%.6f")
    anomalies.to_csv(anomalies_path, index=False, float_format="%.6f")
    lag_table.to_csv(lag_table_path, index=False, float_format="%.6f")
    plot_lag_correlations(lag_table, lag_figure_path)

    print(f"Referencia climatológica fija: {REFERENCE_START:%Y-%m} a {REFERENCE_END:%Y-%m}.")
    print("La serie local completa se conserva; se transforma con la climatología fija del periodo común.")
    print("Años válidos por mes y variable:")
    print(climatology.pivot(index="calendar_month", columns="variable", values="valid_years").to_string())
    print("\nCorrelaciones exploratorias de anomalías para lluvia en t-k frente a caudal en t:")
    print(lag_table.loc[lag_table["flow_variable"] == "Caudal_m3s"].to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print("\nNota: climatologías y rezagos se estiman de forma descriptiva con el registro disponible; aún no son validación fuera de muestra.")
    print(f"Climatología: {climatology_path.relative_to(ROOT_DIR)}")
    print(f"Anomalías: {anomalies_path.relative_to(ROOT_DIR)}")
    print(f"Rezagos: {lag_table_path.relative_to(ROOT_DIR)}")
    print(f"Figura: {lag_figure_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()