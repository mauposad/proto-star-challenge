import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.adjust import (
    CddFromTemperatureSpec,
    PersistenceSpec,
    SkewShiftSpec,
    cdd_from_temperature_forecast,
    persistence_forecast,
    skew_shift_forecast,
)
from proto_star.backtest import baseline_forecaster

KEY = ["city_id", "year", "metric"]
CUTOFF = 2000
YEARS = list(range(2001, 2008))


def _master(persistence: float = 0.0) -> pd.DataFrame:
    """Four cities, 1940-2000. Temperature has AR(1) noise; CDD is exactly linear in it."""
    rng = np.random.default_rng(3)
    rows = []
    for offset, city in enumerate("ABCD"):
        noise = 0.0
        for year in range(1940, CUTOFF + 1):
            noise = persistence * noise + rng.normal()
            temp = 50.0 + 5 * offset + noise
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Avg Temp": temp,
                    "ToT Prcp": 30.0 + 4 * offset + 6 * math.sin(year * 1.3 + offset),
                    "Max Tmax": 95.0 + rng.normal(),
                    "cdd": 1000.0 + (100.0 + 20 * offset) * (temp - 50.0),
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def test_fixed_skew_shift_scales_by_one_minus_q_cv_squared() -> None:
    master = _master()
    base = baseline_forecaster("thirty_year_mean")
    spec = SkewShiftSpec(metrics=["total_precip_in"], q=1 / 3)
    shifted = _indexed(skew_shift_forecast(base, master, CUTOFF, YEARS, spec))
    plain = _indexed(base(master, CUTOFF, YEARS))
    window = master.loc[master["Year"] > CUTOFF - 30]
    stats = window.groupby("ID")["ToT Prcp"].agg(["mean", "std"])
    cv2 = (stats["std"] / stats["mean"]) ** 2
    for city in "ABCD":
        key = (city, 2003, "total_precip_in")
        assert shifted[key] == pytest.approx(plain[key] * (1 - cv2[city] / 3))
        other = (city, 2003, "annual_avg_temp")
        assert shifted[other] == pytest.approx(plain[other])


def test_fitted_skew_shift_runs_and_keeps_every_row() -> None:
    master = _master()
    base = baseline_forecaster("thirty_year_mean")
    spec = SkewShiftSpec(metrics=["total_precip_in"], pseudo_origins=5)
    shifted = skew_shift_forecast(base, master, CUTOFF, YEARS, spec)
    assert len(shifted) == 4 * len(YEARS) * 4
    assert np.isfinite(shifted["predicted_value"]).all()


def test_persistence_leaves_leads_beyond_max_lead_unchanged() -> None:
    master = _master(persistence=0.8)
    base = baseline_forecaster("ten_year_mean")
    spec = PersistenceSpec(base="ten_year_mean", max_lead=2, pseudo_origins=15)
    adjusted = _indexed(persistence_forecast(base, master, CUTOFF, YEARS, spec))
    plain = _indexed(base(master, CUTOFF, YEARS))
    late = adjusted.index.get_level_values("year") > CUTOFF + 2
    pd.testing.assert_series_equal(adjusted[late], plain[late])
    early_temp = (adjusted.index.get_level_values("year") == CUTOFF + 1) & (
        adjusted.index.get_level_values("metric") == "annual_avg_temp"
    )
    assert not np.allclose(adjusted[early_temp], plain[early_temp])


def test_cdd_from_temperature_follows_the_temperature_forecast() -> None:
    master = _master()
    base = baseline_forecaster("ten_year_mean")
    spec = CddFromTemperatureSpec(base="ten_year_mean")
    derived = _indexed(cdd_from_temperature_forecast(base, master, CUTOFF, YEARS, spec))
    window = master.loc[master["Year"] > CUTOFF - 30]
    for offset, city in enumerate("ABCD"):
        t_hat = derived[(city, 2004, "annual_avg_temp")]
        expected = window.loc[window["ID"] == city, "cdd"].mean() + (100.0 + 20 * offset) * (
            t_hat - window.loc[window["ID"] == city, "Avg Temp"].mean()
        )
        assert derived[(city, 2004, "cdd")] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("spec", "params"),
    [(SkewShiftSpec, {"metrics": ["snow"]}), (PersistenceSpec, {"base": "x", "max_lead": 9})],
)
def test_specs_reject_bad_settings(spec: type, params: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        spec.model_validate(params)
