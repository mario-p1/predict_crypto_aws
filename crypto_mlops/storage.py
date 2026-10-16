import json
import os

import boto3
import pandas as pd

from crypto_mlops import utils

s3 = boto3.client("s3")
data_bucket = os.environ["DATA_BUCKET"]


def file_exists(bucket, key):
    return s3.list_objects_v2(Bucket=bucket, Prefix=key).get("KeyCount", 0) > 0


def get_symbol_base(symbol, timeframe):
    return f"raw/symbol={symbol.replace('/', '_')}/timeframe={timeframe}/"


def get_state_file_key(symbol, timeframe):
    return f"{get_symbol_base(symbol, timeframe)}state.json"


def get_month_ohlcv_file_key(file_base_key, month):
    return f"{file_base_key}month={month}/ohlcv.csv"


def read_state(symbol, timeframe):
    state_file_key = get_state_file_key(symbol, timeframe)
    if file_exists(data_bucket, state_file_key):
        state_obj = s3.get_object(Bucket=data_bucket, Key=state_file_key)
        state = json.loads(state_obj["Body"].read())
        print(f"Found state file, last timestamp: {state['last_timestamp']}")
        return state
    return None


def write_state(symbol, timeframe, last_timestamp):
    s3.put_object(
        Bucket=data_bucket,
        Key=get_state_file_key(symbol, timeframe),
        Body=json.dumps({"last_timestamp": str(last_timestamp)}),
    )


def read_csv(file_key):
    if file_exists(data_bucket, file_key):
        return pd.read_csv(f"s3://{data_bucket}/{file_key}")
    return None


def list_months(symbol, timeframe):
    prefix = get_symbol_base(symbol, timeframe)
    response = s3.list_objects_v2(Bucket=data_bucket, Prefix=prefix, Delimiter="/")
    return sorted(
        [
            p["Prefix"][len(prefix) :].removeprefix("month=").rstrip("/")
            for p in response.get("CommonPrefixes", [])
        ]
    )


def read_monthly_ohlcv(symbol, timeframe, n_months: int | None = None):
    file_base_key = get_symbol_base(symbol, timeframe)
    months = list_months(symbol, timeframe)
    if n_months is not None:
        months = months[-n_months:]
    return [
        read_csv(get_month_ohlcv_file_key(file_base_key, month)) for month in months
    ]
