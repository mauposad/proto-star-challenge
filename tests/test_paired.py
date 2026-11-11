import pytest

from proto_star.backtest import backtest_forecaster, baseline_forecaster
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.paired import fold_rows, paired_year_bootstrap

CUTOFFS = (1990, 2000)


def test_paired_difference_reproduces_the_official_raw_score_difference() -> None:
    master = make_climate_master(seed=5)
    kind = get_kind("pooled_trend")
    trend = kind.build(kind.make_spec({"level_years": [10, 15], "trend_window": 40}))
    flat = baseline_forecaster("ten_year_mean")
    official = {
        name: backtest_forecaster(forecaster, master, name=name, cutoffs=CUTOFFS)
        for name, forecaster in {"flat": flat, "trend": trend}.items()
    }
    rows = {
        name: fold_rows(forecaster, master, name=name, cutoffs=CUTOFFS)
        for name, forecaster in {"flat": flat, "trend": trend}.items()
    }
    for window in ("all", "years_1_3", "years_4_7"):
        means = {
            name: frame.loc[frame["window"] == window, "raw_score"].mean()
            for name, frame in official.items()
        }
        result = paired_year_bootstrap(rows["flat"], rows["trend"], window=window, n_boot=200)
        assert result["difference"] == pytest.approx(means["trend"] - means["flat"], abs=1e-9)
        assert result["low"] <= result["difference"] <= result["high"]
