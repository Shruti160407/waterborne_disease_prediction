"""
============================================
YOLO Water Contamination Dataset Generator
============================================
Creates a small but effective training dataset for water contamination
detection by downloading real images and generating synthetic labeled data.

Usage: python models/yolo/create_training_data.py
"""

import sys
import os
import random
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

try:
    import cv2
except ImportError:
    print("ERROR: pip install opencv-python")
    sys.exit(1)


# Dataset paths
DATASET_DIR = PROJECT_ROOT / "datasets" / "yolo_data" / "water_contamination"
IMAGES_TRAIN = DATASET_DIR / "images" / "train"
IMAGES_VAL = DATASET_DIR / "images" / "val"
LABELS_TRAIN = DATASET_DIR / "labels" / "train"
LABELS_VAL = DATASET_DIR / "labels" / "val"
YAML_PATH = PROJECT_ROOT / "datasets" / "yolo_configs" / "water_contamination.yaml"

# Classes: 0=contaminated, 1=clean, 2=industrial_waste, 3=sewage, 4=chemical_spill
CLASSES = ["contaminated", "clean", "industrial_waste", "sewage", "chemical_spill"]


def create_dirs():
    """Create directory structure."""
    for d in [IMAGES_TRAIN, IMAGES_VAL, LABELS_TRAIN, LABELS_VAL]:
        d.mkdir(parents=True, exist_ok=True)
    print("Directories created.")


def generate_water_image(width=640, height=640, style="clean"):
    """
    Generate a synthetic water image with various contamination styles.
    
    Args:
        width: Image width
        height: Image height
        style: One of 'clean', 'contaminated', 'industrial', 'sewage', 'chemical'
    
    Returns:
        image (numpy array), list of bounding boxes [(class_id, cx, cy, w, h), ...]
    """
    img = np.zeros((height, width, 3), dtype=np.uint8)
    bboxes = []
    
    if style == "clean":
        # Clean blue water
        base_color = [random.randint(140, 180), random.randint(100, 140), random.randint(30, 60)]
        img[:] = base_color
        
        # Add water ripple texture
        for _ in range(random.randint(5, 15)):
            y = random.randint(0, height - 1)
            color_var = [c + random.randint(-20, 20) for c in base_color]
            color_var = [max(0, min(255, c)) for c in color_var]
            thickness = random.randint(1, 3)
            cv2.line(img, (0, y), (width, y + random.randint(-10, 10)), color_var, thickness)
        
        # Add slight noise
        noise = np.random.randint(-10, 10, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Full-image class label for clean water
        bboxes.append((1, 0.5, 0.5, 0.95, 0.95))
    
    elif style == "contaminated":
        # Murky brownish-green water
        base_color = [random.randint(60, 90), random.randint(80, 120), random.randint(70, 110)]
        img[:] = base_color
        
        # Add murky patches
        for _ in range(random.randint(8, 20)):
            cx = random.randint(50, width - 50)
            cy = random.randint(50, height - 50)
            rx = random.randint(30, 120)
            ry = random.randint(20, 80)
            color = [random.randint(40, 80), random.randint(60, 100), random.randint(50, 90)]
            cv2.ellipse(img, (cx, cy), (rx, ry), random.randint(0, 360), 0, 360, color, -1)
        
        # Add floating debris
        for _ in range(random.randint(5, 15)):
            x = random.randint(20, width - 20)
            y = random.randint(20, height - 20)
            w = random.randint(10, 40)
            h = random.randint(5, 20)
            debris_color = [random.randint(100, 160), random.randint(100, 140), random.randint(80, 130)]
            cv2.rectangle(img, (x, y), (x + w, y + h), debris_color, -1)
        
        # Add noise
        noise = np.random.randint(-15, 15, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Contamination regions
        num_regions = random.randint(2, 5)
        for _ in range(num_regions):
            cx = random.uniform(0.15, 0.85)
            cy = random.uniform(0.15, 0.85)
            w = random.uniform(0.15, 0.4)
            h = random.uniform(0.1, 0.35)
            bboxes.append((0, cx, cy, w, h))
    
    elif style == "industrial":
        # Dark polluted water with chemical streaks
        base_color = [random.randint(30, 60), random.randint(40, 70), random.randint(30, 60)]
        img[:] = base_color
        
        # Add chemical streaks (colorful pollution)
        for _ in range(random.randint(3, 8)):
            y_start = random.randint(0, height)
            color = [random.randint(0, 100), random.randint(0, 50), random.randint(100, 255)]
            pts = []
            x = 0
            y = y_start
            while x < width:
                pts.append([x, y])
                x += random.randint(10, 30)
                y += random.randint(-20, 20)
                y = max(0, min(height - 1, y))
            if len(pts) > 1:
                pts = np.array(pts, dtype=np.int32)
                cv2.polylines(img, [pts], False, color, random.randint(3, 12))
        
        # Oil slick effect
        for _ in range(random.randint(2, 6)):
            cx = random.randint(50, width - 50)
            cy = random.randint(50, height - 50)
            rx = random.randint(40, 150)
            ry = random.randint(30, 80)
            overlay = img.copy()
            cv2.ellipse(overlay, (cx, cy), (rx, ry), random.randint(0, 180), 0, 360,
                       [random.randint(20, 80), random.randint(0, 40), random.randint(80, 180)], -1)
            cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)
        
        noise = np.random.randint(-10, 10, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        num_regions = random.randint(1, 4)
        for _ in range(num_regions):
            cx = random.uniform(0.1, 0.9)
            cy = random.uniform(0.1, 0.9)
            w = random.uniform(0.2, 0.5)
            h = random.uniform(0.15, 0.4)
            bboxes.append((2, cx, cy, w, h))
    
    elif style == "sewage":
        # Brown/gray murky water
        base_color = [random.randint(60, 90), random.randint(80, 110), random.randint(90, 130)]
        img[:] = base_color
        
        # Sewage foam/scum
        for _ in range(random.randint(10, 25)):
            cx = random.randint(20, width - 20)
            cy = random.randint(20, height - 20)
            r = random.randint(10, 50)
            foam_color = [random.randint(160, 220), random.randint(170, 210), random.randint(150, 190)]
            cv2.circle(img, (cx, cy), r, foam_color, -1)
            # Bubble highlight
            cv2.circle(img, (cx - r // 3, cy - r // 3), r // 4, 
                      [min(255, c + 40) for c in foam_color], -1)
        
        # Solid waste particles
        for _ in range(random.randint(5, 12)):
            x = random.randint(10, width - 10)
            y = random.randint(10, height - 10)
            size = random.randint(5, 25)
            color = [random.randint(40, 80), random.randint(50, 90), random.randint(60, 100)]
            if random.random() > 0.5:
                cv2.rectangle(img, (x, y), (x + size, y + size // 2), color, -1)
            else:
                cv2.circle(img, (x, y), size // 2, color, -1)
        
        noise = np.random.randint(-8, 8, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        num_regions = random.randint(2, 5)
        for _ in range(num_regions):
            cx = random.uniform(0.1, 0.9)
            cy = random.uniform(0.1, 0.9)
            w = random.uniform(0.1, 0.35)
            h = random.uniform(0.1, 0.3)
            bboxes.append((3, cx, cy, w, h))
    
    elif style == "chemical":
        # Bright unnatural colored water
        hue = random.choice(["green", "yellow", "purple", "red"])
        if hue == "green":
            base_color = [random.randint(30, 60), random.randint(150, 220), random.randint(30, 80)]
        elif hue == "yellow":
            base_color = [random.randint(20, 50), random.randint(170, 230), random.randint(180, 240)]
        elif hue == "purple":
            base_color = [random.randint(120, 180), random.randint(30, 70), random.randint(100, 160)]
        else:
            base_color = [random.randint(20, 50), random.randint(30, 70), random.randint(170, 230)]
        
        img[:] = base_color
        
        # Chemical swirls
        for _ in range(random.randint(5, 12)):
            cx = random.randint(50, width - 50)
            cy = random.randint(50, height - 50)
            rx = random.randint(30, 100)
            ry = random.randint(20, 60)
            angle = random.randint(0, 360)
            swirl_color = [max(0, min(255, c + random.randint(-50, 50))) for c in base_color]
            cv2.ellipse(img, (cx, cy), (rx, ry), angle, 0, 360, swirl_color, random.randint(2, 6))
        
        # Chemical foam
        for _ in range(random.randint(3, 8)):
            cx = random.randint(30, width - 30)
            cy = random.randint(30, height - 30)
            r = random.randint(15, 40)
            cv2.circle(img, (cx, cy), r, [200, 200, 200], -1)
        
        noise = np.random.randint(-12, 12, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        num_regions = random.randint(1, 3)
        for _ in range(num_regions):
            cx = random.uniform(0.15, 0.85)
            cy = random.uniform(0.15, 0.85)
            w = random.uniform(0.2, 0.5)
            h = random.uniform(0.15, 0.45)
            bboxes.append((4, cx, cy, w, h))
    
    # Apply slight blur for realism
    if random.random() > 0.3:
        ksize = random.choice([3, 5])
        img = cv2.GaussianBlur(img, (ksize, ksize), 0)
    
    return img, bboxes


def save_yolo_label(filepath, bboxes):
    """Save bounding boxes in YOLO format."""
    with open(str(filepath), "w") as f:
        for cls_id, cx, cy, w, h in bboxes:
            # Clip values to [0, 1]
            cx = max(0, min(1, cx))
            cy = max(0, min(1, cy))
            w = max(0.01, min(1, w))
            h = max(0.01, min(1, h))
            f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")


def generate_dataset(n_train=200, n_val=50):
    """Generate full training and validation datasets."""
    styles = ["clean", "contaminated", "industrial", "sewage", "chemical"]
    
    for split, n, img_dir, lbl_dir in [
        ("train", n_train, IMAGES_TRAIN, LABELS_TRAIN),
        ("val", n_val, IMAGES_VAL, LABELS_VAL)
    ]:
        print(f"\nGenerating {split} set ({n} images)...")
        per_class = n // len(styles)
        
        idx = 0
        for style in styles:
            count = per_class if style != styles[-1] else (n - idx)
            for i in range(count):
                # Vary image size slightly
                w = random.choice([480, 512, 640])
                h = random.choice([480, 512, 640])
                
                img, bboxes = generate_water_image(w, h, style)
                
                # Random augmentations
                if random.random() > 0.5:
                    img = cv2.flip(img, 1)  # horizontal flip
                if random.random() > 0.7:
                    img = cv2.flip(img, 0)  # vertical flip
                if random.random() > 0.5:
                    # Brightness variation
                    factor = random.uniform(0.7, 1.3)
                    img = np.clip(img * factor, 0, 255).astype(np.uint8)
                
                # Resize to 640x640
                img = cv2.resize(img, (640, 640))
                
                filename = f"{style}_{idx:04d}"
                cv2.imwrite(str(img_dir / f"{filename}.jpg"), img)
                save_yolo_label(lbl_dir / f"{filename}.txt", bboxes)
                
                idx += 1
        
        print(f"  Generated {idx} images in {img_dir}")


def create_yaml():
    """Create YOLO training YAML config."""
    yaml_content = f"""# Water Contamination Detection Dataset
# Auto-generated for YOLOv8 training

path: {str(DATASET_DIR).replace(chr(92), '/')}
train: images/train
val: images/val

# Classes
nc: {len(CLASSES)}
names: {CLASSES}
"""
    YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(str(YAML_PATH), "w") as f:
        f.write(yaml_content)
    print(f"\nYAML config saved: {YAML_PATH}")


def main():
    print("=" * 60)
    print("  YOLO WATER CONTAMINATION DATASET GENERATOR")
    print("=" * 60)
    
    create_dirs()
    generate_dataset(n_train=250, n_val=60)
    create_yaml()
    
    # Verify
    train_imgs = len(list(IMAGES_TRAIN.glob("*.jpg")))
    val_imgs = len(list(IMAGES_VAL.glob("*.jpg")))
    print(f"\nDataset Summary:")
    print(f"  Train: {train_imgs} images")
    print(f"  Val:   {val_imgs} images")
    print(f"  Classes: {CLASSES}")
    print(f"\nReady for training!")
    print(f"Run: python models/yolo/train_yolo.py --model water_contamination --epochs 30")


if __name__ == "__main__":
    main()
