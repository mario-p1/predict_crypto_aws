import traceback
from datetime import UTC, datetime

import pandas as pd

from crypto_mlops import exchange, storage, transform, utils


def lambda_handler(event, context):
    try:
        symbol = event["symbol"]
        since = event.get("since", "last")
        timeframe = event.get("timeframe", "5m")
        request_limit = 1000
        fetch_candles = int(event.get("fetch_candles", request_limit))

        series_prefix = storage.get_series_prefix(symbol, timeframe)

        print(
            f"Fetching data for {symbol}, timeframe {timeframe}, since {since}, "
            f"request limit {request_limit}, fetch candles {fetch_candles}"
        )

        if since == "last":
            state = storage.read_state(series_prefix)
            if state is not None:
                since = int(state["last_timestamp"]) + 1
                print(
                    f"Continuing from last state timestamp {utils.timestamp_to_str(since)}"
                )
            else:
                return {
                    "statusCode": 400,
                    "result": "No state file found when 'since' is set to 'last'",
                }
        else:
            since = int(
                datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=UTC)
                .timestamp()
                * 1000
            )
            print(f"Continuing from {utils.timestamp_to_str(since)}")

        ex = exchange.create_exchange()
        parsed_timeframe = ex.parse_timeframe(timeframe) * 1000
        end_time = exchange.get_end_time(ex, parsed_timeframe)

        fetched = 0
        affected_files = set()
        while fetched < fetch_candles:
            print(
                f"Fetching candles from {utils.timestamp_to_str(since)} up to "
                f"{utils.timestamp_to_str(end_time)}, "
                f"fetched {fetched}/{fetch_candles}"
            )

            candles = exchange.fetch_candles(
                ex, symbol, timeframe, since, end_time, request_limit
            )

            if len(candles) < 1:
                print("No more candles to fetch")
                break

            fetched += len(candles)

            df = transform.candles_to_df(candles)

            months = df["month"].unique()

            for month in months:
                file_key = storage.get_month_ohlcv_file_key(series_prefix, month)

                df_to_save = df[df["month"] == month].copy()
                existing_df = storage.read_csv(file_key)

                # If file already exists, append to it
                if existing_df is not None:
                    df_to_save = pd.concat([existing_df, df_to_save])

                # Save only the required columns
                df_to_save = df_to_save[
                    ["timestamp", "open", "high", "low", "close", "volume"]
                ].copy()

                storage.write_csv(file_key, df_to_save, index=False)

                # Save last timestamp
                last_timestamp = int(df_to_save["timestamp"].max())
                storage.write_state(series_prefix, last_timestamp)
                affected_files.add(file_key)

                since = last_timestamp + 1
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
