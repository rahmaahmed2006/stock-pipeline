import argparse
import os
import time
from datetime import date

import yfinance as yf

COLUMNS = ["ticker", "trade_date", "open", "high", "low", "close", "volume"]
MAX_RETRIES = 5
SLEEP_BETWEEN_TICKERS = 3


def fetch_ticker(ticker, period="2y"):
    df = yf.download(ticker, period=period, interval="1d",
                     auto_adjust=False, progress=False)
    if df is None or df.empty:
        raise ValueError("empty response")
    df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"date": "trade_date"})
    df["ticker"] = ticker
    df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")
    return df[COLUMNS]


def fetch_with_retry(ticker, period):
    for attempt in range(MAX_RETRIES):
        try:
            return fetch_ticker(ticker, period)
        except Exception as e:
            wait = 2 ** attempt
            print(f"{ticker}: attempt {attempt + 1}/{MAX_RETRIES} failed ({e}) -> waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"{ticker} failed after {MAX_RETRIES} attempts")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers-file", default="extract/tickers.txt")
    parser.add_argument("--run-date", default=str(date.today()))
    parser.add_argument("--output-dir", default="raw/prices")
    parser.add_argument("--period", default="2y")
    args = parser.parse_args()

    with open(args.tickers_file) as f:
        tickers = [line.strip() for line in f if line.strip()]
    print("Total tickers:", len(tickers))

    out_dir = os.path.join(args.output_dir, args.run_date)
    os.makedirs(out_dir, exist_ok=True)
    failed = []

    for t in tickers:
        try:
            df = fetch_with_retry(t, args.period)
            df.to_csv(os.path.join(out_dir, f"{t}.csv"), index=False)
            print(t, "->", len(df), "rows")
        except Exception as e:
            print(f"{t}: FAILED -> {e}")
            failed.append(t)
        time.sleep(SLEEP_BETWEEN_TICKERS)

    print("Done. failed =", failed)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()