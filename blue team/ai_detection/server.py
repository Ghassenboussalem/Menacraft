"""
Flask API server for the AI Image Detection pipeline.

Endpoints:
  POST /detect           - Full combined analysis (classifier + pipeline)
  POST /detect/quick     - Quick classifier-only analysis
  POST /detect/annotated - Full analysis, returns annotated image
  GET  /health           - Health check
"""

import os
import base64
import tempfile
from pathlib import Path
from io import BytesIO

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

from combined_detector import CombinedDetector

# Load env
load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__)
CORS(app)

# Singleton detector
_detector = None


def get_detector():
    global _detector
    if _detector is None:
        _detector = CombinedDetector()
    return _detector


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    det = get_detector()
    return jsonify({
        "status": "ok",
        "service": "ai-image-detector",
        "classifier_available": det.classifier.available,
    })


@app.route("/detect", methods=["POST"])
def detect():
    """
    Full combined analysis — classifier + pipeline.

    Accepts:
      - multipart/form-data with 'image' file
      - JSON with 'image_url' (public URL)
      - JSON with 'image_base64'
    """
    try:
        image_source, tmp_path = _extract_image(request)
        det = get_detector()
        result = det.detect(image_source, annotate=False)
        _cleanup(tmp_path)
        return jsonify({"success": True, "result": result})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@app.route("/detect/quick", methods=["POST"])
def detect_quick():
    """Quick classifier-only analysis (fast, ~1 sec)."""
    try:
        image_source, tmp_path = _extract_image(request)
        det = get_detector()
        result = det.detect_quick(image_source)
        _cleanup(tmp_path)
        return jsonify({"success": True, "result": result})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@app.route("/detect/annotated", methods=["POST"])
def detect_annotated():
    """
    Full analysis + returns annotated image as JPEG.
    The JSON result is in the X-Detection-Result header.
    """
    try:
        image_source, tmp_path = _extract_image(request)
        det = get_detector()

        # Create temp output for annotated image
        out_fd, out_path = tempfile.mkstemp(suffix=".jpg")
        os.close(out_fd)

        result = det.detect(image_source, annotate=True, output_path=out_path)
        _cleanup(tmp_path)

        if os.path.exists(out_path):
            # Put JSON result in header
            import json
            response = send_file(
                out_path,
                mimetype="image/jpeg",
                as_attachment=False,
                download_name="ai_analysis.jpg",
            )
            # Attach result as header (truncated for header safety)
            summary = {
                "verdict": result.get("verdict"),
                "confidence": result.get("confidence"),
                "method": result.get("method"),
                "scores": result.get("scores"),
            }
            response.headers["X-Detection-Result"] = json.dumps(summary)
            return response
        else:
            return jsonify({"success": True, "result": result})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _extract_image(req):
    """
    Extract image from request. Returns (image_source, tmp_path).
    tmp_path is set if we saved to a temp file (for classifier).
    """
    tmp_path = None

    # Option 1: File upload
    if "image" in req.files:
        file = req.files["image"]
        if file.filename == "":
            raise ValueError("Empty file uploaded")
        # Save to temp file so classifier can read it
        fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        file.save(tmp_path)
        return tmp_path, tmp_path

    # Option 2/3: JSON body
    data = req.get_json(silent=True)
    if data:
        if "image_url" in data:
            url = data["image_url"]
            if url.startswith("http") or url.startswith("data:"):
                return url, None
            raise ValueError("Invalid image_url")

        if "image_base64" in data:
            b64 = data["image_base64"]
            mime = data.get("mime_type", "image/jpeg")
            # Save to temp for classifier
            image_bytes = base64.b64decode(b64)
            fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(image_bytes)
            return tmp_path, tmp_path

    raise ValueError(
        "No image provided. Send 'image' file, 'image_url', or 'image_base64'."
    )


def _cleanup(tmp_path):
    """Remove temp file if it exists."""
    if tmp_path and os.path.exists(tmp_path):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"AI Image Detector API on http://localhost:{port}")
    print(f"  POST /detect           Full analysis")
    print(f"  POST /detect/quick     Classifier only")
    print(f"  POST /detect/annotated Full + annotated image")
    print(f"  GET  /health           Health check")
    app.run(host="0.0.0.0", port=port, debug=True)
