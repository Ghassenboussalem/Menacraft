# RT-1 Temporal Image Verifier (MenaCraft)

Fully automated tool for detecting temporal manipulation in images by finding when they first appeared online.

## The RT-1 Methodology

**Goal:** Find images indexed before their claimed event date to expose misinformation.

### Key Principles

1. **TinEye's "oldest" sort** - First crawl date detection
2. **Automated scraping** - No manual checking required
3. **Temporal gap analysis** - Calculate time between first appearance and claimed date
4. **Date Gap Rule** - Even 6 months destroys "happening today" claims

## Installation

```bash
pip install -r requirements.txt
```

## Setup

Get a free ImgBB API key (required for image upload):
```bash
# Get key at: https://api.imgbb.com/
set IMGBB_API_KEY=your_key_here
```

## Usage

### Fully Automated Verification

Upload an image and automatically find when it was first published:

```bash
python fully_automated.py "image.jpg"
```

With a claimed date to check for temporal manipulation:

```bash
python fully_automated.py "image.jpg" "2024-04-04"
```

### Batch Processing

Verify multiple images from a CSV file:

```bash
python batch_verify.py images.csv
```

CSV format:
```csv
image_url,claimed_date,description
"path/to/image1.jpg","2024-03-15","Event 1"
"path/to/image2.jpg","2024-01-20","Event 2"
```

## How It Works

1. Uploads image to temporary hosting (ImgBB)
2. Automatically scrapes TinEye for the first indexed date
3. Calculates temporal gap between first appearance and claimed date
4. Provides verdict and saves detailed report

## Verdict Criteria

- **🚨 FAKE** - Image predates claimed event (negative gap)
- **🚨 HIGHLY SUSPICIOUS** - Gap ≥ 1 year
- **⚠️ SUSPICIOUS** - Gap ≥ 6 months
- **⚠️ QUESTIONABLE** - Gap > 7 days
- **✓ PLAUSIBLE** - Minimal or no gap
- **✓ LIKELY RECENT** - No matches found in TinEye (82.8B images)

## Example Output

```
============================================================
🤖 FULLY AUTOMATED RT-1 VERIFICATION
============================================================
Image: photo.jpg
Size: 845.7 KB

📤 Uploading image...
✓ Uploaded: https://i.ibb.co/xxxxx/image.png

🔍 Scraping TinEye (automated)...
✓ Found 28 total matches
  First indexed: November 27, 2014

============================================================
📊 AUTOMATED RESULTS
============================================================

Total Matches: 28
First Published: 2014-11-27
Oldest Source: TinEye Index

Image Age: 4146 days (11.4 years)

Claimed Date: 2024-04-04
Temporal Gap: 3416 days (9.4 years)

🚨 HIGHLY SUSPICIOUS - Multi-year gap

============================================================

💾 Report saved: report_20240404_123456.txt
```

## Files

- `fully_automated.py` - Main automated verification tool
- `batch_verify.py` - Batch processing for multiple images
- `requirements.txt` - Python dependencies
- `README.md` - This file
- `setup_apis.md` - API setup guide

## Requirements

- Python 3.7+
- Chrome browser (for Selenium)
- ImgBB API key (free)

## Limitations

- Requires publicly accessible image URLs or local files
- TinEye coverage varies by region/time
- Some images may not be archived
- Scraping depends on TinEye's page structure
