"""
============================================
Train YOLOv8 on Real Water Pollution Data
============================================
Downloads real water pollution images from open sources,
creates proper annotations, and trains YOLOv8.

Usage:
  python models/yolo/train_real_yolo.py
  python models/yolo/train_real_yolo.py --epochs 50
"""

import sys
import os
import json
import random
import shutil
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Classes for water contamination detection
CLASSES = [
    "contaminated_water",   # 0 - general polluted/dirty water
    "clean_water",          # 1 - clear/clean water
    "foam_scum",            # 2 - white foam/scum on water
    "floating_debris",      # 3 - trash/garbage floating on water
    "oil_spill",            # 4 - oil/chemical on water surface
    "sewage",               # 5 - sewage discharge
    "algae_bloom",          # 6 - green algae growth
    "industrial_waste",     # 7 - industrial discharge/effluent
    "turbid_water",         # 8 - muddy/murky water
]

# Open-license image URLs for each class (Pexels, Unsplash, Pixabay — all free)
IMAGE_SOURCES = {
    "contaminated_water": [
        "https://images.pexels.com/photos/2480807/pexels-photo-2480807.jpeg?w=640",
        "https://images.pexels.com/photos/3186574/pexels-photo-3186574.jpeg?w=640",
        "https://images.pexels.com/photos/4239547/pexels-photo-4239547.jpeg?w=640",
        "https://images.pexels.com/photos/2547565/pexels-photo-2547565.jpeg?w=640",
        "https://images.pexels.com/photos/3059606/pexels-photo-3059606.jpeg?w=640",
        "https://images.pexels.com/photos/4388167/pexels-photo-4388167.jpeg?w=640",
        "https://images.pexels.com/photos/2827735/pexels-photo-2827735.jpeg?w=640",
        "https://images.pexels.com/photos/3186574/pexels-photo-3186574.jpeg?w=640",
    ],
    "clean_water": [
        "https://images.pexels.com/photos/355321/pexels-photo-355321.jpeg?w=640",
        "https://images.pexels.com/photos/1535162/pexels-photo-1535162.jpeg?w=640",
        "https://images.pexels.com/photos/1497586/pexels-photo-1497586.jpeg?w=640",
        "https://images.pexels.com/photos/346529/pexels-photo-346529.jpeg?w=640",
        "https://images.pexels.com/photos/462162/pexels-photo-462162.jpeg?w=640",
        "https://images.pexels.com/photos/1023953/pexels-photo-1023953.jpeg?w=640",
        "https://images.pexels.com/photos/2382325/pexels-photo-2382325.jpeg?w=640",
        "https://images.pexels.com/photos/1533720/pexels-photo-1533720.jpeg?w=640",
    ],
    "foam_scum": [
        "https://images.pexels.com/photos/6475062/pexels-photo-6475062.jpeg?w=640",
        "https://images.pexels.com/photos/4916255/pexels-photo-4916255.jpeg?w=640",
        "https://images.pexels.com/photos/6024784/pexels-photo-6024784.jpeg?w=640",
        "https://images.pexels.com/photos/4792510/pexels-photo-4792510.jpeg?w=640",
    ],
    "floating_debris": [
        "https://images.pexels.com/photos/2547565/pexels-photo-2547565.jpeg?w=640",
        "https://images.pexels.com/photos/4000093/pexels-photo-4000093.jpeg?w=640",
        "https://images.pexels.com/photos/2827735/pexels-photo-2827735.jpeg?w=640",
        "https://images.pexels.com/photos/3059606/pexels-photo-3059606.jpeg?w=640",
    ],
    "turbid_water": [
        "https://images.pexels.com/photos/4388167/pexels-photo-4388167.jpeg?w=640",
        "https://images.pexels.com/photos/5824863/pexels-photo-5824863.jpeg?w=640",
        "https://images.pexels.com/photos/3280130/pexels-photo-3280130.jpeg?w=640",
        "https://images.pexels.com/photos/4239547/pexels-photo-4239547.jpeg?w=640",
    ],
}


def download_images(output_dir: Path):
    """Download real images from open sources."""
    import cv2
    import numpy as np

    img_dir = output_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for class_name, urls in IMAGE_SOURCES.items():
        for i, url in enumerate(urls):
            filename = f"{class_name}_{i:03d}.jpg"
            filepath = img_dir / filename

            if filepath.exists():
                print(f"  [skip] {filename} exists")
                downloaded.append((filepath, class_name))
                continue

            try:
                print(f"  [download] {filename}...", end=" ")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    img_data = resp.read()

                # Verify it's a valid image
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None and img.shape[0] > 100 and img.shape[1] > 100:
                    # Resize to 640x640 for consistency
                    img = cv2.resize(img, (640, 640))
                    cv2.imwrite(str(filepath), img)
                    downloaded.append((filepath, class_name))
                    print("OK")
                else:
                    print("invalid image")
            except Exception as e:
                print(f"failed: {e}")

    return downloaded


def create_augmented_images(base_images: list, output_dir: Path, augment_count: int = 3):
    """
    Create augmented versions of downloaded images for more training data.
    Applies: flip, rotate, brightness, blur, crop variations.
    """
    import cv2
    import numpy as np

    img_dir = output_dir / "images"
    augmented = []

    for filepath, class_name in base_images:
        img = cv2.imread(str(filepath))
        if img is None:
            continue

        for aug_i in range(augment_count):
            aug_img = img.copy()
            aug_name = f"{class_name}_aug{aug_i:02d}_{filepath.stem}.jpg"
            aug_path = img_dir / aug_name

            if aug_path.exists():
                augmented.append((aug_path, class_name))
                continue

            # Random augmentations
            # 1. Horizontal flip
            if random.random() > 0.5:
                aug_img = cv2.flip(aug_img, 1)

            # 2. Brightness/contrast
            alpha = 0.7 + random.random() * 0.6  # 0.7-1.3
            beta = random.randint(-30, 30)
            aug_img = cv2.convertScaleAbs(aug_img, alpha=alpha, beta=beta)

            # 3. Slight rotation
            if random.random() > 0.5:
                angle = random.uniform(-15, 15)
                M = cv2.getRotationMatrix2D((320, 320), angle, 1.0)
                aug_img = cv2.warpAffine(aug_img, M, (640, 640))

            # 4. Gaussian blur
            if random.random() > 0.7:
                ksize = random.choice([3, 5])
                aug_img = cv2.GaussianBlur(aug_img, (ksize, ksize), 0)

            # 5. Color shift
            if random.random() > 0.5:
                hsv = cv2.cvtColor(aug_img, cv2.COLOR_BGR2HSV).astype(float)
                hsv[:, :, 0] += random.randint(-10, 10)
                hsv[:, :, 1] *= (0.8 + random.random() * 0.4)
                hsv = np.clip(hsv, 0, 255).astype(np.uint8)
                aug_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            cv2.imwrite(str(aug_path), aug_img)
            augmented.append((aug_path, class_name))

    return augmented


def create_auto_labels(images: list, output_dir: Path):
    """
    Create YOLO labels using OpenCV analysis.
    Analyzes each image and creates bounding box labels based on
    what's actually visible in the image.
    """
    import cv2
    import numpy as np

    lbl_dir = output_dir / "labels"
    lbl_dir.mkdir(parents=True, exist_ok=True)

    class_to_id = {c: i for i, c in enumerate(CLASSES)}

    for filepath, primary_class in images:
        lbl_path = lbl_dir / (filepath.stem + ".txt")

        img = cv2.imread(str(filepath))
        if img is None:
            continue

        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h_ch, s_ch, v_ch = cv2.split(hsv)
        b, g, r = cv2.split(img)

        labels = []

        # Primary label: full image classification
        cls_id = class_to_id.get(primary_class, 0)
        # Full image bounding box (with small margin)
        labels.append(f"{cls_id} 0.5 0.5 0.96 0.96")

        # Also detect specific sub-regions
        # Foam/white patches
        foam_mask = ((v_ch > 180) & (s_ch < 50)).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        foam_mask = cv2.morphologyEx(foam_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        foam_mask = cv2.morphologyEx(foam_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(foam_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        foam_cls = class_to_id["foam_scum"]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (w * h * 0.01):  # > 1% of image
                x, y, bw, bh = cv2.boundingRect(cnt)
                cx = (x + bw / 2) / w
                cy = (y + bh / 2) / h
                nw = bw / w
                nh = bh / h
                if nw > 0.03 and nh > 0.03:  # Minimum size
                    labels.append(f"{foam_cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        # Brown/turbid regions
        brown_mask = (
            (r.astype(float) > g.astype(float) * 0.85) &
            (g.astype(float) > b.astype(float) * 1.05) &
            (r > 60) & (v_ch > 40) & (v_ch < 200)
        ).astype(np.uint8) * 255
        brown_mask = cv2.morphologyEx(brown_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        contours, _ = cv2.findContours(brown_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        turbid_cls = class_to_id["turbid_water"]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (w * h * 0.05):  # > 5%
                x, y, bw, bh = cv2.boundingRect(cnt)
                cx = (x + bw / 2) / w
                cy = (y + bh / 2) / h
                nw = bw / w
                nh = bh / h
                if nw > 0.1 and nh > 0.1:
                    labels.append(f"{turbid_cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        # Dark oily patches
        dark_mask = ((v_ch < 50) & (s_ch < 30)).astype(np.uint8) * 255
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        oil_cls = class_to_id["oil_spill"]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (w * h * 0.02):
                x, y, bw, bh = cv2.boundingRect(cnt)
                cx = (x + bw / 2) / w
                cy = (y + bh / 2) / h
                nw = bw / w
                nh = bh / h
                if nw > 0.05 and nh > 0.05:
                    labels.append(f"{oil_cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        # Green algae regions
        green_mask = (
            (g.astype(float) > r.astype(float) * 1.15) &
            (g.astype(float) > b.astype(float) * 1.15) &
            (s_ch > 50) & (v_ch > 50)
        ).astype(np.uint8) * 255
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        algae_cls = class_to_id["algae_bloom"]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (w * h * 0.03):
                x, y, bw, bh = cv2.boundingRect(cnt)
                cx = (x + bw / 2) / w
                cy = (y + bh / 2) / h
                nw = bw / w
                nh = bh / h
                if nw > 0.08:
                    labels.append(f"{algae_cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        # Write labels (limit to 20 per image)
        lbl_path.write_text("\n".join(labels[:20]))

    print(f"  Created labels for {len(images)} images")


def create_data_yaml(dataset_dir: Path):
    """Create YOLO data.yaml config."""
    yaml_content = f"""# AquaGuard AI - Water Pollution Detection Dataset
path: {dataset_dir.resolve()}
train: train/images
val: valid/images

nc: {len(CLASSES)}
names: {CLASSES}
"""
    yaml_path = dataset_dir / "data.yaml"
    yaml_path.write_text(yaml_content)
    print(f"  Created: {yaml_path}")
    return yaml_path


def split_dataset(all_images: list, dataset_dir: Path, val_ratio: float = 0.2):
    """Split images into train/val sets."""
    import shutil

    random.shuffle(all_images)
    val_count = max(2, int(len(all_images) * val_ratio))
    val_images = all_images[:val_count]
    train_images = all_images[val_count:]

    train_img_dir = dataset_dir / "train" / "images"
    train_lbl_dir = dataset_dir / "train" / "labels"
    val_img_dir = dataset_dir / "valid" / "images"
    val_lbl_dir = dataset_dir / "valid" / "labels"

    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)

    src_img_dir = dataset_dir / "raw" / "images"
    src_lbl_dir = dataset_dir / "raw" / "labels"

    for filepath, cls in train_images:
        dst = train_img_dir / filepath.name
        if not dst.exists():
            shutil.copy(filepath, dst)
        lbl = src_lbl_dir / (filepath.stem + ".txt")
        if lbl.exists():
            shutil.copy(lbl, train_lbl_dir / lbl.name)

    for filepath, cls in val_images:
        dst = val_img_dir / filepath.name
        if not dst.exists():
            shutil.copy(filepath, dst)
        lbl = src_lbl_dir / (filepath.stem + ".txt")
        if lbl.exists():
            shutil.copy(lbl, val_lbl_dir / lbl.name)

    print(f"  Train: {len(train_images)} images | Val: {len(val_images)} images")


def train_yolo(data_yaml: Path, epochs: int = 30):
    """Train YOLOv8 on the dataset."""
    from ultralytics import YOLO

    print("\n" + "=" * 60)
    print("  TRAINING YOLOv8n on Water Pollution Data")
    print(f"  Epochs: {epochs}")
    print("=" * 60)

    model = YOLO("yolov8n.pt")

    weights_dir = Path("weights")
    weights_dir.mkdir(exist_ok=True)

    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=640,
        batch=4,
        name="water_contamination_real",
        project=str(weights_dir),
        exist_ok=True,
        patience=15,
        save=True,
        plots=True,
        verbose=True,
        workers=0,
        device="cpu",
        mosaic=1.0,
        flipud=0.5,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
    )

    # Copy best weights
    best_pt = Path(results.save_dir) / "weights" / "best.pt"
    if best_pt.exists():
        dest = weights_dir / "water_contamination_best.pt"
        shutil.copy(best_pt, dest)
        print(f"\n  *** Best weights: {dest} ***")
        print("  Model is ready! Restart Flask to use it.")
    else:
        print("\n  WARNING: No best.pt found")

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train YOLOv8 on water pollution data")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs")
    parser.add_argument("--skip-download", action="store_true", help="Skip image download")
    args = parser.parse_args()

    print("=" * 60)
    print("  AquaGuard AI - Real YOLO Training Pipeline")
    print("=" * 60)

    dataset_dir = Path("datasets/water_pollution_real")
    raw_dir = dataset_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_download:
        # Step 1: Download real images
        print("\n[Step 1/5] Downloading real water images...")
        base_images = download_images(raw_dir)
        print(f"  Downloaded: {len(base_images)} base images")

        # Step 2: Augment
        print("\n[Step 2/5] Creating augmented training data...")
        augmented = create_augmented_images(base_images, raw_dir, augment_count=4)
        all_images = base_images + augmented
        print(f"  Total images: {len(all_images)}")

        # Step 3: Auto-label
        print("\n[Step 3/5] Creating YOLO labels...")
        create_auto_labels(all_images, raw_dir)
    else:
        print("\n  Skipping download, using existing data...")
        img_dir = raw_dir / "images"
        all_images = [(p, p.stem.split("_")[0]) for p in img_dir.glob("*.jpg")]

    # Step 4: Split train/val
    print("\n[Step 4/5] Splitting train/val...")
    split_dataset(all_images, dataset_dir)

    # Step 5: Create config + train
    data_yaml = create_data_yaml(dataset_dir)

    print(f"\n[Step 5/5] Training YOLOv8 ({args.epochs} epochs)...")
    train_yolo(data_yaml, epochs=args.epochs)

    print("\n" + "=" * 60)
    print("  DONE! Restart Flask to use the new model.")
    print("=" * 60)


if __name__ == "__main__":
    main()
