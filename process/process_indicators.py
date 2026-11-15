import argparse
import os
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="raw/prices/2026-11-15")
    parser.add_argument("--output-dir", default="curated/indicators")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("indicators").master("local[*]").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    files = [os.path.join(args.input_dir, f)
             for f in sorted(os.listdir(args.input_dir)) if f.endswith(".csv")]
    df = spark.read.csv(files, header=True, inferSchema=True)

    # تنضيف
    df = (df.dropDuplicates(["ticker", "trade_date"])
            .dropna(subset=["ticker", "trade_date", "close"]))

    w = Window.partitionBy("ticker").orderBy("trade_date")

    df = (df
          .withColumn("row_num", F.row_number().over(w))
          .withColumn("daily_return", F.col("close") / F.lag("close", 1).over(w) - 1)
          .withColumn("ma20", F.avg("close").over(w.rowsBetween(-19, 0)))
          .withColumn("ma50", F.avg("close").over(w.rowsBetween(-49, 0)))
          .withColumn("vol20", F.stddev("daily_return").over(w.rowsBetween(-19, 0)))
          .withColumn("delta", F.col("close") - F.lag("close", 1).over(w))
          .withColumn("gain", F.when(F.col("delta") > 0, F.col("delta")).otherwise(0.0))
          .withColumn("loss", F.when(F.col("delta") < 0, -F.col("delta")).otherwise(0.0))
          .withColumn("avg_gain", F.avg("gain").over(w.rowsBetween(-13, 0)))
          .withColumn("avg_loss", F.avg("loss").over(w.rowsBetween(-13, 0)))
          .withColumn("rsi14", F.when(F.col("avg_loss") == 0, None)
                               .otherwise(100 - 100 / (1 + F.col("avg_gain") / F.col("avg_loss"))))
          .withColumn("is_warm", F.col("row_num") >= 50)
          .drop("delta", "gain", "loss", "avg_gain", "avg_loss"))

    # الكتابة بـ pandas بدل Spark (لتفادي مشكلة winutils على Windows)
    pdf = df.orderBy("ticker", "trade_date").toPandas()
    pdf["trade_date"] = pd.to_datetime(pdf["trade_date"]).dt.date
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, "indicators.parquet")
    pdf.to_parquet(out_path, index=False)

    print("rows written:", len(pdf))
    print("tickers:", pdf["ticker"].nunique())
    print("file:", out_path)
    print(pdf.dtypes)

    spark.stop()


if __name__ == "__main__":
    main()