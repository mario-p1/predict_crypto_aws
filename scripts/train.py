import pandas as pd

from crypto_mlops import storage


def main():
    symbol = "BTC/USDT"
    timeframe = "5m"
    n_months = 3

    dfs = storage.read_monthly_ohlcv(symbol, timeframe, n_months)
    df = pd.concat(dfs, ignore_index=True)
    print(df)


if __name__ == "__main__":
    main()
