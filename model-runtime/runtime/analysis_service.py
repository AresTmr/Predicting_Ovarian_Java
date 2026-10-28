from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .balance_runtime import apply_oocyte_ohss_balance_recommendation
from .candidate_runtime import CandidateRuntime, patient_form_to_snapshot
from .dose_runtime import DoseRuntime
from .knn_runtime import KnnRuntime


def _risk_level(probability: float) -> str:
    if probability < 0.05:
        return "低风险"
    if probability < 0.10:
        return "中风险"
    return "高风险"


def _risk_percent(probability: float) -> float:
    return round(max(0.0, min(1.0, float(probability))) * 100.0, 2)


class AnalysisService:
    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.assets_root = self.runtime_root / "assets"
        self.dose_runtime = DoseRuntime(self.assets_root)
        self.candidate_runtime = CandidateRuntime(self.assets_root / "models")
        self.knn_runtime = KnnRuntime(self.runtime_root)

    @staticmethod
    def _latest_form(
        patient: Mapping[str, Any],
        records: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        clean_records = [dict(row) for row in records if isinstance(row, Mapping)]
        if not clean_records:
            raise ValueError("At least one monitoring record is required")
        merged = dict(patient)
        merged.update(clean_records[-1])
        previous = clean_records[-2] if len(clean_records) > 1 else {}
        merged.update(
            {
                "reference_fsh": previous.get("current_fsh", patient.get("initial_fsh", 0.0)),
                "reference_lh": previous.get("current_lh", patient.get("initial_lh", 0.0)),
                "reference_hmg": previous.get("current_hmg", patient.get("initial_hmg", 0.0)),
            }
        )
        return merged

    @staticmethod
    def _candidate_plans(
        fsh: float,
        lh: float,
        hmg: float,
    ) -> list[dict[str, float]]:
        levels = {
            "fsh": [40.0, 120.0, 200.0],
            "lh": [0.0, 75.0, 150.0],
            "hmg": [0.0, 75.0, 150.0, 225.0],
        }
        base = {"fsh": float(fsh), "lh": float(lh), "hmg": float(hmg)}
        plans: list[dict[str, float]] = []
        seen: set[tuple[float, float, float]] = set()
        for axis in ("fsh", "lh", "hmg"):
            for dose in levels[axis]:
                combo = dict(base)
                combo[axis] = float(dose)
                key = (round(combo["fsh"], 3), round(combo["lh"], 3), round(combo["hmg"], 3))
                if key in seen:
                    continue
                seen.add(key)
                plans.append(combo)
        return plans

    def _score_candidate(
        self,
        snapshot: Mapping[str, Any],
        fsh: float,
        lh: float,
        hmg: float,
        role: str = "candidate",
        name: str = "",
    ) -> dict[str, Any]:
        outcome = self.candidate_runtime.score(snapshot, fsh, lh, hmg)
        return {
            "name": name,
            "candidateRole": role,
            "candidate_role": role,
            "fsh": float(fsh),
            "lh": float(lh),
            "hmg": float(hmg),
            "candidateTotal": float(fsh + lh + hmg),
            "candidate_total": float(fsh + lh + hmg),
            "oocytes": outcome["oocytes"],
            "mii": outcome["mii"],
            "o": outcome["oocytes"],
            "oocytesRaw": outcome["oocytesRaw"],
            "miiRaw": outcome["miiRaw"],
            "ohssRisk": outcome["ohssRisk"],
            "ohss_risk_probability": outcome["ohssRisk"],
            "safety_probability": outcome["ohssRisk"],
            "ohssRiskProbability": outcome["ohssRisk"],
            "safetyProbability": outcome["ohssRisk"],
            "oSelectionValue": outcome["oocytes"],
            "o_selection_value": outcome["oocytes"],
        }

    def analyze(
        self,
        patient: Mapping[str, Any],
        records: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        latest = self._latest_form(patient, records)
        dose_result = self.dose_runtime.predict(patient, records)
        predictions = dose_result["predictions"]
        fsh = float(predictions["fsh"]["dose"])
        lh = float(predictions["lh"]["dose"])
        hmg = float(predictions["hmg"]["dose"])
        snapshot = patient_form_to_snapshot(latest)

        anchor_outcome = self.candidate_runtime.score(snapshot, fsh, lh, hmg)
        raw_plans = self._candidate_plans(fsh, lh, hmg)
        candidates = [
            self._score_candidate(
                snapshot,
                plan["fsh"],
                plan["lh"],
                plan["hmg"],
                role="candidate",
                name=f"情景 {chr(65 + index)}",
            )
            for index, plan in enumerate(raw_plans)
        ]
        balanced = apply_oocyte_ohss_balance_recommendation(candidates)
        ranked = sorted(
            balanced,
            key=lambda row: (
                int(row.get("balance_rank", 999)),
                -float(row.get("oocytes", 0.0)),
                float(row.get("ohssRisk", 1.0)),
            ),
        )
        for index, row in enumerate(ranked, start=1):
            row["name"] = f"情景 {chr(64 + index)}"
            row["rank"] = index
            row["fshCategory"] = self._fsh_category(float(row.get("fsh", 0.0)))

        curve_levels = {
            "fsh": [40.0, 120.0, 200.0],
            "lh": [0.0, 75.0, 150.0],
            "hmg": [0.0, 75.0, 150.0, 225.0],
        }
        curves: dict[str, list[dict[str, Any]]] = {}
        for drug in ("fsh", "lh", "hmg"):
            points = []
            for dose in curve_levels[drug]:
                candidate = {"fsh": fsh, "lh": lh, "hmg": hmg}
                candidate[drug] = dose
                scored = self.candidate_runtime.score(
                    snapshot,
                    candidate["fsh"],
                    candidate["lh"],
                    candidate["hmg"],
                )
                points.append(
                    {
                        "dose": float(dose),
                        "oocytes": scored["oocytes"],
                        "ohssRisk": scored["ohssRisk"],
                        "recommended": abs(float(dose) - float({"fsh": fsh, "lh": lh, "hmg": hmg}[drug])) < 1e-9,
                    }
                )
            curves[drug] = points
        if curves["fsh"]:
            curves["fsh"].insert(
                0,
                {
                    **curves["fsh"][0],
                    "dose": 0.0,
                    "recommended": False,
                },
            )
            curves["fsh"].append(
                {
                    **curves["fsh"][-1],
                    "dose": 240.0,
                    "recommended": False,
                }
            )

        oocyte_explanation = self.candidate_runtime.explain(
            snapshot,
            fsh,
            lh,
            hmg,
            task="layer2_oocytes",
            limit=128,
        )
        ohss_explanation = self.candidate_runtime.explain(
            snapshot,
            fsh,
            lh,
            hmg,
            task="layer2_ohss",
            limit=128,
        )
        dose_explanations = {}
        for target in ("fsh", "lh", "hmg"):
            label = predictions[target]["label"]
            class_index = self.dose_runtime.configs[target]["labels"].index(label)
            dose_explanations[target] = self.dose_runtime.explain(
                patient,
                records,
                target,
                class_index,
            )
        knn_summary = self.knn_runtime.build_summary(latest, limit=3)

        summary = {
            "fsh": {
                **predictions["fsh"],
                "actualDose": fsh,
                "category": predictions["fsh"]["display"],
            },
            "lh": {
                **predictions["lh"],
                "actualDose": lh,
                "category": predictions["lh"]["display"],
            },
            "hmg": {
                **predictions["hmg"],
                "actualDose": hmg,
                "category": predictions["hmg"]["display"],
            },
            "oocytes": anchor_outcome["oocytes"],
            "mii": anchor_outcome["mii"],
            "ohssRisk": anchor_outcome["ohssRisk"],
            "ohssRiskPercent": _risk_percent(anchor_outcome["ohssRisk"]),
            "ohssRiskLevel": _risk_level(anchor_outcome["ohssRisk"]),
        }

        return {
            "status": "OK",
            "source": "local-python-runtime-day2",
            "model": {
                "dose": "FSH/LH/HMG local checkpoint runtime",
                "outcome": "XGBoost + RandomForest packaged bundles",
                "efficacyRunId": anchor_outcome["efficacyRunId"],
                "safetyRunId": anchor_outcome["safetyRunId"],
            },
            "summary": summary,
            "candidates": ranked,
            "curves": curves,
            "explanations": {
                "oocytes": oocyte_explanation,
                "ohss": ohss_explanation,
                "dose": dose_explanations,
                "knn": {
                    "status": "OK",
                    "items": knn_summary,
                },
            },
            "warnings": dose_result.get("warnings", []),
        }

    @staticmethod
    def _fsh_category(dose: float) -> str:
        if dose < 80:
            return "0-80"
        if dose <= 160:
            return "80-160"
        return ">160"
