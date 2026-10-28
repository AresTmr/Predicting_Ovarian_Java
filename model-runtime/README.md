# Model Runtime

## Current status

Day 1 and Day 2 milestones are complete.

- Day 1: real checkpoint and outcome-bundle validation.
- Day 2: frozen preprocessing, independent dose/outcome inference and local
  `/analyze` service.
- The service no longer imports the original project source tree at runtime.
- Representative-case inference takes about 1.7 seconds including outcome SHAP.

This directory contains the first real-model validation package for the Java
project.

Day 1 verifies:

- the FSH/LH/HMG PyTorch checkpoints can be loaded;
- model feature and class metadata match the expected contract;
- the efficacy and safety outcome bundles can be loaded;
- the representative case produces the same output as the Chinese backup
  project;
- model hashes are stable and recorded.

The original project and the Chinese backup are read-only inputs. This package
does not modify either directory.

## Run

From the Java project root:

```powershell
.\model-runtime\run-day1.ps1
```

The preprocessing parameters are frozen under `assets/preprocessing/`, so the
service does not refit from the training panel.

The validation report is written to:

```text
model-runtime/artifacts/day1-validation.json
```

## Expected representative output

```text
FSH: >160 / 200 IU/day
LH:  75 IU/day
HMG: 150 IU/day
Oocytes: 12.0
MII: 11.1963
Moderate-to-severe OHSS risk: 0.010482 (display 1.05%)
```

## Day 2 service

Start the local service:

```powershell
.\model-runtime\run-service.ps1
```

Endpoints:

```text
GET  /health
GET  /models
POST /analyze
```

`POST /analyze` request:

```json
{
  "patient": {},
  "records": []
}
```

The response contains:

- FSH/LH/HMG categories, actual doses and class probabilities;
- oocytes, MII, moderate-to-severe OHSS probability and risk level;
- eight ranked candidate scenarios;
- FSH/LH/HMG dose-response points;
- FSH/LH/HMG local integrated-gradient explanations;
- oocyte and OHSS Tree SHAP items.
- KNN dose evidence with case count, selection rate and success rate.

If a model cannot be loaded or inference fails, the service returns an HTTP
error. It does not return mock clinical output.

## Model replacement contract

Models may be replaced only when the same contract is retained:

- `assets/models/dose/{fsh,lh,hmg}.pt`
- `assets/preprocessing/{fsh,lh,hmg}.json`
- `assets/models/dose-calibration/{fsh,lh,hmg}_temperature.json`
- `assets/models/candidate/efficacy/bundle.joblib`
- `assets/models/candidate/safety/bundle.joblib`

The replacement model must keep:

- the same task meaning;
- named input fields and units;
- class-label meaning;
- output field meaning;
- probability semantics;
- model version and checksum traceability.

Java and Vue code must not need changes for a same-contract model replacement.

## Day 3 Java integration

The Java backend exposes:

```text
POST /api/v1/recommendation-runs
GET  /api/v1/recommendation-runs/{runId}
GET  /api/v1/recommendation-runs/runtime/health
```

Each successful request creates one `runId` and stores the complete result in
the H2 table `analysis_run`. Model failure returns HTTP 503 and does not produce
or display mock clinical output.

## Day 4 frontend integration

All three result pages now consume the same analysis run:

- `PatientEntry.vue` creates the run and stores it in Pinia.
- `MonitoringResult.vue` renders the same summary and monitoring records.
- `DecisionCurve.vue` renders the returned curve points and eight candidates.
- `Recommendation.vue` renders dose/outcome SHAP and KNN evidence.

The browser receives one shared `runId`; tab switching does not recalculate the
model.

## Validation reports

- `artifacts/day1-validation.json`: real checkpoint parity
- `artifacts/day2-validation.json`: independent model runtime
- `artifacts/day3-validation.json`: Java API and H2 persistence
- `artifacts/day4-validation.json`: four-page integration
- `artifacts/multi-case-validation.json`: representative, low-reserve and
  high-response cases
- `artifacts/day5-validation.json`: dedicated environment and final integration

## Local Python environment

The project now uses its own runtime environment:

```text
model-runtime/.venv
```

Recreate it on a new machine with:

```powershell
python -m venv model-runtime\.venv
.\model-runtime\.venv\Scripts\python.exe -m pip install `
  torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
.\model-runtime\.venv\Scripts\python.exe -m pip install -r model-runtime\requirements.txt
```

`run-service.ps1` and the validation scripts default to this environment.

No mock clinical output is accepted as a successful validation.
