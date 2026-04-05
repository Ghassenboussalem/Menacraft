"""
AI Image Detection Pipeline — Core Detector

Uses Groq's vision model (Llama 4 Scout) in a multi-stage pipeline:
  1. Scene Analysis      → Understand what's in the image
  2. Feature ID          → Decide what AI-tells to look for
  3. Feature Inspection  → Deep-check each feature
  4. Final Verdict       → Aggregate into confidence score
"""

import os
import json
import base64
import time
import re
from pathlib import Path
from io import BytesIO

from groq import Groq
from dotenv import load_dotenv

from prompts import (
    SCENE_ANALYSIS_PROMPT,
    FEATURE_IDENTIFICATION_PROMPT,
    FEATURE_INSPECTION_PROMPT,
    FINAL_VERDICT_PROMPT,
    INSPECTION_GUIDELINES,
)

# Load .env from this directory
load_dotenv(Path(__file__).parent / ".env")

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_FEATURES_TO_INSPECT = 8  # cap how many features we deep-check (cost control)
MAX_RETRIES = 2


def _init_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to ai_detection/.env")
    import httpx
    timeout = httpx.Timeout(120.0, connect=10.0, read=90.0, write=10.0)
    return Groq(api_key=api_key, timeout=timeout)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
MAX_IMAGE_DIMENSION = 1280  # Groq rejects overly large images
JPEG_QUALITY = 85


def _resize_image_bytes(image_bytes: bytes) -> bytes:
    """Resize image if it exceeds MAX_IMAGE_DIMENSION, always output JPEG."""
    from PIL import Image

    img = Image.open(BytesIO(image_bytes))

    # Convert RGBA/P/palette to RGB for JPEG output
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if too large
    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIMENSION:
        ratio = MAX_IMAGE_DIMENSION / max(w, h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        print(f"   📐 Resized image: {w}x{h} → {new_w}x{new_h}")

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def image_to_data_url(image_path: str) -> str:
    """Convert a local image file to a resized base64 data URL (JPEG)."""
    with open(image_path, "rb") as f:
        raw_bytes = f.read()

    resized = _resize_image_bytes(raw_bytes)
    b64 = base64.b64encode(resized).decode("utf-8")
    size_kb = len(resized) / 1024
    print(f"   📦 Image payload: {size_kb:.0f} KB")
    return f"data:image/jpeg;base64,{b64}"


def image_bytes_to_data_url(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Convert raw image bytes to a resized base64 data URL (JPEG)."""
    resized = _resize_image_bytes(image_bytes)
    b64 = base64.b64encode(resized).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _parse_json_response(text: str) -> dict:
    """Robustly extract JSON from model response (may contain markdown fences)."""
    # Try direct parse
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` or ``` ... ```
    patterns = [
        r"```json\s*\n(.*?)```",
        r"```\s*\n(.*?)```",
        r"\{.*\}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1) if match.lastindex else match.group(0)
            try:
                return json.loads(candidate.strip())
            except json.JSONDecodeError:
                continue

    # Last resort — return raw text wrapped
    return {"raw_response": text, "parse_error": True}


OLLAMA_BASE = "http://localhost:11434/api/generate"
OLLAMA_VISION_MODEL = "llava:latest"
OLLAMA_TEXT_MODEL = "llama3.2:latest"


def _is_rate_limit(e: Exception) -> bool:
    return "ratelimit" in type(e).__name__.lower() or "rate_limit" in str(e).lower() or "429" in str(e)


def _ollama_vision(prompt: str, image_data_url: str) -> dict:
    """Call Ollama LLaVA with an image. Returns parsed JSON dict."""
    import base64 as _b64
    # Extract base64 bytes from data URL
    if image_data_url.startswith("data:"):
        b64_data = image_data_url.split(",", 1)[1]
    else:
        # It's a URL — download and encode
        r = __import__("requests").get(image_data_url, timeout=15)
        b64_data = _b64.b64encode(r.content).decode("utf-8")

    payload = {"model": OLLAMA_VISION_MODEL, "prompt": prompt, "stream": False, "images": [b64_data]}
    r = __import__("requests").post(OLLAMA_BASE, json=payload, timeout=120)
    r.raise_for_status()
    return _parse_json_response(r.json().get("response", ""))


def _ollama_text(prompt: str) -> dict:
    """Call Ollama text model. Returns parsed JSON dict."""
    payload = {"model": OLLAMA_TEXT_MODEL, "prompt": prompt, "stream": False}
    r = __import__("requests").post(OLLAMA_BASE, json=payload, timeout=120)
    r.raise_for_status()
    return _parse_json_response(r.json().get("response", ""))


def _call_vision(client: Groq, prompt: str, image_data_url: str) -> dict:
    """Try Groq; return empty result on rate limit (LLaVA fallback removed — causes GPU OOM)."""
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }],
            temperature=0.3,
            max_completion_tokens=2048,
            top_p=1,
        )
        return _parse_json_response(completion.choices[0].message.content)
    except Exception as e:
        print(f"       Groq vision failed ({type(e).__name__}) — skipping stage")
        return {"skipped": True, "confidence_ai": 0, "artifacts_detected": [], "findings": "", "reasoning": "Groq unavailable"}


def _call_text(client: Groq, prompt: str) -> dict:
    """Try Groq; fall back to Ollama llama3.2 on rate limit (text-only, no GPU OOM risk)."""
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_completion_tokens=2048,
            top_p=1,
        )
        return _parse_json_response(completion.choices[0].message.content)
    except Exception as e:
        print(f"       Groq text failed ({type(e).__name__}) — falling back to Ollama llama3.2")
        return _ollama_text(prompt)


# ──────────────────────────────────────────────
# Pipeline Stages
# ──────────────────────────────────────────────
def stage_1_scene_analysis(client: Groq, image_data_url: str) -> dict:
    """Stage 1: Understand what's in the image."""
    print("🔍 Stage 1: Analyzing scene...")
    result = _call_vision(client, SCENE_ANALYSIS_PROMPT, image_data_url)
    print(f"   Subject: {result.get('subject', 'unknown')}")
    print(f"   Style: {result.get('style', 'unknown')}")
    return result


def stage_2_feature_identification(client: Groq, scene_analysis: dict) -> list:
    """Stage 2: Decide which features to inspect based on scene content."""
    print("🧠 Stage 2: Identifying features to inspect...")
    prompt = FEATURE_IDENTIFICATION_PROMPT.format(
        scene_analysis=json.dumps(scene_analysis, indent=2)
    )
    result = _call_text(client, prompt)
    features = result.get("features_to_check", [])

    # Sort by priority and cap
    priority_order = {"high": 0, "medium": 1, "low": 2}
    features.sort(key=lambda f: priority_order.get(f.get("priority", "low"), 2))
    features = features[:MAX_FEATURES_TO_INSPECT]

    print(f"   Will inspect {len(features)} features:")
    for f in features:
        print(f"    • [{f.get('priority', '?')}] {f.get('category', '?')}")
    return features


def stage_3_feature_inspection(
    client: Groq,
    image_data_url: str,
    scene_analysis: dict,
    features: list,
) -> list:
    """Stage 3: Deep-inspect each identified feature."""
    print("🔬 Stage 3: Inspecting features...")
    results = []
    scene_summary = (
        f"{scene_analysis.get('subject', 'Image')} — "
        f"{scene_analysis.get('setting', '')} — "
        f"{scene_analysis.get('style', '')}"
    )

    for i, feat in enumerate(features, 1):
        category = feat.get("category", "overall_coherence")
        reason = feat.get("reason", "General inspection")
        guidelines = INSPECTION_GUIDELINES.get(
            category, INSPECTION_GUIDELINES["overall_coherence"]
        )

        prompt = FEATURE_INSPECTION_PROMPT.format(
            category=category,
            scene_summary=scene_summary,
            reason=reason,
            inspection_guidelines=guidelines,
        )

        print(f"   [{i}/{len(features)}] Inspecting: {category}...")
        result = _call_vision(client, prompt, image_data_url)
        results.append(result)

        confidence = result.get("confidence_ai", 0)
        artifacts = result.get("artifacts_detected", [])
        print(f"       AI confidence: {confidence:.0%} | Artifacts: {len(artifacts)}")

        # Small pause between features to avoid Groq burst limit
        if i < len(features):
            time.sleep(1)

    return results


def stage_4_final_verdict(
    client: Groq,
    scene_analysis: dict,
    feature_inspections: list,
) -> dict:
    """Stage 4: Aggregate all findings into a final verdict."""
    print("⚖️  Stage 4: Computing final verdict...")
    prompt = FINAL_VERDICT_PROMPT.format(
        scene_analysis=json.dumps(scene_analysis, indent=2),
        feature_inspections=json.dumps(feature_inspections, indent=2),
    )
    result = _call_text(client, prompt)
    verdict = result.get("verdict", "uncertain")
    confidence = result.get("confidence", 0)
    print(f"   Verdict: {verdict} ({confidence:.0%} confidence)")
    return result


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────
def detect_ai_image(image_source: str | bytes, mime: str = "image/jpeg") -> dict:
    """
    Run the full AI detection pipeline on an image.

    Args:
        image_source: Either a file path (str) or raw image bytes.
        mime: MIME type if providing bytes. Ignored for file paths.

    Returns:
        dict with keys: verdict, confidence, summary, key_findings,
                        overall_reasoning, stages (raw stage data)
    """
    client = _init_client()

    # Prepare image data URL
    if isinstance(image_source, str):
        if image_source.startswith("data:"):
            image_data_url = image_source
        elif image_source.startswith("http"):
            image_data_url = image_source
        else:
            image_data_url = image_to_data_url(image_source)
    else:
        image_data_url = image_bytes_to_data_url(image_source, mime)

    start = time.time()

    # Stage 1: Scene Analysis
    scene = stage_1_scene_analysis(client, image_data_url)

    # Stage 2: Feature Identification
    features = stage_2_feature_identification(client, scene)

    # Stage 3: Feature Inspection
    inspections = stage_3_feature_inspection(client, image_data_url, scene, features)

    # Stage 4: Final Verdict
    verdict = stage_4_final_verdict(client, scene, inspections)

    elapsed = time.time() - start
    print(f"\n✅ Analysis complete in {elapsed:.1f}s")

    # Combine everything
    return {
        "verdict": verdict.get("verdict", "uncertain"),
        "confidence": verdict.get("confidence", 0),
        "summary": verdict.get("summary", ""),
        "key_findings": verdict.get("key_findings", []),
        "overall_reasoning": verdict.get("overall_reasoning", ""),
        "stages": {
            "scene_analysis": scene,
            "features_identified": features,
            "feature_inspections": inspections,
            "final_verdict": verdict,
        },
        "elapsed_seconds": round(elapsed, 1),
    }


# ──────────────────────────────────────────────
# Quick confidence summary (for API responses)
# ──────────────────────────────────────────────
def get_quick_summary(result: dict) -> dict:
    """Return a minimal summary for API consumers."""
    return {
        "verdict": result["verdict"],
        "confidence": result["confidence"],
        "summary": result["summary"],
        "key_findings": [
            {
                "feature": f.get("feature", ""),
                "finding": f.get("finding", ""),
                "severity": f.get("severity", "none"),
            }
            for f in result.get("key_findings", [])
            if f.get("severity") in ("critical", "moderate")
        ],
        "elapsed_seconds": result.get("elapsed_seconds", 0),
    }
