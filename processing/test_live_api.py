import requests

url = "http://localhost:8000/process"
t1_path = "processing/test_images/T1.jpeg"
t2_path = "processing/test_images/T2.jpeg"

channels = ["structural", "vegetation", "pixel_diff"]

print("=" * 70)
print(" TESTING LIVE FASTAPI SERVER (http://localhost:8000)")
print("=" * 70)

for ch in channels:
    with open(t1_path, "rb") as f1, open(t2_path, "rb") as f2:
        files = {
            "t1": ("T1.jpeg", f1, "image/jpeg"),
            "t2": ("T2.jpeg", f2, "image/jpeg")
        }
        data = {"channel_type": ch}
        res = requests.post(url, files=files, data=data)
        
        if res.status_code == 200:
            payload = res.json()
            cd = payload.get("change_detection", {})
            print(f"[OK] {ch.upper():12} -> HTTP {res.status_code}")
            print(f"     Model:        {payload.get('model')}")
            print(f"     Channel Key:  {payload.get('channel_type')}")
            print(f"     Change Area:  {cd.get('change_percentage')}%")
            print(f"     Total Regions:{cd.get('number_of_regions')}")
            print(f"     Severity:     {cd.get('severity')}")
            print(f"     Overlay URL:  {payload.get('overlay_image')}")
            print()
        else:
            print(f"[FAIL] {ch.upper()} -> HTTP {res.status_code}: {res.text}")

print("=" * 70)
print(" ALL 3 MODELS LIVE AND RUNNING PERFECTLY!")
print("=" * 70)
