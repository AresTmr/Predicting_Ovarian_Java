from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .candidate_runtime import patient_form_to_snapshot


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _to_int(value: Any, default: int = 0) -> int:
    return int(round(_to_float(value, float(default))))


def _drug_dose_group(drug: str, dose: float) -> tuple[str, str]:
    value = max(0.0, _to_float(dose, 0.0))
    if drug == "fsh":
        if value < 80:
            return "low_or_none", "0-80"
        if value <= 160:
            return "moderate", "80-160"
        return "high", ">160"
    if drug == "lh":
        if value <= 0:
            return "dose_0", "0"
        if value < 150:
            return "dose_75", "75"
        return "dose_ge150", "≥150"
    if value <= 0:
        return "dose_0", "0"
    if value < 150:
        return "dose_75", "75"
    if value < 225:
        return "dose_150", "150"
    return "dose_ge225", "≥225"


class KnnRuntime:
    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.vendor_root = self.runtime_root / "vendor"
        self.data_root = self.runtime_root / "assets" / "knn"
        sys.path.insert(0, str(self.vendor_root))
        from models.layer1_strategy.action_model import (
            augment_layer1_action_features,
            create_gn_action_labels,
        )
        from models.layer1_strategy.knn_retrieval import (
            fit_knn_retriever,
            get_similar_cases,
        )

        self._augment = augment_layer1_action_features
        self._get_similar_cases = get_similar_cases
        history = pd.read_csv(
            self.data_root / "layer1_strategy_dataset.csv",
            low_memory=False,
        )
        history = self._augment(history)
        history = create_gn_action_labels(history)
        if "has_next_visit" in history.columns:
            history = history[history["has_next_visit"].astype(bool)].copy()
        if "strategy_eligible_flag" in history.columns:
            history = history[history["strategy_eligible_flag"].astype(bool)].copy()
        history = history[history["combined_gn_action"].isin(["increase", "maintain", "decrease"])].copy()
        manifest = pd.read_csv(self.data_root / "split_manifest_v1.csv")
        split_map = manifest.drop_duplicates("cycle_uid").set_index("cycle_uid")["split"]
        history["split"] = history["cycle_uid"].map(split_map).fillna("train")
        history = history[history["split"] == "train"].copy()
        if history.empty:
            raise ValueError("KNN history is empty")
        self.retriever = fit_knn_retriever(history.reset_index(drop=True), k=50)
        labels = pd.read_csv(self.data_root / "successful_cycle_labels_v1.csv", low_memory=False)
        self.label_lookup = {
            str(row["cycle_uid"]): row
            for _, row in labels.iterrows()
        }

    def build_summary(
        self,
        latest_form: Mapping[str, Any],
        limit: int = 3,
    ) -> dict[str, list[dict[str, Any]]]:
        snapshot = patient_form_to_snapshot(latest_form)
        snapshot = self._augment(snapshot.to_frame().T).iloc[0]
        similar = self._get_similar_cases(
            self.retriever,
            snapshot,
            k=50,
            exclude_patient_id=snapshot.get("art_id"),
            exclude_cycle_id=snapshot.get("cycle_uid"),
        )
        if similar.empty:
            return {"fsh": [], "lh": [], "hmg": []}
        total = max(len(similar), 1)
        summaries: dict[str, list[dict[str, Any]]] = {}
        for drug in ("fsh", "lh", "hmg"):
            dose_universe = {
                "fsh": [("low_or_none", "0-80"), ("moderate", "80-160"), ("high", ">160")],
                "lh": [("dose_0", "0"), ("dose_75", "75"), ("dose_ge150", "≥150")],
                "hmg": [("dose_0", "0"), ("dose_75", "75"), ("dose_150", "150"), ("dose_ge225", "≥225")],
            }[drug]
            groups = {
                key: {
                    "dose": display,
                    "case_count": 0,
                    "success_count": 0,
                    "success_denominator": 0,
                }
                for key, display in dose_universe
            }
            for _, row in similar.iterrows():
                current = _to_float(row.get(f"current_{drug}_daily_dose"), 0.0)
                dose = _to_float(row.get(f"next_{drug}_daily_dose"), current)
                key, display = _drug_dose_group(drug, dose)
                group = groups.setdefault(
                    key,
                    {
                        "dose": display,
                        "case_count": 0,
                        "success_count": 0,
                        "success_denominator": 0,
                    },
                )
                group["case_count"] += 1
                label_row = self.label_lookup.get(str(row.get("cycle_uid")), {})
                exact_evaluable = bool(_to_int(label_row.get("exact_evaluable"), 0))
                exact_value = label_row.get("kong_aligned_exact_success")
                if exact_evaluable and not pd.isna(exact_value):
                    group["success_denominator"] += 1
                    group["success_count"] += int(bool(_to_int(exact_value, 0)))
            ranked = []
            for group in groups.values():
                selection = group["case_count"] / total
                denominator = group["success_denominator"]
                success = group["success_count"] / denominator if denominator else None
                composite = (selection + success) / 2.0 if success is not None else -1.0
                ranked.append(
                    {
                        "dose": group["dose"],
                        "case_count": int(group["case_count"]),
                        "selection_rate_value": round(selection, 4),
                        "success_rate_value": round(success, 4) if success is not None else None,
                        "selection_rate": f"{selection * 100:.0f}%",
                        "success_rate": f"{success * 100:.0f}%" if success is not None else "--",
                        "composite_score": round(composite, 4),
                    }
                )
            ranked.sort(
                key=lambda item: (
                    -float(item["composite_score"]),
                    -float(item["success_rate_value"] if item["success_rate_value"] is not None else -1.0),
                    -float(item["selection_rate_value"]),
                    -int(item["case_count"]),
                )
            )
            rows = ranked[: max(1, int(limit))]
            for index, row in enumerate(rows, start=1):
                row["case"] = f"Case {index}"
            summaries[drug] = rows
        return summaries
