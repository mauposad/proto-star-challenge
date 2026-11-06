import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import CURRENT_BEST, resolve_forecaster
from proto_star.climate import (
    BASELINE_DESCRIPTIONS,
    BASELINE_METHODS,
    DEFAULT_CUTOFFS,
    baseline_forecast,
)


def _history(years: list[int], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"city_id": "A", "year": years, "metric": "annual_avg_temp", "actual_value": values}
    )


def _predict(history: pd.DataFrame, method: str, years: list[int] | None = None) -> np.ndarray:
    forecast = baseline_forecast(
        history, cutoff_year=2018, forecast_years=years or [2019], method=method
    )
    return forecast["predicted_value"].to_numpy()


def test_agreed_cutoffs_are_the_kickoff_deck_origins() -> None:
    assert DEFAULT_CUTOFFS == (1980, 1995, 2011)


def test_every_baseline_has_a_description() -> None:
    assert set(BASELINE_DESCRIPTIONS) == set(BASELINE_METHODS)


def test_fifteen_year_mean_uses_last_fifteen_valid_years() -> None:
    history = _history(list(range(1990, 2019)), [1000.0] * 14 + [10.0] * 15)
    assert _predict(history, "fifteen_year_mean")[0] == pytest.approx(10.0)


def test_medians_ignore_an_outlier_that_moves_the_mean() -> None:
    values = [10.0] * 9 + [1000.0]
    history = _history(list(range(2009, 2019)), values)
    assert _predict(history, "ten_year_median")[0] == pytest.approx(10.0)
    assert _predict(history, "ten_year_mean")[0] > 100.0


def test_thirty_year_median_uses_calendar_window() -> None:
    history = _history([1950, 1988, 1989, 2000, 2018], [1e6, 1e6, 1.0, 2.0, 30.0])
    assert _predict(history, "thirty_year_median")[0] == pytest.approx(2.0)


def test_hinge_fit_recovers_flat_then_ramp() -> None:
    years = list(range(1989, 2019))
    values = [50.0 if y <= 2000 else 50.0 + 0.5 * (y - 2000) for y in years]
    forecast = _predict(_history(years, values), "hinge_fit", [2019, 2020])
    assert forecast == pytest.approx([59.5, 60.0])


def test_hinge_fit_on_a_flat_series_stays_flat() -> None:
    years = list(range(1989, 2019))
    assert _predict(_history(years, [7.0] * 30), "hinge_fit", [2019, 2025]) == pytest.approx(7.0)


def test_hinge_fit_falls_back_to_mean_on_short_series() -> None:
    history = _history([2010, 2012, 2014, 2016, 2018], [1.0, 2.0, 3.0, 4.0, 10.0])
    assert _predict(history, "hinge_fit")[0] == pytest.approx(4.0)


def test_hinge_fit_ignores_years_after_the_cutoff() -> None:
    years = list(range(1989, 2019))
    history = _history(years, [50.0 + 0.1 * (y - 1989) for y in years])
    extra = _history([2019, 2020], [1e6, 1e6])
    both = pd.concat([history, extra], ignore_index=True)
    assert _predict(both, "hinge_fit") == pytest.approx(_predict(history, "hinge_fit"))


def test_resolve_forecaster_knows_every_baseline_and_current_best() -> None:
    for name in (*BASELINE_METHODS, CURRENT_BEST):
        assert callable(resolve_forecaster(name))


def test_resolve_forecaster_rejects_unknown_names_and_bad_ensembles() -> None:
    with pytest.raises(ValueError, match="unknown forecaster"):
        resolve_forecaster("magic")
    with pytest.raises(ValueError, match="must map exactly"):
        resolve_forecaster("mine", {"mine": {"cdd": "hinge_fit"}})
