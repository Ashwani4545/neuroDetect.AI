"""
Quantitative measurements computed directly from a segmentation mask PNG.

Everything here is a real calculation on real pixel data — no fabricated or
estimated values. Pixel spacing metadata isn't reliably available across the
input formats this app accepts, so all areas are reported in pixels, never
converted to mm² without valid calibration.
"""
import cv2
import numpy as np


def compute_measurements(mask_path: str) -> dict:
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return {'available': False, 'reason': f'Could not read mask file: {mask_path}'}

    height, width = mask.shape
    total_pixels = height * width
    binary = (mask > 0).astype(np.uint8)
    foreground_pixels = int(binary.sum())
    foreground_percentage = round(foreground_pixels / total_pixels * 100, 3) if total_pixels else 0.0

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    regions = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]
        regions.append({
            'region_id': i,
            'area_px': int(area),
            'bounding_box': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
            'centroid': {'x': round(float(cx), 1), 'y': round(float(cy), 1)},
        })
    regions.sort(key=lambda r: r['area_px'], reverse=True)

    region_areas = [r['area_px'] for r in regions]
    size_distribution = {
        'min_px': min(region_areas) if region_areas else None,
        'max_px': max(region_areas) if region_areas else None,
        'mean_px': round(float(np.mean(region_areas)), 1) if region_areas else None,
        'median_px': round(float(np.median(region_areas)), 1) if region_areas else None,
    }

    return {
        'available': True,
        'image_dimensions': {'width': width, 'height': height},
        'total_foreground_pixels': foreground_pixels,
        'foreground_percentage': foreground_percentage,
        'region_count': len(regions),
        'regions': regions,
        'region_size_distribution': size_distribution,
        'pixel_spacing_available': False,
        'physical_units_note': (
            'Pixel spacing metadata is not available for this input, so all '
            'areas are reported in pixels only — not converted to physical '
            'units (mm²) without valid spatial calibration.'
        ),
    }
