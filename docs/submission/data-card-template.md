# Data card: `data/`

The forecasting pipeline reads the official CMU dataset directly from the
Hugging Face Hub and regenerates all forecasts from code. No weather data after
2018-12-31 is downloaded, stored, or used as a forecast input.

## Files

| File | What it holds | Source | License | Years covered | How prepared | Used for |
| --- | --- | --- | --- | --- | --- | --- |
| No curated forecast-input files uploaded | The pipeline loads `annual_indices` and `city_info` directly | `CMU-OSPO/protostar-climate-train-to-2018` | CC0-1.0 | Through 2018 only | Quality-screened in code by metric-specific missing-day rules | Forecast input |

## Not uploaded (download instead)

| Source | Exact version | How to download | Why not uploaded |
| --- | --- | --- | --- |
| `CMU-OSPO/protostar-climate-train-to-2018` | Hub revision used by the final run; record commit hash before upload | `uv run python scripts/download_protostar_data.py` | Official source is already public and reproducibly downloaded |
| NOAA `ghcnd-stations.txt` | SHA-256 `437ee87f0343bcad408a492cf7a02163fb69255364c541b4006d5d76055d0dc3` | `uv run python scripts/download_ghcn_station_metadata.py` | Static metadata is used only for the interoperability report, not forecasts |

## How the files fit together

- **Join key:** `city_id` is the CMU `city_info.ID`; static NOAA metadata joins
  on the identical GHCN station ID.
- **Units:** temperature in °F, precipitation in inches, CDD in °F-days,
  station elevation in meters.
- **Known limitations:** station records are mostly airport-based; station
  threads can shift location; incomplete days can bias annual indices; static
  station metadata must not be interpreted as weather observations.

## Data rule check

- [x] Every forecast-input weather value is on or before 2018-12-31.
- [x] No 2019–2025 weather-responsive series is read by forecasting code.
- [x] NOAA station metadata is static and used only for interoperability
  reporting, not as a forecast input.
