# Instagram Post & Account Analyzer

Analyze Instagram posts with account information and bot detection using Serper API.

## Features

- Load Instagram post data from JSON
- Scrape account information using Serper API
- Merge post and account data
- Run rule-based bot detection analysis
- Save complete results with bot score and classification

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Serper API key in `.env`:
```bash
SERPER_API_KEY=your_api_key_here
```

## Usage

```bash
python analyze_post_with_account.py <post_json_file>
```

### Example

```bash
python analyze_post_with_account.py lovable_dev_post.json
```

### Input JSON Format

```json
{
  "idx": 5,
  "id": "post-id",
  "post_url": "https://www.instagram.com/p/...",
  "username": "account_username",
  "caption": "Post caption...",
  "likes_count": "14K",
  "comments_count": "109",
  "hashtags": ["#tag1", "#tag2"],
  "post_date": "2026-04-03 20:30:05+00",
  "post_type": "image"
}
```

### Output

The script generates a `<filename>_analyzed.json` file containing:

- Original post data
- Scraped account information (followers, following, posts, bio, etc.)
- Bot detection analysis with:
  - Bot score (0-100)
  - Classification (real/inconclusive/bot)
  - Risk level (LOW/MEDIUM/HIGH)
  - Detailed features
  - Suspicious flags

## Files

- `analyze_post_with_account.py` - Main analyzer script
- `instagram_scraper.py` - Serper API scraper
- `bot_detection_pipeline.py` - Bot detection pipeline
- `feature_extraction.py` - Feature extraction from account data
- `scoring_engine.py` - Rule-based scoring engine
- `network_analysis.py` - Network analysis utilities
- `utils.py` - Helper utilities
- `requirements.txt` - Python dependencies

## Bot Detection

The analyzer uses rule-based scoring to detect bot accounts based on:

- Profile signals (username, bio, profile picture)
- Activity patterns (posting frequency, intervals)
- Engagement metrics (followers, following ratio)
- Content signals (hashtags, locations, URLs)

Bot scores range from 0-100:
- 0-30: Real account (LOW RISK)
- 31-69: Inconclusive (MEDIUM RISK)
- 70-100: Bot account (HIGH RISK)
