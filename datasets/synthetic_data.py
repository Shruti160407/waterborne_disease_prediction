"""
============================================
Synthetic Data Generation
============================================
Generates synthetic training images using OpenCV.
Applies overlays, noise, blur, brightness, and rotation
to create additional training samples.

Usage:
    python datasets/synthetic_data.py --input_dir <path> --output_dir <path>
"""

import os
import sys
import argparse
import random
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


def add_gaussian_noise(image: np.ndarray, mean: float = 0, std: float = 25) -> np.ndarray:
    """Add Gaussian noise to an image."""
    noise = np.random.normal(mean, std, image.shape).astype(np.float32)
    noisy = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return noisy


def add_salt_pepper_noise(image: np.ndarray, amount: float = 0.02) -> np.ndarray:
    """Add salt and pepper noise to an image."""
    noisy = image.copy()
    h, w = image.shape[:2]
    num_salt = int(amount * h * w)
    
    # Salt (white pixels)
    coords = [np.random.randint(0, i, num_salt) for i in image.shape[:2]]
    noisy[coords[0], coords[1]] = 255
    
    # Pepper (black pixels)
    coords = [np.random.randint(0, i, num_salt) for i in image.shape[:2]]
    noisy[coords[0], coords[1]] = 0
    
    return noisy


def adjust_brightness(image: np.ndarray, factor: float = 1.3) -> np.ndarray:
    """Adjust image brightness by a factor."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def adjust_contrast(image: np.ndarray, factor: float = 1.5) -> np.ndarray:
    """Adjust image contrast by a factor."""
    mean = np.mean(image, axis=(0, 1), keepdims=True)
    adjusted = np.clip(mean + factor * (image.astype(np.float32) - mean), 0, 255)
    return adjusted.astype(np.uint8)


def add_color_tint(image: np.ndarray, tint_color: str = "green") -> np.ndarray:
    """
    Add a color tint to simulate water contamination appearance.
    
    Args:
        image: Input image
        tint_color: One of "green", "brown", "red", "yellow"
    """
    tints = {
        "green": np.array([0, 40, 0], dtype=np.float32),    # Algae-like
        "brown": np.array([10, 20, 30], dtype=np.float32),   # Turbid water
        "red": np.array([0, 0, 30], dtype=np.float32),       # Red tide
        "yellow": np.array([0, 30, 40], dtype=np.float32),   # Chemical
    }
    
    tint = tints.get(tint_color, tints["green"])
    tinted = np.clip(image.astype(np.float32) + tint, 0, 255).astype(np.uint8)
    return tinted


def add_water_ripple_effect(image: np.ndarray, strength: float = 5.0) -> np.ndarray:
    """Apply a water ripple distortion effect."""
    h, w = image.shape[:2]
    map_x = np.zeros((h, w), dtype=np.float32)
    map_y = np.zeros((h, w), dtype=np.float32)
    
    for i in range(h):
        for j in range(w):
            map_x[i, j] = j + strength * np.sin(2 * np.pi * i / 60)
            map_y[i, j] = i + strength * np.sin(2 * np.pi * j / 60)
    
    return cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def add_fog_effect(image: np.ndarray, intensity: float = 0.3) -> np.ndarray:
    """Add a fog/haze effect to simulate atmospheric conditions."""
    fog = np.full_like(image, 220, dtype=np.uint8)
    foggy = cv2.addWeighted(image, 1 - intensity, fog, intensity, 0)
    return foggy


def random_crop_and_resize(image: np.ndarray, crop_ratio: float = 0.8) -> np.ndarray:
    """Randomly crop and resize back to original dimensions."""
    h, w = image.shape[:2]
    new_h, new_w = int(h * crop_ratio), int(w * crop_ratio)
    
    top = random.randint(0, h - new_h)
    left = random.randint(0, w - new_w)
    
    cropped = image[top:top + new_h, left:left + new_w]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def overlay_particles(image: np.ndarray, num_particles: int = 50) -> np.ndarray:
    """
    Overlay small particles/dots to simulate microscopic view
    of pathogens or contaminants in water.
    """
    result = image.copy()
    h, w = image.shape[:2]
    
    for _ in range(num_particles):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        radius = random.randint(1, 4)
        color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
        )
        opacity = random.uniform(0.3, 0.8)
        
        overlay = result.copy()
        cv2.circle(overlay, (x, y), radius, color, -1)
        result = cv2.addWeighted(overlay, opacity, result, 1 - opacity, 0)
    
    return result


def generate_synthetic_images(
    input_dir: Path,
    output_dir: Path,
    num_variants: int = 5,
    copy_labels: bool = True,
    label_dir: Path = None
):
    """
    Generate synthetic variants for all images in a directory.
    
    Applies random combinations of effects to create diverse
    training samples for water contamination detection.
    
    Args:
        input_dir: Directory with original images
        output_dir: Directory to save synthetic images
        num_variants: Number of synthetic variants per image
        copy_labels: Whether to copy YOLO labels for each variant
        label_dir: Directory containing YOLO label files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if label_dir and copy_labels:
        output_label_dir = output_dir.parent / "labels" / output_dir.name
        output_label_dir.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    image_files = [f for f in input_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"  ⚠️  No images found in {input_dir}")
        return
    
    # Available transformations
    transforms = [
        ("noise", lambda img: add_gaussian_noise(img, std=random.uniform(10, 40))),
        ("salt_pepper", lambda img: add_salt_pepper_noise(img, amount=random.uniform(0.01, 0.05))),
        ("bright", lambda img: adjust_brightness(img, factor=random.uniform(0.7, 1.5))),
        ("contrast", lambda img: adjust_contrast(img, factor=random.uniform(0.7, 1.8))),
        ("blur", lambda img: cv2.GaussianBlur(img, (random.choice([3, 5, 7]), random.choice([3, 5, 7])), 0)),
        ("green_tint", lambda img: add_color_tint(img, "green")),
        ("brown_tint", lambda img: add_color_tint(img, "brown")),
        ("fog", lambda img: add_fog_effect(img, intensity=random.uniform(0.1, 0.4))),
        ("particles", lambda img: overlay_particles(img, num_particles=random.randint(20, 80))),
        ("crop", lambda img: random_crop_and_resize(img, crop_ratio=random.uniform(0.7, 0.95))),
    ]
    
    print(f"  🧪 Generating {num_variants} synthetic variants for {len(image_files)} images")
    total = 0
    
    for img_path in tqdm(image_files, desc="  Synthesizing"):
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        
        for i in range(num_variants):
            # Apply 2-4 random transforms
            num_transforms = random.randint(2, 4)
            selected = random.sample(transforms, min(num_transforms, len(transforms)))
            
            result = image.copy()
            suffix_parts = []
            
            for name, transform_fn in selected:
                try:
                    result = transform_fn(result)
                    suffix_parts.append(name)
                except Exception:
                    continue
            
            # Save synthetic image
            syn_name = f"{img_path.stem}_syn{i}{''.join(['_' + s for s in suffix_parts[:2]])}{img_path.suffix}"
            cv2.imwrite(str(output_dir / syn_name), result)
            
            # Copy label file if exists (bboxes don't change for pixel-level transforms)
            if copy_labels and label_dir:
                src_label = label_dir / f"{img_path.stem}.txt"
                if src_label.exists():
                    dst_label = output_label_dir / f"{img_path.stem}_syn{i}{''.join(['_' + s for s in suffix_parts[:2]])}.txt"
                    import shutil
                    shutil.copy2(src_label, dst_label)
            
            total += 1
    
    print(f"  ✅ Generated {total} synthetic images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic training images")
    parser.add_argument("--input_dir", type=str, required=True, help="Input image directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--label_dir", type=str, default=None, help="Label directory (YOLO)")
    parser.add_argument("--num_variants", type=int, default=5, help="Variants per image")
    parser.add_argument("--no_labels", action="store_true", help="Don't copy labels")
    
    args = parser.parse_args()
    
    generate_synthetic_images(
        Path(args.input_dir),
        Path(args.output_dir),
        args.num_variants,
        not args.no_labels,
        Path(args.label_dir) if args.label_dir else None
    )
