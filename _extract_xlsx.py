import sys, csv
import pandas as pd
from pathlib import Path

src = Path(sys.argv[1])
dst_dir = Path(sys.argv[2])
dst_dir.mkdir(parents=True, exist_ok=True)

print("reading " + src.name + "...")
df = pd.read_excel(src, engine="openpyxl", nrows=200)
print("  rows: " + str(len(df)) + ", cols: " + str(len(df.columns)))

# (col_idx, field, default) -- 0-based column index
FIELDS = [
    (0,  "case_no",          "P_MOCK"),   # A 总编号
    (7,  "age",              "30"),       # H 女年龄
    (9,  "bmi",              "22.0"),     # J 女体重指数
    (52, "amh",              "2.0"),      # BA 基础激素AMH (BA = 26+0, 0-based = 52)
    (28, "afc",              "10"),       # AC AFC (AC = 26+2, 0-based = 28)
    (45, "basal_fsh",        "6.0"),      # AT 基础激素FSH (AT = 26+19, 0-based = 45)
    (46, "basal_lh",         "5.0"),      # AU
    (49, "basal_e2",         "40.0"),     # AX
    (50, "basal_p",          "0.3"),      # AY
    (10, "infertility_years", "3.0"),     # K
]

rows = []
for i, row in df.iterrows():
    out = {"patient_uuid": "P" + str(i+1).zfill(5)}
    for col_idx, field, default in FIELDS:
        if col_idx < len(df.columns):
            v = row.iloc[col_idx]
            if pd.notna(v) and str(v).strip():
                try:
                    if field == "case_no":
                        out[field] = str(v).strip()
                    else:
                        out[field] = float(v)
                except (ValueError, TypeError):
                    out[field] = default
            else:
                out[field] = default
        else:
            out[field] = default
    out["source_type"] = "EXCEL_IMPORT"
    rows.append(out)

out_csv = dst_dir / "patient_import.csv"
with open(out_csv, "w", encoding="utf-8", newline="") as f:
    if rows:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
print("  -> " + str(out_csv) + " (" + str(len(rows)) + " rows)")
print("  first row: " + str(rows[0] if rows else None))

