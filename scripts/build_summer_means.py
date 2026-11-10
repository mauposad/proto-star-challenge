"""Build the per-city, per-year June-August means used by the H2/H14 hottest-day trials.

Reads data/raw/protostar/daily.parquet; writes data/interim/protostar/summer_means.parquet.
Every value uses only its own year's days (see proto_star.data.summer).

Usage: uv run python scripts/build_summer_means.py
"""

from proto_star.data.protostar import load_daily
from proto_star.data.summer import SUMMER_DIR, SUMMER_FILE, summer_means


def main() -> None:
    table = summer_means(load_daily(columns=("tmax", "tmin")))
    SUMMER_DIR.mkdir(parents=True, exist_ok=True)
    table.to_parquet(SUMMER_DIR / SUMMER_FILE, index=False)
    print(
        f"wrote {len(table)} city-years to {SUMMER_DIR / SUMMER_FILE}; "
        f"{int(table['jja_tmax'].notna().sum())} with at least 85 summer days"
    )


if __name__ == "__main__":
    main()
