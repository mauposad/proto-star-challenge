"""Download the official ProtoStar challenge tables, enforcing the 2018 cutoff.

Only the compact annual indices and city metadata are needed for the initial
baselines.  The much larger daily table is intentionally not downloaded here.
"""

from pathlib import Path

from datasets import load_dataset

from proto_star.climate import FORECAST_CUTOFF, annual_to_long
from proto_star.paths import RAW_DIR

REPO = "CMU-OSPO/protostar-climate-train-to-2018"


def main(destination: Path = RAW_DIR / "protostar") -> None:
    """Write immutable official annual and city tables to the local raw-data store."""
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"{destination} already contains raw data; refusing to overwrite it")

    annual = load_dataset(REPO, "annual_indices", split="train").to_pandas()
    cities = load_dataset(REPO, "city_info", split="train").to_pandas()
    annual_to_long(annual, cutoff_year=FORECAST_CUTOFF)

    destination.mkdir(parents=True, exist_ok=False)
    annual.to_parquet(destination / "annual_indices.parquet", index=False)
    cities.to_parquet(destination / "city_info.parquet", index=False)
    (destination / "SOURCE.txt").write_text(
        "\n".join(
            [
                f"source={REPO}",
                "configs=annual_indices,city_info",
                "license=CC0-1.0",
                f"enforced_weather_cutoff={FORECAST_CUTOFF}-12-31",
                "downloaded_by=scripts/download_protostar_data.py",
                "",
            ]
        )
    )
    print(f"Wrote official ProtoStar tables to {destination}")


if __name__ == "__main__":
    main()
