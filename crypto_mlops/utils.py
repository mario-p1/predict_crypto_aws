from datetime import UTC, datetime


def timestamp_to_str(ts):
    return datetime.fromtimestamp(ts / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
