"""
============================================
YOLO Model Training Script
============================================
Train YOLOv8 detection models for waterborne disease detection.

Supports training separate models for:
- Algal Bloom Detection
- Fish Disease Detection
- Malaria Parasite Detection
- Micro-Pathogens Detection
- Water Contamination Detection

Usage:
    # Train a specific model:
    python models/yolo/train_yolo.py --model algal_bloom

    # Train all models:
    python models/yolo/train_yolo.py --all

    # Custom training:
    python models/yolo/train_yolo.py --model fish_disease --epochs 100 --batch 16 --imgsz 640
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import YOLO_MODELS, WEIGHTS_DIR, YOLO_CONFIG_DIR


def train_model(
    model_name: str,
    epochs: int = 50,
    batch_size: int = 16,
    img_size: int = 640,
    pretrained: str = "yolov8n.pt",
    device: str = "",
    patience: int = 20,
    workers: int = 4,
    resume: bool = False
):
    """
    Train a YOLOv8 model for a specific detection task.
    
    Args:
        model_name: Key from YOLO_MODELS config (e.g., "algal_bloom")
        epochs: Number of training epochs (default: 50)
        batch_size: Batch size for training (default: 16)
        img_size: Input image size (default: 640)
        pretrained: Pretrained model to use as base (default: "yolov8n.pt")
        device: Device to train on ("", "cpu", "0", "0,1")
        patience: Early stopping patience (default: 20)
        workers: Number of data loader workers (default: 4)
        resume: Resume training from last checkpoint
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)
    
    if model_name not in YOLO_MODELS:
        print(f"❌ Unknown model: {model_name}")
        print(f"   Available models: {list(YOLO_MODELS.keys())}")
        sys.exit(1)
    
    model_config = YOLO_MODELS[model_name]
    config_path = YOLO_CONFIG_DIR / f"{model_name}.yaml"
    
    if not config_path.exists():
        print(f"❌ Dataset config not found: {config_path}")
        print(f"   Run: python datasets/prepare_all_datasets.py")
        sys.exit(1)
    
    print("=" * 60)
    print(f"🚀 Training: {model_config['name']}")
    print("=" * 60)
    print(f"  📋 Config:     {config_path}")
    print(f"  🏷️  Classes:    {model_config['classes']}")
    print(f"  📐 Image Size: {img_size}")
    print(f"  📦 Batch Size: {batch_size}")
    print(f"  🔄 Epochs:     {epochs}")
    print(f"  🧠 Pretrained: {pretrained}")
    print(f"  💾 Output:     {WEIGHTS_DIR}")
    print("=" * 60)
    
    # Load pretrained model
    model = YOLO(pretrained)
    
    # Train the model
    results = model.train(
        data=str(config_path),
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device if device else None,
        patience=patience,
        workers=workers,
        project=str(WEIGHTS_DIR / "runs"),
        name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        exist_ok=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        resume=resume,
        verbose=True,
    )
    
    # Save the best model weights
    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    if best_weights.exists():
        output_path = WEIGHTS_DIR / f"{model_name}_best.pt"
        import shutil
        shutil.copy2(best_weights, output_path)
        print(f"\n✅ Best weights saved to: {output_path}")
    
    # Print results
    print(f"\n{'=' * 60}")
    print(f"📊 Training Results for {model_config['name']}")
    print(f"{'=' * 60}")
    
    return results


def train_all_models(epochs: int = 50, batch_size: int = 16, img_size: int = 640):
    """
    Train all YOLO models sequentially.
    
    Args:
        epochs: Number of epochs for each model
        batch_size: Batch size
        img_size: Input image size
    """
    print("=" * 60)
    print("🌊 TRAINING ALL YOLO MODELS")
    print("=" * 60)
    
    results = {}
    
    for model_name in YOLO_MODELS:
        try:
            print(f"\n{'─' * 60}")
            result = train_model(model_name, epochs, batch_size, img_size)
            results[model_name] = "✅ Success"
        except Exception as e:
            print(f"  ❌ Failed to train {model_name}: {e}")
            results[model_name] = f"❌ Failed: {str(e)[:50]}"
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("📊 TRAINING SUMMARY")
    print(f"{'=' * 60}")
    for name, status in results.items():
        print(f"  {YOLO_MODELS[name]['name']}: {status}")


def validate_model(model_name: str, img_size: int = 640):
    """
    Validate a trained YOLO model on the validation set.
    
    Args:
        model_name: Key from YOLO_MODELS config
        img_size: Input image size
    """
    from ultralytics import YOLO
    
    weights_path = WEIGHTS_DIR / f"{model_name}_best.pt"
    if not weights_path.exists():
        print(f"❌ Weights not found: {weights_path}")
        print(f"   Train the model first: python models/yolo/train_yolo.py --model {model_name}")
        return
    
    config_path = YOLO_CONFIG_DIR / f"{model_name}.yaml"
    
    model = YOLO(str(weights_path))
    results = model.val(
        data=str(config_path),
        imgsz=img_size,
        verbose=True
    )
    
    print(f"\n📊 Validation Results:")
    print(f"   mAP50:    {results.box.map50:.4f}")
    print(f"   mAP50-95: {results.box.map:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 models for waterborne disease detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python models/yolo/train_yolo.py --model algal_bloom
  python models/yolo/train_yolo.py --model fish_disease --epochs 100
  python models/yolo/train_yolo.py --all --epochs 30
  python models/yolo/train_yolo.py --validate --model malaria
        """
    )
    
    parser.add_argument("--model", type=str, default=None,
                       choices=list(YOLO_MODELS.keys()),
                       help="Model to train")
    parser.add_argument("--all", action="store_true",
                       help="Train all models")
    parser.add_argument("--validate", action="store_true",
                       help="Validate instead of train")
    parser.add_argument("--epochs", type=int, default=50,
                       help="Number of training epochs (default: 50)")
    parser.add_argument("--batch", type=int, default=16,
                       help="Batch size (default: 16)")
    parser.add_argument("--imgsz", type=int, default=640,
                       help="Image size (default: 640)")
    parser.add_argument("--pretrained", type=str, default="yolov8n.pt",
                       help="Pretrained model (default: yolov8n.pt)")
    parser.add_argument("--device", type=str, default="",
                       help="Device: '', 'cpu', '0', '0,1'")
    parser.add_argument("--resume", action="store_true",
                       help="Resume training from last checkpoint")
    
    args = parser.parse_args()
    
    if args.validate:
        if not args.model:
            print("❌ Please specify --model for validation")
        else:
            validate_model(args.model, args.imgsz)
    elif args.all:
        train_all_models(args.epochs, args.batch, args.imgsz)
    elif args.model:
        train_model(
            args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            img_size=args.imgsz,
            pretrained=args.pretrained,
            device=args.device,
            resume=args.resume
        )
    else:
        parser.print_help()
