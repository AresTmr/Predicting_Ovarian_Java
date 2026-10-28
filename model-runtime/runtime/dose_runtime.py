from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence

from .candidate_runtime import UI_INPUT_ATTRIBUTION_FEATURES


TARGETS = ("fsh", "lh", "hmg")
MAX_HISTORY_DAYS = 16

STATIC_ALIASES = {
    "age": ("age",),
    "bmi": ("bmi",),
    "amh": ("amh",),
    "afc": ("afc",),
    "basal_fsh": ("basal_fsh",),
    "basal_lh": ("basal_lh",),
    "basal_e2": ("basal_e2",),
    "basal_p": ("basal_p",),
    "infertility_duration": ("infertility_duration", "years"),
}

DYNAMIC_ALIASES = {
    "current_e2": ("current_e2", "e2"),
    "current_lh": ("current_lh", "lh_value", "current_lh_value"),
    "current_p": ("current_p", "p"),
    "current_fsh": ("current_fsh_value", "serum_fsh", "current_serum_fsh"),
    "current_endometrium": ("current_endometrium", "endometrium_thickness"),
    "total_follicle_count": ("total_follicle_count", "total_follicles"),
    "left_follicle_count": ("left_follicle_count", "left_follicles"),
    "right_follicle_count": ("right_follicle_count", "right_follicles"),
    "max_follicle_diameter": ("max_follicle_diameter", "max_f"),
    "mean_follicle_diameter": ("mean_follicle_diameter", "mean_f"),
    "follicle_count_lt_10": ("follicle_count_lt_10", "f_lt10"),
    "follicle_count_10_12": ("follicle_count_10_12", "f_10_12"),
    "follicle_count_13_15": ("follicle_count_13_15", "f_13_15"),
    "follicle_count_16_18": ("follicle_count_16_18", "f_16_18"),
    "follicle_count_gt_18": ("follicle_count_gt_18", "f_gt18"),
    "previous_fsh_daily_dose": ("previous_fsh_daily_dose", "current_fsh"),
    "previous_lh_daily_dose": ("previous_lh_daily_dose", "current_lh"),
    "previous_hmg_daily_dose": ("previous_hmg_daily_dose", "current_hmg"),
}

PREVIOUS_DOSE_FROM_PRIOR_RECORD = {
    "previous_fsh_daily_dose": "current_fsh",
    "previous_lh_daily_dose": "current_lh",
    "previous_hmg_daily_dose": "current_hmg",
}


def _to_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _first_numeric(source: Mapping[str, Any], aliases: Sequence[str]) -> tuple[float, bool]:
    for key in aliases:
        if key in source and source.get(key) not in (None, ""):
            value = _to_float(source.get(key))
            if math.isfinite(value):
                return value, True
    return float("nan"), False


def _apply_imputer(values: np.ndarray, statistics: Sequence[float]) -> np.ndarray:
    output = np.asarray(values, dtype=np.float64).copy()
    stats = np.asarray(statistics, dtype=np.float64)
    missing = ~np.isfinite(output)
    if output.ndim == 1:
        output[missing] = stats[missing]
    else:
        np.copyto(output, np.broadcast_to(stats, output.shape), where=missing)
    return output


def _apply_scaler(
    values: np.ndarray,
    mean: Sequence[float],
    scale: Sequence[float],
) -> np.ndarray:
    mean_array = np.asarray(mean, dtype=np.float64)
    scale_array = np.asarray(scale, dtype=np.float64)
    scale_array = np.where(np.abs(scale_array) < 1e-12, 1.0, scale_array)
    return (np.asarray(values, dtype=np.float64) - mean_array) / scale_array


class FusionGRUAddGate(nn.Module):
    """The checkpoint architecture used by the original dose models."""

    def __init__(self, static_dim: int, dynamic_dim: int, hidden_dim: int, num_classes: int, dropout: float):
        super().__init__()
        self.dynamic_rnn = nn.GRU(dynamic_dim, hidden_dim, batch_first=True)
        self.cross_rnn = nn.GRU(static_dim + dynamic_dim, hidden_dim, batch_first=True)
        self.gate = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.Sigmoid())
        self.fuse = nn.Sequential(nn.LayerNorm(hidden_dim), nn.Dropout(dropout))
        self.classifier = nn.Linear(hidden_dim, num_classes)

    @staticmethod
    def _last(rnn: nn.GRU, sequence: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        lengths = mask.sum(dim=1).long().clamp_min(1).cpu()
        packed = pack_padded_sequence(sequence, lengths, batch_first=True, enforce_sorted=False)
        _, hidden = rnn(packed)
        return hidden[-1]

    def forward(self, static_x: torch.Tensor, dynamic_x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        static_sequence = static_x.unsqueeze(1).expand(-1, dynamic_x.shape[1], -1)
        dynamic_h = self._last(self.dynamic_rnn, dynamic_x, mask)
        cross_h = self._last(
            self.cross_rnn,
            torch.cat([static_sequence, dynamic_x], dim=-1),
            mask,
        )
        joint = torch.cat([dynamic_h, cross_h], dim=1)
        embedding = self.fuse(dynamic_h + self.gate(joint) * cross_h)
        return self.classifier(embedding)


class DoseRuntime:
    def __init__(self, model_root: Path, preprocessing_root: Path | None = None):
        self.model_root = Path(model_root)
        self.preprocessing_root = Path(preprocessing_root or self.model_root / "preprocessing")
        self.models: dict[str, FusionGRUAddGate] = {}
        self.configs: dict[str, dict[str, Any]] = {}
        self.backgrounds: dict[str, dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]] = {}
        self._load()

    def _load(self) -> None:
        for target in TARGETS:
            config_path = self.preprocessing_root / f"{target}.json"
            if not config_path.exists():
                raise FileNotFoundError(f"Missing preprocessing config: {config_path}")
            config = json.loads(config_path.read_text(encoding="utf-8"))
            checkpoint = torch.load(
                self.model_root / "models" / "dose" / f"{target}.pt",
                map_location="cpu",
                weights_only=False,
            )
            model = FusionGRUAddGate(
                static_dim=len(config["staticFeatures"]),
                dynamic_dim=len(config["dynamicFeatures"]),
                hidden_dim=int(config["hiddenDim"]),
                num_classes=len(config["labels"]),
                dropout=float(config["dropout"]),
            )
            model.load_state_dict(checkpoint["state_dict"])
            model.eval()
            self.models[target] = model
            self.configs[target] = config
            background_path = self.preprocessing_root / config["backgroundPath"]
            background_data = np.load(background_path)
            backgrounds: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
            for count in config.get("backgroundCounts", []):
                key = f"count_{int(count)}"
                backgrounds[int(count)] = (
                    np.asarray(background_data[f"{key}_static"], dtype=np.float32),
                    np.asarray(background_data[f"{key}_dynamic"], dtype=np.float32),
                    np.asarray(background_data[f"{key}_mask"], dtype=np.float32),
                )
            self.backgrounds[target] = backgrounds

    def build_sequence_input(
        self,
        patient: Mapping[str, Any],
        records: Sequence[Mapping[str, Any]],
        target: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
        config = self.configs[target]
        static_features = config["staticFeatures"]
        dynamic_features = config["dynamicFeatures"]
        active_records = [dict(row) for row in records if isinstance(row, Mapping)]
        if not active_records:
            active_records = [dict(patient)]
        warnings: list[str] = []

        static_values: dict[str, float] = {}
        for feature in static_features:
            if feature == "male_factor_infertility_flag":
                raw = str(
                    patient.get(
                        "male_factor_infertility",
                        patient.get("male_factor_infertility_flag", "?"),
                    )
                ).strip().lower()
                static_values[feature] = 0.0 if raw in {"?", "0", "false", "no", "none", ""} else 1.0
                continue
            value, found = _first_numeric(patient, STATIC_ALIASES.get(feature, (feature,)))
            static_values[feature] = value
            if not found:
                warnings.append(f"missing static feature: {feature}")

        sequence_rows: list[list[float]] = []
        for index, record in enumerate(active_records):
            row: dict[str, float] = dict(static_values)
            stim_day = _to_float(
                record.get("stim_day", patient.get("stim_day")),
                float(index + 1),
            )
            row["Day"] = stim_day
            row["gn_day"] = stim_day
            row["monitoring_order"] = float(index + 1)
            previous = active_records[index - 1] if index else {}
            previous_day = _to_float(previous.get("stim_day"), float("nan"))
            row["days_since_previous_visit"] = (
                max(0.0, stim_day - previous_day)
                if math.isfinite(previous_day)
                else (0.0 if index == 0 else float("nan"))
            )
            row["cycle_day"] = _to_float(record.get("cycle_day"), stim_day)

            for feature in dynamic_features:
                if feature in row:
                    continue
                if feature == "growing_follicle_count":
                    values = [
                        _first_numeric(record, DYNAMIC_ALIASES.get(key, (key,)))[0]
                        for key in (
                            "follicle_count_10_12",
                            "follicle_count_13_15",
                            "follicle_count_16_18",
                            "follicle_count_gt_18",
                        )
                    ]
                    row[feature] = sum(value for value in values if math.isfinite(value))
                    continue
                value, found = _first_numeric(record, DYNAMIC_ALIASES.get(feature, (feature,)))
                if not found and feature in PREVIOUS_DOSE_FROM_PRIOR_RECORD and index > 0:
                    value, found = _first_numeric(
                        previous,
                        (PREVIOUS_DOSE_FROM_PRIOR_RECORD[feature],),
                    )
                row[feature] = value
                if not found:
                    warnings.append(f"missing dynamic feature in record {index + 1}: {feature}")
            sequence_rows.append([row.get(feature, float("nan")) for feature in dynamic_features])

        history = sequence_rows[-MAX_HISTORY_DAYS:]
        raw_dynamic = np.full((MAX_HISTORY_DAYS, len(dynamic_features)), np.nan, dtype=np.float64)
        mask = np.zeros((MAX_HISTORY_DAYS,), dtype=np.float32)
        raw_dynamic[: len(history), :] = np.asarray(history, dtype=np.float64)
        mask[: len(history)] = 1.0

        static_vector = np.asarray(
            [static_values.get(feature, np.nan) for feature in static_features],
            dtype=np.float64,
        )
        static_vector = _apply_scaler(
            _apply_imputer(static_vector, config["staticImputer"]["statistics"]),
            config["staticScaler"]["mean"],
            config["staticScaler"]["scale"],
        )
        dynamic_vector = _apply_scaler(
            _apply_imputer(raw_dynamic, config["dynamicImputer"]["statistics"]),
            config["dynamicScaler"]["mean"],
            config["dynamicScaler"]["scale"],
        )
        dynamic_vector = dynamic_vector * mask[:, None]
        return (
            static_vector.astype(np.float32),
            dynamic_vector.astype(np.float32),
            mask.astype(np.float32),
            sorted(set(warnings)),
        )

    def predict(
        self,
        patient: Mapping[str, Any],
        records: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        predictions: dict[str, Any] = {}
        all_warnings: list[str] = []
        for target in TARGETS:
            static_vector, dynamic_vector, mask, warnings = self.build_sequence_input(
                patient,
                records,
                target,
            )
            all_warnings.extend(warnings)
            with torch.no_grad():
                logits = self.models[target](
                    torch.tensor(static_vector[None, :], dtype=torch.float32),
                    torch.tensor(dynamic_vector[None, :, :], dtype=torch.float32),
                    torch.tensor(mask[None, :], dtype=torch.float32),
                )
                temperature = float(self.configs[target]["calibration"]["deployedTemperature"])
                probabilities = torch.softmax(logits / temperature, dim=1).cpu().numpy()[0]
            config = self.configs[target]
            labels = config["labels"]
            index = int(np.argmax(probabilities))
            label = labels[index]
            predictions[target] = {
                "label": label,
                "display": self._display(target, label),
                "dose": self._dose(target, label),
                "probability": float(probabilities[index]),
                "probabilities": {
                    label_name: float(probabilities[i])
                    for i, label_name in enumerate(labels)
                },
                "calibration": config["calibration"],
            }
        return {
            "source": "local-python-runtime-v1",
            "predictions": predictions,
            "warnings": sorted(set(all_warnings)),
        }

    def explain(
        self,
        patient: Mapping[str, Any],
        records: Sequence[Mapping[str, Any]],
        target: str,
        class_index: int,
    ) -> dict[str, Any]:
        static_vector, dynamic_vector, mask, warnings = self.build_sequence_input(
            patient,
            records,
            target,
        )
        count = int(round(float(mask.sum())))
        available = self.backgrounds[target]
        if not available:
            raise RuntimeError(f"No frozen explanation background for {target}")
        background_count = min(available, key=lambda value: abs(value - count))
        background_static_np, background_dynamic_np, background_mask_np = available[background_count]

        query_static = torch.tensor(static_vector[None, :], dtype=torch.float32)
        query_dynamic = torch.tensor(dynamic_vector[None, :, :], dtype=torch.float32)
        query_mask = torch.tensor(mask[None, :], dtype=torch.float32)
        background_static = torch.tensor(background_static_np, dtype=torch.float32)
        background_dynamic = torch.tensor(background_dynamic_np, dtype=torch.float32)
        background_mask = torch.tensor(background_mask_np, dtype=torch.float32)
        model = self.models[target]
        temperature = float(self.configs[target]["calibration"]["deployedTemperature"])
        for index, feature in enumerate(self.configs[target]["staticFeatures"]):
            if str(feature) not in UI_INPUT_ATTRIBUTION_FEATURES:
                background_static[:, index] = query_static[0, index]
        for index, feature in enumerate(self.configs[target]["dynamicFeatures"]):
            if str(feature) not in UI_INPUT_ATTRIBUTION_FEATURES:
                background_dynamic[:, :, index] = query_dynamic[0, :, index]

        nodes, quadrature_weights = np.polynomial.legendre.leggauss(16)
        alphas = torch.tensor((nodes + 1.0) / 2.0, dtype=torch.float32)
        weights = torch.tensor(quadrature_weights / 2.0, dtype=torch.float32)
        static_delta = query_static - background_static
        dynamic_delta = (query_dynamic - background_dynamic) * background_mask.unsqueeze(-1)
        static_path = (
            background_static[:, None, :]
            + alphas[None, :, None] * static_delta[:, None, :]
        ).reshape(-1, query_static.shape[-1]).requires_grad_(True)
        dynamic_path = (
            background_dynamic[:, None, :, :]
            + alphas[None, :, None, None] * dynamic_delta[:, None, :, :]
        ).reshape(-1, query_dynamic.shape[1], query_dynamic.shape[2]).requires_grad_(True)
        path_mask = (
            background_mask[:, None, :]
            .repeat(1, len(alphas), 1)
            .reshape(-1, query_mask.shape[1])
        )
        logits = model(static_path, dynamic_path, path_mask)
        selected_probability = torch.softmax(logits / temperature, dim=1)[:, int(class_index)]
        static_grad, dynamic_grad = torch.autograd.grad(
            selected_probability.sum(),
            (static_path, dynamic_path),
            retain_graph=False,
            create_graph=False,
        )
        background_size = background_static.shape[0]
        static_grad = static_grad.reshape(background_size, len(alphas), -1)
        dynamic_grad = dynamic_grad.reshape(
            background_size,
            len(alphas),
            query_dynamic.shape[1],
            query_dynamic.shape[2],
        )
        integrated_static_grad = (static_grad * weights[None, :, None]).sum(dim=1)
        integrated_dynamic_grad = (
            dynamic_grad * weights[None, :, None, None]
        ).sum(dim=1)
        static_values = (
            static_delta * integrated_static_grad
        ).mean(dim=0).detach().cpu().numpy()
        dynamic_values = (
            dynamic_delta * integrated_dynamic_grad * background_mask.unsqueeze(-1)
        ).mean(dim=0).sum(dim=0).detach().cpu().numpy()
        attribution = {
            str(feature): float(static_values[index])
            for index, feature in enumerate(self.configs[target]["staticFeatures"])
        }
        for index, feature in enumerate(self.configs[target]["dynamicFeatures"]):
            attribution[str(feature)] = attribution.get(str(feature), 0.0) + float(dynamic_values[index])
        with torch.no_grad():
            baseline_logits = model(background_static, background_dynamic, background_mask)
            baseline_probability = float(
                torch.softmax(baseline_logits / temperature, dim=1)[:, int(class_index)]
                .mean()
                .cpu()
                .item()
            )
            current_logits = model(query_static, query_dynamic, query_mask)
            current_probability = float(
                torch.softmax(current_logits / temperature, dim=1)[0, int(class_index)]
                .cpu()
                .item()
            )
        items = [
            {
                "feature": feature,
                "mean_shap": value,
                "mean_abs_shap": abs(value),
                "direction": "局部正向" if value >= 0 else "局部负向",
            }
            for feature, value in attribution.items()
        ]
        items.sort(key=lambda item: abs(float(item["mean_abs_shap"])), reverse=True)
        return {
            "target": target,
            "baselineProbability": baseline_probability,
            "currentProbability": current_probability,
            "backgroundSize": background_size,
            "backgroundVisitCount": background_count,
            "items": items,
            "attributionSum": float(sum(attribution.values())),
            "completenessResidual": float(
                current_probability - baseline_probability - sum(attribution.values())
            ),
            "warnings": warnings,
        }

    @staticmethod
    def _display(target: str, label: str) -> str:
        display = {
            "fsh": {"low_or_none": "0-80", "moderate": "80-160", "high": ">160"},
            "lh": {"dose_0": "0", "dose_75": "75", "dose_ge150": ">75"},
            "hmg": {
                "dose_0": "0",
                "dose_75": "75",
                "dose_150": "150",
                "dose_ge225": ">150",
            },
        }
        return display[target].get(label, label)

    @staticmethod
    def _dose(target: str, label: str) -> float:
        doses = {
            "fsh": {"low_or_none": 40.0, "moderate": 120.0, "high": 200.0},
            "lh": {"dose_0": 0.0, "dose_75": 75.0, "dose_ge150": 150.0},
            "hmg": {"dose_0": 0.0, "dose_75": 75.0, "dose_150": 150.0, "dose_ge225": 225.0},
        }
        return doses[target].get(label, 0.0)
