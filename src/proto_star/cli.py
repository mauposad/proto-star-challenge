"""Command line interface: `uv run proto-star --help`."""

from pathlib import Path

import typer
from dotenv import load_dotenv

app = typer.Typer(no_args_is_help=True, help="proto-star training & submission tools.")
load_dotenv()  # picks up HF_TOKEN etc. from .env


@app.command()
def train(config: Path = typer.Argument(..., help="Path to experiment YAML")) -> None:
    """Train a model and save it to runs/."""
    from proto_star.config import load_config
    from proto_star.train import train as _train

    run_dir = _train(load_config(config))
    typer.echo(run_dir)


@app.command()
def predict(run_dir: Path = typer.Argument(..., help="A runs/<run> directory")) -> None:
    """Write a validated leaderboard submission to submissions/."""
    from proto_star.predict import predict as _predict

    typer.echo(_predict(run_dir))


@app.command("validate-data")
def validate_data(config: Path) -> None:
    """Load and validate the training (and test) data without training."""
    from proto_star.config import load_config
    from proto_star.data.load import load_test, load_train
    from proto_star.data.validate import validate

    cfg = load_config(config)
    df = load_train(cfg.data)
    validate(df, cfg.data)
    typer.echo(f"train OK: {len(df)} rows, {df.shape[1]} columns")
    if cfg.data.test_path or cfg.data.source == "hf":
        test = load_test(cfg.data)
        validate(test, cfg.data, has_target=False)
        typer.echo(f"test OK: {len(test)} rows")


@app.command()
def models() -> None:
    """List registered model names."""
    from proto_star.models import available_models

    typer.echo("\n".join(available_models()))


@app.command("download-climate-data")
def download_climate_data() -> None:
    """Download official annual challenge data, enforcing the 2018 cutoff."""
    from scripts.download_protostar_data import main

    main()


@app.command("download-station-metadata")
def download_station_metadata() -> None:
    """Download static NOAA station metadata for interoperability analysis."""
    from scripts.download_ghcn_station_metadata import main

    main()


@app.command("climate-metadata-report")
def climate_metadata_report() -> None:
    """Join CMU challenge cities to the downloaded static NOAA station metadata."""
    from scripts.build_station_metadata_report import main

    main()


@app.command("climate-backtest")
def climate_backtest(
    annual_path: Path = typer.Argument(
        ..., help="Local annual_indices.parquet downloaded from CMU"
    ),
    cutoff: list[int] = typer.Option(
        [1997, 2002, 2007, 2011], help="Historical origin year; may be provided repeatedly"
    ),
) -> None:
    """Compare leakage-safe climate baselines over seven-year historical horizons."""
    import pandas as pd

    from proto_star.climate import annual_to_long, backtest_baselines

    history = annual_to_long(pd.read_parquet(annual_path))
    results = backtest_baselines(history, cutoffs=cutoff)
    typer.echo(results.to_csv(index=False))


@app.command("climate-submission")
def climate_submission(
    annual_path: Path = typer.Argument(
        ..., help="Local annual_indices.parquet downloaded from CMU"
    ),
    city_path: Path = typer.Argument(..., help="Local city_info.parquet downloaded from CMU"),
    method: str = typer.Option("linear_trend", help="Baseline method selected from backtests"),
    output: Path = typer.Option(Path("submissions/protostar_baseline.csv")),
) -> None:
    """Write and validate a complete 2019-2025 ProtoStar forecast submission."""
    import pandas as pd

    from proto_star.climate import (
        FORECAST_CUTOFF,
        FORECAST_YEARS,
        annual_to_long,
        baseline_forecast,
        validate_submission,
    )

    annual = pd.read_parquet(annual_path)
    cities = pd.read_parquet(city_path)
    history = annual_to_long(annual)
    submission = baseline_forecast(
        history,
        cutoff_year=FORECAST_CUTOFF,
        forecast_years=FORECAST_YEARS,
        method=method,
    ).sort_values(["city_id", "year", "metric"])
    validate_submission(submission, cities["ID"].astype(str).unique())
    output.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(output, index=False)
    typer.echo(output)


@app.command("climate-ensemble-submission")
def climate_ensemble_submission(
    annual_path: Path = typer.Argument(
        ..., help="Local annual_indices.parquet downloaded from CMU"
    ),
    city_path: Path = typer.Argument(..., help="Local city_info.parquet downloaded from CMU"),
    output: Path = typer.Option(Path("submissions/protostar_metric_ensemble.csv")),
) -> None:
    """Write the backtest-selected metric-specific 2019-2025 forecast submission."""
    import pandas as pd

    from proto_star.climate import (
        FORECAST_CUTOFF,
        FORECAST_YEARS,
        annual_to_long,
        backtest_baselines,
        metric_ensemble_forecast,
        select_metric_methods,
        validate_submission,
    )

    history = annual_to_long(pd.read_parquet(annual_path))
    backtests = backtest_baselines(history, cutoffs=[1997, 2002, 2007, 2011])
    methods = select_metric_methods(backtests)
    submission = metric_ensemble_forecast(
        history,
        cutoff_year=FORECAST_CUTOFF,
        forecast_years=FORECAST_YEARS,
        methods_by_metric=methods,
    ).sort_values(["city_id", "year", "metric"])
    validate_submission(submission, pd.read_parquet(city_path)["ID"].astype(str).unique())
    output.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(output, index=False)
    typer.echo(f"{output} using {methods}")


if __name__ == "__main__":
    app()
