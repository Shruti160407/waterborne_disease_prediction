# Annotation Guide for Waterborne Disease Detection

## 📋 Overview

This guide explains how to annotate images for YOLO object detection training.
All annotations must be in **YOLO format** (normalized bounding boxes).

---

## 🛠️ Tools

### Option 1: LabelImg (Desktop - Recommended for Beginners)
```bash
pip install labelImg
labelImg
```
1. Open LabelImg
2. Click "Open Dir" → select your images folder
3. Click "Change Save Dir" → select your labels folder
4. **IMPORTANT**: Click "PascalVOC" button and switch to **YOLO** format
5. Draw bounding boxes around objects
6. Enter class name
7. Save (Ctrl+S)

### Option 2: Roboflow (Web-based - Recommended for Teams)
1. Go to [roboflow.com](https://roboflow.com)
2. Create a free account
3. Upload images
4. Draw bounding boxes using the web interface
5. Export in YOLO format

### Option 3: CVAT (Advanced - Open Source)
```bash
# Run with Docker
docker run -p 8080:8080 cvat/server
```

---

## 📐 YOLO Label Format

Each image `image_name.jpg` needs a corresponding `image_name.txt` label file.

### Format:
```
<class_id> <x_center> <y_center> <width> <height>
```

All values are **normalized** (0.0 to 1.0):
- `x_center` = center_x / image_width
- `y_center` = center_y / image_height  
- `width` = bbox_width / image_width
- `height` = bbox_height / image_height

### Example:
For a 640x480 image with an object at pixel coordinates (100, 150, 200, 180):
- Center X = (100 + 200/2) / 640 = 0.3125
- Center Y = (150 + 180/2) / 480 = 0.5
- Width = 200 / 640 = 0.3125
- Height = 180 / 480 = 0.375

Label file content:
```
0 0.3125 0.5000 0.3125 0.3750
```

---

## 🏷️ Class Labels

### Algal Bloom Detection
| Class ID | Label |
|----------|-------|
| 0 | harmful_algae |
| 1 | green_algae |
| 2 | blue_green_algae |
| 3 | red_tide |

### Fish Disease Detection
| Class ID | Label |
|----------|-------|
| 0 | epizootic_ulcerative |
| 1 | bacterial_infection |
| 2 | fungal_infection |
| 3 | healthy |

### Malaria Detection
| Class ID | Label |
|----------|-------|
| 0 | parasitized |
| 1 | uninfected |

### Micro-Pathogens Detection
| Class ID | Label |
|----------|-------|
| 0 | e_coli |
| 1 | cholera_vibrio |
| 2 | giardia |
| 3 | cryptosporidium |
| 4 | rotavirus |

### Water Contamination Detection
| Class ID | Label |
|----------|-------|
| 0 | contaminated |
| 1 | clean |
| 2 | industrial_waste |
| 3 | sewage |
| 4 | chemical_spill |

---

## 📁 Directory Structure

```
dataset/
├── images/
│   ├── train/
│   │   ├── img_001.jpg
│   │   ├── img_002.jpg
│   │   └── ...
│   └── val/
│       ├── img_100.jpg
│       └── ...
├── labels/
│   ├── train/
│   │   ├── img_001.txt
│   │   ├── img_002.txt
│   │   └── ...
│   └── val/
│       ├── img_100.txt
│       └── ...
```

---

## ✅ Best Practices

1. **Tight bounding boxes**: Draw boxes as close to the object as possible
2. **All instances**: Label ALL instances of each class in every image
3. **Consistent labeling**: Use the same class ID for the same object type
4. **No overlapping**: Minimize overlapping bounding boxes
5. **Minimum size**: Object should be at least 20x20 pixels
6. **Variety**: Include objects at different scales, angles, and lighting
7. **80/20 split**: Keep ~80% for training, ~20% for validation
