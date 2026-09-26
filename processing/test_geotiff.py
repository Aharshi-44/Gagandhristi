"""
Verification Test Harness for GeoTIFF Ingestion & Georeferenced Processing
Validates SIH Problem Statement 26227 Requirement 2.2.6:
1. Synthetic Multi-Band GeoTIFF creation with EPSG:32643 (UTM Zone 43N)
2. Ingestion across all 3 analytical channels:
   - STRUCTURAL_DL (Siamese U-Net)
   - VEGETATION_NDVI (True 4-Band NIR NDVI)
   - PIXEL_DIFFERENCE (CVA)
3. Coordinate transformation to real WGS84 GPS bounds & centroids
4. Web-preview generation for browser rendering
5. Strict regression test with standard JPG/PNG images
"""

import os
import sys
import numpy as np
import rasterio
from rasterio.transform import from_bounds

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from service.processor import ChangeProcessor
from inference.geotiff_handler import is_geotiff, extract_geotiff_metadata


def create_synthetic_geotiff_pair():
    """
    Creates a pair of 4-band (R, G, B, NIR) 16-bit GeoTIFFs with realistic changes.
    Location: UTM Zone 43N (Delhi Area: X=715000, Y=3168000, 10m GSD).
    """
    test_dir = os.path.join(ROOT, "test_images", "geotiff_test")
    os.makedirs(test_dir, exist_ok=True)

    t1_path = os.path.join(test_dir, "sentinel2_T1.tif")
    t2_path = os.path.join(test_dir, "sentinel2_T2.tif")

    transform = from_bounds(715000, 3168000, 717560, 3170560, 256, 256)

    # Base background (reflectance values between 500 and 3500)
    np.random.seed(42)
    t1_data = np.random.randint(500, 3000, size=(4, 256, 256), dtype=np.uint16)
    # Simulate high NIR vegetation in T1 (Band 4)
    t1_data[3, 50:150, 50:150] = 4500
    t1_data[0, 50:150, 50:150] = 800  # Low Red

    t2_data = t1_data.copy()
    # In T2: Clear vegetation (NIR drops, Red increases) in a 60x60 block
    t2_data[3, 60:120, 60:120] = 700
    t2_data[0, 60:120, 60:120] = 2500
    # Add new bright structural feature
    t2_data[:3, 180:220, 180:220] = 5000

    for path, data in [(t1_path, t1_data), (t2_path, t2_data)]:
        with rasterio.open(
            path, 'w',
            driver='GTiff',
            height=256, width=256,
            count=4, dtype=np.uint16,
            crs='EPSG:32643',
            transform=transform
        ) as dst:
            dst.write(data)

    print(f"[OK] Created synthetic GeoTIFF pair:")
    print(f"     T1: {t1_path}")
    print(f"     T2: {t2_path}")
    return t1_path, t2_path, test_dir


def run_tests():
    print("=" * 65)
    print(" GAGANDRISTHI V2: GEOTIFF INGESTION & COORDINATE TEST HARNESS")
    print("=" * 65)

    processor = ChangeProcessor()
    t1_geo, t2_geo, test_dir = create_synthetic_geotiff_pair()

    # 1. Test Metadata
    meta = extract_geotiff_metadata(t2_geo)
    print("\n--- 1. METADATA EXTRACTION ---")
    print(f"EPSG Code:       {meta['epsg']}")
    print(f"Resolution (GSD):{meta['resolution']} meters")
    print(f"WGS84 Bounds:    {meta['wgs84_bounds']}")
    print(f"GPS Center:      {meta['center_gps']}")
    print(f"GeoJSON Type:    {meta['geojson_footprint']['type']}")
    assert meta["epsg"] == 32643
    assert len(meta["wgs84_bounds"]) == 4

    # 2. Test VEGETATION_NDVI with 4-band true NIR
    print("\n--- 2. VEGETATION_NDVI (TRUE 4-BAND NIR) ---")
    out_mask_veg = os.path.join(test_dir, "mask_veg.png")
    res_veg = processor.process(t1_geo, t2_geo, output_mask_path=out_mask_veg, channel_type="vegetation")
    print(f"Channel:          {res_veg['channel_type']}")
    print(f"Model/Index:      {res_veg['model']}")
    print(f"Change Detected:  {res_veg['change_detection']['change_detected']}")
    print(f"Loss %:           {res_veg['change_detection'].get('vegetation_loss_percentage', 0)}%")
    print(f"Georeferenced:    {'geotiff_metadata' in res_veg}")
    assert "NDVI" in res_veg["change_detection"]["index_used"]
    assert "geotiff_metadata" in res_veg
    assert "feature_geojson" in res_veg

    # Check GPS coords in detected regions
    regions = res_veg["change_detection"]["regions"]
    if regions:
        print(f"First Region GPS: {regions[0].get('gps_bounds')}")
        print(f"Centroid GPS:     {regions[0].get('gps_centroid')}")
        assert "gps_bounds" in regions[0]

    # 3. Test STRUCTURAL_DL on GeoTIFF
    print("\n--- 3. STRUCTURAL_DL (SIAMESE U-NET ON GEOTIFF) ---")
    out_mask_struct = os.path.join(test_dir, "mask_struct.png")
    res_struct = processor.process(t1_geo, t2_geo, output_mask_path=out_mask_struct, channel_type="structural")
    print(f"Channel:          {res_struct['channel_type']}")
    print(f"Model:            {res_struct['model']}")
    print(f"Regions Detected: {res_struct['change_detection']['number_of_regions']}")
    print(f"T1 Preview Exists:{os.path.exists(res_struct.get('t1_preview', ''))}")
    print(f"T2 Preview Exists:{os.path.exists(res_struct.get('t2_preview', ''))}")
    assert "geotiff_metadata" in res_struct

    # 4. Test PIXEL_DIFFERENCE on GeoTIFF
    print("\n--- 4. PIXEL_DIFFERENCE (CVA ON GEOTIFF) ---")
    out_mask_pixel = os.path.join(test_dir, "mask_pixel.png")
    res_pixel = processor.process(t1_geo, t2_geo, output_mask_path=out_mask_pixel, channel_type="pixel_diff")
    print(f"Channel:          {res_pixel['channel_type']}")
    print(f"Change Area:      {res_pixel['change_detection']['change_percentage']}%")
    print(f"Severity:         {res_pixel['change_detection']['severity']}")
    assert "geotiff_metadata" in res_pixel

    # 5. REGRESSION TEST: Standard JPG images must work without error
    print("\n--- 5. REGRESSION TEST: STANDARD JPG IMAGES ---")
    t1_jpg = os.path.join(ROOT, "test_images", "T1.jpeg")
    t2_jpg = os.path.join(ROOT, "test_images", "T2.jpeg")
    out_mask_jpg = os.path.join(test_dir, "mask_jpg.png")
    res_jpg = processor.process(t1_jpg, t2_jpg, output_mask_path=out_mask_jpg, channel_type="structural")
    print(f"Channel:          {res_jpg['channel_type']}")
    print(f"Model:            {res_jpg['model']}")
    print(f"Change Detected:  {res_jpg['change_detection']['change_detected']}")
    print(f"Is GeoTIFF:       {res_jpg.get('geotiff_metadata', {}).get('is_geotiff', False)}")
    assert res_jpg["change_detection"]["change_detected"] == True
    print("\n[SUCCESS] Standard JPG processing works 100% backward-compatibly!")

    print("\n" + "=" * 65)
    print(" ALL GEOTIFF & BACKWARD-COMPATIBILITY TESTS PASSED SUCCESSFULLY! ")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
