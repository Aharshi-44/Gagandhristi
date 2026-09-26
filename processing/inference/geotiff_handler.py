"""
Geospatial GeoTIFF & COG Ingestion Engine for Gagandristhi V2
Implements SIH Problem Statement 26227 Requirement 2.2.6:
- Native GeoTIFF (.tif / .tiff) reading using rasterio
- EPSG / CRS and Affine GeoTransform extraction
- WGS84 (Lat/Lon) Bounding Box calculation
- 16-bit to 8-bit Percentile Contrast Normalization (2% - 98%)
- Multispectral 4-Band (RGB + NIR) extraction for true NDVI
- Pixel (x, y) to Real-World GPS (Lon, Lat) coordinate mapping
"""

import os
import numpy as np
import cv2

try:
    import rasterio
    from rasterio.warp import transform_bounds, transform
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False


def is_geotiff(file_path: str) -> bool:
    """
    Checks if a given file is a valid TIFF/GeoTIFF.
    """
    if not file_path or not os.path.exists(file_path):
        return False

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in {".tif", ".tiff", ".geotiff"}:
        return False

    if not RASTERIO_AVAILABLE:
        return False

    try:
        with rasterio.open(file_path) as src:
            return True
    except Exception:
        return False


def extract_geotiff_metadata(file_path: str) -> dict:
    """
    Extracts geospatial metadata, CRS projections, resolution, and real-world bounds.
    """
    if not is_geotiff(file_path):
        return {"is_geotiff": False}

    try:
        with rasterio.open(file_path) as src:
            width = src.width
            height = src.height
            count = src.count
            dtype_str = str(src.dtypes[0]) if src.dtypes else "unknown"
            crs_obj = src.crs

            crs_str = None
            epsg = None
            if crs_obj:
                crs_str = str(crs_obj)
                try:
                    epsg = crs_obj.to_epsg()
                except Exception:
                    epsg = None

            # Affine GeoTransform coefficients
            transform_matrix = list(src.transform)[:6]
            res_x, res_y = src.res

            # Native bounding box (left, bottom, right, top)
            native_bounds = [
                float(src.bounds.left),
                float(src.bounds.bottom),
                float(src.bounds.right),
                float(src.bounds.top)
            ]

            # Transform bounds to WGS84 (EPSG:4326) for Leaflet map & PostGIS
            wgs84_bounds = None
            geojson_footprint = None
            center_gps = None

            if crs_obj:
                try:
                    min_lon, min_lat, max_lon, max_lat = transform_bounds(
                        crs_obj,
                        "EPSG:4326",
                        src.bounds.left,
                        src.bounds.bottom,
                        src.bounds.right,
                        src.bounds.top
                    )
                    wgs84_bounds = [
                        round(float(min_lon), 6),
                        round(float(min_lat), 6),
                        round(float(max_lon), 6),
                        round(float(max_lat), 6)
                    ]
                    center_gps = [
                        round((wgs84_bounds[1] + wgs84_bounds[3]) / 2.0, 6),
                        round((wgs84_bounds[0] + wgs84_bounds[2]) / 2.0, 6)
                    ]

                    # Standard GeoJSON Polygon [lon, lat]
                    geojson_footprint = {
                        "type": "Polygon",
                        "coordinates": [[
                            [wgs84_bounds[0], wgs84_bounds[1]],
                            [wgs84_bounds[2], wgs84_bounds[1]],
                            [wgs84_bounds[2], wgs84_bounds[3]],
                            [wgs84_bounds[0], wgs84_bounds[3]],
                            [wgs84_bounds[0], wgs84_bounds[1]]
                        ]]
                    }
                except Exception as e:
                    print(f"[GeoTIFF] Warning: Could not transform bounds to WGS84: {e}")

            return {
                "is_geotiff": True,
                "file_name": os.path.basename(file_path),
                "width": width,
                "height": height,
                "band_count": count,
                "dtype": dtype_str,
                "crs": crs_str,
                "epsg": epsg,
                "resolution": [round(float(res_x), 3), round(float(res_y), 3)],
                "native_bounds": native_bounds,
                "wgs84_bounds": wgs84_bounds,
                "center_gps": center_gps,
                "geojson_footprint": geojson_footprint,
                "transform": transform_matrix
            }
    except Exception as e:
        print(f"[GeoTIFF] Error reading metadata from {file_path}: {e}")
        return {"is_geotiff": False, "error": str(e)}


def convert_geotiff_for_inference(
    file_path: str,
    preview_png_path: str = None
) -> tuple:
    """
    Reads a GeoTIFF, performs 2%-98% percentile contrast stretching to 8-bit RGB,
    extracts the 4th Near-Infrared (NIR) band if available, and optionally saves
    a standard RGB PNG preview for the frontend.

    Returns:
        tuple: (rgb_uint8_array, nir_band_array_or_none, metadata_dict)
    """
    if not is_geotiff(file_path):
        raise ValueError(f"File is not a valid GeoTIFF: {file_path}")

    meta = extract_geotiff_metadata(file_path)

    with rasterio.open(file_path) as src:
        raw_data = src.read()  # Shape: (bands, height, width)

    band_count = raw_data.shape[0]

    # 1. Band assignment
    nir_band = None
    if band_count >= 4:
        # Standard satellite 4-band: Red, Green, Blue, NIR
        r_raw = raw_data[0].astype(np.float32)
        g_raw = raw_data[1].astype(np.float32)
        b_raw = raw_data[2].astype(np.float32)
        nir_band = raw_data[3].astype(np.float32)
    elif band_count == 3:
        r_raw = raw_data[0].astype(np.float32)
        g_raw = raw_data[1].astype(np.float32)
        b_raw = raw_data[2].astype(np.float32)
    elif band_count == 2:
        r_raw = raw_data[0].astype(np.float32)
        g_raw = raw_data[1].astype(np.float32)
        b_raw = raw_data[0].astype(np.float32)
    else:  # Single band (Panchromatic / Grayscale)
        r_raw = raw_data[0].astype(np.float32)
        g_raw = raw_data[0].astype(np.float32)
        b_raw = raw_data[0].astype(np.float32)

    # 2. Robust 2% - 98% Percentile Dynamic Range Stretch per channel
    def stretch_channel(channel: np.ndarray) -> np.ndarray:
        valid_mask = np.isfinite(channel)
        if not np.any(valid_mask):
            return np.zeros_like(channel, dtype=np.uint8)

        p2, p98 = np.percentile(channel[valid_mask], (2, 98))
        if p98 > p2:
            stretched = np.clip((channel - p2) / (p98 - p2), 0.0, 1.0) * 255.0
        else:
            stretched = np.clip(channel, 0.0, 255.0)
        return stretched.astype(np.uint8)

    r_uint8 = stretch_channel(r_raw)
    g_uint8 = stretch_channel(g_raw)
    b_uint8 = stretch_channel(b_raw)

    # Stack to (height, width, 3) RGB uint8
    rgb_uint8 = np.stack([r_uint8, g_uint8, b_uint8], axis=-1)

    # 3. Save web preview PNG if requested
    if preview_png_path:
        preview_dir = os.path.dirname(preview_png_path)
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
        bgr = cv2.cvtColor(rgb_uint8, cv2.COLOR_RGB2BGR)
        cv2.imwrite(preview_png_path, bgr)

    return rgb_uint8, nir_band, meta


def convert_regions_to_gps(
    regions: list,
    transform_matrix,
    crs_obj
) -> list:
    """
    Translates pixel bounding boxes and centroids into real-world geographic coordinates (WGS84 Lon/Lat).
    Supports bounding_box as dict {'x', 'y', 'width', 'height'} or list [x_min, y_min, x_max, y_max].
    Supports centroid as dict {'x', 'y'} or list [cx, cy].
    """
    if not regions or transform_matrix is None or crs_obj is None:
        return regions

    try:
        from rasterio.transform import Affine
        if isinstance(transform_matrix, (list, tuple)):
            aff = Affine(*transform_matrix[:6])
        else:
            aff = transform_matrix
    except Exception as e:
        print(f"[GeoTIFF] Could not construct Affine transform: {e}")
        return regions

    crs_str = str(crs_obj).upper()
    is_wgs84 = ("4326" in crs_str) or ("WGS 84" in crs_str) or ("WGS84" in crs_str)

    enriched_regions = []
    for reg in regions:
        reg_copy = dict(reg)

        # 1. Extract pixel bounds
        bbox = reg.get("bounding_box") or reg.get("bbox")
        x_min, y_min, x_max, y_max = None, None, None, None

        if isinstance(bbox, dict):
            bx = float(bbox.get("x", 0))
            by = float(bbox.get("y", 0))
            bw = float(bbox.get("width", 0))
            bh = float(bbox.get("height", 0))
            x_min, y_min, x_max, y_max = bx, by, bx + bw, by + bh
        elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            x_min, y_min, x_max, y_max = [float(v) for v in bbox]

        if x_min is not None:
            # Native map coordinates: aff * (col, row)
            x1, y1 = aff * (x_min, y_min)
            x2, y2 = aff * (x_max, y_max)

            try:
                if not is_wgs84:
                    lons, lats = transform(crs_obj, "EPSG:4326", [x1, x2], [y1, y2])
                else:
                    lons, lats = [x1, x2], [y1, y2]

                min_lon, max_lon = min(lons), max(lons)
                min_lat, max_lat = min(lats), max(lats)

                reg_copy["gps_bounds"] = [
                    round(float(min_lon), 6),
                    round(float(min_lat), 6),
                    round(float(max_lon), 6),
                    round(float(max_lat), 6)
                ]
            except Exception as e:
                print(f"[GeoTIFF] Region bbox coordinate conversion error: {e}")

        # 2. Extract centroid
        centroid = reg.get("centroid")
        cx, cy = None, None

        if isinstance(centroid, dict):
            cx = float(centroid.get("x", 0))
            cy = float(centroid.get("y", 0))
        elif isinstance(centroid, (list, tuple)) and len(centroid) == 2:
            cx, cy = float(centroid[0]), float(centroid[1])

        if cx is not None and cy is not None:
            cx_nat, cy_nat = aff * (cx, cy)
            try:
                if not is_wgs84:
                    c_lons, c_lats = transform(crs_obj, "EPSG:4326", [cx_nat], [cy_nat])
                else:
                    c_lons, c_lats = [cx_nat], [cy_nat]

                reg_copy["gps_centroid"] = [
                    round(float(c_lons[0]), 6),
                    round(float(c_lats[0]), 6)
                ]
            except Exception as e:
                print(f"[GeoTIFF] Centroid coordinate conversion error: {e}")

        enriched_regions.append(reg_copy)

    return enriched_regions
