from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from runtime.analysis_service import AnalysisService


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, tolerance: float = 1e-8) -> bool:
    return math.isfinite(float(actual)) and abs(float(actual) - float(expected)) <= tolerance


def main() -> int:
    case = json.loads((ROOT / "fixtures" / "representative_case.json").read_text(encoding="utf-8"))
    expected = json.loads(
        (ROOT / "fixtures" / "representative_case.expected.json").read_text(encoding="utf-8")
    )
    service = AnalysisService(ROOT)
    started = time.time()
    result = service.analyze(case["patient"], case["monitoring_records"])
    elapsed = time.time() - started

    summary = result["summary"]
    for target in ("fsh", "lh", "hmg"):
        expected_target = expected["dose"][target]
        actual = summary[target]
        require(actual["label"] == expected_target["label"], f"{target} label mismatch")
        require(actual["display"] == expected_target["display"], f"{target} display mismatch")
        require(close(actual["dose"], expected_target["dose"]), f"{target} dose mismatch")
        require(
            close(actual["probability"], expected_target["probability"], tolerance=1e-7),
            f"{target} probability mismatch",
        )
    require(close(summary["oocytes"], expected["outcomes"]["oocytes"]), "oocytes mismatch")
    require(close(summary["mii"], expected["outcomes"]["mii"], tolerance=1e-8), "MII mismatch")
    require(
        close(summary["ohssRisk"], expected["outcomes"]["ohssRisk"], tolerance=1e-12),
        "OHSS mismatch",
    )
    require(len(result["candidates"]) == 8, "expected 8 candidate scenarios")
    require(len(result["curves"]["fsh"]) == 5, "expected 5 FSH curve points")
    require(len(result["curves"]["lh"]) == 3, "expected 3 LH curve points")
    require(len(result["curves"]["hmg"]) == 4, "expected 4 HMG curve points")
    fsh_anchor = next(point for point in result["curves"]["fsh"] if point["recommended"])
    require(close(fsh_anchor["dose"], 200.0), "FSH curve anchor is not 200 IU/day")
    require(result["explanations"]["oocytes"]["items"], "oocyte SHAP explanation missing")
    require(result["explanations"]["ohss"]["items"], "OHSS SHAP explanation missing")
    expected_dose_explanations = {
        "fsh": (0.543, 0.896),
        "lh": (0.084, 0.824),
        "hmg": (0.010, 0.875),
    }
    for target, (baseline, current) in expected_dose_explanations.items():
        explanation = result["explanations"]["dose"][target]
        require(
            close(explanation["baselineProbability"], baseline, tolerance=0.001),
            f"{target} dose explanation baseline mismatch",
        )
        require(
            close(explanation["currentProbability"], current, tolerance=0.001),
            f"{target} dose explanation current prediction mismatch",
        )
        require(explanation["items"], f"{target} dose explanation items missing")
    knn_expected = {
        "fsh": [("80-160", 22, "44%", "77%"), ("0-80", 8, "16%", "100%"), (">160", 20, "40%", "65%")],
        "lh": [("75", 23, "46%", "78%"), ("≥150", 17, "34%", "71%"), ("0", 10, "20%", "80%")],
        "hmg": [("150", 27, "54%", "70%"), ("≥225", 9, "18%", "100%"), ("75", 10, "20%", "70%")],
    }
    require(result["explanations"]["knn"]["status"] == "OK", "KNN evidence missing")
    for drug, expected_rows in knn_expected.items():
        rows = result["explanations"]["knn"]["items"][drug]
        require(len(rows) == 3, f"{drug} KNN row count mismatch")
        for row, (dose, count, selection, success) in zip(rows, expected_rows):
            require(row["dose"] == dose, f"{drug} KNN dose mismatch")
            require(int(row["case_count"]) == count, f"{drug} KNN case count mismatch")
            require(row["selection_rate"] == selection, f"{drug} KNN selection rate mismatch")
            require(row["success_rate"] == success, f"{drug} KNN success rate mismatch")
    require(not result["warnings"], f"unexpected warnings: {result['warnings']}")

    report: dict[str, Any] = {
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "elapsedSeconds": round(elapsed, 3),
        "summary": summary,
        "candidateCount": len(result["candidates"]),
        "candidateRanks": [
            {
                "rank": row["rank"],
                "fsh": row["fsh"],
                "lh": row["lh"],
                "hmg": row["hmg"],
                "oocytes": row["oocytes"],
                "ohssRisk": row["ohssRisk"],
            }
            for row in result["candidates"]
        ],
        "curvePointCounts": {key: len(value) for key, value in result["curves"].items()},
        "fshCurveAnchor": fsh_anchor,
        "explanationCounts": {
            "oocytes": len(result["explanations"]["oocytes"]["items"]),
            "ohss": len(result["explanations"]["ohss"]["items"]),
            "dose": {
                target: len(result["explanations"]["dose"][target]["items"])
                for target in ("fsh", "lh", "hmg")
            },
        },
        "assertions": {
            "doseOutput": "PASS",
            "outcomeOutput": "PASS",
            "candidateScenarios": "PASS",
            "curvePoints": "PASS",
            "outcomeExplanations": "PASS",
            "doseExplanations": "PASS",
            "knnEvidence": "PASS",
            "baselineRuntimeDependency": "REMOVED",
        },
        "knownLimitations": [],
        "warnings": result["warnings"],
    }
    output = ROOT / "artifacts" / "day2-validation.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nPASS: report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
