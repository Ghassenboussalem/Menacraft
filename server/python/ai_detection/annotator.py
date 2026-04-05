"""
Visual annotator for AI detection results.

Draws small marker dots on the image with arrows pointing to
clean labels on the margins. Only highlights the top findings
to keep the photo clearly visible.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
MAX_ANNOTATIONS = 5  # Only show the top N findings visually
MARGIN_RIGHT = 320   # Right margin for labels (pixels)
MARGIN_BOTTOM = 60   # Bottom margin for verdict bar
MARKER_RADIUS = 12   # Size of the dot on the image
ARROW_HEAD_SIZE = 8

COLORS_BY_SEVERITY = {
    "critical": (235, 64, 52),      # Red
    "moderate": (245, 166, 35),     # Orange
    "minor":    (66, 165, 245),     # Blue
    "none":     (158, 158, 158),    # Gray
}

VERDICT_COLORS = {
    "likely_ai_generated":    (235, 64, 52),
    "possibly_ai_generated":  (245, 166, 35),
    "likely_authentic":       (76, 175, 80),
    "uncertain":              (158, 158, 158),
}

VERDICT_LABELS = {
    "likely_ai_generated":    "LIKELY AI-GENERATED",
    "possibly_ai_generated":  "POSSIBLY AI-GENERATED",
    "likely_authentic":       "LIKELY AUTHENTIC",
    "uncertain":              "UNCERTAIN",
}

CATEGORY_LABELS = {
    "hands_fingers": "Hands/Fingers",
    "face_anatomy": "Face",
    "text_writing": "Text",
    "reflections_mirrors": "Reflections",
    "background_consistency": "Background",
    "lighting_shadows": "Lighting",
    "skin_texture": "Skin Texture",
    "hair_detail": "Hair",
    "clothing_fabric": "Clothing",
    "symmetry_geometry": "Symmetry",
    "edges_boundaries": "Edges",
    "depth_perspective": "Perspective",
    "teeth_mouth": "Teeth/Mouth",
    "jewelry_accessories": "Accessories",
    "overall_coherence": "Coherence",
}


def _get_font(size: int):
    """Try to load a system font, fall back to default."""
    font_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _get_font_bold(size: int):
    """Try to load a bold system font."""
    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return _get_font(size)


def _color_with_alpha(color: tuple, alpha: int) -> tuple:
    return color[:3] + (alpha,)


def _draw_arrow(draw, start, end, color, width=2):
    """Draw a line with an arrowhead at the end."""
    draw.line([start, end], fill=color, width=width)

    # Arrowhead
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return

    # Normalize
    udx = dx / length
    udy = dy / length

    # Arrow wings
    size = ARROW_HEAD_SIZE
    wing1 = (
        end[0] - size * udx + size * 0.5 * udy,
        end[1] - size * udy - size * 0.5 * udx,
    )
    wing2 = (
        end[0] - size * udx - size * 0.5 * udy,
        end[1] - size * udy + size * 0.5 * udx,
    )
    draw.polygon([end, wing1, wing2], fill=color)


def _collect_top_artifacts(detection_result: dict, max_count: int) -> list:
    """
    Extract the top N artifacts across all inspections,
    ranked by severity and confidence.
    """
    stages = detection_result.get("stages", {})
    inspections = stages.get("feature_inspections", [])

    all_artifacts = []

    for inspection in inspections:
        category = inspection.get("category", "unknown")
        confidence = inspection.get("confidence_ai", 0)
        artifacts = inspection.get("artifacts_detected", [])

        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("bbox"):
                bbox = artifact["bbox"]
                if len(bbox) == 4:
                    severity = artifact.get("severity", "minor")
                    sev_score = {"critical": 3, "moderate": 2, "minor": 1}.get(severity, 0)
                    all_artifacts.append({
                        "category": category,
                        "label": artifact.get("label", CATEGORY_LABELS.get(category, category)),
                        "description": artifact.get("description", ""),
                        "severity": severity,
                        "confidence": confidence,
                        "bbox_pct": bbox,
                        "sort_score": sev_score * 100 + confidence * 100,
                    })

    # Sort by severity first, then confidence
    all_artifacts.sort(key=lambda a: a["sort_score"], reverse=True)
    return all_artifacts[:max_count]


def annotate_image(
    image_path: str,
    detection_result: dict,
    output_path: str = None,
    max_annotations: int = MAX_ANNOTATIONS,
) -> str:
    """
    Draw clean annotations on the image: numbered dots with arrows
    pointing to labels on a right-side panel.

    Args:
        image_path: Path to the original image.
        detection_result: Full result from detect_ai_image().
        output_path: Where to save. If None, auto-generated.
        max_annotations: Max number of visual annotations (default 5).

    Returns:
        Path to the saved annotated image.
    """
    # Load image
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    orig_w, orig_h = img.size

    # Create a larger canvas with right margin for labels + bottom for verdict
    canvas_w = orig_w + MARGIN_RIGHT
    canvas_h = orig_h + MARGIN_BOTTOM
    canvas = Image.new("RGB", (canvas_w, canvas_h), (24, 24, 32))

    # Paste original image
    canvas.paste(img, (0, 0))

    draw = ImageDraw.Draw(canvas, "RGBA")

    # Fonts
    font_title = _get_font_bold(15)
    font_label = _get_font_bold(13)
    font_desc = _get_font(11)
    font_number = _get_font_bold(11)
    font_verdict = _get_font_bold(16)
    font_small = _get_font(11)

    # Collect top artifacts
    top_artifacts = _collect_top_artifacts(detection_result, max_annotations)

    # ── Draw the right panel header ──
    panel_x = orig_w + 12
    panel_y = 12
    draw.text((panel_x, panel_y), "AI ARTIFACTS", fill=(255, 255, 255), font=font_title)
    panel_y += 24

    # Thin separator line
    draw.line([(panel_x, panel_y), (canvas_w - 12, panel_y)], fill=(80, 80, 90), width=1)
    panel_y += 10

    # ── Draw annotations ──
    label_spacing = max(60, (orig_h - 60) // max(max_annotations, 1))

    for i, artifact in enumerate(top_artifacts):
        number = i + 1
        color = COLORS_BY_SEVERITY.get(artifact["severity"], (158, 158, 158))
        bbox = artifact["bbox_pct"]

        # Convert bbox % to pixel coords on original image
        try:
            x_min = int(float(bbox[0]) / 100 * orig_w)
            y_min = int(float(bbox[1]) / 100 * orig_h)
            x_max = int(float(bbox[2]) / 100 * orig_w)
            y_max = int(float(bbox[3]) / 100 * orig_h)
        except (ValueError, TypeError):
            continue

        # Center of the artifact region
        cx = (x_min + x_max) // 2
        cy = (y_min + y_max) // 2

        # Clamp to image
        cx = max(MARKER_RADIUS, min(cx, orig_w - MARKER_RADIUS))
        cy = max(MARKER_RADIUS, min(cy, orig_h - MARKER_RADIUS))

        # ── Draw marker dot on image ──
        # Outer ring
        draw.ellipse(
            [cx - MARKER_RADIUS, cy - MARKER_RADIUS,
             cx + MARKER_RADIUS, cy + MARKER_RADIUS],
            fill=_color_with_alpha(color, 200),
            outline=(255, 255, 255),
            width=2,
        )
        # Number inside the dot
        num_text = str(number)
        num_bbox = draw.textbbox((0, 0), num_text, font=font_number)
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        draw.text(
            (cx - num_w // 2, cy - num_h // 2 - 1),
            num_text,
            fill=(255, 255, 255),
            font=font_number,
        )

        # ── Draw small circle outline around the artifact area (subtle) ──
        artifact_radius = max(15, min((x_max - x_min) // 2, (y_max - y_min) // 2))
        draw.ellipse(
            [cx - artifact_radius, cy - artifact_radius,
             cx + artifact_radius, cy + artifact_radius],
            outline=_color_with_alpha(color, 120),
            width=2,
        )

        # ── Arrow from dot to right panel ──
        arrow_end_x = orig_w - 1
        arrow_end_y = panel_y + 8

        _draw_arrow(
            draw,
            (cx + MARKER_RADIUS + 2, cy),
            (arrow_end_x, arrow_end_y),
            color=_color_with_alpha(color, 160),
            width=2,
        )

        # ── Draw label on right panel ──
        # Number badge
        badge_r = 9
        badge_cx = panel_x + badge_r
        badge_cy = panel_y + badge_r - 1
        draw.ellipse(
            [badge_cx - badge_r, badge_cy - badge_r,
             badge_cx + badge_r, badge_cy + badge_r],
            fill=color,
        )
        draw.text(
            (badge_cx - num_w // 2, badge_cy - num_h // 2 - 1),
            num_text,
            fill=(255, 255, 255),
            font=font_number,
        )

        # Label text
        label_x = panel_x + badge_r * 2 + 8
        label_text = f"{artifact['label']}"
        conf_text = f" {artifact['confidence']:.0%}"
        draw.text((label_x, panel_y - 2), label_text, fill=(255, 255, 255), font=font_label)

        # Confidence next to label
        label_bbox = draw.textbbox((0, 0), label_text, font=font_label)
        label_w = label_bbox[2] - label_bbox[0]
        draw.text(
            (label_x + label_w + 4, panel_y - 1),
            conf_text,
            fill=color,
            font=font_small,
        )

        # Description (truncated)
        desc = artifact.get("description", "")
        if desc:
            max_desc_chars = 35
            short_desc = desc[:max_desc_chars] + ("..." if len(desc) > max_desc_chars else "")
            draw.text(
                (label_x, panel_y + 16),
                short_desc,
                fill=(180, 180, 190),
                font=font_desc,
            )

        # Severity tag
        sev = artifact["severity"]
        sev_text = f"[{sev.upper()}]"
        draw.text(
            (label_x, panel_y + 32),
            sev_text,
            fill=color,
            font=font_desc,
        )

        panel_y += label_spacing

    # ── If no artifacts had bbox, show a note ──
    if not top_artifacts:
        draw.text(
            (panel_x, panel_y),
            "No localized artifacts\nSee text output for details",
            fill=(140, 140, 150),
            font=font_desc,
        )

    # ── Draw verdict bar at bottom ──
    verdict = detection_result.get("verdict", "uncertain")
    confidence = detection_result.get("confidence", 0)
    verdict_color = VERDICT_COLORS.get(verdict, (158, 158, 158))
    verdict_text = VERDICT_LABELS.get(verdict, verdict)

    # Verdict background bar
    bar_y = orig_h
    draw.rectangle([0, bar_y, canvas_w, canvas_h], fill=verdict_color)

    # Verdict text centered
    full_verdict = f"{verdict_text}   |   {confidence:.0%} confidence"
    vt_bbox = draw.textbbox((0, 0), full_verdict, font=font_verdict)
    vt_w = vt_bbox[2] - vt_bbox[0]
    draw.text(
        ((canvas_w - vt_w) // 2, bar_y + (MARGIN_BOTTOM - (vt_bbox[3] - vt_bbox[1])) // 2),
        full_verdict,
        fill=(255, 255, 255),
        font=font_verdict,
    )

    # ── Save ──
    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_ai_analysis{p.suffix}")

    canvas.save(output_path, quality=95)
    print(f"Annotated image saved: {output_path}")
    print(f"   {len(top_artifacts)} key artifacts highlighted (top {max_annotations})")

    return output_path
