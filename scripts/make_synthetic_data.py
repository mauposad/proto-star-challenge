"""Write synthetic train/test parquet files to data/raw/synthetic/.

Usage:
    uv run python scripts/make_synthetic_data.py
"""

from proto_star.data.synthetic import make_train_test
from proto_star.paths import RAW_DIR


def main() -> None:
    out = RAW_DIR / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    train, test = make_train_test()
    train.to_parquet(out / "train.parquet", index=False)
    test.to_parquet(out / "test.parquet", index=False)
    print(f"wrote {len(train)} train / {len(test)} test rows to {out}")


if __name__ == "__main__":
    main()
