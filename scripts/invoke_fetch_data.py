from crypto_mlops.handlers.fetch_data import lambda_handler


def main():
    print(
        lambda_handler(
            {
                "symbol": "BTC/USDT",
                "since": "2024-01-01 00:00:00",
                # "since": "last",
                "fetch_candles": 5_000,
            },
            {},
        )
    )


if __name__ == "__main__":
    main()
