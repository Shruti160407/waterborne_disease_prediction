"""
============================================
Automated Dataset Downloader
============================================
Downloads all required datasets for the waterborne disease
detection system from free sources (Kaggle, Roboflow, Google Drive).

Usage:
    python datasets/download_dataset.py
"""

import os
import sys
import zipfile
import tarfile
import shutil
import hashlib
from pathlib import Path
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import requests
    import gdown
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests gdown tqdm")
    import requests
    import gdown

from config.settings import RAW_DATA_DIR, YOLO_DATASET_BASE


# ============================================
# Dataset Registry
# ============================================
# Each entry contains download info for a specific dataset
DATASETS = {
    "water_disease_csv": {
        "name": "East Region India Water Disease Dataset",
        "source": "google_drive",
        "file_id": "1j1gpnsXFDpgUDPy9vry6uI4HP0p8sl3T",
        "output": RAW_DATA_DIR / "east_region_india_water_disease_cleaned.csv",
        "description": "Primary CSV dataset for ML outbreak prediction model",
    },
    "water_quality_images": {
        "name": "Water Quality Images",
        "source": "kaggle",
        "dataset": "adityaramachandran27/water-quality-image-dataset",
        "output_dir": RAW_DATA_DIR / "water_quality_images",
        "description": "Images of contaminated and clean water samples",
    },
    "malaria_cells": {
        "name": "Malaria Cell Images",
        "source": "kaggle",
        "dataset": "iarunava/cell-images-for-detecting-malaria",
        "output_dir": RAW_DATA_DIR / "malaria_cells",
        "description": "Parasitized and uninfected cell images for malaria detection",
    },
    "fish_disease": {
        "name": "Fish Disease Dataset",
        "source": "kaggle",
        "dataset": "utkarshsaxenadn/fish-disease-dataset",
        "output_dir": RAW_DATA_DIR / "fish_disease",
        "description": "Images of fish with various diseases",
    },
    "algal_bloom": {
        "name": "Algal Bloom Dataset",
        "source": "kaggle",
        "dataset": "saidakbarp/lake-algae-image-dataset",
        "output_dir": RAW_DATA_DIR / "algal_bloom",
        "description": "Satellite and close-up images of algal blooms",
    },
}


def download_from_gdrive(file_id: str, output_path: Path) -> bool:
    """
    Download a file from Google Drive using gdown.
    
    Args:
        file_id: Google Drive file ID
        output_path: Path to save the downloaded file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"  📥 Downloading from Google Drive...")
        gdown.download(url, str(output_path), quiet=False)
        
        if output_path.exists() and output_path.stat().st_size > 0:
            print(f"  ✅ Saved to: {output_path}")
            return True
        else:
            print(f"  ❌ Download failed or file is empty")
            return False
    except Exception as e:
        print(f"  ❌ Error downloading from Google Drive: {e}")
        return False


def download_from_kaggle(dataset_name: str, output_dir: Path) -> bool:
    """
    Download a dataset from Kaggle using the Kaggle API.
    
    Requires KAGGLE_USERNAME and KAGGLE_KEY in environment or 
    ~/.kaggle/kaggle.json file.
    
    Args:
        dataset_name: Kaggle dataset identifier (e.g., "username/dataset-name")
        output_dir: Directory to save the downloaded dataset
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if kaggle credentials exist
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        has_env = os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")
        
        if not kaggle_json.exists() and not has_env:
            print(f"  ⚠️  Kaggle credentials not found.")
            print(f"     Option 1: Create ~/.kaggle/kaggle.json")
            print(f"     Option 2: Set KAGGLE_USERNAME and KAGGLE_KEY env vars")
            print(f"     Skipping Kaggle download: {dataset_name}")
            return create_placeholder_dataset(dataset_name, output_dir)
        
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"  📥 Downloading from Kaggle: {dataset_name}")
        api.dataset_download_files(dataset_name, path=str(output_dir), unzip=True)
        print(f"  ✅ Downloaded to: {output_dir}")
        return True
        
    except ImportError:
        print(f"  ⚠️  Kaggle package not installed. Run: pip install kaggle")
        return create_placeholder_dataset(dataset_name, output_dir)
    except Exception as e:
        print(f"  ⚠️  Kaggle download failed: {e}")
        return create_placeholder_dataset(dataset_name, output_dir)


def create_placeholder_dataset(dataset_name: str, output_dir: Path) -> bool:
    """
    Create placeholder directory structure when dataset can't be auto-downloaded.
    This allows the rest of the pipeline to work with manual dataset placement.
    
    Args:
        dataset_name: Name of the dataset (for documentation)
        output_dir: Directory to create the placeholder structure
        
    Returns:
        True always (placeholder is always created)
    """
    print(f"  📁 Creating placeholder structure for manual download...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a README with download instructions
    readme_path = output_dir / "DOWNLOAD_INSTRUCTIONS.md"
    readme_path.write_text(f"""# Manual Download Required

## Dataset: {dataset_name}

### Steps to download:
1. Go to https://www.kaggle.com/datasets/{dataset_name}
2. Click "Download" button
3. Extract the ZIP file contents into this directory:
   {output_dir}

### Alternative (using Kaggle CLI):
```bash
kaggle datasets download -d {dataset_name} -p "{output_dir}" --unzip
```

### After downloading:
Run `python datasets/prepare_all_datasets.py` to process the data.
""")
    
    # Create subdirectories for manual placement
    (output_dir / "images").mkdir(exist_ok=True)
    print(f"  📝 Created instructions at: {readme_path}")
    return True


def download_from_url(url: str, output_path: Path) -> bool:
    """
    Download a file from a direct URL with progress bar.
    
    Args:
        url: Direct download URL
        output_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  📥 Downloading from URL...")
        
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        
        with open(output_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"  ✅ Saved to: {output_path}")
        return True
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return False


def extract_archive(archive_path: Path, output_dir: Path) -> bool:
    """
    Extract ZIP or TAR archive files.
    
    Args:
        archive_path: Path to the archive file
        output_dir: Directory to extract contents to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if str(archive_path).endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(output_dir)
        elif str(archive_path).endswith((".tar.gz", ".tgz", ".tar")):
            with tarfile.open(archive_path, "r:*") as tf:
                tf.extractall(output_dir)
        else:
            print(f"  ⚠️  Unknown archive format: {archive_path}")
            return False
        
        print(f"  📦 Extracted to: {output_dir}")
        return True
    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return False


def remove_duplicates(directory: Path) -> int:
    """
    Remove duplicate files based on MD5 hash.
    
    Args:
        directory: Directory to scan for duplicates
        
    Returns:
        Number of duplicates removed
    """
    if not directory.exists():
        return 0
    
    seen_hashes = {}
    removed_count = 0
    
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    
    for filepath in directory.rglob("*"):
        if filepath.is_file() and filepath.suffix.lower() in image_extensions:
            try:
                file_hash = hashlib.md5(filepath.read_bytes()).hexdigest()
                if file_hash in seen_hashes:
                    filepath.unlink()
                    removed_count += 1
                else:
                    seen_hashes[file_hash] = filepath
            except Exception:
                continue
    
    if removed_count > 0:
        print(f"  🗑️  Removed {removed_count} duplicate files")
    return removed_count


def remove_corrupt_images(directory: Path) -> int:
    """
    Remove corrupt/unreadable image files.
    
    Args:
        directory: Directory to scan for corrupt images
        
    Returns:
        Number of corrupt files removed
    """
    if not directory.exists():
        return 0
    
    try:
        from PIL import Image
    except ImportError:
        print("  ⚠️  Pillow not installed. Skipping corrupt image check.")
        return 0
    
    removed_count = 0
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    
    for filepath in directory.rglob("*"):
        if filepath.is_file() and filepath.suffix.lower() in image_extensions:
            try:
                with Image.open(filepath) as img:
                    img.verify()
            except Exception:
                filepath.unlink()
                removed_count += 1
    
    if removed_count > 0:
        print(f"  🗑️  Removed {removed_count} corrupt images")
    return removed_count


def download_all_datasets():
    """
    Main function to download all datasets.
    Iterates through the DATASETS registry and downloads each one.
    """
    print("=" * 60)
    print("🌊 Waterborne Disease Dataset Downloader")
    print("=" * 60)
    
    results = {}
    
    for key, info in DATASETS.items():
        print(f"\n{'─' * 50}")
        print(f"📂 {info['name']}")
        print(f"   {info['description']}")
        print(f"{'─' * 50}")
        
        success = False
        
        if info["source"] == "google_drive":
            success = download_from_gdrive(info["file_id"], info["output"])
        elif info["source"] == "kaggle":
            success = download_from_kaggle(info["dataset"], info["output_dir"])
        elif info["source"] == "url":
            success = download_from_url(info["url"], info["output"])
        
        results[key] = success
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Download Summary")
    print(f"{'=' * 60}")
    for key, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {DATASETS[key]['name']}: {status}")
    
    successful = sum(1 for s in results.values() if s)
    print(f"\n  Total: {successful}/{len(results)} datasets ready")
    
    return results


if __name__ == "__main__":
    download_all_datasets()
