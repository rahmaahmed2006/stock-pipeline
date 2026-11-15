import os
import sys

import pandas as pd

RAW_DIR = sys.argv[1] if len(sys.argv) > 1 else "raw/prices/test"
EXPECTED_FILES = 50
EXPECTED_COLUMNS = ["ticker", "trade_date", "open", "high", "low", "close", "volume"]

files = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".csv"))
print("Files found:", len(files), "| expected:", EXPECTED_FILES)

problems = []

for f in files:
    ticker = f.replace(".csv", "")
    df = pd.read_csv(os.path.join(RAW_DIR, f))

    if list(df.columns) != EXPECTED_COLUMNS:
        problems.append(f"{ticker}: wrong columns {list(df.columns)}")
    if df.duplicated(subset=["ticker", "trade_date"]).any():
        problems.append(f"{ticker}: duplicate dates")
    if df.isnull().any().any():
        problems.append(f"{ticker}: has null values")
    if (df["high"] < df["low"]).any():
        problems.append(f"{ticker}: high < low")
    if (df["volume"] < 0).any():
        problems.append(f"{ticker}: negative volume")
    if (df["ticker"] != ticker).any():
        problems.append(f"{ticker}: ticker column mismatch")
    if not (480 <= len(df) <= 520):
        problems.append(f"{ticker}: unusual row count {len(df)}")

if problems:
    print("PROBLEMS FOUND:")
    for p in problems:
        print(" -", p)
else:
    print("All checks passed.")