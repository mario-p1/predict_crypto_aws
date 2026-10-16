import json
import os

import boto3
import pandas as pd

from crypto_mlops import utils

s3 = boto3.client("s3")
data_bucket = os.environ["DATA_BUCKET"]


def file_exists(bucket, key):
    return s3.list_objects_v2(Bucket=bucket, Prefix=key).get("KeyCount", 0) > 0


def get_series_prefix(symbol, timeframe):
    return f"raw/symbol={symbol.replace('/', '_')}/timeframe={timeframe}/"


def get_state_file_key(series_prefix):
    return f"{series_prefix}state.json"


def get_month_ohlcv_file_key(series_prefix, month):
    return f"{series_prefix}month={month}/ohlcv.csv"


def read_state(series_prefix):
    state_file_key = get_state_file_key(series_prefix)
    if file_exists(data_bucket, state_file_key):
        state_obj = s3.get_object(Bucket=data_bucket, Key=state_file_key)
        state = json.loads(state_obj["Body"].read())
        print(f"Found state file, last timestamp: {state['last_timestamp']}")
        return state
    return None


def write_state(series_prefix, last_timestamp):
    s3.put_object(
        Bucket=data_bucket,
        Key=get_state_file_key(series_prefix),
        Body=json.dumps({"last_timestamp": str(last_timestamp)}),
    )


def read_csv(file_key):
    if file_exists(data_bucket, file_key):
        return pd.read_csv(f"s3://{data_bucket}/{file_key}")
    return None


def list_months(series_prefix):
    response = s3.list_objects_v2(
        Bucket=data_bucket, Prefix=series_prefix, Delimiter="/"
    )
    return sorted(
        [
            p["Prefix"][len(series_prefix) :].removeprefix("month=").rstrip("/")
            for p in response.get("CommonPrefixes", [])
        ]
    )


def read_monthly_ohlcv(series_prefix, n_months: int | None = None):
    months = list_months(series_prefix)
    if n_months is not None:
        months = months[-n_months:]
    return [
        read_csv(get_month_ohlcv_file_key(series_prefix, month)) for month in months
    ]
