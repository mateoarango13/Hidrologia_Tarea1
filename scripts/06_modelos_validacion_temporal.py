from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "datos" / "datos_mensuales_maipo.csv"
FIGURES_DIR = ROOT_DIR / "figuras"
MAX_LAG_MONTHS = 12

RAIN_LOCAL = "P_local_mm"
RAIN_SATELLITE = "P_IMERG_mm"
FLOW = "Caudal_m3s"
MONTH_NAMES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
SEASONS = {
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
PREDICTION_COLORS = {
    "IMERG sin corrección": "#75808C",
    "Lineal corregido": "#237A68",
    "Log-lineal corregido": "#C45D35",
    "Climatología mensual Q": "#75808C",
    "Regresión lineal Q~P(t)": "#C45D35",
    "Regresión de anomalías con rezago": "#237A68",
}


def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").set_index("date")
    required_columns = {RAIN_LOCAL, RAIN_SATELLITE, FLOW}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing_columns)}")
    if data.index.has_duplicates:
        raise ValueError("El dataset maestro contiene meses duplicados.")
    expected_index = pd.date_range(data.index.min(), data.index.max(), freq="MS")
    if not data.index.equals(expected_index):
        raise ValueError("La serie no tiene continuidad mensual; los rezagos no se pueden definir por filas con seguridad.")
    return data


def fit_linear(x_values: pd.Series, y_values: pd.Series) -> tuple[float, float]:
    design = np.column_stack([np.ones(len(x_values)), x_values.to_numpy(dtype=float)])
    intercept, slope = np.linalg.lstsq(design, y_values.to_numpy(dtype=float), rcond=None)[0]
    return float(intercept), float(slope)


def predict_linear(x_values: pd.Series, coefficients: tuple[float, float]) -> pd.Series:
    intercept, slope = coefficients
    return pd.Series(intercept + slope * x_values.to_numpy(dtype=float), index=x_values.index)


def fit_precipitation_model(method: str, training: pd.DataFrame, evaluation: pd.DataFrame) -> tuple[pd.Series, dict[str, float]]:
    x_train = training[RAIN_SATELLITE]
    y_train = training[RAIN_LOCAL]
    x_eval = evaluation[RAIN_SATELLITE]

    if method == "Lineal corregido":
        coefficients = fit_linear(x_train, y_train)
        raw_predictions = predict_linear(x_eval, coefficients)
        predictions = raw_predictions.clip(lower=0)
        diagnostics = {
            "intercept": coefficients[0],
            "slope": coefficients[1],
            "smearing_factor": np.nan,
            "negative_predictions_before_clipping": int((raw_predictions < 0).sum()),
        }
        return predictions, diagnostics

    if method == "Log-lineal corregido":
        x_log_train = np.log1p(x_train)
        y_log_train = np.log1p(y_train)
        coefficients = fit_linear(x_log_train, y_log_train)
        fitted_log = predict_linear(x_log_train, coefficients)
        residual_log = y_log_train - fitted_log
        smearing_factor = float(np.exp(residual_log).mean())
        raw_predictions = np.expm1(predict_linear(np.log1p(x_eval), coefficients)) * smearing_factor
        predictions = raw_predictions.clip(lower=0)
        diagnostics = {
            "intercept": coefficients[0],
            "slope": coefficients[1],
            "smearing_factor": smearing_factor,
            "negative_predictions_before_clipping": int((raw_predictions < 0).sum()),
        }
        return predictions, diagnostics

    raise ValueError(f"Modelo de precipitación desconocido: {method}")


def calculate_metrics(observed: pd.Series, predicted: pd.Series) -> dict[str, float]:
    paired = pd.concat([observed.rename("observed"), predicted.rename("predicted")], axis=1).dropna()
    errors = paired["predicted"] - paired["observed"]
    return {
        "n": len(paired),
        "bias_pred_minus_obs": errors.mean(),
        "mae": errors.abs().mean(),
        "rmse": np.sqrt(errors.pow(2).mean()),
        "negative_predictions": int((paired["predicted"] < 0).sum()),
        "minimum_prediction": paired["predicted"].min(),
        "maximum_prediction": paired["predicted"].max(),
    }


def append_predictions(
    records: list[dict[str, object]],
    *,
    task: str,
    predictor: str,
    target: str,
    model: str,
    observed: pd.Series,
    predicted: pd.Series,
    outer_start: pd.Timestamp,
    training_end: pd.Timestamp,
    tuning_start: pd.Timestamp,
    lag_months: int | None = None,
) -> None:
    paired = pd.concat([observed.rename("observed"), predicted.rename("predicted")], axis=1).dropna()
    for date, row in paired.iterrows():
        records.append(
            {
                "task": task,
                "predictor": predictor,
                "target": target,
                "model": model,
                "split": "outer_temporal_test",
                "date": date,
                "year": date.year,
                "calendar_month": date.month,
                "season": SEASONS[date.month],
                "observed": row["observed"],
                "predicted": row["predicted"],
                "residual_pred_minus_obs": row["predicted"] - row["observed"],
                "outer_test_start": outer_start.strftime("%Y-%m"),
                "training_end": training_end.strftime("%Y-%m"),
                "inner_tuning_start": tuning_start.strftime("%Y-%m"),
                "selected_lag_months": lag_months,
            }
        )


def summarize_predictions(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    annual_rows = []
    monthly_rows = []
    seasonal_rows = []

    group_columns = ["task", "predictor", "target", "model"]
    for keys, group in predictions.groupby(group_columns, sort=False):
        task, predictor, target, model = keys
        metrics = calculate_metrics(group["observed"], group["predicted"])
        metric_rows.append(
            {
                "task": task,
                "predictor": predictor,
                "target": target,
                "model": model,
                "test_start": group["date"].min().strftime("%Y-%m"),
                "test_end": group["date"].max().strftime("%Y-%m"),
                **metrics,
            }
        )

        for year, year_group in group.groupby("year"):
            annual_rows.append(
                {
                    "task": task,
                    "predictor": predictor,
                    "target": target,
                    "model": model,
                    "year": year,
                    **calculate_metrics(year_group["observed"], year_group["predicted"]),
                }
            )

        for month, month_group in group.groupby("calendar_month"):
            monthly_rows.append(
                {
                    "task": task,
                    "predictor": predictor,
                    "target": target,
                    "model": model,
                    "calendar_month": month,
                    "season": SEASONS[month],
                    **calculate_metrics(month_group["observed"], month_group["predicted"]),
                }
            )

        for season, season_group in group.groupby("season"):
            seasonal_rows.append(
                {
                    "task": task,
                    "predictor": predictor,
                    "target": target,
                    "model": model,
                    "season": season,
                    **calculate_metrics(season_group["observed"], season_group["predicted"]),
                }
            )

    return (
        pd.DataFrame(metric_rows),
        pd.DataFrame(annual_rows),
        pd.DataFrame(monthly_rows),
        pd.DataFrame(seasonal_rows),
    )


def evaluate_precipitation_estimation(data: pd.DataFrame) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    outer_start = pd.Timestamp("2016-01-01")
    tuning_start = pd.Timestamp("2013-01-01")
    paired = data[[RAIN_SATELLITE, RAIN_LOCAL]].dropna()
    tuning_training = paired.loc[paired.index < tuning_start]
    tuning_validation = paired.loc[(paired.index >= tuning_start) & (paired.index < outer_start)]
    final_training = paired.loc[paired.index < outer_start]
    test = paired.loc[paired.index >= outer_start]
    if min(len(tuning_training), len(tuning_validation), len(final_training), len(test)) < 12:
        raise ValueError("La partición temporal de precipitación deja muy pocos pares para ajustar, seleccionar o evaluar.")

    candidate_rows = []
    candidate_scores = {}
    for model in ["Lineal corregido", "Log-lineal corregido"]:
        validation_predictions, diagnostics = fit_precipitation_model(model, tuning_training, tuning_validation)
        score = calculate_metrics(tuning_validation[RAIN_LOCAL], validation_predictions)
        candidate_scores[model] = score["mae"]
        candidate_rows.append(
            {
                "task": "estimar_precipitacion_local",
                "predictor": RAIN_SATELLITE,
                "candidate_model": model,
                "fit_period_start": tuning_training.index.min().strftime("%Y-%m"),
                "fit_period_end": tuning_training.index.max().strftime("%Y-%m"),
                "tuning_period_start": tuning_validation.index.min().strftime("%Y-%m"),
                "tuning_period_end": tuning_validation.index.max().strftime("%Y-%m"),
                "tuning_n": score["n"],
                "tuning_bias": score["bias_pred_minus_obs"],
                "tuning_mae": score["mae"],
                "tuning_rmse": score["rmse"],
                **diagnostics,
                "selected_on_inner_tuning": False,
            }
        )

    selected_model = min(candidate_scores, key=candidate_scores.get)
    for row in candidate_rows:
        if row["candidate_model"] == selected_model:
            row["selected_on_inner_tuning"] = True

    prediction_records = []
    baseline = test[RAIN_SATELLITE]
    append_predictions(
        prediction_records,
        task="estimar_precipitacion_local",
        predictor=RAIN_SATELLITE,
        target=RAIN_LOCAL,
        model="IMERG sin corrección",
        observed=test[RAIN_LOCAL],
        predicted=baseline,
        outer_start=outer_start,
        training_end=final_training.index.max(),
        tuning_start=tuning_start,
    )

    final_predictions, final_diagnostics = fit_precipitation_model(selected_model, final_training, test)
    append_predictions(
        prediction_records,
        task="estimar_precipitacion_local",
        predictor=RAIN_SATELLITE,
        target=RAIN_LOCAL,
        model=selected_model,
        observed=test[RAIN_LOCAL],
        predicted=final_predictions,
        outer_start=outer_start,
        training_end=final_training.index.max(),
        tuning_start=tuning_start,
    )
    candidate_rows.append(
        {
            "task": "estimar_precipitacion_local",
            "predictor": RAIN_SATELLITE,
            "candidate_model": "seleccion_final_reajustada",
            "fit_period_start": final_training.index.min().strftime("%Y-%m"),
            "fit_period_end": final_training.index.max().strftime("%Y-%m"),
            "tuning_period_start": tuning_start.strftime("%Y-%m"),
            "tuning_period_end": (outer_start - pd.offsets.MonthBegin(1)).strftime("%Y-%m"),
            "tuning_n": len(tuning_validation),
            "tuning_bias": np.nan,
            "tuning_mae": candidate_scores[selected_model],
            "tuning_rmse": np.nan,
            **final_diagnostics,
            "selected_on_inner_tuning": True,
        }
    )
    return prediction_records, candidate_rows


def monthly_climatology(series: pd.Series) -> pd.Series:
    return series.groupby(series.index.month).mean()


def anomalies_from_climatology(series: pd.Series, climatology: pd.Series) -> pd.Series:
    return series - pd.Series(series.index.month, index=series.index).map(climatology)


def select_anomaly_lag(
    data: pd.DataFrame,
    *,
    rain_column: str,
    outer_start: pd.Timestamp,
    tuning_start: pd.Timestamp,
) -> tuple[int, list[dict[str, object]]]:
    fit_mask = data.index < tuning_start
    tuning_mask = (data.index >= tuning_start) & (data.index < outer_start)
    fit_rain = data.loc[fit_mask, rain_column].dropna()
    fit_flow = data.loc[fit_mask, FLOW].dropna()
    rain_climatology = monthly_climatology(fit_rain)
    flow_climatology = monthly_climatology(fit_flow)
    rain_anomaly = anomalies_from_climatology(data[rain_column], rain_climatology)
    flow_anomaly = anomalies_from_climatology(data[FLOW], flow_climatology)

    rows = []
    for lag in range(MAX_LAG_MONTHS + 1):
        lagged_rain = rain_anomaly.shift(lag)
        fit_pairs = pd.DataFrame({"rain_anomaly": lagged_rain, "flow_anomaly": flow_anomaly}).loc[fit_mask].dropna()
        tuning_pairs = pd.DataFrame({"rain_anomaly": lagged_rain, "flow_anomaly": flow_anomaly}).loc[tuning_mask].dropna()
        if min(len(fit_pairs), len(tuning_pairs)) < 12:
            continue
        coefficients = fit_linear(fit_pairs["rain_anomaly"], fit_pairs["flow_anomaly"])
        predicted_flow_anomaly = predict_linear(tuning_pairs["rain_anomaly"], coefficients)
        predicted_flow = predicted_flow_anomaly + pd.Series(tuning_pairs.index.month, index=tuning_pairs.index).map(flow_climatology)
        observed_flow = data.loc[tuning_pairs.index, FLOW]
        score = calculate_metrics(observed_flow, predicted_flow)
        rows.append(
            {
                "candidate_lag_months": lag,
                "fit_n": len(fit_pairs),
                "tuning_n": score["n"],
                "tuning_bias": score["bias_pred_minus_obs"],
                "tuning_mae": score["mae"],
                "tuning_rmse": score["rmse"],
            }
        )

    if not rows:
        raise ValueError(f"No hay suficientes pares para seleccionar un rezago con {rain_column}.")
    selected = min(rows, key=lambda row: (row["tuning_mae"], row["tuning_rmse"]))
    for row in rows:
        row["selected_on_inner_tuning"] = row["candidate_lag_months"] == selected["candidate_lag_months"]
    return int(selected["candidate_lag_months"]), rows


def evaluate_flow_estimation(
    data: pd.DataFrame,
    *,
    rain_column: str,
    outer_start: pd.Timestamp,
    tuning_start: pd.Timestamp,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    lag_months, lag_selection_rows = select_anomaly_lag(
        data,
        rain_column=rain_column,
        outer_start=outer_start,
        tuning_start=tuning_start,
    )
    training_mask = data.index < outer_start
    training = data.loc[training_mask]
    test_mask = data.index >= outer_start

    flow_climatology = monthly_climatology(training[FLOW].dropna())
    rain_climatology = monthly_climatology(training[rain_column].dropna())
    flow_anomaly = anomalies_from_climatology(data[FLOW], flow_climatology)
    rain_anomaly = anomalies_from_climatology(data[rain_column], rain_climatology)
    lagged_rain_anomaly = rain_anomaly.shift(lag_months)

    common_test_mask = test_mask & data[FLOW].notna() & data[rain_column].notna() & lagged_rain_anomaly.notna()
    common_test_dates = data.index[common_test_mask]
    raw_train = data.loc[training_mask, [rain_column, FLOW]].dropna()
    raw_test = data.loc[common_test_dates, [rain_column, FLOW]].dropna()
    if min(len(raw_train), len(raw_test)) < 12:
        raise ValueError(f"Muy pocos pares para regresión contemporánea {FLOW} ~ {rain_column}.")
    raw_coefficients = fit_linear(raw_train[rain_column], raw_train[FLOW])
    raw_predictions = predict_linear(raw_test[rain_column], raw_coefficients)

    anomaly_train = pd.DataFrame({"rain_anomaly": lagged_rain_anomaly, "flow_anomaly": flow_anomaly}).loc[training_mask].dropna()
    anomaly_test = pd.DataFrame({"rain_anomaly": lagged_rain_anomaly, "flow_anomaly": flow_anomaly}).loc[common_test_dates].dropna()
    if min(len(anomaly_train), len(anomaly_test)) < 12:
        raise ValueError(f"Muy pocos pares para modelo de anomalías con {rain_column}.")
    anomaly_coefficients = fit_linear(anomaly_train["rain_anomaly"], anomaly_train["flow_anomaly"])
    predicted_flow_anomaly = predict_linear(anomaly_test["rain_anomaly"], anomaly_coefficients)
    seasonal_baseline = pd.Series(anomaly_test.index.month, index=anomaly_test.index).map(flow_climatology)
    anomaly_predictions = predicted_flow_anomaly + seasonal_baseline
    climatology_test = data.loc[common_test_dates, FLOW]
    climatology_predictions = pd.Series(climatology_test.index.month, index=climatology_test.index).map(flow_climatology)

    predictor_label = f"{rain_column} (mm/mes)"
    prediction_records = []
    models = [
        ("Climatología mensual Q", climatology_test, climatology_predictions, None),
        ("Regresión lineal Q~P(t)", raw_test[FLOW], raw_predictions, 0),
        ("Regresión de anomalías con rezago", data.loc[anomaly_test.index, FLOW], anomaly_predictions, lag_months),
    ]
    for model_name, observed, predicted, selected_lag in models:
        append_predictions(
            prediction_records,
            task="estimar_caudal",
            predictor=predictor_label,
            target=FLOW,
            model=model_name,
            observed=observed,
            predicted=predicted,
            outer_start=outer_start,
            training_end=training.index.max(),
            tuning_start=tuning_start,
            lag_months=selected_lag,
        )

    selection_rows = [
        {
            "task": "estimar_caudal",
            "predictor": rain_column,
            "candidate_model": "Regresión de anomalías con rezago",
            "candidate_lag_months": row["candidate_lag_months"],
            "fit_n": row["fit_n"],
            "tuning_n": row["tuning_n"],
            "tuning_bias": row["tuning_bias"],
            "tuning_mae": row["tuning_mae"],
            "tuning_rmse": row["tuning_rmse"],
            "selected_on_inner_tuning": row["selected_on_inner_tuning"],
            "fit_period_start": data.loc[data.index < tuning_start, rain_column].dropna().index.min().strftime("%Y-%m"),
            "fit_period_end": (tuning_start - pd.offsets.MonthBegin(1)).strftime("%Y-%m"),
            "tuning_period_start": tuning_start.strftime("%Y-%m"),
            "tuning_period_end": (outer_start - pd.offsets.MonthBegin(1)).strftime("%Y-%m"),
            "outer_training_end": training.index.max().strftime("%Y-%m"),
            "raw_regression_intercept": raw_coefficients[0],
            "raw_regression_slope": raw_coefficients[1],
            "anomaly_model_intercept": anomaly_coefficients[0],
            "anomaly_model_slope": anomaly_coefficients[1],
        }
        for row in lag_selection_rows
    ]
    return prediction_records, selection_rows


def plot_validation(predictions: pd.DataFrame, path: Path) -> None:
    plot_specs = [
        ("estimar_precipitacion_local", None, "Lluvia local desde IMERG"),
        ("estimar_caudal", f"{RAIN_LOCAL} (mm/mes)", "Caudal desde lluvia local"),
        ("estimar_caudal", f"{RAIN_SATELLITE} (mm/mes)", "Caudal desde IMERG"),
    ]
    figure, axes = plt.subplots(2, 3, figsize=(17, 9), constrained_layout=True)

    for column, (task, predictor, task_label) in enumerate(plot_specs):
        task_rows = predictions.loc[predictions["task"] == task]
        if predictor is not None:
            task_rows = task_rows.loc[task_rows["predictor"] == predictor]
        for model, group in task_rows.groupby("model", sort=False):
            color = PREDICTION_COLORS.get(model, "#237A68")
            axes[0, column].plot(group["date"], group["predicted"], color=color, linewidth=1.2, alpha=0.85, label=model)
        observed = task_rows.drop_duplicates(subset="date").sort_values("date")
        axes[0, column].plot(observed["date"], observed["observed"], color="#202A35", linewidth=1.7, label="Observado")
        axes[0, column].set_title(task_label)
        axes[0, column].set_ylabel("mm/mes" if task == "estimar_precipitacion_local" else "m3/s")
        axes[0, column].grid(True, color="#D9DEE5", linewidth=0.7, alpha=0.8)
        axes[0, column].legend(frameon=False, fontsize=8)

        for model, group in task_rows.groupby("model", sort=False):
            color = PREDICTION_COLORS.get(model, "#237A68")
            axes[1, column].scatter(group["predicted"], group["residual_pred_minus_obs"], s=22, alpha=0.7, color=color, label=model)
        axes[1, column].axhline(0, color="#202A35", linewidth=0.9)
        axes[1, column].set_xlabel("Predicción")
        axes[1, column].set_ylabel("Residuo (predicho - observado)")
        axes[1, column].grid(True, color="#D9DEE5", linewidth=0.7, alpha=0.8)

    figure.suptitle("Evaluación cronológica fuera del ajuste: predicciones y residuos", fontsize=14)
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_residuals_over_time(predictions: pd.DataFrame, path: Path) -> None:
    plot_specs = [
        ("estimar_precipitacion_local", None, "Lluvia local desde IMERG"),
        ("estimar_caudal", f"{RAIN_LOCAL} (mm/mes)", "Caudal desde lluvia local"),
        ("estimar_caudal", f"{RAIN_SATELLITE} (mm/mes)", "Caudal desde IMERG"),
    ]
    figure, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=False, constrained_layout=True)

    for axis, (task, predictor, task_label) in zip(axes, plot_specs):
        task_rows = predictions.loc[predictions["task"] == task]
        if predictor is not None:
            task_rows = task_rows.loc[task_rows["predictor"] == predictor]
        for model, group in task_rows.groupby("model", sort=False):
            ordered = group.sort_values("date")
            axis.plot(
                ordered["date"],
                ordered["residual_pred_minus_obs"],
                color=PREDICTION_COLORS.get(model, "#237A68"),
                marker="o",
                markersize=3,
                linewidth=1,
                label=model,
            )
        axis.axhline(0, color="#202A35", linewidth=0.9)
        axis.set_title(task_label)
        axis.set_ylabel("Residuo (mm/mes)" if task == "estimar_precipitacion_local" else "Residuo (m3/s)")
        axis.grid(True, color="#D9DEE5", linewidth=0.7, alpha=0.8)
        if not task_rows.empty:
            axis.legend(frameon=False, fontsize=8, ncol=3)

    axes[-1].set_xlabel("Fecha del bloque de evaluación")
    figure.suptitle("Residuos temporales en el test cronológico (predicho - observado)", fontsize=14)
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    data = load_data()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    prediction_records: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []

    rain_predictions, rain_selections = evaluate_precipitation_estimation(data)
    prediction_records.extend(rain_predictions)
    selection_rows.extend(rain_selections)

    local_flow_predictions, local_flow_selections = evaluate_flow_estimation(
        data,
        rain_column=RAIN_LOCAL,
        outer_start=pd.Timestamp("2012-01-01"),
        tuning_start=pd.Timestamp("2008-01-01"),
    )
    prediction_records.extend(local_flow_predictions)
    selection_rows.extend(local_flow_selections)

    satellite_flow_predictions, satellite_flow_selections = evaluate_flow_estimation(
        data,
        rain_column=RAIN_SATELLITE,
        outer_start=pd.Timestamp("2016-01-01"),
        tuning_start=pd.Timestamp("2012-01-01"),
    )
    prediction_records.extend(satellite_flow_predictions)
    selection_rows.extend(satellite_flow_selections)

    predictions = pd.DataFrame(prediction_records)
    selections = pd.DataFrame(selection_rows)
    metrics, annual_metrics, monthly_metrics, seasonal_metrics = summarize_predictions(predictions)

    predictions_path = FIGURES_DIR / "tabla_2_3_predicciones_fuera_ajuste.csv"
    metrics_path = FIGURES_DIR / "tabla_2_3_metricas_fuera_ajuste.csv"
    annual_path = FIGURES_DIR / "tabla_2_3_metricas_por_anio.csv"
    monthly_path = FIGURES_DIR / "tabla_2_3_residuos_por_mes.csv"
    seasonal_path = FIGURES_DIR / "tabla_2_3_metricas_por_estacion.csv"
    selections_path = FIGURES_DIR / "tabla_2_3_seleccion_modelos_ajuste.csv"
    figure_path = FIGURES_DIR / "figura_2_3_validacion_modelos.png"
    residual_time_figure_path = FIGURES_DIR / "figura_2_4_residuos_en_tiempo.png"

    predictions.to_csv(predictions_path, index=False, date_format="%Y-%m-%d", float_format="%.6f")
    metrics.to_csv(metrics_path, index=False, float_format="%.6f")
    annual_metrics.to_csv(annual_path, index=False, float_format="%.6f")
    monthly_metrics.to_csv(monthly_path, index=False, float_format="%.6f")
    seasonal_metrics.to_csv(seasonal_path, index=False, float_format="%.6f")
    selections.to_csv(selections_path, index=False, float_format="%.6f")
    plot_validation(predictions, figure_path)
    plot_residuals_over_time(predictions, residual_time_figure_path)

    test_window_specs = [
        (
            "PL desde IMERG",
            "estimar_precipitacion_local",
            RAIN_SATELLITE,
            "IMERG sin corrección",
            "ajuste 2000-06..2015-12; selección interna 2013-01..2015-12",
        ),
        (
            "Q desde P local",
            "estimar_caudal",
            f"{RAIN_LOCAL} (mm/mes)",
            "Climatología mensual Q",
            "ajuste 1980-01..2011-12; selección interna 2008-01..2011-12",
        ),
        (
            "Q desde IMERG",
            "estimar_caudal",
            f"{RAIN_SATELLITE} (mm/mes)",
            "Climatología mensual Q",
            "ajuste 2000-06..2015-12; selección interna 2012-01..2015-12",
        ),
    ]
    print("Particiones temporales; cortes definidos en años completos:")
    for label, task, predictor, model, training_description in test_window_specs:
        test_summary = metrics.loc[
            (metrics["task"] == task)
            & (metrics["predictor"] == predictor)
            & (metrics["model"] == model)
        ].iloc[0]
        print(
            f"{label}: {training_description}; test válido "
            f"{test_summary['test_start']}..{test_summary['test_end']} "
            f"(n={int(test_summary['n'])})."
        )
    print("La climatología de las anomalías y del benchmark de caudal se calcula solo con el ajuste correspondiente.")
    print("\nMétricas fuera de ajuste:")
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print("\nSelección interna de transformaciones/rezagos (no usa el bloque externo de test):")
    print(selections.loc[selections["selected_on_inner_tuning"]].to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print("\nSalidas generadas:")
    for output_path in [predictions_path, metrics_path, annual_path, monthly_path, seasonal_path, selections_path, figure_path, residual_time_figure_path]:
        print(f"- {output_path.relative_to(ROOT_DIR)}")
    print("\nNota: la prueba externa es cronológica y no aleatoria; sus resultados son una evaluación retrospectiva en una única partición temporal.")


if __name__ == "__main__":
    main()