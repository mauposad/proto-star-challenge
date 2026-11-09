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


# One synthetic city per region: (id, lat, lon). Coordinates fall in the assign_region boxes.
_CITIES = (
    ("NW", 46.0, -120.0),
    ("SW", 33.0, -112.0),
    ("NC", 44.0, -95.0),
    ("SC", 31.0, -97.0),
    ("NE", 42.0, -75.0),
    ("SE", 33.0, -84.0),
)


def make_climate_master(
    first_year: int = 1950, last_year: int = 2018, seed: int = 0
) -> pd.DataFrame:
    """A tiny annual master table (six cities, one per region) for forecaster tests.

    It has the columns forecasters read from the real master: ``ID``, ``Year``, ``Lat``,
    ``Lon``, ``region``, the four metric source columns and the missing-day counts. Values
    are a slow warming trend, a year-to-year signal shared by all cities, and seeded noise.
    """
    from proto_star.data.protostar import assign_region

    rng = np.random.default_rng(seed)
    years = np.arange(first_year, last_year + 1)
    shared = rng.normal(0, 0.6, len(years))  # a common anomaly, like a national cold year
    rows = []
    for offset, (city, lat, lon) in enumerate(_CITIES):
        warm = 0.03 * (years - first_year) + shared + rng.normal(0, 0.5, len(years))
        base = 45.0 + 3 * offset
        rows.append(
            pd.DataFrame(
                {
                    "ID": city,
                    "Year": years,
                    "Lat": lat,
                    "Lon": lon,
                    "Avg Temp": base + warm,
                    "ToT Prcp": 30.0 + 4 * offset + rng.normal(0, 4, len(years)),
                    "Max Tmax": 92.0 + offset + 0.5 * warm + rng.normal(0, 1.5, len(years)),
                    "cdd": 600.0 + 250 * offset + 80 * warm,
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
        )
    master = pd.concat(rows, ignore_index=True)
    master["region"] = assign_region(master["Lat"], master["Lon"])
    return master
