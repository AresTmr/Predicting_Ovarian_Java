from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
import shap

UI_INPUT_ATTRIBUTION_FEATURES = {
    "age",
    "bmi",
    "infertility_duration",
    "amh",
    "afc",
    "basal_fsh",
    "basal_lh",
    "basal_e2",
    "basal_p",
    "Day",
    "gn_day",
    "days_since_previous_visit",
    "current_e2",
    "current_lh",
    "current_p",
    "current_fsh",
    "current_endometrium",
    "total_follicle_count",
    "left_follicle_count",
    "right_follicle_count",
    "max_follicle_diameter",
    "mean_follicle_diameter",
    "follicle_count_lt_10",
    "follicle_count_10_12",
    "follicle_count_13_15",
    "follicle_count_16_18",
    "follicle_count_gt_18",
    "previous_fsh_daily_dose",
    "previous_lh_daily_dose",
    "previous_hmg_daily_dose",
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _to_int(value: Any, default: int = 0) -> int:
    return int(round(_to_float(value, float(default))))


def _safe_divide(numerator: Any, denominator: Any) -> float:
    numerator_value = _to_float(numerator, float("nan"))
    denominator_value = _to_float(denominator, float("nan"))
    if (
        not math.isfinite(numerator_value)
        or not math.isfinite(denominator_value)
        or abs(denominator_value) < 1e-12
    ):
        return float("nan")
    return float(numerator_value / denominator_value)


def _clip_probability(value: Any) -> float:
    return float(np.clip(_to_float(value, 0.0), 0.0, 1.0))


def _bound_count_prediction(value: Any, total_follicles: Any | None = None) -> float:
    prediction = max(0.0, _to_float(value, 0.0))
    if total_follicles is not None and math.isfinite(_to_float(total_follicles, float("nan"))):
        prediction = min(prediction, _to_float(total_follicles, 0.0))
    return float(prediction)


def patient_form_to_snapshot(form: Mapping[str, Any]) -> pd.Series:
    """Build the feature snapshot used by the candidate response bundles."""
    fsh_dose = _to_float(
        form.get("reference_fsh", form.get("previous_fsh_daily_dose", form.get("current_fsh")))
    )
    lh_dose = _to_float(
        form.get("reference_lh", form.get("previous_lh_daily_dose", form.get("current_lh")))
    )
    hmg_dose = _to_float(
        form.get("reference_hmg", form.get("previous_hmg_daily_dose", form.get("current_hmg")))
    )
    lh_like_dose = lh_dose + hmg_dose
    current_total = fsh_dose + lh_like_dose

    f_lt10 = _to_int(form.get("f_lt10"))
    f_10_12 = _to_int(form.get("f_10_12"))
    f_13_15 = _to_int(form.get("f_13_15"))
    f_16_18 = _to_int(form.get("f_16_18"))
    f_gt18 = _to_int(form.get("f_gt18"))
    binned_total = f_lt10 + f_10_12 + f_13_15 + f_16_18 + f_gt18
    explicit_total = form.get("total_follicles", form.get("total_follicle_count"))
    total_follicles = (
        _to_int(explicit_total, binned_total)
        if explicit_total not in (None, "")
        else binned_total
    )
    mature_follicles = f_16_18 + f_gt18
    left_follicles = _to_int(
        form.get("left_follicles", form.get("left_follicle_count")),
        0,
    )
    right_follicles = _to_int(
        form.get("right_follicles", form.get("right_follicle_count")),
        0,
    )
    serum_fsh = _to_float(
        form.get("serum_fsh", form.get("current_fsh_value", form.get("current_serum_fsh"))),
        float("nan"),
    )
    patient_id = str(form.get("patient_id", "ui_patient"))
    visit = _to_int(form.get("visit"), 1)
    stim_day = _to_int(form.get("stim_day"), 1)
    snapshot = {
        "art_id": patient_id,
        "cycle_uid": str(form.get("cycle_uid", f"{patient_id}__ui")),
        "visit_uid": str(form.get("visit_uid", f"{patient_id}__ui_m{visit}")),
        "canonical_visit_key": str(form.get("visit_uid", f"{patient_id}__ui_m{visit}")),
        "monitoring_order": visit,
        "Day": stim_day,
        "age": _to_float(form.get("age")),
        "bmi": _to_float(form.get("bmi")),
        "infertility_duration": _to_float(form.get("years", form.get("infertility_duration"))),
        "diagnosis_primary_secondary": form.get("diagnosis", form.get("infertility", "未知")),
        "afc": _to_float(form.get("afc")),
        "amh": _to_float(form.get("amh")),
        "initial_gn_dose": _to_float(
            form.get("initial_gn", form.get("initial_gn_dose")),
            current_total,
        ),
        "basal_fsh": _to_float(form.get("basal_fsh")),
        "basal_lh": _to_float(form.get("basal_lh")),
        "basal_e2": _to_float(form.get("basal_e2")),
        "basal_p": _to_float(form.get("basal_p")),
        "male_factor_infertility_flag": 0
        if str(form.get("male_factor_infertility", "否")) in {"否", "0", "False"}
        else 1,
        "male_age": _to_float(form.get("male_age"), float("nan")),
        "sperm_source_group": form.get("sperm_source_group", "Unknown"),
        "fertilization_method": form.get("fertilization_method", "Unknown"),
        "current_e2": _to_float(form.get("e2", form.get("current_e2"))),
        "current_lh": _to_float(form.get("lh_value", form.get("current_lh_value"))),
        "current_p": _to_float(form.get("p", form.get("current_p"))),
        "current_fsh": serum_fsh,
        "current_endometrium": _to_float(form.get("current_endometrium"), float("nan")),
        "current_fsh_daily_dose": fsh_dose,
        "current_lh_daily_dose": lh_dose,
        "current_hmg_daily_dose": hmg_dose,
        "current_lh_like_hmg_daily_dose": lh_like_dose,
        "previous_fsh_daily_dose": fsh_dose,
        "previous_lh_daily_dose": lh_dose,
        "previous_hmg_daily_dose": hmg_dose,
        "previous_lh_like_hmg_daily_dose": lh_like_dose,
        "current_gn_dose": current_total,
        "cumulative_fsh_dose": fsh_dose * stim_day,
        "cumulative_lh_dose": lh_dose * stim_day,
        "cumulative_hmg_dose": hmg_dose * stim_day,
        "cumulative_lh_like_hmg_dose": lh_like_dose * stim_day,
        "cumulative_gn_dose": current_total * stim_day,
        "gn_day": stim_day,
        "cycle_day": _to_float(form.get("cycle_day"), float("nan")),
        "previous_gn_dose": _to_float(form.get("previous_gn_dose"), current_total),
        "delta_e2": _to_float(form.get("delta_e2"), float("nan")),
        "delta_lh": _to_float(form.get("delta_lh"), float("nan")),
        "delta_p": _to_float(form.get("delta_p"), float("nan")),
        "days_since_previous_visit": _to_float(
            form.get("days_since_previous_visit"),
            float("nan"),
        ),
        "visits_seen": visit,
        "follicle_count_lt_10": f_lt10,
        "follicle_count_10_12": f_10_12,
        "follicle_count_13_15": f_13_15,
        "follicle_count_16_18": f_16_18,
        "follicle_count_gt_18": f_gt18,
        "total_follicle_count": total_follicles,
        "left_follicle_count": left_follicles,
        "right_follicle_count": right_follicles,
        "mature_follicle_count": mature_follicles,
        "growing_follicle_count": f_10_12 + f_13_15 + f_16_18 + f_gt18,
        "medium_plus_follicle_count": f_13_15 + f_16_18 + f_gt18,
        "max_follicle_diameter": _to_float(form.get("max_f")),
        "mean_follicle_diameter": _to_float(
            form.get("mean_f", form.get("mean_follicle_diameter")),
            float("nan"),
        ),
        "follicle_maturity_index": mature_follicles / total_follicles
        if total_follicles
        else 0.0,
        "mature_follicle_share": mature_follicles / total_follicles
        if total_follicles
        else 0.0,
        "large_follicle_share": f_gt18 / total_follicles if total_follicles else 0.0,
    }
    return pd.Series(snapshot)


def build_candidate_features(
    snapshot: Mapping[str, Any],
    fsh_dose: float,
    lh_dose: float,
    hmg_dose: float,
) -> pd.Series:
    row = pd.Series(snapshot).copy()
    current_fsh = _to_float(row.get("current_fsh_daily_dose"), 0.0)
    current_lh = _to_float(row.get("current_lh_daily_dose"), 0.0)
    current_hmg = _to_float(row.get("current_hmg_daily_dose"), 0.0)
    current_total = _to_float(row.get("current_gn_dose"), current_fsh + current_lh + current_hmg)
    fsh = max(_to_float(fsh_dose), 0.0)
    lh = max(_to_float(lh_dose), 0.0)
    hmg = max(_to_float(hmg_dose), 0.0)
    lh_like = lh + hmg
    total = fsh + lh_like
    total_follicles = _to_float(row.get("total_follicle_count"), float("nan"))
    mature_follicles = _to_float(row.get("mature_follicle_count"), float("nan"))
    current_e2 = _to_float(row.get("current_e2"), float("nan"))
    row["candidate_fsh_daily_dose"] = fsh
    row["candidate_lh_daily_dose"] = lh
    row["candidate_hmg_daily_dose"] = hmg
    row["candidate_lh_like_hmg_daily_dose"] = lh_like
    row["candidate_total_gn_dose"] = total
    row["candidate_fsh_delta"] = fsh - current_fsh
    row["candidate_lh_delta"] = lh - current_lh
    row["candidate_hmg_delta"] = hmg - current_hmg
    row["candidate_lh_like_delta"] = lh_like - (current_lh + current_hmg)
    row["candidate_total_gn_delta"] = total - current_total
    row["candidate_gn_per_total_follicle"] = _safe_divide(total, total_follicles)
    row["candidate_gn_per_mature_follicle"] = _safe_divide(total, mature_follicles)
    row["candidate_e2_per_gn"] = _safe_divide(current_e2, total)
    row["candidate_fsh_share_gn"] = _safe_divide(fsh, total)
    row["candidate_lh_like_share_gn"] = _safe_divide(lh_like, total)
    row["candidate_total_to_current_ratio"] = _safe_divide(total, current_total)
    return row


def _feature_names(bundle: Mapping[str, Any]) -> list[str]:
    preprocessor = bundle["preprocessor"]
    if hasattr(preprocessor, "feature_names_in_"):
        return [str(item) for item in preprocessor.feature_names_in_]
    names = bundle.get("feature_columns") or bundle.get("feature_names")
    if names:
        return [str(item) for item in names]
    raise ValueError("Candidate bundle has no feature contract")


def _predict_task(row: pd.Series, bundle: Mapping[str, Any]) -> float:
    frame = row.to_frame().T.reindex(columns=_feature_names(bundle))
    matrix = bundle["preprocessor"].transform(frame)
    estimator = bundle["estimator"]
    if str(bundle.get("task_type", "regression")) == "classification":
        if hasattr(estimator, "predict_proba"):
            probabilities = np.asarray(estimator.predict_proba(matrix), dtype=float)
            raw = probabilities[0, 1] if probabilities.ndim == 2 and probabilities.shape[1] > 1 else probabilities.reshape(-1)[0]
        else:
            raw = float(np.asarray(estimator.predict(matrix)).reshape(-1)[0])
        calibration = bundle.get("probability_calibration") or {}
        if calibration.get("method") == "isotonic":
            x = np.asarray(calibration.get("x_thresholds", []), dtype=float)
            y = np.asarray(calibration.get("y_thresholds", []), dtype=float)
            if len(x) >= 2 and len(x) == len(y):
                raw = float(np.interp(raw, x, y))
        elif calibration.get("method") == "sigmoid":
            coef = float(calibration.get("coef", 1.0))
            intercept = float(calibration.get("intercept", 0.0))
            raw = float(1.0 / (1.0 + np.exp(-((coef * raw) + intercept))))
        return _clip_probability(raw)
    return float(np.asarray(estimator.predict(matrix)).reshape(-1)[0])


def _calibrated_probability(raw: float, bundle: Mapping[str, Any]) -> float:
    value = float(raw)
    calibration = bundle.get("probability_calibration") or {}
    if calibration.get("method") == "isotonic":
        x = np.asarray(calibration.get("x_thresholds", []), dtype=float)
        y = np.asarray(calibration.get("y_thresholds", []), dtype=float)
        if len(x) >= 2 and len(x) == len(y):
            value = float(np.interp(value, x, y))
    elif calibration.get("method") == "sigmoid":
        coef = float(calibration.get("coef", 1.0))
        intercept = float(calibration.get("intercept", 0.0))
        value = float(1.0 / (1.0 + np.exp(-((coef * value) + intercept))))
    return _clip_probability(value)


def _tree_shap(
    estimator: Any,
    matrix: np.ndarray,
    background: np.ndarray | None = None,
) -> tuple[np.ndarray, float]:
    explainer = (
        shap.TreeExplainer(estimator, data=background)
        if background is not None
        else shap.TreeExplainer(estimator)
    )
    values = explainer.shap_values(matrix)
    expected = explainer.expected_value
    if isinstance(values, list):
        values = values[-1]
    values = np.asarray(values, dtype=float)
    if values.ndim == 3:
        values = values[:, :, -1]
    if values.ndim == 1:
        values = values.reshape(1, -1)
    expected_values = np.asarray(expected, dtype=float).reshape(-1)
    return values, float(expected_values[-1])


def _transformed_source_names(bundle: Mapping[str, Any]) -> list[str]:
    feature_names = _feature_names(bundle)
    transformed = [str(name) for name in bundle["preprocessor"].get_feature_names_out()]
    ordered = sorted(feature_names, key=len, reverse=True)
    sources: list[str] = []
    for transformed_name in transformed:
        stripped = transformed_name.split("__", 1)[-1]
        source = next(
            (
                feature
                for feature in ordered
                if stripped == feature or stripped.startswith(f"{feature}_")
            ),
            stripped,
        )
        sources.append(source)
    return sources


class CandidateRuntime:
    def __init__(self, model_root: Path):
        self.model_root = Path(model_root)
        self.efficacy_bundle = joblib.load(
            self.model_root / "candidate" / "efficacy" / "bundle.joblib"
        )
        self.safety_bundle = joblib.load(
            self.model_root / "candidate" / "safety" / "bundle.joblib"
        )

    @staticmethod
    def _tasks(bundle: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
        return bundle.get("tasks", bundle)

    def score(
        self,
        snapshot: Mapping[str, Any],
        fsh_dose: float,
        lh_dose: float,
        hmg_dose: float,
    ) -> dict[str, Any]:
        row = build_candidate_features(snapshot, fsh_dose, lh_dose, hmg_dose)
        efficacy = self._tasks(self.efficacy_bundle)
        safety = self._tasks(self.safety_bundle)
        raw_oocytes = _predict_task(row, efficacy["layer2_oocytes"])
        raw_mii = _predict_task(row, efficacy["layer2_mii"])
        total_follicles = row.get("total_follicle_count")
        oocytes = _bound_count_prediction(raw_oocytes, total_follicles)
        mii = _bound_count_prediction(raw_mii, total_follicles)
        mii = min(mii, oocytes) if math.isfinite(oocytes) else mii
        ohss = _predict_task(row, safety["layer2_ohss"])
        return {
            "source": "candidate_response_v2_xgb_plus_modsev_ohss",
            "efficacyRunId": self.efficacy_bundle.get("run_id"),
            "safetyRunId": self.safety_bundle.get("run_id"),
            "oocytes": float(oocytes),
            "mii": float(mii),
            "oocytesRaw": float(max(0.0, raw_oocytes)),
            "miiRaw": float(max(0.0, raw_mii)),
            "ohssRisk": float(ohss),
        }

    def explain(
        self,
        snapshot: Mapping[str, Any],
        fsh_dose: float,
        lh_dose: float,
        hmg_dose: float,
        task: str,
        limit: int = 128,
    ) -> dict[str, Any]:
        if task in {"layer2_oocytes", "layer2_mii"}:
            active_bundle = self.efficacy_bundle
        elif task == "layer2_ohss":
            active_bundle = self.safety_bundle
        else:
            raise ValueError(f"Unknown explanation task: {task}")
        task_bundle = self._tasks(active_bundle)[task]
        row = build_candidate_features(snapshot, fsh_dose, lh_dose, hmg_dose)
        frame = row.to_frame().T.reindex(columns=_feature_names(task_bundle))
        matrix = np.asarray(task_bundle["preprocessor"].transform(frame), dtype=float)
        conditional_background = frame.copy()
        for feature in conditional_background.columns:
            if str(feature) in UI_INPUT_ATTRIBUTION_FEATURES:
                conditional_background.loc[:, feature] = np.nan
        background_matrix = np.asarray(
            task_bundle["preprocessor"].transform(conditional_background),
            dtype=float,
        )
        estimator = task_bundle["estimator"]
        values, raw_baseline = _tree_shap(estimator, matrix, background=background_matrix)
        raw_values = values[0]
        task_type = str(task_bundle.get("task_type", "regression"))
        if task_type == "classification":
            probabilities = np.asarray(estimator.predict_proba(matrix), dtype=float)
            raw_prediction = float(
                probabilities[0, 1]
                if probabilities.ndim == 2 and probabilities.shape[1] > 1
                else probabilities.reshape(-1)[0]
            )
            baseline_prediction = _calibrated_probability(raw_baseline, task_bundle)
            prediction = _calibrated_probability(raw_prediction, task_bundle)
            raw_sum = float(raw_values.sum())
            scale = (
                (prediction - baseline_prediction) / raw_sum
                if abs(raw_sum) > 1e-12
                else 0.0
            )
            aligned_values = raw_values * scale
            scale_name = "calibrated_probability"
        else:
            raw_prediction = float(np.asarray(estimator.predict(matrix)).reshape(-1)[0])
            baseline_prediction = float(raw_baseline)
            prediction = raw_prediction
            aligned_values = raw_values
            scale_name = "prediction_value"
        source_names = _transformed_source_names(task_bundle)
        grouped: dict[str, float] = {}
        for source, value in zip(source_names, aligned_values):
            grouped[source] = grouped.get(source, 0.0) + float(value)
        items = [
            {
                "feature": feature,
                "mean_abs_shap": abs(value),
                "mean_shap": value,
                "direction": "increases_prediction" if value >= 0 else "decreases_prediction",
            }
            for feature, value in grouped.items()
        ]
        items.sort(key=lambda item: abs(float(item["mean_shap"])), reverse=True)
        return {
            "task": task,
            "runId": str(active_bundle.get("run_id", "")),
            "modelName": str(task_bundle.get("selected_model_name", task_bundle.get("model_family", ""))),
            "method": f"candidate_response_tree_shap_{task}_{scale_name}",
            "baselinePrediction": float(baseline_prediction),
            "prediction": float(prediction),
            "items": items[: max(1, int(limit))],
        }
