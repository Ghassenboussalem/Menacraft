# AI Image Detector

A combined AI image detection system that uses **two approaches** for better accuracy:

1. **MobileViT Classifier** — Fast binary AI/Real prediction (~1 sec)
2. **Groq Vision Pipeline** — Multi-stage analysis with explainable findings (~20 sec)

The final score is a weighted combination: **30% classifier + 70% pipeline**.

---

## Quick Start

```bash
cd ai_detection

# Install core dependencies
pip install -r requirements.txt

# Set your Groq API key
cp .env.example .env
# Edit .env → GROQ_API_KEY=gsk_your_key_here

# Test on an image
python test_image.py path/to/image.jpg --verbose
```

### Enable the MobileViT classifier (optional)

The classifier adds a fast binary score. It requires PyTorch (~2GB download):

```bash
pip install torch torchvision transformers
```

The trained model is included at `models/mobilevit_best.pth`. If torch is not installed, the detector automatically falls back to pipeline-only mode.

---

## How It Works

```
Image Input
    |
    +---> [MobileViT Classifier] ---> AI probability (0-1)     FAST, ~1 sec
    |
    +---> [Groq Vision Pipeline] ---> Detailed findings + bbox  DETAILED, ~20 sec
    |         |
    |         +-- Stage 1: Scene Analysis
    |         +-- Stage 2: Feature Identification
    |         +-- Stage 3: Feature Inspection (with bounding boxes)
    |         +-- Stage 4: Stage Verdict
    |
    +---> [Final Combiner] ---> Weighted verdict + annotated image
              |
              +-- MobileViT weight: 30%
              +-- Groq Pipeline weight: 70%
```

### Verdicts

| Score Range | Verdict |
|------------|---------|
| >= 70% | `likely_ai_generated` |
| 45-70% | `possibly_ai_generated` |
| 25-45% | `uncertain` |
| < 25% | `likely_authentic` |

### Annotated Image Output

The detector generates an annotated image with:
- Numbered dots on detected artifact regions
- Arrows pointing to a label panel on the right
- Verdict banner at the bottom
- Only top 5 most important findings shown visually

---

## CLI Usage

```bash
# Basic analysis (generates annotated image automatically)
python test_image.py photo.jpg

# Verbose — all stage details
python test_image.py photo.jpg --verbose

# JSON output
python test_image.py photo.jpg --json

# Skip annotated image
python test_image.py photo.jpg --no-annotate

# Custom output path for annotation
python test_image.py photo.jpg -o result.jpg
```

---

## API Server

```bash
python server.py
# Running on http://localhost:5050
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check + classifier status |
| `POST` | `/detect` | Full combined analysis (JSON response) |
| `POST` | `/detect/quick` | Classifier-only (fast, ~1 sec) |
| `POST` | `/detect/annotated` | Full analysis, returns annotated JPEG |

### Request formats

```bash
# File upload
curl -X POST http://localhost:5050/detect -F "image=@photo.jpg"

# URL
curl -X POST http://localhost:5050/detect \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/photo.jpg"}'

# Base64
curl -X POST http://localhost:5050/detect \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "...", "mime_type": "image/jpeg"}'

# Get annotated image
curl -X POST http://localhost:5050/detect/annotated \
  -F "image=@photo.jpg" -o annotated.jpg
```

### Response format

```json
{
  "success": true,
  "result": {
    "verdict": "likely_ai_generated",
    "confidence": 0.72,
    "method": "combined",
    "scores": {
      "classifier_score": 0.87,
      "classifier_weight": 0.3,
      "pipeline_score": 0.65,
      "pipeline_weight": 0.7,
      "combined_score": 0.72
    },
    "summary": "The image shows several indicators of AI generation...",
    "key_findings": [
      {
        "feature": "skin_texture",
        "finding": "Overly smooth skin with no visible pores",
        "severity": "moderate"
      }
    ],
    "elapsed_seconds": 22.4
  }
}
```

---

## Integration into Main Project

### Step 1: Copy the folder

Copy the entire `ai_detection/` folder into your main project:

```
your_project/
  +-- ai_detection/          <-- Copy this entire folder
  |     +-- .env
  |     +-- combined_detector.py
  |     +-- detector.py
  |     +-- classifier.py
  |     +-- annotator.py
  |     +-- prompts.py
  |     +-- server.py
  |     +-- models/
  |     |     +-- mobilevit_best.pth
  |     +-- requirements.txt
  +-- your_other_files...
```

### Step 2: Install dependencies

```bash
pip install -r ai_detection/requirements.txt

# Optional: enable classifier
pip install torch torchvision transformers
```

### Step 3: Set your Groq API key

Create `ai_detection/.env`:
```
GROQ_API_KEY=gsk_your_key_here
```

### Step 4: Use in your code

**Option A — Import as module:**

```python
from ai_detection.combined_detector import combined_detect

# Full analysis
result = combined_detect("path/to/image.jpg")
print(result["verdict"])      # "likely_ai_generated"
print(result["confidence"])   # 0.72
print(result["annotated_image"])  # "path/to/image_ai_analysis.jpg"

# Quick classifier only
from ai_detection.combined_detector import get_detector
detector = get_detector()
quick = detector.detect_quick("path/to/image.jpg")
```

**Option B — Run as API server:**

```bash
python ai_detection/server.py
# Then call http://localhost:5050/detect from your app
```

**Option C — Call from JavaScript (Chrome extension):**

```javascript
// Start server: python ai_detection/server.py

async function checkImage(imageUrl) {
  const response = await fetch('http://localhost:5050/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_url: imageUrl })
  });
  const data = await response.json();

  if (data.success) {
    console.log('Verdict:', data.result.verdict);
    console.log('Confidence:', data.result.confidence);
    console.log('Findings:', data.result.key_findings);
  }
}
```

---

## File Structure

```
ai_detection/
+-- .env                     # GROQ_API_KEY (not committed)
+-- .env.example             # Template
+-- README.md                # This file
+-- requirements.txt         # Dependencies
+-- combined_detector.py     # MAIN ENTRY POINT
+-- detector.py              # Groq vision 4-stage pipeline
+-- classifier.py            # MobileViT classifier (optional)
+-- annotator.py             # Visual annotation engine
+-- prompts.py               # Pipeline prompts + guidelines
+-- server.py                # Flask API server
+-- test_image.py            # CLI test tool
+-- models/
    +-- mobilevit_best.pth   # Trained classifier (~20MB)
```

---

## Notes

- **Groq API key** is required. Get one at [console.groq.com](https://console.groq.com)
- **MobileViT classifier** is optional. Without it, only the Groq pipeline runs (still good results)
- **Large images** are auto-resized to 1280px before sending to Groq
- **Rate limits**: The pipeline makes 3-10 API calls per image. Groq free tier has rate limits
- Results are **guidance, not proof** — treat them as helpful indicators
