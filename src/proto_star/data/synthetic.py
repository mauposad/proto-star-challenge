"""Synthetic daily weather data for smoke tests and pipeline development.

Delete or ignore once the real challenge data is available.
"""

import numpy as np
import pandas as pd


def make_weather(n_days: int = 1500, n_stations: int = 3, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-01", periods=n_days, freq="D")
    frames = []
    for station in range(n_stations):
        doy = dates.day_of_year.to_numpy()
        season = np.sin(2 * np.pi * (doy - 110) / 365.25)
        trend = 0.0008 * np.arange(n_days)  # slow warming
        humidity = 60 + 15 * rng.standard_normal(n_days)
        pressure = 1013 + 8 * rng.standard_normal(n_days)
        temp = 12 + 10 * season + trend + 0.05 * (humidity - 60) + rng.normal(0, 2, n_days)
        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "station_id": station,
                    "humidity": humidity,
                    "pressure": pressure,
                    "max_temp": temp,
                }
            )
        )
    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "id", np.arange(len(df)))
    return df


def make_train_test(
    test_fraction: float = 0.15, **kwargs: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Mimic a leaderboard: test = latest period with the target removed."""
    df = make_weather(**kwargs)
    cutoff = df["date"].quantile(1 - test_fraction)
    train = df[df["date"] < cutoff].reset_index(drop=True)
    test = df[df["date"] >= cutoff].drop(columns="max_temp").reset_index(drop=True)
    return train, test
