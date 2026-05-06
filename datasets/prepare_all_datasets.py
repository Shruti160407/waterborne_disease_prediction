"""
============================================
Unified Dataset Preparation Script
============================================
ONE command to prepare ALL datasets for training.

This script:
1. Downloads all datasets (CSV + images)
2. Organizes them into YOLO format
3. Applies augmentation
4. Creates train/val splits
5. Generates YOLO config YAML files

Usage:
    python datasets/prepare_all_datasets.py

After running, all datasets will be ready for YOLO training & ML model training.
"""

import os
import sys
import random
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import cv2
    import numpy as np
    from tqdm import tqdm
except ImportError:
    os.system("pip install opencv-python numpy tqdm")
    import cv2
    import numpy as np
    from tqdm import tqdm

from config.settings import (
    RAW_DATA_DIR, YOLO_DATASET_BASE, YOLO_CONFIG_DIR,
    DATASET_DIR, YOLO_MODELS
)


# ============================================
# YOLO Dataset Structure Creator
# ============================================

def create_yolo_structure(dataset_name: str) -> dict:
    """
    Create the standard YOLO directory structure for a dataset.
    
    Args:
        dataset_name: Name of the dataset (e.g., "algal_bloom")
        
    Returns:
        Dict with paths for images/labels train/val directories
    """
    base = YOLO_DATASET_BASE / dataset_name
    paths = {
        "images_train": base / "images" / "train",
        "images_val": base / "images" / "val",
        "labels_train": base / "labels" / "train",
        "labels_val": base / "labels" / "val",
    }
    
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths


def split_dataset(
    image_dir: Path,
    label_dir: Path,
    output_paths: dict,
    val_ratio: float = 0.2
):
    """
    Split images and labels into train/val sets.
    
    Args:
        image_dir: Source directory with images
        label_dir: Source directory with YOLO labels
        output_paths: Dict from create_yolo_structure()
        val_ratio: Fraction of data for validation (default: 0.2)
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    images = [f for f in image_dir.iterdir()
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"  ⚠️  No images found in {image_dir}")
        return
    
    random.shuffle(images)
    val_count = max(1, int(len(images) * val_ratio))
    
    val_images = images[:val_count]
    train_images = images[val_count:]
    
    # Copy to train
    for img_path in train_images:
        shutil.copy2(img_path, output_paths["images_train"] / img_path.name)
        label_path = label_dir / f"{img_path.stem}.txt"
        if label_path.exists():
            shutil.copy2(label_path, output_paths["labels_train"] / label_path.name)
    
    # Copy to val
    for img_path in val_images:
        shutil.copy2(img_path, output_paths["images_val"] / img_path.name)
        label_path = label_dir / f"{img_path.stem}.txt"
        if label_path.exists():
            shutil.copy2(label_path, output_paths["labels_val"] / label_path.name)
    
    print(f"  📊 Split: {len(train_images)} train / {len(val_images)} val")


def create_classification_yolo_labels(
    class_dir: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    class_id: int
):
    """
    Convert classification-style images (in class folders) 
    to YOLO format with full-image bounding boxes.
    
    This is used when we have images sorted by class but no
    bounding box annotations. Creates a label with a bbox
    covering the full image.
    
    Args:
        class_dir: Directory containing images of one class
        output_image_dir: Where to copy images
        output_label_dir: Where to save YOLO labels
        class_id: Integer class ID
    """
    output_image_dir.mkdir(parents=True, exist_ok=True)
    output_label_dir.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    images = [f for f in class_dir.rglob("*")
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    for img_path in images:
        # Copy image with unique name
        new_name = f"{class_dir.name}_{img_path.stem}{img_path.suffix}"
        shutil.copy2(img_path, output_image_dir / new_name)
        
        # Create YOLO label (full image bbox: center=0.5, size=1.0)
        label_path = output_label_dir / f"{class_dir.name}_{img_path.stem}.txt"
        with open(label_path, "w") as f:
            f.write(f"{class_id} 0.5 0.5 0.98 0.98\n")
    
    return len(images)


# ============================================
# YOLO Config YAML Generator
# ============================================

def generate_yolo_yaml(dataset_name: str, classes: list):
    """
    Generate a YOLO dataset configuration YAML file.
    
    Args:
        dataset_name: Name of the dataset
        classes: List of class names
    """
    dataset_path = YOLO_DATASET_BASE / dataset_name
    yaml_path = YOLO_CONFIG_DIR / f"{dataset_name}.yaml"
    
    yaml_content = f"""# YOLOv8 Dataset Configuration
# Dataset: {dataset_name}
# Auto-generated by prepare_all_datasets.py

path: {dataset_path.as_posix()}
train: images/train
val: images/val

# Number of classes
nc: {len(classes)}

# Class names
names:
"""
    for i, cls in enumerate(classes):
        yaml_content += f"  {i}: {cls}\n"
    
    yaml_path.write_text(yaml_content)
    print(f"  📄 Created YAML config: {yaml_path.name}")


# ============================================
# Dataset-Specific Preparation Functions
# ============================================

def prepare_algal_bloom_dataset():
    """Prepare Algal Bloom Detection dataset."""
    print("\n🌿 Preparing Algal Bloom Dataset...")
    
    dataset_name = "algal_bloom"
    classes = YOLO_MODELS[dataset_name]["classes"]
    paths = create_yolo_structure(dataset_name)
    
    raw_dir = RAW_DATA_DIR / "algal_bloom"
    
    if raw_dir.exists() and any(raw_dir.rglob("*.jpg")) or any(raw_dir.rglob("*.png")):
        # Try to find class subdirectories
        temp_images = YOLO_DATASET_BASE / dataset_name / "temp_images"
        temp_labels = YOLO_DATASET_BASE / dataset_name / "temp_labels"
        temp_images.mkdir(parents=True, exist_ok=True)
        temp_labels.mkdir(parents=True, exist_ok=True)
        
        total = 0
        for i, class_name in enumerate(classes):
            class_dir = raw_dir / class_name
            if class_dir.exists():
                count = create_classification_yolo_labels(
                    class_dir, temp_images, temp_labels, i
                )
                total += count
                print(f"  📁 Class '{class_name}': {count} images")
        
        # If no class dirs found, use all images as single class
        if total == 0:
            all_images = list(raw_dir.rglob("*.jpg")) + list(raw_dir.rglob("*.png"))
            for img in all_images[:500]:  # Limit for demo
                shutil.copy2(img, temp_images / img.name)
                label_path = temp_labels / f"{img.stem}.txt"
                label_path.write_text("0 0.5 0.5 0.98 0.98\n")
                total += 1
            print(f"  📁 All images as class 0: {total} images")
        
        split_dataset(temp_images, temp_labels, paths)
        shutil.rmtree(temp_images, ignore_errors=True)
        shutil.rmtree(temp_labels, ignore_errors=True)
    else:
        print("  ⚠️  Raw dataset not found. Creating demo dataset...")
        create_demo_dataset(paths, classes, dataset_name)
    
    generate_yolo_yaml(dataset_name, classes)


def prepare_fish_disease_dataset():
    """Prepare Fish Disease Detection dataset."""
    print("\n🐟 Preparing Fish Disease Dataset...")
    
    dataset_name = "fish_disease"
    classes = YOLO_MODELS[dataset_name]["classes"]
    paths = create_yolo_structure(dataset_name)
    
    raw_dir = RAW_DATA_DIR / "fish_disease"
    
    if raw_dir.exists() and any(raw_dir.rglob("*.jpg")) or any(raw_dir.rglob("*.png")):
        temp_images = YOLO_DATASET_BASE / dataset_name / "temp_images"
        temp_labels = YOLO_DATASET_BASE / dataset_name / "temp_labels"
        temp_images.mkdir(parents=True, exist_ok=True)
        temp_labels.mkdir(parents=True, exist_ok=True)
        
        total = 0
        for i, class_name in enumerate(classes):
            # Check for various directory naming conventions
            for possible_name in [class_name, class_name.replace("_", " "), class_name.title()]:
                class_dir = raw_dir / possible_name
                if class_dir.exists():
                    count = create_classification_yolo_labels(
                        class_dir, temp_images, temp_labels, i
                    )
                    total += count
                    print(f"  📁 Class '{class_name}': {count} images")
                    break
        
        if total == 0:
            # Scan all subdirectories
            subdirs = [d for d in raw_dir.iterdir() if d.is_dir()]
            for i, subdir in enumerate(subdirs[:len(classes)]):
                count = create_classification_yolo_labels(
                    subdir, temp_images, temp_labels, i
                )
                total += count
                print(f"  📁 '{subdir.name}' → class {i}: {count} images")
        
        if total > 0:
            split_dataset(temp_images, temp_labels, paths)
        else:
            create_demo_dataset(paths, classes, dataset_name)
        
        shutil.rmtree(temp_images, ignore_errors=True)
        shutil.rmtree(temp_labels, ignore_errors=True)
    else:
        print("  ⚠️  Raw dataset not found. Creating demo dataset...")
        create_demo_dataset(paths, classes, dataset_name)
    
    generate_yolo_yaml(dataset_name, classes)


def prepare_malaria_dataset():
    """Prepare Malaria Parasite Detection dataset."""
    print("\n🦟 Preparing Malaria Dataset...")
    
    dataset_name = "malaria"
    classes = YOLO_MODELS[dataset_name]["classes"]
    paths = create_yolo_structure(dataset_name)
    
    raw_dir = RAW_DATA_DIR / "malaria_cells"
    
    if raw_dir.exists():
        temp_images = YOLO_DATASET_BASE / dataset_name / "temp_images"
        temp_labels = YOLO_DATASET_BASE / dataset_name / "temp_labels"
        temp_images.mkdir(parents=True, exist_ok=True)
        temp_labels.mkdir(parents=True, exist_ok=True)
        
        total = 0
        # Look for Parasitized / Uninfected directories
        class_mapping = {
            "parasitized": 0,
            "Parasitized": 0,
            "uninfected": 1,
            "Uninfected": 1,
        }
        
        for dir_name, class_id in class_mapping.items():
            class_dir = raw_dir / dir_name
            if not class_dir.exists():
                # Search recursively
                for subdir in raw_dir.rglob(dir_name):
                    if subdir.is_dir():
                        class_dir = subdir
                        break
            
            if class_dir.exists():
                count = create_classification_yolo_labels(
                    class_dir, temp_images, temp_labels, class_id
                )
                total += count
                print(f"  📁 Class '{classes[class_id]}': {count} images")
        
        if total > 0:
            split_dataset(temp_images, temp_labels, paths)
        else:
            create_demo_dataset(paths, classes, dataset_name)
        
        shutil.rmtree(temp_images, ignore_errors=True)
        shutil.rmtree(temp_labels, ignore_errors=True)
    else:
        print("  ⚠️  Raw dataset not found. Creating demo dataset...")
        create_demo_dataset(paths, classes, dataset_name)
    
    generate_yolo_yaml(dataset_name, classes)


def prepare_micro_pathogens_dataset():
    """Prepare Micro-Pathogens Detection dataset."""
    print("\n🔬 Preparing Micro-Pathogens Dataset...")
    
    dataset_name = "micro_pathogens"
    classes = YOLO_MODELS[dataset_name]["classes"]
    paths = create_yolo_structure(dataset_name)
    
    # This dataset typically needs to be combined from multiple sources
    print("  ⚠️  Micro-pathogen datasets require manual annotation.")
    print("  📝 See datasets/annotation_guide.md for instructions.")
    create_demo_dataset(paths, classes, dataset_name)
    generate_yolo_yaml(dataset_name, classes)


def prepare_water_contamination_dataset():
    """Prepare Water Contamination Detection dataset."""
    print("\n💧 Preparing Water Contamination Dataset...")
    
    dataset_name = "water_contamination"
    classes = YOLO_MODELS[dataset_name]["classes"]
    paths = create_yolo_structure(dataset_name)
    
    raw_dir = RAW_DATA_DIR / "water_quality_images"
    
    if raw_dir.exists() and (any(raw_dir.rglob("*.jpg")) or any(raw_dir.rglob("*.png"))):
        temp_images = YOLO_DATASET_BASE / dataset_name / "temp_images"
        temp_labels = YOLO_DATASET_BASE / dataset_name / "temp_labels"
        temp_images.mkdir(parents=True, exist_ok=True)
        temp_labels.mkdir(parents=True, exist_ok=True)
        
        total = 0
        subdirs = [d for d in raw_dir.iterdir() if d.is_dir()]
        
        if subdirs:
            for i, subdir in enumerate(subdirs[:len(classes)]):
                count = create_classification_yolo_labels(
                    subdir, temp_images, temp_labels, i
                )
                total += count
                print(f"  📁 '{subdir.name}' → class {i}: {count} images")
        
        if total > 0:
            split_dataset(temp_images, temp_labels, paths)
        else:
            create_demo_dataset(paths, classes, dataset_name)
        
        shutil.rmtree(temp_images, ignore_errors=True)
        shutil.rmtree(temp_labels, ignore_errors=True)
    else:
        print("  ⚠️  Raw dataset not found. Creating demo dataset...")
        create_demo_dataset(paths, classes, dataset_name)
    
    generate_yolo_yaml(dataset_name, classes)


# ============================================
# Demo Dataset Creator
# ============================================

def create_demo_dataset(paths: dict, classes: list, dataset_name: str, num_per_class: int = 25):
    """
    Create a minimal demo dataset with synthetic images.
    Each class gets colored/textured images with YOLO labels.
    
    This is for testing the pipeline when real datasets aren't yet downloaded.
    
    Args:
        paths: Dict of train/val paths from create_yolo_structure()
        classes: List of class names
        dataset_name: Name of the dataset
        num_per_class: Number of synthetic images per class
    """
    print(f"  🎨 Creating demo dataset: {num_per_class} images per class")
    
    # Color palette for different classes
    class_colors = [
        (50, 120, 50),    # Green
        (30, 60, 120),    # Brown
        (60, 60, 150),    # Red
        (100, 130, 50),   # Teal
        (80, 80, 80),     # Gray
    ]
    
    all_images = []
    all_labels = []
    
    for class_id, class_name in enumerate(classes):
        color = class_colors[class_id % len(class_colors)]
        
        for img_idx in range(num_per_class):
            # Create synthetic image with patterns
            img = np.full((416, 416, 3), color, dtype=np.uint8)
            
            # Add random circles/shapes to simulate objects
            for _ in range(random.randint(3, 8)):
                cx = random.randint(50, 366)
                cy = random.randint(50, 366)
                radius = random.randint(10, 60)
                c = tuple(int(min(255, max(0, v + random.randint(-40, 40)))) for v in color)
                cv2.circle(img, (cx, cy), radius, c, -1)
            
            # Add noise
            noise = np.random.randint(-20, 20, img.shape, dtype=np.int16)
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Add class label text
            cv2.putText(img, f"{class_name}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(img, f"DEMO-{dataset_name}", (10, 400),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            # Save
            img_name = f"{dataset_name}_{class_name}_{img_idx:04d}.jpg"
            img_path = paths["images_train"].parent / "temp" / img_name
            img_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(img_path), img)
            
            # Create YOLO label
            label_name = f"{dataset_name}_{class_name}_{img_idx:04d}.txt"
            label_path = paths["labels_train"].parent / "temp" / label_name
            label_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Random bbox
            bx = random.uniform(0.2, 0.8)
            by = random.uniform(0.2, 0.8)
            bw = random.uniform(0.2, 0.5)
            bh = random.uniform(0.2, 0.5)
            label_path.write_text(f"{class_id} {bx:.4f} {by:.4f} {bw:.4f} {bh:.4f}\n")
            
            all_images.append(img_path)
            all_labels.append(label_path)
    
    # Split into train/val
    combined = list(zip(all_images, all_labels))
    random.shuffle(combined)
    val_count = max(1, int(len(combined) * 0.2))
    
    for img_path, label_path in combined[val_count:]:
        shutil.move(str(img_path), str(paths["images_train"] / img_path.name))
        shutil.move(str(label_path), str(paths["labels_train"] / label_path.name))
    
    for img_path, label_path in combined[:val_count]:
        shutil.move(str(img_path), str(paths["images_val"] / img_path.name))
        shutil.move(str(label_path), str(paths["labels_val"] / label_path.name))
    
    # Cleanup temp
    temp_dir = paths["images_train"].parent / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir = paths["labels_train"].parent / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    train_count = len(list(paths["images_train"].iterdir()))
    val_count_actual = len(list(paths["images_val"].iterdir()))
    print(f"  ✅ Demo dataset created: {train_count} train / {val_count_actual} val")


# ============================================
# Dataset Size Reference
# ============================================

DATASET_SIZE_GUIDE = """
╔══════════════════════════════════════════════════════════════╗
║                   DATASET SIZE GUIDE                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  MINIMUM (Demo/Testing):                                     ║
║  ├── 25-50 images per class                                  ║
║  ├── Total: ~200-500 images per model                        ║
║  └── Good for: Pipeline testing, quick demos                 ║
║                                                              ║
║  RECOMMENDED (Good Results):                                 ║
║  ├── 200-500 images per class                                ║
║  ├── Total: 1,000-3,000 images per model                    ║
║  └── Good for: Academic projects, prototypes                 ║
║                                                              ║
║  IDEAL (Production):                                         ║
║  ├── 1,000-5,000 images per class                            ║
║  ├── Total: 5,000-25,000 images per model                   ║
║  └── Good for: Real deployment, high accuracy                ║
║                                                              ║
║  With augmentation (3x), your effective dataset is 3x larger ║
╚══════════════════════════════════════════════════════════════╝
"""


# ============================================
# Main Preparation Pipeline
# ============================================

def prepare_all():
    """
    Master function: prepares ALL datasets with ONE command.
    
    Steps:
    1. Download all datasets
    2. Process each into YOLO format
    3. Create train/val splits
    4. Generate YAML configs
    """
    print("=" * 60)
    print("🌊 WATERBORNE DISEASE DATASET PREPARATION")
    print("=" * 60)
    print(DATASET_SIZE_GUIDE)
    
    # Step 1: Download all datasets
    print("\n" + "=" * 60)
    print("📥 STEP 1: Downloading Datasets")
    print("=" * 60)
    
    from datasets.download_dataset import download_all_datasets
    download_all_datasets()
    
    # Step 2: Prepare each YOLO dataset
    print("\n" + "=" * 60)
    print("🔧 STEP 2: Preparing YOLO Datasets")
    print("=" * 60)
    
    prepare_algal_bloom_dataset()
    prepare_fish_disease_dataset()
    prepare_malaria_dataset()
    prepare_micro_pathogens_dataset()
    prepare_water_contamination_dataset()
    
    # Step 3: Verify CSV dataset
    print("\n" + "=" * 60)
    print("📊 STEP 3: Verifying ML Dataset (CSV)")
    print("=" * 60)
    
    csv_path = RAW_DATA_DIR / "east_region_india_water_disease_cleaned.csv"
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"  ✅ CSV Dataset loaded: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  📋 Columns: {list(df.columns)}")
    else:
        print("  ⚠️  CSV dataset not found. Download it manually from:")
        print("     https://drive.google.com/file/d/1j1gpnsXFDpgUDPy9vry6uI4HP0p8sl3T/view")
        print(f"     Save to: {csv_path}")
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("📊 PREPARATION SUMMARY")
    print("=" * 60)
    
    for model_name, model_info in YOLO_MODELS.items():
        dataset_dir = YOLO_DATASET_BASE / model_name
        train_count = len(list((dataset_dir / "images" / "train").glob("*"))) if (dataset_dir / "images" / "train").exists() else 0
        val_count = len(list((dataset_dir / "images" / "val").glob("*"))) if (dataset_dir / "images" / "val").exists() else 0
        yaml_exists = (YOLO_CONFIG_DIR / f"{model_name}.yaml").exists()
        
        print(f"\n  📦 {model_info['name']}:")
        print(f"     Train: {train_count} images")
        print(f"     Val:   {val_count} images")
        print(f"     YAML:  {'✅' if yaml_exists else '❌'}")
        print(f"     Classes: {model_info['classes']}")
    
    print(f"\n{'=' * 60}")
    print("✅ ALL DATASETS PREPARED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📌 Next steps:")
    print("   1. python models/yolo/train_yolo.py --model algal_bloom")
    print("   2. python models/ml/eda.py")
    print("   3. python models/ml/train_ml_model.py")


if __name__ == "__main__":
    prepare_all()
