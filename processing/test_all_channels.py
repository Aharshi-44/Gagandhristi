import os
import sys
import json

PROCESSING_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROCESSING_ROOT not in sys.path:
    sys.path.insert(0, PROCESSING_ROOT)

from service.processor import ChangeProcessor

def test_all_channels():
    print("=" * 60)
    print(" GAGANDRISTHI V2: MULTI-CHANNEL MODEL TEST HARNESS")
    print("=" * 60)

    t1_path = os.path.join(PROCESSING_ROOT, "test_images", "T1.jpeg")
    t2_path = os.path.join(PROCESSING_ROOT, "test_images", "T2.jpeg")

    if not os.path.exists(t1_path) or not os.path.exists(t2_path):
        print(f"Error: test images not found at {t1_path}")
        return False

    processor = ChangeProcessor()
    channels = ["structural", "vegetation", "pixel_diff"]
    results = {}

    for ch in channels:
        print(f"\n[TESTING] Channel: {ch.upper()}...")
        out_mask = os.path.join(PROCESSING_ROOT, "test_images", f"mask_{ch}.png")
        res = processor.process(t1_path, t2_path, output_mask_path=out_mask, channel_type=ch)

        cd = res["change_detection"]
        print(f"  [OK] Model: {res['model']}")
        print(f"  [OK] Channel Type: {res['channel_type']}")
        print(f"  [OK] Change Detected: {cd['change_detected']}")
        print(f"  [OK] Change Area: {cd['change_percentage']}%")
        print(f"  [OK] Total Regions: {cd['number_of_regions']}")
        print(f"  [OK] Severity Rating: {cd['severity']}")

        if ch == "vegetation":
            print(f"  [OK] Index Used: {cd['index_used']}")
            print(f"  [OK] Loss (Clearance): {cd['vegetation_loss_percentage']}%")
            print(f"  [OK] Gain (Regrowth): {cd['vegetation_gain_percentage']}%")
        elif ch == "pixel_diff":
            print(f"  [OK] Algorithm: {cd['algorithm']}")

        assert os.path.exists(out_mask), f"Mask file {out_mask} was not created!"
        overlay_path = res.get("overlay_image")
        assert overlay_path and os.path.exists(overlay_path), f"Overlay file was not created!"
        print(f"  [OK] Output Mask: {out_mask} (exists)")
        print(f"  [OK] Output Overlay: {overlay_path} (exists)")

        results[ch] = res

    print("\n" + "=" * 60)
    print(" ALL 3 CHANNELS TESTED SUCCESSFULLY WITH ZERO ERRORS!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_all_channels()
    sys.exit(0 if success else 1)
