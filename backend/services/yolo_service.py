"""
============================================
YOLO Detection Service (Hybrid + Smart CV)
============================================
Two-stage analysis:
  1. Find water regions in the image
  2. Analyze water quality + detect contamination features
     (foam, debris, discoloration) ONLY within water areas
"""

import sys
import io
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np

try:
    import cv2
    from PIL import Image
except ImportError:
    pass

from config.settings import YOLO_MODELS, WEIGHTS_DIR
from backend.utils.logger import app_logger

BBOX_COLORS = {
    "contaminated_water": (0, 0, 255),
    "turbid_water": (0, 140, 255),
    "clean_water": (0, 200, 0),
    "sewage": (0, 100, 200),
    "industrial_waste": (0, 50, 180),
    "chemical_runoff": (255, 0, 200),
    "algae_bloom": (0, 180, 0),
    "stagnant_water": (50, 150, 200),
    "flood_water": (0, 180, 255),
    "foam_scum": (255, 255, 0),
    "oil_film": (50, 50, 200),
    "floating_debris": (255, 200, 0),
}


class WaterImageAnalyzer:
    """
    Two-stage water contamination analyzer:
    Stage 1: Find water regions, analyze water color/turbidity
    Stage 2: Detect contamination features (foam, debris, oil) ON water
    """

    def analyze(self, image: np.ndarray) -> dict:
        if image is None or image.size == 0:
            return {"error": "Invalid image", "detections": [], "annotated_image": None}

        h, w = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Stage 1: Find water regions
        water_mask = self._find_water_regions(image, hsv, gray, h, w)

        # Stage 2A: Analyze overall water quality
        water_quality = self._analyze_water_quality(image, hsv, water_mask, h, w)

        # Stage 2B: Detect specific contamination features ON the water
        feature_detections = self._detect_contamination_features(
            image, hsv, gray, water_mask, h, w
        )

        # Combine: feature detections + water quality
        detections = []
        is_clean_base = water_quality.get("water_type") == "clean_water"

        # If water is fundamentally clean, suppress CV false positives
        if is_clean_base:
            # Only keep feature detections with very high confidence
            feature_detections = [d for d in feature_detections if d["confidence"] > 0.75]

        if feature_detections:
            detections.extend(feature_detections)

        # Add water quality detection
        wq_detection = self._water_quality_detection(water_quality, water_mask, h, w)
        if wq_detection:
            has_foam = any(d["class"] == "foam_scum" for d in detections)
            has_oil = any(d["class"] == "oil_film" for d in detections)

            # Only upgrade to industrial_waste if water is NOT clean
            if (has_foam or has_oil) and not is_clean_base:
                wq_detection["class"] = "industrial_waste"
                wq_detection["risk"] = "CRITICAL"
                wq_detection["confidence"] = max(wq_detection["confidence"], 0.85)

            detections.append(wq_detection)

        detections.sort(key=lambda x: x["confidence"], reverse=True)
        detections = detections[:10]

        is_dangerous = any(
            d["class"] not in ("clean_water",) and d["confidence"] > 0.35
            for d in detections
        )

        if detections and any(d["class"] != "clean_water" for d in detections):
            contam = [d for d in detections if d["class"] != "clean_water"]
            risk_score = min(99, int(max(d["confidence"] for d in contam) * 100))
        else:
            risk_score = 5

        risk_level = (
            "CRITICAL" if risk_score >= 75 else
            "HIGH" if risk_score >= 55 else
            "MEDIUM" if risk_score >= 35 else "LOW"
        )

        annotated = self._draw_annotations(image, detections)
        _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
        annotated_b64 = base64.b64encode(buffer).decode('utf-8')

        class_dist = {}
        for d in detections:
            class_dist[d["class"]] = class_dist.get(d["class"], 0) + 1

        return {
            "detections": detections,
            "is_dangerous": is_dangerous,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "class_distribution": class_dist,
            "total_objects": len(detections),
            "annotated_image": annotated_b64,
        }

    # -------------------------------------------------------
    # Stage 1: Find water regions
    # -------------------------------------------------------
    def _find_water_regions(self, image, hsv, gray, h, w):
        b, g, r = cv2.split(image)
        h_ch, s_ch, v_ch = cv2.split(hsv)

        # Smooth texture regions (water is smoother than land/objects)
        blurred = cv2.GaussianBlur(gray, (15, 15), 0)
        diff = cv2.absdiff(gray, blurred)
        _, smooth = cv2.threshold(diff, 12, 255, cv2.THRESH_BINARY_INV)

        # Brown/muddy water
        brown = (
            (r.astype(float) > 50) &
            (r.astype(float) > b.astype(float) * 1.05) &
            (g.astype(float) > b.astype(float) * 0.85) &
            (v_ch > 30) & (v_ch < 230)
        ).astype(np.uint8) * 255

        # Blue/dark water
        blue_water = (
            (b.astype(float) > r.astype(float) * 0.9) &
            (s_ch > 15) & (v_ch > 30)
        ).astype(np.uint8) * 255

        # Greenish water (stagnant/algae)
        green_water = (
            (g.astype(float) > r.astype(float) * 0.9) &
            (g.astype(float) > b.astype(float) * 1.0) &
            (s_ch > 20) & (v_ch > 40) & (v_ch < 200)
        ).astype(np.uint8) * 255

        # Also include bright/white water surface areas (foam-covered)
        # This is water that has foam/scum on it — still water region
        white_surface = (
            (v_ch > 160) & (s_ch < 60) &
            (np.abs(r.astype(int) - g.astype(int)) < 30) &
            (np.abs(g.astype(int) - b.astype(int)) < 30)
        ).astype(np.uint8) * 255

        water_color = cv2.bitwise_or(brown, blue_water)
        water_color = cv2.bitwise_or(water_color, green_water)
        water_color = cv2.bitwise_or(water_color, white_surface)

        water_mask = cv2.bitwise_and(smooth, water_color)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel, iterations=2)

        # If too little water, broader fallback
        ratio = float(np.sum(water_mask > 0) / water_mask.size)
        if ratio < 0.10:
            water_mask = cv2.bitwise_or(brown, blue_water)
            water_mask = cv2.bitwise_or(water_mask, white_surface)
            water_mask[:int(h * 0.2), :] = 0  # exclude top sky
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
            water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel, iterations=3)

        return water_mask

    # -------------------------------------------------------
    # Stage 2A: Overall water quality
    # -------------------------------------------------------
    def _analyze_water_quality(self, image, hsv, water_mask, h, w):
        b, g, r = cv2.split(image)
        h_ch, s_ch, v_ch = cv2.split(hsv)

        water_ratio = float(np.sum(water_mask > 0) / water_mask.size)
        if water_ratio < 0.05:
            return {"water_type": "insufficient", "turbidity": 0, "contam_score": 0,
                    "water_ratio": water_ratio}

        wr = r[water_mask > 0].astype(float)
        wg = g[water_mask > 0].astype(float)
        wb = b[water_mask > 0].astype(float)
        ws = s_ch[water_mask > 0].astype(float)
        wv = v_ch[water_mask > 0].astype(float)
        wh = h_ch[water_mask > 0].astype(float)

        mr, mg, mb = float(np.mean(wr)), float(np.mean(wg)), float(np.mean(wb))
        ms, mv, mh = float(np.mean(ws)), float(np.mean(wv)), float(np.mean(wh))
        rb_ratio = mr / max(mb, 1)

        # Turbidity — conservative: requires STRONG evidence of brown/muddy
        turb = 0.0
        if rb_ratio > 1.4:  # Strong red-brown dominance (was 1.2)
            turb += min((rb_ratio - 1.2) * 0.4, 0.4)
        if ms < 40:  # Very desaturated — grey/muddy
            turb += 0.10
        if mr > mb * 1.2 and mg > mb * 1.0 and mr > 80:  # Brown water
            turb += 0.25

        # Structural turbidity: heavily polluted water/sewage has immense clutter
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edges_on_water = cv2.bitwise_and(edges, water_mask)
        edge_density = float(np.sum(edges_on_water > 0) / max(water_mask.size, 1)) * (water_mask.size / max(np.sum(water_mask > 0), 1))
        
        white_water_pixels = float(np.sum((wv > 180) & (ws < 40)))
        white_ratio_on_water = white_water_pixels / max(np.sum(water_mask > 0), 1)
        
        # If highly textured but NOT white rapids
        if edge_density > 0.08 and white_ratio_on_water < 0.30:
            turb += edge_density * 2.0  # Boost turbidity if water is full of structural clutter (diffuse garbage/sewage)
            
        turb = min(1.0, turb)

        # Classify water — CONSERVATIVE: default is clean
        # Flood: high turbidity + brown dominance + large water area
        is_flood = bool(turb > 0.5 and water_ratio > 0.20 and mr > mb * 1.25 and mr > 80)
        # Stagnant: uniformly green, NOT from tree reflections
        # Tree reflections have high saturation variation; stagnant is more uniform
        green_ratio = mg / max(max(mr, mb), 1)
        is_stagnant = bool(green_ratio > 1.3 and ms > 60 and mv < 150 and
                           turb < 0.3 and float(np.std(ws)) < 30)
        # Sewage: dark/desaturated/brownish OR highly cluttered desaturated water (diffuse garbage)
        is_sewage = bool((mv < 60 and ms < 40 and rb_ratio > 1.2 and turb > 0.3) or
                         (ms < 60 and edge_density > 0.10 and white_ratio_on_water < 0.20))
        # Chemical: very vivid unnatural colors (exclude natural greens/blues from trees/sky)
        # Unnatural water hues: Red/Pink/Magenta/Purple (h < 15 or h > 130)
        is_chemical = bool(ms > 160 and mv > 160 and (mh < 15 or mh > 130))

        # Has a lot of white/foam on water?
        # Must be truly white-opaque patches, not sunlight reflections
        white_on_water = float(np.sum((wv > 180) & (ws < 40)) / max(len(wv), 1))
        # Reflections on clean water: bright patches but water elsewhere is dark
        # Real foam: bright patches AND water elsewhere is also somewhat bright/murky
        avg_non_white_v = float(np.mean(wv[wv < 170])) if len(wv[wv < 170]) > 0 else 50.0
        # If the entire water surface is overwhelmingly white (>50%), it's undeniably foam.
        is_reflection_likely = avg_non_white_v < 80 and turb < 0.3 and white_on_water < 0.50
        has_foam_surface = bool(white_on_water > 0.30 and not is_reflection_likely)

        contam = 0.0
        if turb > 0.3:
            contam += turb * 0.5
        if is_flood:
            contam += 0.25
        if is_stagnant:
            contam += 0.2
        if is_sewage:
            contam += 0.3
        if is_chemical:
            contam += 0.4
        if has_foam_surface:
            if white_on_water > 0.50 or turb > 0.4:
                contam += 0.3
        contam = min(1.0, contam)

        if is_chemical:
            wtype = "chemical_runoff"
        elif has_foam_surface and (white_on_water > 0.50 or turb > 0.4):
            wtype = "industrial_waste"
        elif is_flood:
            wtype = "flood_water"
        elif is_sewage:
            wtype = "sewage"
        elif is_stagnant:
            wtype = "stagnant_water"
        elif turb > 0.3:
            wtype = "turbid_water"
        elif turb > 0.20:
            wtype = "contaminated_water"
        else:
            wtype = "clean_water"

        return {
            "water_type": wtype,
            "turbidity": round(float(turb), 3),
            "contam_score": round(float(contam), 3),
            "water_ratio": round(float(water_ratio), 3),
            "has_foam_surface": has_foam_surface,
            "is_flood": is_flood,
        }

    # -------------------------------------------------------
    # Stage 2B: Detect contamination features ON water surface
    # -------------------------------------------------------
    def _detect_contamination_features(self, image, hsv, gray, water_mask, h, w):
        """
        Detect specific visible contamination ON the water surface:
        - Foam / scum (white/cream patches floating on water)
        - Oil film (dark iridescent patches)
        - Floating debris (multi-colored objects on water)
        """
        detections = []
        h_ch, s_ch, v_ch = cv2.split(hsv)
        b, g, r = cv2.split(image)

        # Expand water mask slightly
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
        water_expanded = cv2.dilate(water_mask, kernel, iterations=2)

        # ---- NATURAL SCENE ANALYSIS ----
        # Detect vegetation (green areas NOT in water) — indicates natural scene
        veg_mask = (
            (g.astype(float) > r.astype(float) * 1.2) &
            (g.astype(float) > b.astype(float) * 1.2) &
            (s_ch > 40) & (v_ch > 30) &
            (water_expanded == 0)  # not in water
        ).astype(np.uint8) * 255
        veg_ratio = float(np.sum(veg_mask > 0) / veg_mask.size)
        is_natural_scene = veg_ratio > 0.08  # >8% vegetation = natural scene

        # White water from rapids = high edge density within white areas
        edges = cv2.Canny(gray, 80, 200)
        water_pixels = float(np.sum(water_expanded > 0))
        if water_pixels > 0:
            edges_on_water = cv2.bitwise_and(edges, water_expanded)
            edge_density = float(np.sum(edges_on_water > 0) / water_pixels)
        else:
            edge_density = 0.0

        # High edge density on water = flowing/rapids OR massive floating garbage
        # Rapids are mostly bright white. Garbage is highly textured but mixed brightness.
        white_water_pixels = float(np.sum((v_ch > 180) & (s_ch < 40) & (water_expanded > 0)))
        white_ratio_on_water = white_water_pixels / max(water_pixels, 1)
        
        # If water is OVERWHELMINGLY white (>60%), it's a massive foam spill, not just rapids.
        has_rapids = edge_density > 0.12 and 0.30 < white_ratio_on_water < 0.60
        has_heavy_garbage = edge_density > 0.15 and white_ratio_on_water < 0.20

        if has_heavy_garbage:
            # Massive accumulation of garbage/debris spanning the water
            detections.append({
                "class": "industrial_waste",
                "class_id": 4,
                "confidence": min(0.85, 0.40 + edge_density),
                "bbox": [0, int(h*0.2), w, h],
                "risk": "CRITICAL",
                "source": "cv_analysis",
            })

        # ---- FOAM / SCUM DETECTION ----
        # REAL foam: very bright, very low saturation, large opaque patches
        # NOT: rapids (high texture), reflections (on dark water), waves
        foam_mask = (
            (v_ch > 200) & (s_ch < 30) &  # Very white, very unsaturated
            (water_expanded > 0)
        ).astype(np.uint8) * 255

        foam_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        foam_mask = cv2.morphologyEx(foam_mask, cv2.MORPH_OPEN, foam_kernel, iterations=2)
        foam_mask = cv2.morphologyEx(foam_mask, cv2.MORPH_CLOSE, foam_kernel, iterations=3)

        foam_contours, _ = cv2.findContours(foam_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_foam_area = w * h * 0.03  # At least 3% of image (very conservative)

        foam_regions = []
        for cnt in foam_contours:
            area = cv2.contourArea(cnt)
            if area > min_foam_area:
                x, y, bw, bh = cv2.boundingRect(cnt)

                # Skip if scene has rapids (white = water spray, not foam)
                if has_rapids:
                    continue

                # Skip in natural scenes unless patch is HUGE and opaque
                if is_natural_scene and area < w * h * 0.08:
                    continue

                # Shape filter: foam is blobby, not streaky
                aspect = max(bw, bh) / max(min(bw, bh), 1)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = area / max(hull_area, 1)

                if aspect > 4.0:
                    continue  # Too elongated
                if solidity < 0.4:
                    continue  # Too fragmented

                # Texture check: foam has SOME texture (bubbles), sky reflections are totally smooth
                foam_region_edges = edges[y:y+bh, x:x+bw]
                foam_edge_density = float(np.sum(foam_region_edges > 0) / max(bw * bh, 1))
                if foam_edge_density > 0.15 and white_ratio_on_water < 0.60:
                    continue  # High edge density = rapids/waves, not foam (unless >60% white)
                if foam_edge_density < 0.005:
                    continue  # Zero edges = completely smooth sky/cloud reflection

                # Surrounding water check
                # ONLY apply strong reflection filter if foam patch is relatively small (<15%)
                if area < w * h * 0.15:
                    pad = 30
                    sx1, sy1 = max(0, x - pad), max(0, y - pad)
                    sx2, sy2 = min(w, x + bw + pad), min(h, y + bh + pad)
                    surround_v = v_ch[sy1:sy2, sx1:sx2].astype(float)
                    surround_mean_v = float(np.median(surround_v))
                    if surround_mean_v < 90:
                        continue  # Dark water around = reflection/glare

                roi_water = water_expanded[y:y+bh, x:x+bw]
                overlap = float(np.sum(roi_water > 0) / max(roi_water.size, 1))
                if overlap > 0.5:
                    conf = min(0.85, 0.35 + (area / (w * h)) * 2.0)
                    foam_regions.append((x, y, x+bw, y+bh, area, conf))

        foam_regions = self._merge_nearby_boxes(foam_regions, w, h)

        for (x1, y1, x2, y2, area, conf) in foam_regions:
            detections.append({
                "class": "foam_scum",
                "class_id": 3,
                "confidence": round(float(conf), 4),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "risk": "HIGH" if conf > 0.6 else "MEDIUM",
                "source": "cv_analysis",
            })

        # ---- OIL FILM DETECTION ----
        # Oil has slight iridescence (color variation) — NOT just dark patches
        # Dark rocks/shadows are simply dark with NO color; oil has subtle hues
        oil_mask = (
            (v_ch < 50) & (s_ch < 30) &
            (water_expanded > 0)
        ).astype(np.uint8) * 255
        oil_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 12))
        oil_mask = cv2.morphologyEx(oil_mask, cv2.MORPH_CLOSE, oil_kernel, iterations=2)
        oil_mask = cv2.morphologyEx(oil_mask, cv2.MORPH_OPEN, oil_kernel, iterations=2)

        oil_contours, _ = cv2.findContours(oil_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_oil_area = w * h * 0.03  # At least 3%

        for cnt in oil_contours:
            area = cv2.contourArea(cnt)
            if area > min_oil_area:
                x, y, bw, bh = cv2.boundingRect(cnt)

                # Skip in natural scenes (dark patches = rocks/shadows)
                if is_natural_scene:
                    continue

                # Oil should be smooth (low edge density), rocks have sharp edges
                region_edges = edges[y:y+bh, x:x+bw]
                region_edge_density = float(np.sum(region_edges > 0) / max(bw * bh, 1))
                if region_edge_density > 0.10:
                    continue  # High edges = rocks/hard objects, not oil

                roi_water = water_expanded[y:y+bh, x:x+bw]
                overlap = float(np.sum(roi_water > 0) / max(roi_water.size, 1))
                if overlap > 0.5:
                    conf = min(0.80, 0.35 + (area / (w * h)) * 2.0)
                    detections.append({
                        "class": "oil_film",
                        "class_id": 5,
                        "confidence": round(float(conf), 4),
                        "bbox": [int(x), int(y), int(x+bw), int(y+bh)],
                        "risk": "HIGH",
                        "source": "cv_analysis",
                    })

        # ---- FLOATING DEBRIS (Plastics/Garbage) ----
        # Identify scattered debris: small, highly textured objects natively floating on water.
        
        # 1. Saturated generic debris (neon packaging)
        sat_debris = ((s_ch > 140) & (v_ch > 120) & ~((h_ch > 25) & (h_ch < 140)))
        
        # 2. Desaturated plastics (bright white/grey plastic bags)
        white_plastic = ((v_ch > 160) & (s_ch < 40))
        
        # 3. Dark plastics/sludge 
        dark_plastic = ((v_ch < 50))
        
        # Combine everything as potential debris
        debris_raw = (sat_debris | white_plastic | dark_plastic)
        debris_mask = (debris_raw & (water_expanded > 0)).astype(np.uint8) * 255
        
        debris_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        debris_mask = cv2.morphologyEx(debris_mask, cv2.MORPH_OPEN, debris_kernel, iterations=1)
        debris_mask = cv2.morphologyEx(debris_mask, cv2.MORPH_CLOSE, debris_kernel, iterations=2)

        debris_contours, _ = cv2.findContours(debris_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_debris_area = w * h * 0.001   # 0.1% min (small floating wrappers)
        max_debris_area = w * h * 0.15    # 15% max

        debris_count = 0
        for cnt in debris_contours:
            area = cv2.contourArea(cnt)
            if min_debris_area < area < max_debris_area:
                x, y, bw, bh = cv2.boundingRect(cnt)

                # Filter rocks in natural scenes (skip dark objects if river is surrounded by nature)
                roi_v = v_ch[y:y+bh, x:x+bw]
                is_mostly_dark = float(np.sum(roi_v < 60) / max(roi_v.size, 1)) > 0.6
                if is_natural_scene and is_mostly_dark:
                    continue  # Likely a rock
                
                # Filter sun glare/reflections (glare is smooth, plastic bags have edges/wrinkles)
                region_edges = edges[y:y+bh, x:x+bw]
                edge_density = float(np.sum(region_edges > 0) / max(bw * bh, 1))
                if edge_density < 0.05:
                    continue  # Smooth = glare/reflection/shadow

                roi_water = water_expanded[y:y+bh, x:x+bw]
                overlap = float(np.sum(roi_water > 0) / max(roi_water.size, 1))
                if overlap > 0.6 and debris_count < 8:
                    conf = min(0.85, 0.40 + (area / (w * h)) * 3.0)
                    
                    # Deduplicate with other boxes (e.g. oil or massive structural garbage)
                    overlap_found = False
                    for d in detections:
                        dx1, dy1, dx2, dy2 = d["bbox"]
                        if not (x > dx2 or dx1 > x+bw or y > dy2 or dy1 > y+bh):
                            overlap_found = True
                            break
                    
                    if not overlap_found:
                        detections.append({
                            "class": "floating_debris",
                            "class_id": 6,
                            "confidence": round(float(conf), 4),
                            "bbox": [int(x), int(y), int(x+bw), int(y+bh)],
                            "risk": "MEDIUM",
                            "source": "cv_analysis",
                        })
                        debris_count += 1

        # ---- HEAVY STRUCTURAL GARBAGE / PLASTIC DUMP ----
        # Identify massive structural garbage dumps that are desaturated and highly textured.
        # Garbage forms dense clusters of sharp edges, unlike smooth water or solid land.
        edges_all = cv2.Canny(gray, 100, 200)
        
        # Remove edges that belong to natural green vegetation
        edges_not_veg = cv2.bitwise_and(edges_all, cv2.bitwise_not(veg_mask))
        # Remove edges that are part of the sky (upper 25%)
        edges_not_veg[:int(h * 0.25), :] = 0
        
        # Dilate these edges to form solid blobs where garbage is clustered
        kernel_cluster = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        edge_clusters = cv2.morphologyEx(edges_not_veg, cv2.MORPH_CLOSE, kernel_cluster, iterations=2)
        
        cluster_contours, _ = cv2.findContours(edge_clusters, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in cluster_contours:
            area = cv2.contourArea(cnt)
            # Must be a significantly large pile of garbage (e.g. > 3% of image area)
            if area > w * h * 0.03:
                x, y, bw, bh = cv2.boundingRect(cnt)
                
                # Garbage shouldn't be too elongated (like a single shoreline boundary)
                aspect = max(bw, bh) / max(min(bw, bh), 1)
                if aspect > 6.0:
                    continue
                
                # Must sit on or near water
                roi_water = water_expanded[y:y+bh, x:x+bw]
                water_touch = float(np.sum(roi_water > 0) / max(roi_water.size, 1))
                
                # Check for white water (rapids) and dark rocks
                roi_v = v_ch[y:y+bh, x:x+bw]
                roi_s = s_ch[y:y+bh, x:x+bw]
                white_ratio = float(np.sum((roi_v > 180) & (roi_s < 40)) / max(roi_v.size, 1))
                dark_ratio = float(np.sum(roi_v < 60) / max(roi_v.size, 1))
                
                # If touching water + not fully white + not fully black = textured garbage
                if water_touch > 0.10 and white_ratio < 0.35 and dark_ratio < 0.60:
                    conf = min(0.95, 0.50 + (area / (w * h)) * 1.5)
                    # Deduplicate with existing feature detections (don't overlap if foam/oil is already here)
                    overlap_found = False
                    for d in detections:
                        dx1, dy1, dx2, dy2 = d["bbox"]
                        # rough intersection check
                        if not (x > dx2 or dx1 > x+bw or y > dy2 or dy1 > y+bh):
                            overlap_found = True
                            break
                    
                    if not overlap_found:
                        detections.append({
                            "class": "industrial_waste",
                            "class_id": 4,
                            "confidence": round(float(conf), 4),
                            "bbox": [int(x), int(y), int(x+bw), int(y+bh)],
                            "risk": "CRITICAL",
                            "source": "cv_analysis",
                        })

        return detections

    def _merge_nearby_boxes(self, regions, w, h):
        """Merge overlapping or nearby bounding boxes."""
        if len(regions) <= 1:
            return regions

        merged = True
        while merged:
            merged = False
            new_regions = []
            used = set()
            for i, (x1a, y1a, x2a, y2a, aa, ca) in enumerate(regions):
                if i in used:
                    continue
                mx1, my1, mx2, my2, ma, mc = x1a, y1a, x2a, y2a, aa, ca
                for j, (x1b, y1b, x2b, y2b, ab, cb) in enumerate(regions):
                    if j <= i or j in used:
                        continue
                    # Check if boxes overlap or are close
                    gap = min(w, h) * 0.05
                    if (mx1 - gap < x2b and mx2 + gap > x1b and
                            my1 - gap < y2b and my2 + gap > y1b):
                        mx1 = min(mx1, x1b)
                        my1 = min(my1, y1b)
                        mx2 = max(mx2, x2b)
                        my2 = max(my2, y2b)
                        ma += ab
                        mc = max(mc, cb)
                        used.add(j)
                        merged = True
                new_regions.append((mx1, my1, mx2, my2, ma, mc))
                used.add(i)
            regions = new_regions
        return regions

    # -------------------------------------------------------
    # Fish Disease Fallback
    # -------------------------------------------------------
    def analyze_fish_disease(self, image):
        """Fallback CV Analyzer for Fish Diseases (e.g. EUS lesions, red sores)"""
        h, w = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)
        b, g, r = cv2.split(image)
        
        detections = []
        
        # 1. Detect red/bloody lesions (EUS - Epizootic Ulcerative Syndrome)
        # Lesions are strongly red, with decent saturation
        red_mask_1 = ((h_ch < 15) | (h_ch > 165))
        red_ulcer = (red_mask_1 & (s_ch > 60) & (v_ch > 40) & (r.astype(float) > g.astype(float) * 1.5)).astype(np.uint8) * 255
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        red_ulcer = cv2.morphologyEx(red_ulcer, cv2.MORPH_OPEN, kernel, iterations=1)
        red_ulcer = cv2.morphologyEx(red_ulcer, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        contours, _ = cv2.findContours(red_ulcer, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_lesion_area = w * h * 0.001  # 0.1% area
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_lesion_area:
                x, y, bw, bh = cv2.boundingRect(cnt)
                
                aspect = max(bw, bh) / max(min(bw, bh), 1)
                if aspect > 6.0:
                    continue  # maybe a red string or background object
                
                conf = min(0.95, 0.60 + (area / (w * h)) * 5.0)
                detections.append({
                    "class": "diseased_fish",
                    "class_id": 0,
                    "confidence": round(float(conf), 4),
                    "bbox": [int(x), int(y), int(x+bw), int(y+bh)],
                    "risk": "CRITICAL",
                    "source": "cv_analysis",
                })
                
        wtype = "diseased_fish" if detections else "healthy_fish"
        return {"water_type": wtype, "detections": detections, "contam_score": 0.8 if detections else 0}



    # -------------------------------------------------------
    # Build water quality detection
    # -------------------------------------------------------
    def _water_quality_detection(self, wq, water_mask, h, w):
        wtype = wq.get("water_type", "clean_water")
        if wtype == "insufficient":
            return None

        contours, _ = cv2.findContours(water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            x, y, bw, bh = cv2.boundingRect(cnt)
            bbox = [int(x), int(y), int(x+bw), int(y+bh)]
        else:
            bbox = [int(w*0.02), int(h*0.3), int(w*0.98), int(h*0.95)]

        risk_map = {
            "flood_water": ("CRITICAL", 0.88),
            "sewage": ("CRITICAL", 0.85),
            "chemical_runoff": ("CRITICAL", 0.90),
            "industrial_waste": ("CRITICAL", 0.88),
            "stagnant_water": ("HIGH", 0.70),
            "turbid_water": ("HIGH", 0.72),
            "contaminated_water": ("MEDIUM", 0.55),
            "diseased_fish": ("CRITICAL", 0.85),
            "healthy_fish": ("LOW", 0.10),
            "clean_water": ("LOW", 0.10),
        }

        risk, base_conf = risk_map.get(wtype, ("MEDIUM", 0.50))
        conf = min(0.98, base_conf + wq.get("contam_score", 0) * 0.12)

        return {
            "class": wtype,
            "class_id": 0,
            "confidence": round(float(conf), 4),
            "bbox": bbox,
            "risk": risk,
            "source": "cv_analysis",
        }

    # -------------------------------------------------------
    # Draw annotations
    # -------------------------------------------------------
    def _draw_annotations(self, image, detections):
        annotated = image.copy()
        h, w = annotated.shape[:2]

        for det in detections:
            bbox = det["bbox"]
            cls = det["class"]
            conf = det["confidence"]
            risk = det.get("risk", "MEDIUM")

            color = BBOX_COLORS.get(cls, (0, 255, 255))
            x1, y1 = max(0, int(bbox[0])), max(0, int(bbox[1]))
            x2, y2 = min(w, int(bbox[2])), min(h, int(bbox[3]))

            thickness = max(2, int(min(w, h) / 200))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            label = f"{cls} {conf:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.4, min(w, h) / 1000)
            text_thick = max(1, thickness - 1)
            (tw, th_t), _ = cv2.getTextSize(label, font, font_scale, text_thick)

            label_y = max(y1, th_t + 10)
            overlay = annotated.copy()
            cv2.rectangle(overlay, (x1, label_y - th_t - 10), (x1 + tw + 10, label_y + 2),
                          color, -1)
            cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
            cv2.putText(annotated, label, (x1 + 5, label_y - 4), font, font_scale,
                        (255, 255, 255), text_thick, cv2.LINE_AA)

            risk_colors = {"CRITICAL": (0, 0, 255), "HIGH": (0, 100, 255),
                           "MEDIUM": (0, 200, 255), "LOW": (0, 200, 0)}
            cv2.putText(annotated, f"[{risk}]", (x1 + tw + 15, label_y - 4), font,
                        font_scale * 0.8, risk_colors.get(risk, (0, 200, 255)),
                        text_thick, cv2.LINE_AA)

        cv2.putText(annotated, "AQUACARE - WATER QUALITY ANALYSIS",
                    (8, h - 12), cv2.FONT_HERSHEY_SIMPLEX,
                    max(0.3, min(w, h) / 1800), (0, 200, 200), 1, cv2.LINE_AA)

        return annotated


class YOLOService:
    """Hybrid detection: YOLO + Smart CV Analysis."""

    def __init__(self):
        self._models = {}
        self._analyzer = WaterImageAnalyzer()
        self.logger = app_logger

    def _get_model(self, model_name):
        if model_name not in self._models:
            try:
                from ultralytics import YOLO
                weights_path = WEIGHTS_DIR / f"{model_name}_best.pt"
                if weights_path.exists():
                    self.logger.info(f"Loading YOLO model: {model_name}")
                    self._models[model_name] = YOLO(str(weights_path))
                else:
                    self.logger.warning(f"No weights for {model_name}")
                    self._models[model_name] = YOLO("yolov8n.pt")
            except ImportError:
                raise ImportError("pip install ultralytics")
        return self._models[model_name]

    def detect_from_bytes(self, image_bytes, model_name="water_contamination",
                          conf_threshold=0.20):
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return {"error": "Could not decode image", "detections": []}

        # Run YOLO (trained on real data)
        yolo_result = self._run_yolo(image, model_name, conf_threshold)
        yolo_dets = yolo_result.get("detections", [])
        
        # Filter to meaningful YOLO detections (use the actual threshold, don't hardcode 0.3)
        good_yolo = [d for d in yolo_dets if d["confidence"] >= conf_threshold and d["class"] != "clean_water"]
        
        # Also run CV analysis depending on module
        cv_dets = []
        cv_result = {}
        if model_name == "water_contamination":
            cv_result = self._analyzer.analyze(image)
        elif model_name == "fish_disease":
            cv_result = self._analyzer.analyze_fish_disease(image)
            
        cv_dets = cv_result.get("detections", [])

        # Combine: YOLO detections take priority, CV fills gaps
        all_detections = []
        good_yolo_classes = set(d["class"] for d in good_yolo)
        
        for d in good_yolo:
            d["source"] = "yolo"
            all_detections.append(d)
        
        for d in cv_dets:
            if d["class"] not in good_yolo_classes:
                d["source"] = "cv_analysis"
                all_detections.append(d)
        
        if not good_yolo and cv_dets:
            all_detections = cv_dets

        # Global fallback box if literally nothing structural was detected but the CV classified overall risk
        if not all_detections and cv_result:
            h, w = image.shape[:2]
            fallback_box = self._analyzer._water_quality_detection(cv_result, np.ones((h, w), dtype=np.uint8)*255, h, w)
            if fallback_box:
                all_detections.append(fallback_box)

        all_detections.sort(key=lambda x: x["confidence"], reverse=True)
        all_detections = all_detections[:10]

        # Determine analysis method
        if good_yolo:
            method = "yolo" if not cv_dets else "yolo+cv"
        else:
            method = "computer_vision"

        # Risk assessment
        is_dangerous = any(
            d["class"] not in ("clean_water", "healthy_fish") and d["confidence"] > 0.35
            for d in all_detections
        )

        if all_detections and any(d["class"] not in ("clean_water", "healthy_fish") for d in all_detections):
            contam = [d for d in all_detections if d["class"] not in ("clean_water", "healthy_fish")]
            risk_score = min(99, int(max(d["confidence"] for d in contam) * 100))
        else:
            risk_score = 5

        risk_level = (
            "CRITICAL" if risk_score >= 75 else
            "HIGH" if risk_score >= 55 else
            "MEDIUM" if risk_score >= 35 else "LOW"
        )

        # Draw annotated image
        annotated = self._analyzer._draw_annotations(image, all_detections)
        _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
        annotated_b64 = base64.b64encode(buf).decode('utf-8')

        class_dist = {}
        for d in all_detections:
            class_dist[d["class"]] = class_dist.get(d["class"], 0) + 1

        return {
            "model": model_name,
            "model_name": YOLO_MODELS[model_name]["name"],
            "detections": all_detections,
            "total_detections": len(all_detections),
            "is_dangerous": is_dangerous,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "class_distribution": class_dist,
            "total_objects": len(all_detections),
            "annotated_image": annotated_b64,
            "analysis_method": method,
            "yolo_detections": len(good_yolo),
            "cv_detections": len(cv_dets),
            "timestamp": datetime.now().isoformat(),
        }

    def detect_from_file(self, image_path, model_name="water_contamination",
                         conf_threshold=0.25):
        with open(image_path, "rb") as f:
            return self.detect_from_bytes(f.read(), model_name, conf_threshold)

    def detect_from_pil(self, pil_image, model_name="water_contamination",
                        conf_threshold=0.25):
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG")
        return self.detect_from_bytes(buf.getvalue(), model_name, conf_threshold)

    def detect_all_models(self, image_bytes, conf_threshold=0.25):
        all_results = {}
        for model_name in YOLO_MODELS:
            try:
                all_results[model_name] = self.detect_from_bytes(
                    image_bytes, model_name, conf_threshold)
            except Exception as e:
                all_results[model_name] = {"error": str(e), "detections": []}
        return all_results

    def _run_yolo(self, image, model_name, conf_threshold):
        try:
            model = self._get_model(model_name)
            class_names = YOLO_MODELS[model_name]["classes"]
            results = model.predict(source=image, conf=conf_threshold, save=False, verbose=False)
            return self._parse_results(results, class_names, model_name)
        except Exception as e:
            self.logger.error(f"YOLO failed: {e}")
            return {
                "model": model_name,
                "model_name": YOLO_MODELS.get(model_name, {}).get("name", model_name),
                "detections": [], "total_detections": 0, "is_dangerous": False,
                "timestamp": datetime.now().isoformat(),
            }

    def _parse_results(self, results, class_names, model_name):
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    box = boxes[i]
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()
                    cls_name = class_names[cls_id] if cls_id < len(class_names) else f"class_{cls_id}"
                    risk = ("CRITICAL" if conf > 0.85 else "HIGH" if conf > 0.65 else
                            "MEDIUM" if conf > 0.4 else "LOW")
                    detections.append({
                        "class": cls_name, "class_id": cls_id,
                        "confidence": round(conf, 4), "bbox": [round(b, 2) for b in bbox],
                        "risk": risk, "source": "yolo"
                    })
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        dangerous = {"contaminated", "industrial_waste", "sewage", "chemical_spill",
                     "parasitized", "harmful_algae", "bacterial_infection"}
        is_dangerous = any(d["class"] in dangerous and d["confidence"] > 0.4 for d in detections)
        return {
            "model": model_name,
            "model_name": YOLO_MODELS[model_name]["name"],
            "detections": detections, "total_detections": len(detections),
            "is_dangerous": is_dangerous, "timestamp": datetime.now().isoformat(),
        }

    def get_available_models(self):
        models = []
        for name, config in YOLO_MODELS.items():
            wp = WEIGHTS_DIR / f"{name}_best.pt"
            models.append({
                "key": name, "name": config["name"], "classes": config["classes"],
                "weights_available": wp.exists(), "loaded": name in self._models,
            })
        return models


yolo_service = YOLOService()
