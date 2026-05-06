"""
============================================
YOLO Inference Pipeline
============================================
Run inference on images using trained YOLO models.

Usage:
    python models/yolo/inference.py --model algal_bloom --image path/to/image.jpg
    python models/yolo/inference.py --model water_contamination --dir path/to/images/
    python models/yolo/inference.py --model malaria --camera 0
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import cv2
    import numpy as np
except ImportError:
    os.system("pip install opencv-python numpy")
    import cv2
    import numpy as np

from config.settings import YOLO_MODELS, WEIGHTS_DIR


def load_model(model_name: str):
    """
    Load a trained YOLO model by name.
    
    Args:
        model_name: Key from YOLO_MODELS config
        
    Returns:
        Loaded YOLO model instance
    """
    from ultralytics import YOLO
    
    if model_name not in YOLO_MODELS:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(YOLO_MODELS.keys())}")
    
    weights_path = WEIGHTS_DIR / f"{model_name}_best.pt"
    
    if not weights_path.exists():
        print(f"⚠️  Trained weights not found: {weights_path}")
        print(f"   Using pretrained YOLOv8n for demo...")
        return YOLO("yolov8n.pt"), YOLO_MODELS[model_name]["classes"]
    
    model = YOLO(str(weights_path))
    return model, YOLO_MODELS[model_name]["classes"]


def predict_image(
    model_name: str,
    image_path: str,
    conf_threshold: float = 0.25,
    save_output: bool = True,
    output_dir: str = None
) -> dict:
    """
    Run YOLO inference on a single image.
    
    Args:
        model_name: Key from YOLO_MODELS config
        image_path: Path to the input image
        conf_threshold: Confidence threshold (default: 0.25)
        save_output: Whether to save annotated output image
        output_dir: Directory to save output (default: runs/detect/)
        
    Returns:
        Dict with detection results:
        {
            "model": str,
            "image": str,
            "detections": [
                {"class": str, "confidence": float, "bbox": [x1,y1,x2,y2]},
                ...
            ],
            "total_detections": int,
            "timestamp": str
        }
    """
    model, class_names = load_model(model_name)
    
    # Run prediction
    results = model.predict(
        source=image_path,
        conf=conf_threshold,
        save=save_output,
        project=output_dir or str(WEIGHTS_DIR / "runs" / "detect"),
        name=f"{model_name}_inference",
        exist_ok=True,
        verbose=False,
    )
    
    # Parse results
    detections = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for i in range(len(boxes)):
                box = boxes[i]
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                # Map class ID to name
                if cls_id < len(class_names):
                    cls_name = class_names[cls_id]
                else:
                    cls_name = f"class_{cls_id}"
                
                detections.append({
                    "class": cls_name,
                    "class_id": cls_id,
                    "confidence": round(confidence, 4),
                    "bbox": [round(b, 2) for b in bbox],
                })
    
    output = {
        "model": model_name,
        "model_name": YOLO_MODELS[model_name]["name"],
        "image": str(image_path),
        "detections": detections,
        "total_detections": len(detections),
        "timestamp": datetime.now().isoformat(),
    }
    
    return output


def predict_directory(
    model_name: str,
    image_dir: str,
    conf_threshold: float = 0.25,
    save_output: bool = True
) -> list:
    """
    Run YOLO inference on all images in a directory.
    
    Args:
        model_name: Key from YOLO_MODELS config
        image_dir: Path to directory containing images
        conf_threshold: Confidence threshold
        save_output: Whether to save annotated images
        
    Returns:
        List of detection result dicts
    """
    image_dir = Path(image_dir)
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    
    images = [f for f in image_dir.iterdir()
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"❌ No images found in {image_dir}")
        return []
    
    print(f"🔍 Processing {len(images)} images with {model_name}...")
    
    all_results = []
    for img_path in images:
        result = predict_image(model_name, str(img_path), conf_threshold, save_output)
        all_results.append(result)
        print(f"  ✅ {img_path.name}: {result['total_detections']} detections")
    
    return all_results


def predict_camera(
    model_name: str,
    camera_id: int = 0,
    conf_threshold: float = 0.25
):
    """
    Run real-time YOLO inference on camera feed.
    
    Args:
        model_name: Key from YOLO_MODELS config
        camera_id: Camera device ID (default: 0)
        conf_threshold: Confidence threshold
    """
    model, class_names = load_model(model_name)
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_id}")
        return
    
    print(f"📷 Real-time detection with {YOLO_MODELS[model_name]['name']}")
    print(f"   Press 'q' to quit, 's' to save screenshot")
    
    # Color palette for bounding boxes
    colors = [
        (0, 255, 0), (0, 0, 255), (255, 0, 0),
        (255, 255, 0), (0, 255, 255), (255, 0, 255),
    ]
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run inference
        results = model.predict(
            source=frame,
            conf=conf_threshold,
            verbose=False,
        )
        
        # Draw results on frame
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    box = boxes[i]
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    
                    color = colors[cls_id % len(colors)]
                    cls_name = class_names[cls_id] if cls_id < len(class_names) else f"class_{cls_id}"
                    label = f"{cls_name} {conf:.2f}"
                    
                    # Draw box and label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Add info overlay
        cv2.putText(frame, f"Model: {model_name} | FPS: {frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(f"YOLO Detection - {model_name}", frame)
        frame_count += 1
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_path = f"screenshot_{model_name}_{datetime.now().strftime('%H%M%S')}.jpg"
            cv2.imwrite(save_path, frame)
            print(f"  📸 Saved: {save_path}")
    
    cap.release()
    cv2.destroyAllWindows()


def predict_all_models(image_path: str, conf_threshold: float = 0.25) -> dict:
    """
    Run ALL YOLO models on a single image.
    Useful for comprehensive water quality assessment.
    
    Args:
        image_path: Path to the image
        conf_threshold: Confidence threshold
        
    Returns:
        Dict with results from all models
    """
    all_results = {}
    
    for model_name in YOLO_MODELS:
        try:
            result = predict_image(model_name, image_path, conf_threshold, save_output=False)
            all_results[model_name] = result
        except Exception as e:
            all_results[model_name] = {"error": str(e)}
    
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO Inference Pipeline")
    parser.add_argument("--model", type=str, required=True,
                       choices=list(YOLO_MODELS.keys()),
                       help="Model to use for detection")
    parser.add_argument("--image", type=str, default=None,
                       help="Path to single image")
    parser.add_argument("--dir", type=str, default=None,
                       help="Path to image directory")
    parser.add_argument("--camera", type=int, default=None,
                       help="Camera ID for real-time detection")
    parser.add_argument("--conf", type=float, default=0.25,
                       help="Confidence threshold (default: 0.25)")
    parser.add_argument("--no-save", action="store_true",
                       help="Don't save output images")
    
    args = parser.parse_args()
    
    if args.camera is not None:
        predict_camera(args.model, args.camera, args.conf)
    elif args.dir:
        results = predict_directory(args.model, args.dir, args.conf, not args.no_save)
        print(f"\n📊 Total images processed: {len(results)}")
    elif args.image:
        result = predict_image(args.model, args.image, args.conf, not args.no_save)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
