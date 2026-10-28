from __future__ import annotations

import copy
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from runtime.analysis_service import AnalysisService


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def finite_probability(value: Any) -> bool:
    number = float(value)
    return math.isfinite(number) and 0.0 <= number <= 1.0


def make_variant(base: dict[str, Any], name: str, patient: dict[str, Any], last: dict[str, Any]) -> dict[str, Any]:
    case = copy.deepcopy(base)
    case["audit"]["case_name"] = name
    case["patient"].update(patient)
    case["monitoring_records"][-1].update(last)
    return case


def validate_case(service: AnalysisService, case: dict[str, Any]) -> dict[str, Any]:
    name = str(case["audit"]["case_name"])
    started = time.time()
    result = service.analyze(case["patient"], case["monitoring_records"])
    elapsed = time.time() - started
    summary = result["summary"]
    require(result["status"] == "OK", f"{name}: status is not OK")
    require(finite_probability(summary["fsh"]["probability"]), f"{name}: invalid FSH probability")
    require(finite_probability(summary["lh"]["probability"]), f"{name}: invalid LH probability")
    require(finite_probability(summary["hmg"]["probability"]), f"{name}: invalid HMG probability")
    require(math.isfinite(float(summary["oocytes"])), f"{name}: invalid oocyte count")
    require(float(summary["oocytes"]) >= 0, f"{name}: negative oocyte count")
    require(finite_probability(summary["ohssRisk"]), f"{name}: invalid OHSS probability")
    require(len(result["candidates"]) == 8, f"{name}: candidate count is not 8")
    require(len(result["curves"]["fsh"]) == 5, f"{name}: FSH curve count mismatch")
    require(len(result["curves"]["lh"]) == 3, f"{name}: LH curve count mismatch")
    require(len(result["curves"]["hmg"]) == 4, f"{name}: HMG curve count mismatch")
    require(result["explanations"]["knn"]["status"] == "OK", f"{name}: KNN unavailable")
    require(result["explanations"]["dose"]["fsh"]["items"], f"{name}: dose explanation missing")
    require(result["explanations"]["oocytes"]["items"], f"{name}: outcome explanation missing")
    return {
        "name": name,
        "elapsedSeconds": round(elapsed, 3),
        "fsh": summary["fsh"]["category"],
        "fshActualDose": summary["fsh"]["actualDose"],
        "lh": summary["lh"]["actualDose"],
        "hmg": summary["hmg"]["actualDose"],
        "oocytes": summary["oocytes"],
        "ohssRiskPercent": summary["ohssRiskPercent"],
        "candidateCount": len(result["candidates"]),
    }


def main() -> int:
    base = json.loads((ROOT / "fixtures" / "representative_case.json").read_text(encoding="utf-8"))
    variants = [
        make_variant(
            base,
            "baseline-representative",
            {},
            {},
        ),
        make_variant(
            base,
            "low-ovarian-reserve",
            {
                "age": 42,
                "amh": 0.45,
                "afc": 4,
                "basal_fsh": 12.4,
                "basal_lh": 7.2,
            },
            {
                "e2": 260,
                "serum_fsh": 24.0,
                "total_follicles": 4,
                "left_follicles": 2,
                "right_follicles": 2,
                "max_f": 9.0,
                "mean_f": 6.0,
                "f_lt10": 4,
                "f_10_12": 0,
                "f_13_15": 0,
                "f_16_18": 0,
                "f_gt18": 0,
            },
        ),
        make_variant(
            base,
            "high-response-risk",
            {
                "age": 29,
                "bmi": 20.1,
                "amh": 5.6,
                "afc": 22,
                "basal_fsh": 4.6,
                "basal_lh": 3.9,
            },
            {
                "e2": 2200,
                "serum_fsh": 12.0,
                "total_follicles": 24,
                "left_follicles": 12,
                "right_follicles": 12,
                "max_f": 17.0,
                "mean_f": 12.0,
                "f_lt10": 3,
                "f_10_12": 7,
                "f_13_15": 8,
                "f_16_18": 5,
                "f_gt18": 1,
            },
        ),
    ]
    service = AnalysisService(ROOT)
    started = time.time()
    rows = [validate_case(service, case) for case in variants]
    report = {
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "elapsedSeconds": round(time.time() - started, 3),
        "cases": rows,
    }
    output = ROOT / "artifacts" / "multi-case-validation.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nPASS: report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
