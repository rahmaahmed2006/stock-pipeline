# Data Extraction (Member 1)

## Source
Daily stock prices from Yahoo Finance via the `yfinance` Python library (no API key needed).
50 tickers listed in `extract/tickers.txt`.

## Output
One CSV per ticker, in `raw/prices/<run_date>/<TICKER>.csv`

| Column | Type | Example |
|---|---|---|
| ticker | string | AAPL |
| trade_date | date (YYYY-MM-DD) | 2024-11-14 |
| open | double | 225.02 |
| high | double | 228.87 |
| low | double | 225.00 |
| close | double | 228.22 |
| volume | long | 44923900 |

Notes: `close` is the raw (unadjusted) close price. CSV files have a header row.

## Setup
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run
Initial load (2 years):
```
python extract/extract_prices.py --period 2y
```

Daily update (last 10 trading days, covers the 5-day lookback):
```
python extract/extract_prices.py --period 10d
```

Arguments: `--tickers-file`, `--run-date` (default today), `--output-dir` (default raw/prices), `--period` (default 2y).

## Behavior
- 3 seconds wait between tickers (rate limiting).
- Up to 5 retries per ticker with exponential backoff (1, 2, 4, 8, 16 s).
- If any ticker fails, the script exits with code 1 so Airflow marks the task as failed.

## Validation
```
python extract/validate_raw.py raw/prices/<run_date>
```
Checks: 50 files, expected columns, no duplicates, no nulls, high >= low, volume >= 0, row count.