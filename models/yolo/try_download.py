"""
Download and train YOLOv8 on a real water pollution dataset from Roboflow.
"""
import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def try_download():
    """Try multiple known public water pollution datasets on Roboflow."""
    from roboflow import Roboflow
    
    dest = Path("datasets/water_pollution_real")
    dest.mkdir(parents=True, exist_ok=True)
    
    # Known public water pollution datasets on Roboflow Universe
    # Format: (api_key, workspace, project, version)
    attempts = [
        # Public datasets don't need real API keys on Universe
        ("", "aquatic-hbptl", "aquatic-weeds-and-garbage", 2),
        ("", "garbage-detection-yjebp", "garbage-classification-3", 2),
        ("", "school-d9sxo", "water-pollution-bmphg", 1),
        ("", "my-datasets-lbkri", "water-pollution-detector", 1),
    ]
    
    for api_key, ws, proj, ver in attempts:
        try:
            print(f"  Trying: {ws}/{proj}/v{ver}...")
            rf = Roboflow(api_key=api_key) if api_key else Roboflow()
            project = rf.workspace(ws).project(proj)
            dataset = project.version(ver).download("yolov8", location=str(dest))
            print(f"  ✅ Success! Downloaded to {dest}")
            return str(dest)
        except Exception as e:
            print(f"  ❌ {e}")
            continue
    
    return None

if __name__ == "__main__":
    print("="*60)
    print("  Searching for public water pollution datasets...")
    print("="*60)
    result = try_download()
    if result:
        print(f"\n  Dataset ready at: {result}")
    else:
        print("\n  Could not auto-download. Will try direct URL approach.")
