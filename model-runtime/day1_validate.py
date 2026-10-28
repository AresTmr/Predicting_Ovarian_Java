from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

sys.dont_write_bytecode = True

MODEL_RUNTIME_ROOT = Path(__file__).resolve().parent
JAVA_PROJECT_ROOT = MODEL_RUNTIME_ROOT.parent
DEFAULT_BASELINE_ROOT = Path(
    r"C:\Users\24986\Desktop\FJNU\git\Predicting_Ovarian_UI_backup_2026-09-17"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return math.isfinite(float(actual)) and abs(float(actual) - float(expected)) <= tolerance


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dose_checkpoints(
    torch_module: Any,
    manifest: Mapping[str, Any],
    baseline_root: Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for target, spec in manifest["doseModels"].items():
        path = MODEL_RUNTIME_ROOT / spec["path"]
        require(path.exists(), f"Missing dose checkpoint: {path}")
        actual_hash = sha256_file(path)
        require(actual_hash == spec["sha256"], f"{target} checkpoint hash mismatch")
        baseline_path = baseline_root / spec["source"]
        require(baseline_path.exists(), f"{target} baseline checkpoint not found: {baseline_path}")
        baseline_hash = sha256_file(baseline_path)
        require(baseline_hash == actual_hash, f"{target} baseline checkpoint differs from packaged asset")
        checkpoint = torch_module.load(path, map_location="cpu", weights_only=False)
        require(isinstance(checkpoint, dict), f"{target} checkpoint is not a mapping")
        require("state_dict" in checkpoint, f"{target} checkpoint has no state_dict")
        require(
            len(checkpoint.get("static_features") or []) == spec["staticFeatures"],
            f"{target} static feature count mismatch",
        )
        require(
            len(checkpoint.get("dynamic_features") or []) == spec["dynamicFeatures"],
            f"{target} dynamic feature count mismatch",
        )
        require(
            len(checkpoint.get("labels") or []) == spec["classes"],
            f"{target} class count mismatch",
        )
        result[target] = {
            "path": spec["path"],
            "sha256": actual_hash,
            "baselineSource": spec["source"],
            "baselineSourceSha256": baseline_hash,
            "labels": checkpoint.get("labels"),
            "staticFeatureCount": len(checkpoint.get("static_features") or []),
            "dynamicFeatureCount": len(checkpoint.get("dynamic_features") or []),
            "bestEpoch": checkpoint.get("best_epoch"),
            "bestValidationWeightedF1": checkpoint.get("best_validation_weighted_f1"),
        }
    return result


def validate_outcome_bundles(
    joblib_module: Any,
    manifest: Mapping[str, Any],
    baseline_root: Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for bundle_name in ("efficacy", "safety"):
        spec = manifest["outcomeModels"][bundle_name]
        path = MODEL_RUNTIME_ROOT / spec["path"]
        require(path.exists(), f"Missing outcome bundle: {path}")
        actual_hash = sha256_file(path)
        require(actual_hash == spec["sha256"], f"{bundle_name} bundle hash mismatch")
        baseline_path = baseline_root / spec["source"]
        require(baseline_path.exists(), f"{bundle_name} baseline bundle not found: {baseline_path}")
        baseline_hash = sha256_file(baseline_path)
        require(baseline_hash == actual_hash, f"{bundle_name} baseline bundle differs from packaged asset")
        bundle = joblib_module.load(path)
        tasks = bundle.get("tasks", bundle)
        for task_name, expected_type in spec["tasks"].items():
            require(task_name in tasks, f"{bundle_name} bundle missing task {task_name}")
            estimator = tasks[task_name].get("estimator")
            actual_type = f"{type(estimator).__module__}.{type(estimator).__name__}"
            require(actual_type == expected_type, f"{task_name} expected {expected_type}, got {actual_type}")
        result[bundle_name] = {
            "runId": bundle.get("run_id"),
            "modelName": bundle.get("model_name"),
            "sha256": actual_hash,
            "baselineSource": spec["source"],
            "baselineSourceSha256": baseline_hash,
            "tasks": list(tasks.keys()),
        }
    return result


def build_runtime_inputs(case: Mapping[str, Any]) -> tuple[Any, list[Any]]:
    from layer1_action_inference_service import patient_form_to_snapshot

    patient = dict(case["patient"])
    records = [dict(row) for row in case["monitoring_records"]]
    latest = dict(patient)
    latest.update(records[-1])
    previous = records[-2] if len(records) > 1 else {}
    latest.update(
        {
            "reference_fsh": previous.get("current_fsh", patient.get("initial_fsh", 0.0)),
            "reference_lh": previous.get("current_lh", patient.get("initial_lh", 0.0)),
            "reference_hmg": previous.get("current_hmg", patient.get("initial_hmg", 0.0)),
        }
    )
    snapshot = patient_form_to_snapshot(latest)

    history_snapshots = []
    for index, record in enumerate(records):
        form = dict(patient)
        form.update(record)
        prior = records[index - 1] if index else {}
        form["reference_fsh"] = prior.get("current_fsh", form.get("initial_fsh", 0.0))
        form["reference_lh"] = prior.get("current_lh", form.get("initial_lh", 0.0))
        form["reference_hmg"] = prior.get("current_hmg", form.get("initial_hmg", 0.0))
        history_snapshots.append(patient_form_to_snapshot(form))
    return snapshot, history_snapshots


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 1 real-model validation")
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=DEFAULT_BASELINE_ROOT,
        help="Read-only Chinese baseline project containing original inference sources and data",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=MODEL_RUNTIME_ROOT / "artifacts" / "day1-validation.json",
    )
    args = parser.parse_args()

    baseline_root = args.baseline_root.resolve()
    require(baseline_root.exists(), f"Baseline project not found: {baseline_root}")

    sys.path.insert(0, str(baseline_root / "prototype" / "streamlit_app"))
    sys.path.insert(0, str(baseline_root))

    import joblib
    import torch
    from candidate_response_service import score_candidate_response
    from dose_recommendation_service import predict_ui_reduced_dose_context

    manifest = load_json(MODEL_RUNTIME_ROOT / "manifest" / "day1-models.json")
    expected = load_json(MODEL_RUNTIME_ROOT / "fixtures" / "representative_case.expected.json")
    case = load_json(MODEL_RUNTIME_ROOT / "fixtures" / "representative_case.json")

    started = time.time()
    checkpoint_report = validate_dose_checkpoints(torch, manifest, baseline_root)
    outcome_asset_report = validate_outcome_bundles(joblib, manifest, baseline_root)

    dose_started = time.time()
    dose_context = predict_ui_reduced_dose_context(
        case["patient"],
        case["monitoring_records"],
        deployment_mode="holdout",
    )
    dose_elapsed = time.time() - dose_started
    require(not dose_context.get("warnings"), f"Dose model warnings: {dose_context.get('warnings')}")

    predictions = dose_context["predictions"]
    for target in ("fsh", "lh", "hmg"):
        actual = predictions[target]
        expected_target = expected["dose"][target]
        require(actual["label"] == expected_target["label"], f"{target} label mismatch")
        require(actual["display"] == expected_target["display"], f"{target} display mismatch")
        require(close(actual["dose"], expected_target["dose"]), f"{target} dose mismatch")
        require(
            close(actual["probability"], expected_target["probability"], tolerance=1e-10),
            f"{target} probability mismatch",
        )

    snapshot, history_snapshots = build_runtime_inputs(case)
    outcome_started = time.time()
    outcome_result = score_candidate_response(
        snapshot,
        fsh_dose=predictions["fsh"]["dose"],
        lh_dose=predictions["lh"]["dose"],
        hmg_dose=predictions["hmg"]["dose"],
        history_snapshots=history_snapshots,
    )
    outcome_elapsed = time.time() - outcome_started
    expected_outcomes = expected["outcomes"]
    require(close(outcome_result["oocytes"], expected_outcomes["oocytes"]), "oocytes mismatch")
    require(close(outcome_result["mii"], expected_outcomes["mii"], tolerance=1e-9), "MII mismatch")
    require(
        close(outcome_result["ohss_risk"], expected_outcomes["ohssRisk"], tolerance=1e-12),
        "OHSS mismatch",
    )

    report = {
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baselineRoot": str(baseline_root),
        "javaProjectRoot": str(JAVA_PROJECT_ROOT),
        "elapsedSeconds": round(time.time() - started, 3),
        "doseInferenceSeconds": round(dose_elapsed, 3),
        "outcomeInferenceSeconds": round(outcome_elapsed, 3),
        "checkpoints": checkpoint_report,
        "outcomeAssets": outcome_asset_report,
        "dosePrediction": {
            target: {
                key: predictions[target][key]
                for key in (
                    "label",
                    "display",
                    "dose",
                    "probability",
                    "probability_calibrated",
                    "calibration_method",
                )
            }
            for target in ("fsh", "lh", "hmg")
        },
        "outcomePrediction": {
            key: outcome_result.get(key)
            for key in (
                "source",
                "run_id",
                "efficacy_run_id",
                "ohss_run_id",
                "oocytes",
                "mii",
                "oocytes_raw",
                "mii_raw",
                "ohss_risk",
            )
        },
        "assertions": {
            "modelHashes": "PASS",
            "checkpointMetadata": "PASS",
            "outcomeBundleTasks": "PASS",
            "doseOutput": "PASS",
            "outcomeOutput": "PASS",
            "noModelWarnings": "PASS",
        },
        "knownLimitations": [
            "Day 1 validation still imports the read-only Chinese baseline inference modules.",
            "Day 2 will freeze preprocessing statistics and remove the baseline runtime dependency.",
            "The first dose-model call takes about two minutes because the baseline pipeline refits preprocessing from training data.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nPASS: report written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
