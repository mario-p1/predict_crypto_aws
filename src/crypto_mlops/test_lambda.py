from src.crypto_mlops.fetch_data_function import lambda_handler


def main():
    # print(lambda_handler({"symbol": "BTC/USDT", "since": 1735988400000}, {}))
    print(lambda_handler({"symbol": "BTC/USDT", "since": "last"}, {}))


if __name__ == "__main__":
    main()
