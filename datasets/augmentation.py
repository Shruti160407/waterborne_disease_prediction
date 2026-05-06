"""
============================================
Data Augmentation Pipeline
============================================
Uses Albumentations library for robust image augmentation.
Supports flip, rotate, scale, brightness, blur, noise, etc.

Usage:
    python datasets/augmentation.py --input_dir <path> --output_dir <path>
"""

import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import cv2
    import numpy as np
    import albumentations as A
    from tqdm import tqdm
except ImportError:
    print("Installing required packages...")
    os.system("pip install opencv-python albumentations tqdm numpy")
    import cv2
    import numpy as np
    import albumentations as A
    from tqdm import tqdm


def get_augmentation_pipeline(level: str = "medium") -> A.Compose:
    """
    Create an augmentation pipeline based on desired intensity level.
    
    Args:
        level: "light", "medium", or "heavy" augmentation
        
    Returns:
        Albumentations Compose pipeline
    """
    if level == "light":
        return A.Compose([
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.3),
            A.Rotate(limit=10, p=0.3),
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    elif level == "medium":
        return A.Compose([
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.Rotate(limit=20, p=0.4),
            A.RandomScale(scale_limit=0.15, p=0.3),
            A.GaussianBlur(blur_limit=(3, 5), p=0.2),
            A.GaussNoise(var_limit=(10.0, 40.0), p=0.2),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=15, p=0.3),
            A.CLAHE(clip_limit=2.0, p=0.2),
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    else:  # heavy
        return A.Compose([
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.6),
            A.Rotate(limit=30, p=0.5),
            A.RandomScale(scale_limit=0.2, p=0.4),
            A.GaussianBlur(blur_limit=(3, 7), p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=30, val_shift_limit=20, p=0.4),
            A.CLAHE(clip_limit=3.0, p=0.3),
            A.RandomShadow(p=0.2),
            A.RandomFog(fog_coef_lower=0.1, fog_coef_upper=0.3, p=0.15),
            A.RandomRain(slant_lower=-5, slant_upper=5, p=0.1),
            A.Perspective(scale=(0.02, 0.05), p=0.2),
            A.CoarseDropout(max_holes=5, max_height=20, max_width=20, p=0.2),
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))


def parse_yolo_label(label_path: Path):
    """
    Parse YOLO format label file.
    
    Args:
        label_path: Path to the YOLO label .txt file
        
    Returns:
        Tuple of (bboxes, class_labels) in YOLO format
    """
    bboxes = []
    class_labels = []
    
    if not label_path.exists():
        return bboxes, class_labels
    
    with open(label_path, "r") as f:
        for line in f.readlines():
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Clamp values to [0, 1]
                x_center = max(0.001, min(0.999, x_center))
                y_center = max(0.001, min(0.999, y_center))
                width = max(0.001, min(0.999, width))
                height = max(0.001, min(0.999, height))
                
                bboxes.append([x_center, y_center, width, height])
                class_labels.append(class_id)
    
    return bboxes, class_labels


def save_yolo_label(label_path: Path, bboxes: list, class_labels: list):
    """
    Save bounding boxes and class labels in YOLO format.
    
    Args:
        label_path: Output path for the label file
        bboxes: List of bounding boxes [x_center, y_center, width, height]
        class_labels: List of class IDs
    """
    label_path.parent.mkdir(parents=True, exist_ok=True)
    with open(label_path, "w") as f:
        for bbox, cls in zip(bboxes, class_labels):
            f.write(f"{cls} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")


def augment_dataset(
    input_image_dir: Path,
    input_label_dir: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    num_augmentations: int = 3,
    level: str = "medium"
):
    """
    Apply augmentations to an entire dataset.
    
    For each image, generates `num_augmentations` augmented versions
    while preserving the original bounding box annotations.
    
    Args:
        input_image_dir: Directory containing original images
        input_label_dir: Directory containing YOLO format labels
        output_image_dir: Directory to save augmented images
        output_label_dir: Directory to save augmented labels
        num_augmentations: Number of augmented copies per image
        level: Augmentation intensity ("light", "medium", "heavy")
    """
    output_image_dir.mkdir(parents=True, exist_ok=True)
    output_label_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline = get_augmentation_pipeline(level)
    
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    image_files = [f for f in input_image_dir.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"  ⚠️  No images found in {input_image_dir}")
        return
    
    print(f"  🔄 Augmenting {len(image_files)} images ({num_augmentations}x each, level={level})")
    
    total_generated = 0
    
    for img_path in tqdm(image_files, desc="  Augmenting"):
        # Read image
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Read corresponding label
        label_path = input_label_dir / f"{img_path.stem}.txt"
        bboxes, class_labels = parse_yolo_label(label_path)
        
        # Copy original
        cv2.imwrite(
            str(output_image_dir / img_path.name),
            cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        )
        if label_path.exists():
            save_yolo_label(output_label_dir / label_path.name, bboxes, class_labels)
        
        # Generate augmented versions
        for i in range(num_augmentations):
            try:
                if bboxes:
                    augmented = pipeline(
                        image=image,
                        bboxes=bboxes,
                        class_labels=class_labels
                    )
                    aug_bboxes = augmented["bboxes"]
                    aug_labels = augmented["class_labels"]
                else:
                    # No bboxes - use simple transform without bbox params
                    simple_pipeline = A.Compose([
                        t for t in pipeline.transforms
                    ])
                    augmented = simple_pipeline(image=image)
                    aug_bboxes = []
                    aug_labels = []
                
                # Save augmented image
                aug_name = f"{img_path.stem}_aug{i}{img_path.suffix}"
                aug_image = cv2.cvtColor(augmented["image"], cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(output_image_dir / aug_name), aug_image)
                
                # Save augmented label
                if aug_bboxes:
                    aug_label_name = f"{img_path.stem}_aug{i}.txt"
                    save_yolo_label(
                        output_label_dir / aug_label_name,
                        aug_bboxes,
                        aug_labels
                    )
                
                total_generated += 1
                
            except Exception as e:
                continue
    
    print(f"  ✅ Generated {total_generated} augmented images")


def augment_classification_dataset(
    input_dir: Path,
    output_dir: Path,
    num_augmentations: int = 3,
    level: str = "medium"
):
    """
    Augment a classification dataset (images organized in class folders).
    No bounding box handling needed.
    
    Args:
        input_dir: Directory with class subdirectories containing images
        output_dir: Directory to save augmented dataset
        num_augmentations: Number of augmented copies per image
        level: Augmentation intensity
    """
    # Simple pipeline without bbox params for classification
    if level == "light":
        pipeline = A.Compose([
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.3),
            A.Rotate(limit=10, p=0.3),
        ])
    elif level == "medium":
        pipeline = A.Compose([
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.Rotate(limit=20, p=0.4),
            A.GaussianBlur(blur_limit=(3, 5), p=0.2),
            A.GaussNoise(var_limit=(10.0, 40.0), p=0.2),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=15, p=0.3),
        ])
    else:
        pipeline = A.Compose([
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.6),
            A.Rotate(limit=30, p=0.5),
            A.GaussianBlur(blur_limit=(3, 7), p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.CLAHE(clip_limit=3.0, p=0.3),
            A.Perspective(scale=(0.02, 0.05), p=0.2),
        ])
    
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    total = 0
    
    for class_dir in input_dir.iterdir():
        if not class_dir.is_dir():
            continue
        
        out_class_dir = output_dir / class_dir.name
        out_class_dir.mkdir(parents=True, exist_ok=True)
        
        images = [f for f in class_dir.iterdir() 
                  if f.is_file() and f.suffix.lower() in image_extensions]
        
        for img_path in images:
            image = cv2.imread(str(img_path))
            if image is None:
                continue
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Copy original
            cv2.imwrite(str(out_class_dir / img_path.name), 
                       cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            
            for i in range(num_augmentations):
                try:
                    augmented = pipeline(image=image)
                    aug_name = f"{img_path.stem}_aug{i}{img_path.suffix}"
                    cv2.imwrite(str(out_class_dir / aug_name),
                               cv2.cvtColor(augmented["image"], cv2.COLOR_RGB2BGR))
                    total += 1
                except Exception:
                    continue
    
    print(f"  ✅ Generated {total} augmented classification images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Augment image datasets")
    parser.add_argument("--input_dir", type=str, required=True, help="Input image directory")
    parser.add_argument("--label_dir", type=str, default=None, help="Input label directory (YOLO)")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--num_aug", type=int, default=3, help="Number of augmentations per image")
    parser.add_argument("--level", type=str, default="medium", choices=["light", "medium", "heavy"])
    parser.add_argument("--classification", action="store_true", help="Use classification mode")
    
    args = parser.parse_args()
    
    if args.classification:
        augment_classification_dataset(
            Path(args.input_dir), Path(args.output_dir),
            args.num_aug, args.level
        )
    else:
        label_dir = Path(args.label_dir) if args.label_dir else Path(args.input_dir).parent / "labels"
        augment_dataset(
            Path(args.input_dir), label_dir,
            Path(args.output_dir) / "images", Path(args.output_dir) / "labels",
            args.num_aug, args.level
        )
