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


if __name__ == "__main__":
    app()
