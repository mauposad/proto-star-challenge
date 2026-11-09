# External data (agent D, plan Section 6): what was fetched and what was not

Branch `agent/external-data`. Data and loaders only: no forecast values were written or
adjusted, and nothing here was scored. Full data cards are in `docs/data.md`
("External data for the regional model").

## Delivered

| Rank | Source | Status | Output |
|---|---|---|---|
| 1 | Census county population 1970-2023 | done | `city_static.parquet` `pop_*`, `log_pop_growth_*` |
| 3 | Elevation (GHCN inventory), distance to coast and Great Lakes (Natural Earth 10m) | done | `city_static.parquet` |
| 4 | ONI-style Nino 3.4, AMO, PDO (from ERSSTv5), CPC PDO, NAO (NCEP R1 SLP), to 2018-12 | done | `indices_to_2018.parquet` |
| 2 | NLCD impervious 2001/2011/2016, tree canopy 2011, 1/5/10 km buffers | done (840 windows, 210 cities x 4 layers, all buffers non-missing) | `city_static.parquet` `imperv_*`, `canopy_*` |
| 5 | GHCN-Daily neighbors within 100 km, annual summaries to 2018 | done (995 stations, 1,044 city links, 208 cities with 5, 74,004 station-years 1843-2018) | `data/interim/external/ghcn_neighbors_annual_to_2018.parquet` |
| 6 | ERSSTv5 grid (global 4-degree + three 2-degree boxes) to 2018-12 | done | `data/external/ersst_v5/`, `load_sst_grid` |

## Validation status

Validation resumed on 2026-11-08 with the repository's existing `geo` optional extra
(`uv sync --extra geo`); no dependency or lock-file change was needed.

- `make check`: 156 passed, 2 existing pandas performance warnings, no skips; Ruff,
  formatting, and mypy passed. The ten climate-index/SST tests that were previously
  skipped without xarray all ran.
- Read-only 1980-fold smoke test on the persisted artifacts: `load_indices(1980)` returned
  1,524 months through 1980-12; `load_sst_grid(cutoff_year=1980)` returned 1,523 months
  through 1980-12 (the documented 1902-10 gap); `load_neighbor_annual(1980)` returned
  44,268 station-years through 1980.
- Every individual SHA-256 recorded in `docs/data.md` matches the local artifact. The
  multi-file NLCD and GHCN hashes remain recorded below.

No source defect was found in this audit. The policy questions below remain human decisions;
passing the cutoff and unit tests does not resolve them.

## How the 2018 cap is enforced

- Every weather-responding request is limited on the server: ERDDAP griddap time range
  ending `2018-12-15` (ERSSTv5), ERDDAP tabledap `time<=2018-12-31T23:59:59Z` (CPC PDO),
  an OPeNDAP index range ending at the last 2018 month (NCEP R1 SLP), and the NCEI Access
  Data Service `endDate=2018-12-31` (neighbors).
- The response is parsed and passed through `assert_weather_cutoff` in memory; only then is
  it written (`indices.fetch_checked`, `parse_gsoy`). A 2019 value would stop the script
  with nothing saved.
- Loaders check the file against 2018, drop rows after the fold cut-off, and check again
  against the fold cut-off. Leak tests: `tests/test_external_indices.py`,
  `tests/test_external_ghcn_neighbors.py`.
- The indices computed here use base periods that end by 1980 (anomaly base 1951-1980,
  PDO EOF 1900-1980), so their values do not depend on any year after the earliest fold
  cut-off. The ONI is a trailing (not centred) 3-month mean for the same reason.

## Not fetched, and why

- **CPC ONI** (`oni.ascii.txt`, and the CCIEA ERDDAP copy): recent values use the 1991-2020
  base period, i.e. they are fitted on 2019-2020 SST. Replaced by our own Nino 3.4 index.
- **PSL / CPC index ASCII files** (AMO, NAO, PDO, ONI): one full file each, running to the
  present; no date-limited endpoint. Not downloaded (honor-code rule). NAO and AMO have no
  ERDDAP copy that we could find (searched CoastWatch, Upwell, CCIEA, APDRC, NCEI ERDDAP).
- **NLCD national files** (> 1 GB each): replaced by per-station WCS windows.
- **Annual NLCD (1985-2023) fractional impervious**: not offered on the MRLC WCS (only
  change-count layers), so the 1985 and 1995 states of the surface are not available.
- **Census Data API**: now needs an API key; the flat Population Estimates files were used.

## Data-access friction (for the README Feedback section)

- Most climate-index providers (NOAA PSL, CPC) publish only whole files that run to the
  present. A team under a hard data cut-off cannot download them without seeing 2019+
  values. A date-limited endpoint (or ERDDAP copies) for the standard indices would help.
- CPC's ONI changes its base period every five years, so "the ONI for 1985" depends on
  data from 2019-2020 in today's file. Reproducible, cut-off-safe research needs a
  fixed-base version.
- The Census Data API requires a key for every call, even for a handful of counties.
- `99c8_00.txt` (1990s county estimates) as served has corrupted bytes in a few lines;
  the parser reads it by fixed column so the error stays local.
- The ERDDAP copy of ERSSTv5 has no 1902-10 time step; the 4-degree global request
  failed once with HTTP 503 and worked on retry.
- No library for GeoTIFF/projection was installed (no rasterio, pyproj); the Albers
  projection and GeoTIFF tags are handled in code (PIL only).

## Needs a human decision

- **NCEP/NCAR Reanalysis 1** (used for the NAO) is a reanalysis: a frozen 1995 model
  assimilating observations. It is not climate-model projection output like CMIP6, but the
  honor code asks for a ruling on "climate model output". If ruled out, drop the `nao`
  column; nothing else uses it.
- **ERSSTv5** is a statistical reconstruction that NOAA re-runs monthly. Its low-frequency
  component uses a multi-year filter, so values near 2018 in today's version may be
  slightly influenced by later observations. The plan approved ERSSTv5 (rank 6); flagging
  only so the team can decide whether to weight late-2010s SST indices less.
- **CPC PDO** (`pdo_cpc`): EOF and climatology are pre-2019 (1900-1993), but the
  normalisation period is not documented. `pdo` (ours, 1900-1980 fit) correlates 1.00 with
  it since 1950 and is the safe choice.
- **Neighbor distance 0 km**: some neighbors share coordinates with the city station
  under another ID (co-located or earlier thread). Useful for station-step estimates, but
  not independent evidence; users should decide whether to drop `distance_km < 1`.
- **NLCD for early folds**: the earliest NLCD is 2001, so for the 1980 and 1995 folds the
  land-cover covariates describe the future (non-weather) state of the station area.

## Checksums of multi-file downloads

- NLCD windows (`data/external/nlcd/*/*.tif`, 840 files, 133.6 MB): combined sha256
  `c4c18cf6029bd3a555cb5366a69ff651a693ad6ad364288abc73c0c8eb21d318`
  (as printed by `scripts/download_nlcd.py`).
- GHCN neighbor annual batches (`data/external/ghcn_neighbors/gsoy/*.csv`, 100 files):
  combined sha256 `e65817a15f945ef3c3b59e0ceabb13c608ad7a5d31f9cbcb8c7adcbfa9da601c`;
  `ghcnd-inventory.txt` sha256
  `3d7378c3ecad6841340b47392f10b391c42a5f47369765e6bb032704d2301125`. The inventory is
  updated daily by NCEI, so a fresh download can select slightly different neighbors.

## Max date in every weather-responding output

| Output | Max date |
|---|---|
| `indices_to_2018.parquet` (all columns) | 2018-12 |
| `data/external/ersst_v5/*.nc` | 2018-12-15 |
| `cpc_pdo_to_2018.csv` | 2018-12-01 |
| `ncep_r1_slp_natl_to_2018.nc` | 2018-12-01 |
| `ghcn_neighbors_annual_to_2018.parquet` | year 2018 |
