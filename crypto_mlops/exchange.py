import ccxt

from crypto_mlops.utils import timestamp_to_str


def create_exchange():
    return ccxt.binance()


def get_end_time(ex, parsed_timeframe):
    exchange_time = int(ex.fetch_time())  # type: ignore
    print(f"Current Binance time: {timestamp_to_str(exchange_time)}")
    return (exchange_time // parsed_timeframe - 1) * parsed_timeframe


def fetch_candles(ex, symbol, timeframe, since, end_time, request_limit):
    return ex.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=request_limit,
        since=since,
        params={"endTime": end_time},
    )
