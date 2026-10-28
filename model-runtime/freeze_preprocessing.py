from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

sys.dont_write_bytecode = True

MODEL_RUNTIME_ROOT = Path(__file__).resolve().parent
DEFAULT_BASELINE_ROOT = Path(
    r"C:\Users\24986\Desktop\FJNU\git\Predicting_Ovarian_UI_backup_2026-09-17"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze dose-model preprocessing statistics")
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE_ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=MODEL_RUNTIME_ROOT / "assets" / "preprocessing",
    )
    args = parser.parse_args()

    baseline_root = args.baseline_root.resolve()
    if not baseline_root.exists():
        raise FileNotFoundError(f"Baseline project not found: {baseline_root}")

    sys.path.insert(0, str(baseline_root / "prototype" / "streamlit_app"))
    sys.path.insert(0, str(baseline_root))

    from dose_recommendation_service import (
        _cached_target_training_raw,
        _split_manifest,
        _holdout_checkpoint,
        load_ui_reduced_contract,
    )

    contract = load_ui_reduced_contract()
    split_lookup = _split_manifest().set_index("cycle_uid")["split"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baselineRoot": str(baseline_root),
        "models": {},
    }
    started = time.time()

    for target in ("fsh", "lh", "hmg"):
        target_started = time.time()
        checkpoint = _holdout_checkpoint(target)
        raw = _cached_target_training_raw(target)
        train_splits = raw.row_index["cycle_uid"].astype(str).map(split_lookup)
        if train_splits.isna().any():
            missing = int(train_splits.isna().sum())
            raise ValueError(f"{target}: {missing} training rows missing from split manifest")
        fit_mask = train_splits.eq("train").to_numpy(dtype=bool)
        if not fit_mask.any():
            raise ValueError(f"{target}: no training rows available for preprocessing fit")

        static_imputer = SimpleImputer(strategy="median").fit(raw.static[fit_mask])
        static_scaler = StandardScaler().fit(
            static_imputer.transform(raw.static[fit_mask])
        )

        observed_dynamic = raw.dynamic[fit_mask][raw.mask[fit_mask].astype(bool)]
        dynamic_imputer = SimpleImputer(strategy="median").fit(observed_dynamic)
        dynamic_scaler = StandardScaler().fit(
            dynamic_imputer.transform(observed_dynamic)
        )

        train_static = static_scaler.transform(
            static_imputer.transform(raw.static[fit_mask])
        ).astype(np.float32)
        train_dynamic_flat = dynamic_scaler.transform(
            dynamic_imputer.transform(
                raw.dynamic[fit_mask].reshape(-1, raw.dynamic.shape[-1])
            )
        ).reshape(raw.dynamic[fit_mask].shape).astype(np.float32)
        train_mask = raw.mask[fit_mask].astype(np.float32)
        train_dynamic_flat = train_dynamic_flat * train_mask[:, :, None]
        visit_counts = train_mask.sum(axis=1).astype(int)
        background_arrays: dict[str, np.ndarray] = {}
        background_counts: list[int] = []
        for count in sorted(int(value) for value in np.unique(visit_counts) if value > 0):
            indices = np.flatnonzero(visit_counts == count)
            if indices.size == 0:
                continue
            positions = np.linspace(
                0,
                max(int(indices.size) - 1, 0),
                min(12, int(indices.size)),
                dtype=int,
            )
            selected = indices[positions]
            background_arrays[f"count_{count}_static"] = train_static[selected]
            background_arrays[f"count_{count}_dynamic"] = train_dynamic_flat[selected]
            background_arrays[f"count_{count}_mask"] = train_mask[selected]
            background_counts.append(count)
        background_path = args.output_dir / f"{target}-backgrounds.npz"
        np.savez_compressed(background_path, **background_arrays)

        calibration = json.loads(
            (
                MODEL_RUNTIME_ROOT
                / "assets"
                / "models"
                / "dose-calibration"
                / f"{target}_temperature.json"
            ).read_text(encoding="utf-8")
        )
        payload = {
            "schemaVersion": "dose-preprocessing-v1",
            "target": target,
            "labels": list(checkpoint["labels"]),
            "staticFeatures": list(checkpoint["static_features"]),
            "dynamicFeatures": list(checkpoint["dynamic_features"]),
            "maxHistoryDays": 16,
            "hiddenDim": int(checkpoint.get("hyperparameters", {}).get("hidden_dim", 96)),
            "dropout": float(checkpoint.get("hyperparameters", {}).get("dropout", 0.15)),
            "staticImputer": {
                "strategy": "median",
                "statistics": static_imputer.statistics_.astype(float).tolist(),
            },
            "staticScaler": {
                "mean": static_scaler.mean_.astype(float).tolist(),
                "scale": static_scaler.scale_.astype(float).tolist(),
                "variance": static_scaler.var_.astype(float).tolist(),
            },
            "dynamicImputer": {
                "strategy": "median",
                "statistics": dynamic_imputer.statistics_.astype(float).tolist(),
            },
            "dynamicScaler": {
                "mean": dynamic_scaler.mean_.astype(float).tolist(),
                "scale": dynamic_scaler.scale_.astype(float).tolist(),
                "variance": dynamic_scaler.var_.astype(float).tolist(),
            },
            "calibration": {
                "deployedTemperature": float(calibration["deployed_temperature"]),
                "calibrationApplied": bool(calibration["calibration_applied"]),
                "method": str(calibration["method"]),
            },
            "trainingRowCount": int(fit_mask.sum()),
            "observedDynamicRowCount": int(observed_dynamic.shape[0]),
            "backgroundPath": background_path.name,
            "backgroundCounts": background_counts,
        }
        output_path = args.output_dir / f"{target}.json"
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report["models"][target] = {
            "path": str(output_path.relative_to(MODEL_RUNTIME_ROOT)),
            "trainingRowCount": payload["trainingRowCount"],
            "observedDynamicRowCount": payload["observedDynamicRowCount"],
            "staticFeatureCount": len(payload["staticFeatures"]),
            "dynamicFeatureCount": len(payload["dynamicFeatures"]),
            "elapsedSeconds": round(time.time() - target_started, 3),
        }

    (args.output_dir / "feature-contract.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report["elapsedSeconds"] = round(time.time() - started, 3)
    report_path = args.output_dir / "freeze-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nPreprocessing statistics frozen in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
