import json
import os
import traceback
from datetime import UTC, datetime

import boto3
import ccxt
import pandas as pd

s3 = boto3.client("s3")
data_bucket = os.environ["DATA_BUCKET"]


def file_exists(bucket, key):
    return s3.list_objects_v2(Bucket=bucket, Prefix=key).get("KeyCount", 0) > 0


def timestamp_to_str(ts):
    return datetime.fromtimestamp(ts / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")


def lambda_handler(event, context):
    try:
        symbol = event["symbol"]
        since = event.get("since", "last")
        timeframe = event.get("timeframe", "5m")
        request_limit = 1000
        fetch_candles = int(event.get("fetch_candles", request_limit))

        file_base_key = f"raw/symbol={symbol.replace('/', '_')}/timeframe={timeframe}/"
        state_file_key = f"{file_base_key}state.json"

        print(
            f"Fetching data for {symbol} since {since} with timeframe {timeframe}, of total {fetch_candles}"
        )

        if since == "last":
            if file_exists(data_bucket, state_file_key):
                state_obj = s3.get_object(Bucket=data_bucket, Key=state_file_key)
                state = json.loads(state_obj["Body"].read())
                since = int(state["last_timestamp"]) + 1
                print(f"Found state file, last timestamp: {state['last_timestamp']}")
                print(f"Continuing from last state timestamp {since}")
            else:
                return {
                    "statusCode": 400,
                    "result": "No state file found when 'since' is set to 'last'",
                }
        else:
            since = int(since)
            print(f"Continuing from timestamp {since}")

        ex = ccxt.binance()
        parsed_timeframe = ex.parse_timeframe(timeframe) * 1000
        fetched = 0
        affected_files = set()

        while fetched < fetch_candles:
            current_binance_time = int(ex.fetch_time())  # type: ignore

            print(f"Current Binance time: {timestamp_to_str(current_binance_time)}")

            end_time = (current_binance_time // parsed_timeframe - 1) * parsed_timeframe

            print(
                f"Fetching candles from {timestamp_to_str(since)} up to {timestamp_to_str(end_time)}, fetched {fetched}/{fetch_candles}"
            )

            candles = ex.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=request_limit,
                since=since,
                params={"endTime": end_time},
            )

            if len(candles) < 1:
                print("No more candles to fetch")
                break

            fetched += len(candles)

            df = pd.DataFrame(
                candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["month"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime(
                "%Y-%m"
            )
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            df = df.set_index("timestamp")

            months = df["month"].unique()

            for month in months:
                # If file already exists, append to it
                file_key = f"{file_base_key}month={month}/ohlcv.csv"

                df_to_save = df[df["month"] == month].copy()
                if file_exists(data_bucket, file_key):
                    existing_df = pd.read_csv(
                        f"s3://{data_bucket}/{file_key}"
                    ).set_index("timestamp")
                    df_to_save = pd.concat([existing_df, df[df["month"] == month]])

                df_to_save = df_to_save.drop(columns=["month"])
                df_to_save.to_csv(f"s3://{data_bucket}/{file_key}")

                # Save last timestamp
                s3.put_object(
                    Bucket=data_bucket,
                    Key=state_file_key,
                    Body=json.dumps({"last_timestamp": str(df_to_save.index.max())}),
                )
                since = df_to_save.index.max() + 1
                affected_files.add(file_key)

        return {
            "statusCode": 200,
            "result": {
                "affected_files": list(affected_files),
                "total_fetched": fetched,
                "last_timestamp": since - 1,
            },
        }
    except Exception as e:  # noqa: BLE001
        traceback.print_exception(e)
        return {"statusCode": 500, "result": str(e)}
