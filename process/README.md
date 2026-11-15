# Data Processing (Member 2)

## What it does
Reads the raw CSV files from the extraction step, cleans them, computes indicators per ticker with PySpark window functions, and writes one Parquet file.

## Input
`raw/prices/<run_date>/<TICKER>.csv` with columns: ticker, trade_date, open, high, low, close, volume

## Output
`curated/indicators/indicators.parquet` (one row per ticker per trading day)

| Column | Meaning |
|---|---|
| row_num | Trading-day number per ticker (1 = first day) |
| daily_return | (close / previous close) - 1 |
| ma20 | Average close over the last 20 rows |
| ma50 | Average close over the last 50 rows |
| vol20 | Std. deviation of daily_return over the last 20 rows |
| rsi14 | RSI over 14 rows (simple average of gains/losses) |
| is_warm | true when row_num >= 50 (indicators are reliable) |

## Notes
- Windows use rowsBetween (trading days), not calendar days.
- Rows where is_warm = false have indicators based on fewer days; reports should exclude them.
- rsi14 is NULL when there were no losses in the window.
- Parquet is written with pandas/pyarrow because Spark's native write needs Hadoop native libraries on Windows.

## Run
```
python process/process_indicators.py --input-dir raw/prices/2026-11-15 --output-dir curated/indicators
```

Requires Java 17+.