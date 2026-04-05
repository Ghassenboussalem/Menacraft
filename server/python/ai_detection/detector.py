"""
AI Image Detection Pipeline — Core Detector

Uses Groq's vision model (Llama 4 Scout) in a multi-stage pipeline:
  1. Scene Analysis      -> Understand what's in the image
  2. Feature ID          -> Decide what AI-tells to look for
  3. Feature Inspection  -> Deep-check each feature
  4. Final Verdict       -> Aggregate into confidence score

Debug logging enabled throughout. Rate-limit aware with retries.
"""

import os
import json
import base64
import time
import re
from pathlib import Path
from io import BytesIO
from datetime import datetime

from groq import Groq
from dotenv import load_dotenv

from .prompts import (
    SCENE_ANALYSIS_PROMPT,
    FEATURE_IDENTIFICATION_PROMPT,
    FEATURE_INSPECTION_PROMPT,
    FINAL_VERDICT_PROMPT,
    INSPECTION_GUIDELINES,
)

# Load .env from server/python/ (parent of ai_detection/)
_ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(_ENV_PATH)

# Also try ai_detection-level .env as fallback
_LOCAL_ENV = Path(__file__).parent / ".env"
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=False)

# ──────────────────────────────────────────────
# Config
# ────────���─────────────────────────────────────
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_FEATURES_TO_INSPECT = 8  # cap how many features we deep-check (cost control)
MAX_RETRIES = 2
RATE_LIMIT_WAIT = 5          # seconds to wait on rate limit before retry
INTER_FEATURE_DELAY = 1.5    # seconds between feature inspections (Groq burst limit)

# Debug flag — set DEBUG_AI_DETECTION=1 in .env for verbose output
DEBUG = os.getenv("DEBUG_AI_DETECTION", "1") == "1"


def _debug(msg: str, indent: int = 0):
    """Print debug message with timestamp if DEBUG is on."""
    if DEBUG:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = "  " * indent
        print(f"   [{ts}] {prefix}{msg}", flush=True)


def _init_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to server/python/.env")
    _debug(f"Groq client init — key ends with ...{api_key[-6:]}")
    import httpx
    timeout = httpx.Timeout(120.0, connect=10.0, read=90.0, write=10.0)
    return Groq(api_key=api_key, timeout=timeout)


# ──────���───────────────────────���───────────────
# Helpers
# ────────────────────────────────��─────────────
MAX_IMAGE_DIMENSION = 1280  # Groq rejects overly large images
JPEG_QUALITY = 85


def _resize_image_bytes(image_bytes: bytes) -> bytes:
    """Resize image if it exceeds MAX_IMAGE_DIMENSION, always output JPEG."""
    from PIL import Image

    img = Image.open(BytesIO(image_bytes))
    _debug(f"Image opened: {img.size[0]}x{img.size[1]}, mode={img.mode}")

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
        _debug(f"Resized: {w}x{h} -> {new_w}x{new_h}")

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    result = buf.getvalue()
    _debug(f"JPEG payload: {len(result) / 1024:.0f} KB")
    return result


def image_to_data_url(image_path: str) -> str:
    """Convert a local image file to a resized base64 data URL (JPEG)."""
    _debug(f"Loading image: {image_path}")
    with open(image_path, "rb") as f:
        raw_bytes = f.read()
    _debug(f"Raw file size: {len(raw_bytes) / 1024:.0f} KB")

    resized = _resize_image_bytes(raw_bytes)
    b64 = base64.b64encode(resized).decode("utf-8")
    size_kb = len(resized) / 1024
    print(f"   Image payload: {size_kb:.0f} KB")
    return f"data:image/jpeg;base64,{b64}"


def image_bytes_to_data_url(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Convert raw image bytes to a resized base64 data URL (JPEG)."""
    resized = _resize_image_bytes(image_bytes)
    b64 = base64.b64encode(resized).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _parse_json_response(text: str) -> dict:
    """Robustly extract JSON from model response (may contain markdown fences)."""
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
    _debug(f"JSON parse failed, raw response: {text[:200]}...")
    return {"raw_response": text, "parse_error": True}


OLLAMA_BASE = "http://localhost:11434/api/generate"
OLLAMA_VISION_MODEL = "llava:latest"
OLLAMA_TEXT_MODEL = "llama3.2:latest"


def _is_rate_limit(e: Exception) -> bool:
    """Check if the exception is a Groq rate limit error."""
    name_check = "ratelimit" in type(e).__name__.lower()
    str_check = "rate_limit" in str(e).lower()
    code_check = "429" in str(e)
    result = name_check or str_check or code_check
    if result:
        _debug(f"Rate limit detected: {type(e).__name__}: {str(e)[:150]}")
    return result


def _ollama_text(prompt: str) -> dict:
    """Call Ollama text model as fallback. Returns parsed JSON dict."""
    _debug("Falling back to Ollama llama3.2 (text)")
    payload = {"model": OLLAMA_TEXT_MODEL, "prompt": prompt, "stream": False}
    r = __import__("requests").post(OLLAMA_BASE, json=payload, timeout=120)
    r.raise_for_status()
    return _parse_json_response(r.json().get("response", ""))


def _call_vision(client: Groq, prompt: str, image_data_url: str) -> dict:
    """
    Call Groq vision model with retry on rate limit.
    Returns empty result on persistent failure (pipeline continues).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _debug(f"Groq vision call (attempt {attempt}/{MAX_RETRIES})")
            t0 = time.time()
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
            elapsed = time.time() - t0
            _debug(f"Groq vision response in {elapsed:.1f}s")
            result = _parse_json_response(completion.choices[0].message.content)
            _debug(f"Parsed response keys: {list(result.keys())}")
            return result
        except Exception as e:
            _debug(f"Groq vision error (attempt {attempt}): {type(e).__name__}: {str(e)[:200]}")
            if _is_rate_limit(e) and attempt < MAX_RETRIES:
                wait = RATE_LIMIT_WAIT * attempt
                _debug(f"Rate limited — waiting {wait}s before retry...")
                time.sleep(wait)
                continue
            # Non-rate-limit error or final attempt
            print(f"       Groq vision failed ({type(e).__name__}) — skipping stage")
            return {
                "skipped": True,
                "confidence_ai": 0,
                "artifacts_detected": [],
                "findings": "",
                "reasoning": f"Groq unavailable: {type(e).__name__}",
            }


def _call_text(client: Groq, prompt: str) -> dict:
    """
    Call Groq text model with retry on rate limit.
    Falls back to Ollama llama3.2 on persistent failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _debug(f"Groq text call (attempt {attempt}/{MAX_RETRIES})")
            t0 = time.time()
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_completion_tokens=2048,
                top_p=1,
            )
            elapsed = time.time() - t0
            _debug(f"Groq text response in {elapsed:.1f}s")
            result = _parse_json_response(completion.choices[0].message.content)
            _debug(f"Parsed response keys: {list(result.keys())}")
            return result
        except Exception as e:
            _debug(f"Groq text error (attempt {attempt}): {type(e).__name__}: {str(e)[:200]}")
            if _is_rate_limit(e) and attempt < MAX_RETRIES:
                wait = RATE_LIMIT_WAIT * attempt
                _debug(f"Rate limited ��� waiting {wait}s before retry...")
                time.sleep(wait)
                continue
            print(f"       Groq text failed ({type(e).__name__}) — falling back to Ollama llama3.2")
            try:
                return _ollama_text(prompt)
            except Exception as fallback_err:
                _debug(f"Ollama fallback also failed: {fallback_err}")
                return {"error": str(e), "parse_error": True}


# ────────��────────────────────────��────────────
# Pipeline Stages
# ──────────────────────────────────────────────
def stage_1_scene_analysis(client: Groq, image_data_url: str) -> dict:
    """Stage 1: Understand what's in the image."""
    print("Stage 1: Analyzing scene...")
    _debug("Starting scene analysis (vision call)")
    result = _call_vision(client, SCENE_ANALYSIS_PROMPT, image_data_url)

    subject = result.get("subject", "unknown")
    style = result.get("style", "unknown")
    print(f"   Subject: {subject}")
    print(f"   Style: {style}")
    _debug(f"Scene: subject_type={result.get('subject_type')}, setting={result.get('setting')}, "
           f"elements={result.get('notable_elements', [])}")
    _debug(f"Flags: people={result.get('contains_people')}, text={result.get('contains_text')}, "
           f"reflections={result.get('contains_reflections')}")
    return result


def stage_2_feature_identification(client: Groq, scene_analysis: dict) -> list:
    """Stage 2: Decide which features to inspect based on scene content."""
    print("Stage 2: Identifying features to inspect...")
    _debug("Building feature identification prompt from scene analysis")
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
        print(f"    - [{f.get('priority', '?')}] {f.get('category', '?')}")
        _debug(f"  Reason: {f.get('reason', 'N/A')}", indent=1)
    return features


def stage_3_feature_inspection(
    client: Groq,
    image_data_url: str,
    scene_analysis: dict,
    features: list,
) -> list:
    """Stage 3: Deep-inspect each identified feature."""
    print("Stage 3: Inspecting features...")
    results = []
    scene_summary = (
        f"{scene_analysis.get('subject', 'Image')} — "
        f"{scene_analysis.get('setting', '')} — "
        f"{scene_analysis.get('style', '')}"
    )
    _debug(f"Scene summary for inspection: {scene_summary}")

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
        _debug(f"Feature {i}: {category} (priority={feat.get('priority')})")
        result = _call_vision(client, prompt, image_data_url)
        results.append(result)

        confidence = result.get("confidence_ai", 0)
        artifacts = result.get("artifacts_detected", [])
        skipped = result.get("skipped", False)

        if skipped:
            print(f"       SKIPPED (Groq unavailable)")
            _debug(f"Feature {category} skipped: {result.get('reasoning', 'unknown')}")
        else:
            print(f"       AI confidence: {confidence:.0%} | Artifacts: {len(artifacts)}")
            _debug(f"Feature {category}: confidence={confidence:.2f}, artifacts={len(artifacts)}")
            for j, art in enumerate(artifacts):
                _debug(f"  Artifact {j+1}: [{art.get('severity', '?')}] {art.get('label', '?')} "
                       f"bbox={art.get('bbox', 'none')}", indent=1)

        # Pause between features to respect Groq burst rate limit
        if i < len(features):
            _debug(f"Sleeping {INTER_FEATURE_DELAY}s between features (rate limit)")
            time.sleep(INTER_FEATURE_DELAY)

    return results


def stage_4_final_verdict(
    client: Groq,
    scene_analysis: dict,
    feature_inspections: list,
) -> dict:
    """Stage 4: Aggregate all findings into a final verdict."""
    print("Stage 4: Computing final verdict...")
    _debug(f"Aggregating {len(feature_inspections)} feature inspections")

    # Count non-skipped inspections
    active = [f for f in feature_inspections if not f.get("skipped")]
    skipped = len(feature_inspections) - len(active)
    _debug(f"Active inspections: {len(active)}, skipped: {skipped}")

    if active:
        avg_conf = sum(f.get("confidence_ai", 0) for f in active) / len(active)
        _debug(f"Average AI confidence across active features: {avg_conf:.2f}")

    prompt = FINAL_VERDICT_PROMPT.format(
        scene_analysis=json.dumps(scene_analysis, indent=2),
        feature_inspections=json.dumps(feature_inspections, indent=2),
    )
    result = _call_text(client, prompt)
    verdict = result.get("verdict", "uncertain")
    confidence = result.get("confidence", 0)
    print(f"   Verdict: {verdict} ({confidence:.0%} confidence)")
    _debug(f"Final verdict: {verdict}, confidence={confidence:.4f}")
    _debug(f"Summary: {result.get('summary', 'N/A')[:200]}")
    _debug(f"Key findings: {len(result.get('key_findings', []))}")
    return result


# ───���─────────────────��────────────────────────
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
    _debug("=" * 60)
    _debug("STARTING AI DETECTION PIPELINE")
    _debug("=" * 60)

    client = _init_client()

    # Prepare image data URL
    if isinstance(image_source, str):
        if image_source.startswith("data:"):
            _debug("Input: data URL")
            image_data_url = image_source
        elif image_source.startswith("http"):
            _debug(f"Input: URL ({image_source[:80]}...)")
            image_data_url = image_source
        else:
            _debug(f"Input: local file ({image_source})")
            image_data_url = image_to_data_url(image_source)
    else:
        _debug(f"Input: raw bytes ({len(image_source)} bytes)")
        image_data_url = image_bytes_to_data_url(image_source, mime)

    start = time.time()

    # Stage 1: Scene Analysis
    _debug("-" * 40)
    scene = stage_1_scene_analysis(client, image_data_url)
    _debug(f"Stage 1 done in {time.time() - start:.1f}s")

    # Stage 2: Feature Identification
    _debug("-" * 40)
    t2 = time.time()
    features = stage_2_feature_identification(client, scene)
    _debug(f"Stage 2 done in {time.time() - t2:.1f}s")

    # Stage 3: Feature Inspection
    _debug("-" * 40)
    t3 = time.time()
    inspections = stage_3_feature_inspection(client, image_data_url, scene, features)
    _debug(f"Stage 3 done in {time.time() - t3:.1f}s")

    # Stage 4: Final Verdict
    _debug("-" * 40)
    t4 = time.time()
    verdict = stage_4_final_verdict(client, scene, inspections)
    _debug(f"Stage 4 done in {time.time() - t4:.1f}s")

    elapsed = time.time() - start
    print(f"\n   Analysis complete in {elapsed:.1f}s")
    _debug(f"PIPELINE COMPLETE — total time: {elapsed:.1f}s")
    _debug("=" * 60)

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


# ────────────────────────────────────���─────────
# Quick confidence summary (for API responses)
# ───────────────���──────────────────────────────
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
