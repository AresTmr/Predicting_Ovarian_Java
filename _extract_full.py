import sys, csv
import pandas as pd
from pathlib import Path

src = Path(r"C:\Users\24986\Desktop\FJNU\git\Predicting_Ovarian_Java\20-24\u5e74\u4e0d\u5b55\u75c7\u60a3\u8005\u4e34\u5e8a\u8d44\u6599.xlsx")
dst_dir = Path(r"C:\Users\24986\Desktop\FJNU\git\Predicting_Ovarian_Java\data")
dst_dir.mkdir(parents=True, exist_ok=True)
out_csv = dst_dir / "patient_import.csv"

print("reading xlsx...")
df = pd.read_excel(src, engine="openpyxl", nrows=200)
print(f"rows: {len(df)}, cols: {len(df.columns)}")

FIELDS = [
    (0,  "case_no",          "P_MOCK"),
    (7,  "age",              "30"),
    (9,  "bmi",              "22.0"),
    (52, "amh",              "2.0"),
    (28, "afc",              "10"),
    (45, "basal_fsh",        "6.0"),
    (46, "basal_lh",         "5.0"),
    (49, "basal_e2",         "40.0"),
    (50, "basal_p",          "0.3"),
    (10, "infertility_years", "3.0"),
]

rows = []
for i in range(len(df)):
    out = {"patient_uuid": "P" + str(i + 1).zfill(5)}
    for col_idx, field, default in FIELDS:
        v = df.iat[i, col_idx] if col_idx < len(df.columns) else None
        if v is not None and str(v).strip() and str(v) != "nan":
            try:
                if field == "case_no":
                    out[field] = str(v).strip()
                else:
                    out[field] = float(v)
            except (ValueError, TypeError):
                out[field] = default
        else:
            out[field] = default
    out["source_type"] = "EXCEL_IMPORT"
    rows.append(out)

with open(out_csv, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print(f"written: {out_csv}, {len(rows)} rows")
print(f"first row: {rows[0]}")
print(f"last row:  {rows[-1]}")
