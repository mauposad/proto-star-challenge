<!-- For docs/data.md: a new subsection under "Datasets", plus one row in "Input artifact checksums". -->

### NOAA GML Mauna Loa annual mean CO2 (forcing, capped at 2018)

- **Source / URL:** NOAA Global Monitoring Laboratory, Mauna Loa annual mean CO2:
  `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv`.
- **Download:** `uv run python scripts/download_noaa_co2.py`. Keeps years ≤ 2018 only, checks
  them with `assert_weather_cutoff`, writes a `SOURCE.txt` receipt, and refuses to overwrite an
  existing folder.
- **Files:** `data/external/noaa_co2/co2_annmean_mlo_to_2018.csv` (60 rows, 1959–2018) and
  `data/external/noaa_co2/SOURCE.txt`.
- **Schema:** `year` (int), `co2_ppm` (float, annual mean dry-air mole fraction, ppm).
- **License:** public-domain U.S. government work (NOAA GML). NOAA asks users to cite the data
  (Lan, Tans and Thoning, NOAA GML).
- **Vintage:** downloaded on 2026-11-07 from the current file, so pre-2019 values are from
  NOAA's current calibration, not a 2018 vintage. CO2 is a forcing, not a weather observation,
  and no value after 2018 is kept.
- **Use:** forcing for the P21 forced-trend benchmark (`forced_trend_ar1_p21`, `shift10_co2`
  in `configs/agent_paper_cdd_forcing_p06_p21.yaml`). Inside a backtest fold only values up to
  that fold's cut-off are read. Later years are extrapolated linearly from the last 10 values.
- **CI:** the publish workflow does not download this file, so a CO2-based `submit:` would not
  rebuild on CI. No CO2 forecaster is submitted.

Checksum row:

| `data/external/noaa_co2/co2_annmean_mlo_to_2018.csv` | `0ef2a07a4f2a5961efd070912079140446eb5ddd1b1d5587fddeb5844056a245` |
