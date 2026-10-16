import pandas as pd


def candles_to_df(candles):
    df = pd.DataFrame(
        candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["month"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m")
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return df
