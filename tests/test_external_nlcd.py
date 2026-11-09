import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.climate import ClimateDataError
from proto_star.data.external.nlcd import (
    LAYERS,
    albers_conus,
    buffer_means,
    load_city_land_cover,
    read_geotiff,
    tile_path,
    wcs_params,
    wcs_query,
)

Image = pytest.importorskip("PIL.Image")
TiffImagePlugin = pytest.importorskip("PIL.TiffImagePlugin")


def _geotiff(values: np.ndarray, left: float, top: float) -> bytes:
    tags = TiffImagePlugin.ImageFileDirectory_v2()
    tags[34264] = (30.0, 0.0, 0.0, left, 0.0, -30.0, 0.0, top) + (0.0,) * 7 + (1.0,)
    tags.tagtype[34264] = 12  # double
    buffer = io.BytesIO()
    Image.fromarray(values.astype(np.uint8)).save(buffer, format="TIFF", tiffinfo=tags)
    return buffer.getvalue()


def test_albers_matches_snyder_example() -> None:
    assert albers_conus(23.0, -96.0) == pytest.approx((0.0, 0.0), abs=1e-6)
    # Snyder (1987) p. 292 gives (1885472.7, 1535925.0) on Clarke 1866; GRS80 differs < 100 m
    x, y = albers_conus(35.0, -75.0)
    assert x == pytest.approx(1885472.7, abs=100)
    assert y == pytest.approx(1535925.0, abs=100)


def test_wcs_query_has_two_subsets() -> None:
    query = wcs_query(wcs_params("cov", 1000.0, 2000.0))
    assert "subset=X(-9050,11050)" in query and "subset=Y(-8050,12050)" in query


def test_buffer_means_skip_nodata_and_use_radius() -> None:
    values = np.zeros((101, 101))
    values[50, 50] = 90.0  # station pixel
    values[0, :] = 127  # no-data flag, outside any buffer used here anyway
    transform = (0.0, 101 * 30.0, 30.0, -30.0)
    x, y = 50.5 * 30, 101 * 30 - 50.5 * 30
    means = buffer_means(values, transform, x, y, radii=[10, 1000])
    assert means[10] == 90.0
    assert 0 < means[1000] < 1


def test_geotiff_roundtrip_and_land_cover_table(tmp_path: Path) -> None:
    x, y = albers_conus(40.0, -80.0)
    values = np.full((11, 11), 50)
    content = _geotiff(values, x - 165.0, y + 165.0)
    read, transform = read_geotiff(content)
    assert read.shape == (11, 11) and transform[2] == 30.0
    for layer in LAYERS:
        path = tile_path(tmp_path, layer, "A")
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
    cities = pd.DataFrame({"ID": ["A"], "Lat": [40.0], "Lon": [-80.0]})
    table = load_city_land_cover(cities, tmp_path)
    assert table.loc[0, "imperv_2001_1km"] == 50.0
    assert set(table.columns) >= {"canopy_2011_10km", "imperv_2016_5km"}
    with pytest.raises(FileNotFoundError):
        load_city_land_cover(cities.assign(ID="B"), tmp_path)


def test_geotiff_without_georeference_is_rejected() -> None:
    buffer = io.BytesIO()
    Image.fromarray(np.zeros((2, 2), dtype=np.uint8)).save(buffer, format="TIFF")
    with pytest.raises(ClimateDataError):
        read_geotiff(buffer.getvalue())
