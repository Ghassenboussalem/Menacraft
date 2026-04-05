"""
Python microservice — seven real AI agents:
  POST /ocr-claim           — OCR + Claim Checker       (Groq Llama4 Scout Vision)
  POST /reverse-image       — Reverse Image Search      (TinEye via Selenium)
  POST /ai-detect           — Image Forensics AI        (Groq Llama4 + MobileViT)
  POST /bot-detect          — Bot Pattern Detector      (Serper + Feature Extraction + Scoring)
  POST /caption-alignment   — Caption-Image Alignment   (Groq Llama4 Scout Vision)
  POST /source-credibility  — Source Credibility        (Groq Llama4 Scout)
  POST /link-scan           — Link Scanner              (Groq Llama4 Scout)
  POST /text-content        — Text Content Analyzer     (OCR.space + Groq Llama4 Scout)
  GET  /health
"""

import os
import sys
import tempfile
import base64
import requests as req_lib
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load .env from this directory
load_dotenv(Path(__file__).parent / ".env")

# ai_detection is now a local package under server/python/ai_detection/

# Make red team bot detection modules importable
BOT_DETECTION_DIR = Path(__file__).parent.parent.parent / "red team" / "menacraft-main"
if str(BOT_DETECTION_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DETECTION_DIR))

app = Flask(__name__)

# ── helpers ────────────────────────────────────────────────────────────────

def download_image(url: str) -> str:
    """Download image from URL to a temp file. Returns local path."""
    ext = '.jpg'
    for fmt in ['.png', '.gif', '.webp', '.jpeg']:
        if fmt in url.lower():
            ext = fmt
            break
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        r = req_lib.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        r.raise_for_status()
        tmp.write(r.content)
        tmp.flush()
        return tmp.name
    finally:
        tmp.close()


# ── OCR + Claim Checker ────────────────────────────────────────────────────

GROQ_TEXT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

def _groq_chat(prompt: str, image_path: str = None) -> str:
    """Call Groq API for text (and optionally vision) with rate-limit retry. Returns raw text."""
    import base64 as _b64
    import time as _time
    from groq import Groq
    import httpx

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    timeout = httpx.Timeout(120.0, connect=10.0, read=90.0, write=10.0)
    client = Groq(api_key=api_key, timeout=timeout)

    if image_path:
        # Vision call
        with open(image_path, 'rb') as f:
            b64 = _b64.b64encode(f.read()).decode('utf-8')
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]
    else:
        content = prompt

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=GROQ_TEXT_MODEL,
                messages=[{"role": "user", "content": content}],
                temperature=0.3,
                max_completion_tokens=2048,
                top_p=1,
            )
            return completion.choices[0].message.content or ''
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate_limit" in err_str or "429" in str(e) or "ratelimit" in type(e).__name__.lower()
            if is_rate_limit and attempt < max_retries:
                wait = 5 * attempt
                print(f"   [groq] Rate limited (attempt {attempt}/{max_retries}), waiting {wait}s...")
                _time.sleep(wait)
                continue
            raise


def _ollama_chat(model: str, prompt: str, image_path: str = None) -> str:
    """Try Groq first; fall back to Ollama if Groq fails."""
    try:
        print(f"   [groq] Calling Groq ({GROQ_TEXT_MODEL.split('/')[-1]}) {'with image' if image_path else 'text-only'}...")
        result = _groq_chat(prompt, image_path)
        print(f"   [groq] Success — {len(result)} chars")
        return result
    except Exception as e:
        print(f"   [groq] Failed ({type(e).__name__}: {str(e)[:100]}), falling back to Ollama {model}...")

    # Ollama fallback
    import base64 as _b64
    payload = {'model': model, 'prompt': prompt, 'stream': False, 'keep_alive': 0}
    if image_path:
        with open(image_path, 'rb') as f:
            payload['images'] = [_b64.b64encode(f.read()).decode('utf-8')]

    resp = req_lib.post('http://localhost:11434/api/generate', json=payload, timeout=300)
    if not resp.ok:
        print(f"   [ollama] {model} returned {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()
    return resp.json().get('response', '')


UNIVERSAL_OCR_PROMPT = """You are a forensic image-caption verifier. Your ONLY job: determine whether the caption accurately represents what the image shows.

GROUND RULES:
• Describe ONLY what you directly observe. Never assume, infer, or fill in gaps.
• "I cannot verify this from the image" is always a valid answer.
• A video play button means you're seeing a single frame — score only what this frame shows.
• Screenshots, collages, memes, and overlaid text are all valid image types — adapt accordingly.

CAPTION:
\"\"\"{caption}\"\"\"

INSTRUCTIONS:

1) OBSERVE — Describe what the image actually contains. Be specific and factual.

2) DECOMPOSE — Break the caption into individual claims. For each, assign exactly one label:
   • VERIFIED — directly confirmed by visible evidence
   • UNVERIFIABLE — could be true, but nothing in the image proves or disproves it
   • CONTRADICTED — the image shows evidence against this
   • METADATA — hashtags, @mentions, CTAs, links (not factual claims)

3) DETECT INTENT — What type of content is this? (news, ad, meme, personal, political, satire, etc.)
   Flag any commercial indicators (brand mentions, #ad, #partner, affiliate links, promotional language).

4) REASON — In 2-4 sentences, explain your overall assessment. Address:
   • What proportion of core claims are verified vs unverifiable vs contradicted?
   • Does the image provide ANY supporting context, even indirect?
   • Are there structural red flags (emotional exploitation, viral bait, misleading framing)?

5) JUDGE — Apply these rules strictly:
   • Any CONTRADICTED core claim → cap at 45%
   • Zero VERIFIED claims + no supporting visual context → cap at 55%
   • Sponsored/ad content with unverifiable claims → cap at 60%
   • Multiple VERIFIED claims + no contradictions → 80%+

Respond ONLY with this JSON (no markdown, no preamble):
{{
  "visual_description": "what you directly observe in the image",
  "claims": [
    {{"text": "the claim", "status": "VERIFIED|UNVERIFIABLE|CONTRADICTED|METADATA", "evidence": "brief reason"}}
  ],
  "content_type": "news|ad|meme|personal|political|satire|promotional|informational|other",
  "commercial_signals": ["list of signals found, or empty array"],
  "manipulation_type": "NONE|FALSE_CONTEXT|EXAGGERATION|FABRICATION|OUT_OF_CONTEXT|EMOTIONAL_MANIPULATION|PROMOTIONAL_DISGUISE|SELECTIVE_FRAMING|SATIRE_AS_FACT|TEMPORAL_MISMATCH",
  "red_flags": ["list of concerns, or empty array"],
  "reasoning": "2-4 sentence explanation",
  "verdict": "CONSISTENT|PARTIAL|INCONSISTENT",
  "score": 0
}}"""


def _parse_universal_ocr(raw: str) -> dict:
    import json as _json, re as _re
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        cleaned = '\n'.join(cleaned.split('\n')[1:])
    if cleaned.endswith('```'):
        cleaned = '\n'.join(cleaned.split('\n')[:-1])
    cleaned = cleaned.strip()
    try:
        parsed = _json.loads(cleaned)
    except _json.JSONDecodeError:
        m = _re.search(r'\{[\s\S]*\}', cleaned)
        if m:
            try:
                parsed = _json.loads(m.group())
            except Exception:
                parsed = {}
        else:
            parsed = {}

    verdict = parsed.get('verdict', 'UNKNOWN')
    score = parsed.get('score', 0)
    # Map to legacy format expected by verifyService.js
    verdict_map = {'CONSISTENT': 'CONSISTENT', 'PARTIAL': 'PARTIAL', 'INCONSISTENT': 'INCONSISTENT'}
    return {
        'verdict': verdict_map.get(verdict, 'UNKNOWN'),
        'match_score': score,
        'manipulation_type': parsed.get('manipulation_type', 'NONE'),
        'ocr_detected': [c.get('text', '') for c in parsed.get('claims', []) if c.get('status') == 'VERIFIED'],
        'visual_signals': parsed.get('visual_description', ''),
        'core_claims_status': '; '.join(
            f"{c.get('status')}: {c.get('text', '')}" for c in parsed.get('claims', [])
            if c.get('status') not in ('METADATA',)
        ),
        'metadata_status': '; '.join(
            c.get('text', '') for c in parsed.get('claims', []) if c.get('status') == 'METADATA'
        ),
        'red_flags': parsed.get('red_flags', []),
        'explanation': parsed.get('reasoning', ''),
        'content_type': parsed.get('content_type', 'other'),
        'commercial_signals': parsed.get('commercial_signals', []),
        'claims': parsed.get('claims', []),
    }


def run_ocr_claim(image_path: str, caption: str) -> dict:
    """Use Groq vision (with Ollama fallback) for caption claim checking."""
    prompt = UNIVERSAL_OCR_PROMPT.format(caption=caption)
    text = _ollama_chat('llama3.2:latest', prompt, image_path=image_path)
    return _parse_universal_ocr(text)


# ── Reverse Image Search ───────────────────────────────────────────────────

def run_reverse_image(image_path: str, claimed_date: str = None) -> dict:
    import base64 as b64_mod
    import time
    import re
    from datetime import datetime
    from dateutil import parser as date_parser
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from bs4 import BeautifulSoup

    imgbb_key = os.getenv('IMGBB_API_KEY')
    if not imgbb_key:
        return {'error': 'IMGBB_API_KEY not set', 'skipped': True}

    with open(image_path, 'rb') as f:
        image_data = b64_mod.b64encode(f.read()).decode('utf-8')

    upload_resp = req_lib.post(
        'https://api.imgbb.com/1/upload',
        data={'key': imgbb_key, 'image': image_data},
        timeout=30
    )
    upload_json = upload_resp.json()
    if not upload_json.get('success'):
        return {'error': 'ImgBB upload failed', 'skipped': True}

    image_url = upload_json['data']['url']

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(f'https://tineye.com/search?url={image_url}&sort=crawl_date&order=asc')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    total_matches = 0
    title_tag = soup.find('title')
    if title_tag:
        m = re.search(r'(\d+)\s+TinEye', title_tag.get_text())
        if m:
            total_matches = int(m.group(1))

    first_indexed_date = None
    for h4 in soup.find_all('h4', class_='text-sm'):
        if 'First indexed by TinEye on' in h4.get_text():
            strong = h4.find('strong')
            if strong:
                first_indexed_date = strong.get_text().strip()
                break

    if not first_indexed_date:
        return {
            'total_matches': 0,
            'verdict': 'ORIGINAL',
            'explanation': "Image not found in TinEye's indexed database. Suggests recent creation or original content.",
            'oldest_date': None,
            'gap_days': None,
        }

    months_fr = {
        'janvier': 'January', 'février': 'February', 'mars': 'March',
        'avril': 'April', 'mai': 'May', 'juin': 'June',
        'juillet': 'July', 'août': 'August', 'septembre': 'September',
        'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
    }
    date_text = first_indexed_date.lower()
    for fr, en in months_fr.items():
        date_text = date_text.replace(fr, en)

    try:
        oldest_dt = date_parser.parse(date_text)
    except Exception:
        return {'error': f'Could not parse date: {first_indexed_date}', 'skipped': True}

    gap_days = None
    temporal_verdict = 'PLAUSIBLE'
    if claimed_date:
        try:
            claimed_dt = date_parser.parse(claimed_date)
            gap_days = (claimed_dt - oldest_dt).days
            if gap_days < 0:
                temporal_verdict = 'FAKE'
            elif gap_days >= 365:
                temporal_verdict = 'HIGHLY_SUSPICIOUS'
            elif gap_days >= 180:
                temporal_verdict = 'SUSPICIOUS'
            elif gap_days >= 7:
                temporal_verdict = 'QUESTIONABLE'
            else:
                temporal_verdict = 'PLAUSIBLE'
        except Exception:
            pass

    return {
        'total_matches': total_matches,
        'oldest_date': oldest_dt.strftime('%Y-%m-%d'),
        'verdict': temporal_verdict,
        'gap_days': gap_days,
        'explanation': f'TinEye found {total_matches} matches. Oldest appearance: {oldest_dt.strftime("%Y-%m-%d")}.'
                       + (f' Gap from claimed date: {gap_days} days.' if gap_days is not None else ''),
    }


# ── AI Image Forensics ─────────────────────────────────────────────────────

_ai_detector = None

def get_ai_detector():
    global _ai_detector
    if _ai_detector is None:
        try:
            from ai_detection import CombinedDetector
            print("[ai_detection] Initializing combined detector (MobileViT + Groq pipeline)...")
            _ai_detector = CombinedDetector()
            print("[ai_detection] Detector ready.")
        except Exception as e:
            import traceback
            print(f"[ai_detection] Failed to init detector: {e}")
            traceback.print_exc()
            _ai_detector = None
    return _ai_detector


def run_ai_detection(image_path: str) -> dict:
    import time as _time
    start = _time.time()

    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        print("[ai-detect] ERROR: GROQ_API_KEY not set in .env")
        return {'error': 'GROQ_API_KEY not set', 'skipped': True}

    print(f"[ai-detect] Starting analysis on: {image_path}")
    print(f"[ai-detect] GROQ_API_KEY: ...{groq_key[-6:]}")

    detector = get_ai_detector()
    if detector is None:
        print("[ai-detect] ERROR: AI detector failed to initialize")
        return {'error': 'AI detector failed to initialize', 'skipped': True}

    # Create temp output path for the annotated image
    out_fd, out_path = tempfile.mkstemp(suffix='.jpg')
    os.close(out_fd)

    try:
        print(f"[ai-detect] Running combined detect (annotate=True, output={out_path})")
        result = detector.detect(image_path, annotate=True, output_path=out_path)

        # Read annotated image as base64
        annotated_b64 = None
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            with open(out_path, 'rb') as f:
                annotated_b64 = base64.b64encode(f.read()).decode('utf-8')
            print(f"[ai-detect] Annotated image: {os.path.getsize(out_path) / 1024:.0f} KB")
        else:
            print("[ai-detect] WARNING: No annotated image generated")

        elapsed = _time.time() - start
        print(f"[ai-detect] DONE in {elapsed:.1f}s — verdict={result.get('verdict')}, "
              f"confidence={result.get('confidence')}, method={result.get('method')}")

        return {
            'verdict': result.get('verdict'),
            'confidence': result.get('confidence'),
            'summary': result.get('summary', ''),
            'method': result.get('method'),
            'scores': result.get('scores', {}),
            'key_findings': result.get('key_findings', []),
            'overall_reasoning': result.get('overall_reasoning', ''),
            'stages': result.get('stages', {}),
            'annotated_image_b64': annotated_b64,
        }
    except Exception as e:
        import traceback
        elapsed = _time.time() - start
        print(f"[ai-detect] FAILED after {elapsed:.1f}s: {type(e).__name__}: {e}")
        traceback.print_exc()
        return {'error': str(e), 'skipped': True}
    finally:
        if os.path.exists(out_path):
            try:
                os.unlink(out_path)
            except Exception:
                pass


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    det = get_ai_detector()
    return jsonify({
        'status': 'ok',
        'groq_key': bool(os.getenv('GROQ_API_KEY')),
        'gemini_key': bool(os.getenv('GEMINI_API_KEY')),
        'imgbb_key': bool(os.getenv('IMGBB_API_KEY')),
        'ai_detector_ready': det is not None,
    })


@app.route('/ocr-claim', methods=['POST'])
def ocr_claim_route():
    data = request.get_json()
    image_url = data.get('image_url')
    caption = data.get('caption', '')

    if not image_url:
        return jsonify({'error': 'image_url required'}), 400

    tmp_path = None
    try:
        tmp_path = download_image(image_url)
        result = run_ocr_claim(tmp_path, caption)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.route('/reverse-image', methods=['POST'])
def reverse_image_route():
    data = request.get_json()
    image_url = data.get('image_url')
    claimed_date = data.get('claimed_date')

    if not image_url:
        return jsonify({'error': 'image_url required'}), 400

    tmp_path = None
    try:
        tmp_path = download_image(image_url)
        result = run_reverse_image(tmp_path, claimed_date)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.route('/ai-detect', methods=['POST'])
def ai_detect_route():
    data = request.get_json()
    image_url = data.get('image_url')

    print(f"\n{'='*60}")
    print(f"[ai-detect] POST /ai-detect")
    print(f"[ai-detect] image_url: {image_url[:100] if image_url else 'NONE'}...")
    print(f"{'='*60}")

    if not image_url:
        return jsonify({'error': 'image_url required'}), 400

    tmp_path = None
    try:
        print(f"[ai-detect] Downloading image...")
        tmp_path = download_image(image_url)
        print(f"[ai-detect] Downloaded to: {tmp_path} ({os.path.getsize(tmp_path) / 1024:.0f} KB)")
        result = run_ai_detection(tmp_path)
        if result.get('error'):
            print(f"[ai-detect] Returning error: {result['error']}")
        else:
            print(f"[ai-detect] Returning verdict={result.get('verdict')}, "
                  f"confidence={result.get('confidence')}, "
                  f"has_annotated={'yes' if result.get('annotated_image_b64') else 'no'}")
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"[ai-detect] ROUTE ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Bot Detection (Full PostAccountAnalyzer flow from analyze_post_with_account.py) ──

def run_bot_detection(post_data: dict) -> dict:
    """
    Run the full bot detection pipeline exactly as analyze_post_with_account.py does:
      1. Take the Supabase post JSON (same structure as lovable_dev_post.json)
      2. Scrape account data for the username via Serper API
      3. Merge post data + account data (PostAccountAnalyzer.merge_data)
      4. Extract features across 4 signal categories (FeatureExtractor)
      5. Score with weighted rules (BotScoringEngine)
      6. Classify and return the full combined result
    """
    try:
        from instagram_scraper import InstagramScraper
        from feature_extraction import FeatureExtractor
        from scoring_engine import BotScoringEngine
        import pandas as pd
    except ImportError as e:
        return {'error': f'Bot detection modules not available: {e}', 'skipped': True}

    serper_key = os.getenv('SERPER_API_KEY')
    if not serper_key:
        return {'error': 'SERPER_API_KEY not set', 'skipped': True}

    username = post_data.get('username')
    if not username:
        return {'error': 'No username in post data', 'skipped': True}

    # ── Step 1: Scrape account data via Serper API (like analyze_post_with_account.py) ──
    try:
        scraper = InstagramScraper(serper_api_key=serper_key)
        account_data = scraper.scrape_account(username)
    except Exception as e:
        return {'error': f'Account scraping failed: {e}', 'skipped': True}

    if not account_data:
        return {'error': f'Could not find account data for @{username}', 'skipped': True}

    # ── Step 2: Merge post + account data (PostAccountAnalyzer.merge_data) ──
    combined_data = {
        'post': {
            'idx': post_data.get('idx'),
            'id': post_data.get('id'),
            'post_url': post_data.get('post_url'),
            'caption': post_data.get('caption'),
            'likes_count': post_data.get('likes_count'),
            'comments_count': post_data.get('comments_count'),
            'image_url': post_data.get('image_url'),
            'post_date': post_data.get('post_date'),
            'post_date_raw': post_data.get('post_date_raw'),
            'hashtags': post_data.get('hashtags', []),
            'scraped_at': post_data.get('scraped_at'),
            'media_urls': post_data.get('media_urls', []),
            'video_url': post_data.get('video_url'),
            'post_type': post_data.get('post_type'),
        },
        'account': account_data,
        'bot_detection_input': account_data,
    }

    # ── Step 3: Extract features (FeatureExtractor.extract_all_features) ──
    feature_extractor = FeatureExtractor()
    features = feature_extractor.extract_all_features(account_data)

    # ── Step 4: Score with weighted rules (BotScoringEngine) ──
    scoring_engine = BotScoringEngine(method='weighted_rules')
    features_df = pd.DataFrame([features])
    score_series = scoring_engine.score_accounts(features_df)
    if not isinstance(score_series, pd.Series):
        score_series = pd.Series(score_series)
    bot_score = float(score_series.iloc[0])

    # ── Step 5: Classify (like PostAccountAnalyzer.detect_bot) ──
    classification = scoring_engine.classify_account(bot_score)

    if classification == 'bot':
        risk_level = 'HIGH'
    elif classification == 'inconclusive':
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'

    # ── Step 6: Identify suspicious flags (from analyze_post_with_account.py) ──
    suspicious_flags = []
    if features.get('no_profile_pic', 0) == 1:
        suspicious_flags.append('No profile picture')
    if features.get('no_bio', 0) == 1:
        suspicious_flags.append('No biography')
    if features.get('high_digit_username', 0) == 1:
        suspicious_flags.append('Username has many digits')
    if features.get('suspicious_follower_ratio', 0) == 1:
        suspicious_flags.append('Suspicious follower/following ratio')
    if features.get('high_following', 0) == 1:
        suspicious_flags.append('Following too many accounts')
    if features.get('low_engagement', 0) == 1:
        suspicious_flags.append('Low engagement rate')
    if features.get('excessive_hashtags', 0) == 1:
        suspicious_flags.append('Excessive hashtag usage')

    # ── Build full result (mirrors analyze_post_with_account.py output JSON) ──
    bot_analysis = {
        'bot_score': bot_score,
        'classification': classification,
        'risk_level': risk_level,
        'features': features,
        'suspicious_flags': suspicious_flags,
    }

    combined_data['bot_analysis'] = bot_analysis

    # Return the full combined result for the web app
    return {
        'bot_score': bot_score,
        'classification': classification,
        'risk_level': risk_level,
        'features': features,
        'suspicious_flags': suspicious_flags,
        'account_data': {
            'username': account_data.get('username'),
            'followers': account_data.get('user_follower_count', 0),
            'following': account_data.get('user_following_count', 0),
            'posts': account_data.get('user_media_count', 0),
            'bio_length': account_data.get('user_biography_length', 0),
            'has_profile_pic': account_data.get('user_has_profil_pic', 0),
            'is_private': account_data.get('user_is_private', 0),
            'has_external_url': account_data.get('user_has_external_url', 0),
        },
        'post_context': {
            'likes_count': post_data.get('likes_count'),
            'comments_count': post_data.get('comments_count'),
            'hashtags': post_data.get('hashtags', []),
            'post_type': post_data.get('post_type'),
            'has_image': bool(post_data.get('image_url')),
        },
        'combined_data': combined_data,
    }


@app.route('/bot-detect', methods=['POST'])
def bot_detect_route():
    data = request.get_json()

    # Accept full post JSON from Supabase (same structure as lovable_dev_post.json)
    # OR just a username for backward compat
    if 'post' in data:
        post_data = data['post']
    elif 'username' in data:
        # backward compat: wrap username into minimal post structure
        post_data = {'username': data['username']}
    else:
        return jsonify({'error': 'post object or username required'}), 400

    if not post_data.get('username'):
        return jsonify({'error': 'username required in post data'}), 400

    try:
        result = run_bot_detection(post_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Caption-Image Alignment (Groq Vision) ─────────────────────────────────

@app.route('/caption-alignment', methods=['POST'])
def caption_alignment_route():
    data = request.get_json()
    image_url = data.get('image_url')
    caption = data.get('caption', '')

    if not image_url:
        return jsonify({'error': 'No image to analyze', 'skipped': True})

    tmp_path = None
    try:
        import json, re
        tmp_path = download_image(image_url)

        prompt = f"""You are an expert media verification analyst. Analyze whether the image and the caption below are semantically aligned — does the image actually depict what the caption describes?

Caption: \"{caption[:1500]}\"

Evaluate:
1. ALIGNMENT_SCORE: A float from 0.0 (completely unrelated) to 1.0 (perfect match)
2. VERDICT: one of "strong_match", "partial_match", "weak_match", "mismatch"
3. REASONING: 2-3 sentences explaining specifically what the image shows vs what the caption claims
4. KEY_OBSERVATIONS: list of 2-4 specific observations about match/mismatch

Respond ONLY with valid JSON:
{{"alignment_score": 0.85, "verdict": "strong_match", "reasoning": "...", "key_observations": ["...", "..."]}}"""

        # Pass image_path so Groq vision can actually SEE the image
        raw_text = _ollama_chat('llama3.2:latest', prompt, image_path=tmp_path)

        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                'alignment_score': 0.5,
                'verdict': 'uncertain',
                'reasoning': raw_text[:300],
                'key_observations': [],
            }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'skipped': True}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Source Credibility (Gemini) ────────────────────────────────────────────

@app.route('/source-credibility', methods=['POST'])
def source_credibility_route():
    data = request.get_json()
    username = data.get('username', '')
    caption = data.get('caption', '')
    likes = data.get('likes_count', '0')
    comments = data.get('comments_count', '0')
    hashtags = data.get('hashtags', [])
    post_type = data.get('post_type', 'unknown')

    try:
        import json, re
        prompt = f"""You are an expert social media source credibility analyst. Analyze the following Instagram account/post for credibility signals.

Account: @{username}
Caption: "{caption[:1500]}"
Engagement: {likes} likes, {comments} comments
Hashtags: {', '.join(hashtags[:15]) if isinstance(hashtags, list) else str(hashtags)}
Post type: {post_type}

Evaluate the SOURCE CREDIBILITY by analyzing:
1. Username patterns — does it look like a credible/established account or suspicious (e.g., "breaking_news_REAL_facts_2024")?
2. Writing style — is the caption written professionally? Sensationalist? Clickbait? Contains urgency language?
3. Engagement ratios — are the likes/comments ratios normal or suspicious?
4. Hashtag strategy — are hashtags relevant and measured, or spammy/manipulative?
5. Content indicators — any red flags like "share before deleted", "they don't want you to know", etc.?

Respond ONLY with valid JSON, no extra text:
{{"credibility_score": 0.75, "verdict": "credible", "risk_factors": ["...", "..."], "positive_signals": ["...", "..."], "reasoning": "2-3 sentence summary"}}

Where verdict is one of: "highly_credible", "credible", "mixed", "low_credibility", "not_credible"
credibility_score is 0.0 (not credible) to 1.0 (highly credible)"""

        raw_text = _ollama_chat('llama3.2:latest', prompt)

        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                'credibility_score': 0.5,
                'verdict': 'mixed',
                'risk_factors': [],
                'positive_signals': [],
                'reasoning': raw_text[:300],
            }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'skipped': True}), 500


# ── Link Scanner (Gemini + URL extraction) ─────────────────────────────────

@app.route('/link-scan', methods=['POST'])
def link_scan_route():
    data = request.get_json()
    caption = data.get('caption', '')
    post_url = data.get('post_url', '')
    username = data.get('username', '')

    import re
    # Extract URLs from caption
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    found_urls = re.findall(url_pattern, caption)

    # Also check for shortened/suspicious URL patterns without http
    short_pattern = r'(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|buff\.ly|adf\.ly|linktr\.ee)[/\w.-]*'
    short_urls = re.findall(short_pattern, caption, re.IGNORECASE)
    if short_urls:
        found_urls.extend(['http://' + u for u in short_urls])

    # Check for mentions of external domains in text
    domain_pattern = r'(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|net|org|io|co|info|biz|xyz|click|top|link|site|online|live))\b'
    mentioned_domains = re.findall(domain_pattern, caption, re.IGNORECASE)

    all_links = list(set(found_urls))
    all_domains = list(set(mentioned_domains))

    if not all_links and not all_domains:
        return jsonify({
            'urls_found': [],
            'domains_found': [],
            'verdict': 'clean',
            'risk_score': 0.0,
            'reasoning': 'No external URLs or domains found in caption.',
            'flags': [],
        })

    try:
        import json as json_lib

        prompt = f"""You are a link safety analyst. Analyze the following URLs and domains found in an Instagram post caption for safety risks.

Post by: @{username}
Post URL: {post_url}

URLs found in caption: {json_lib.dumps(all_links) if all_links else 'none'}
Domains mentioned: {json_lib.dumps(all_domains) if all_domains else 'none'}

Full caption: "{caption[:1500]}"

Evaluate each URL/domain for:
1. Is it a known phishing or scam domain?
2. Does it use URL shorteners to hide the destination?
3. Does the domain name try to impersonate a legitimate organization?
4. Is it a suspicious newly-registerable TLD (.xyz, .click, .top, etc.)?
5. Does the URL structure look designed to deceive (typosquatting, extra subdomains)?

Respond ONLY with valid JSON, no extra text:
{{"risk_score": 0.3, "verdict": "safe", "flags": ["list of specific concerns if any"], "url_analysis": [{{"url": "...", "safe": true, "reason": "..."}}], "reasoning": "2-3 sentence summary"}}

Where verdict is one of: "safe", "caution", "suspicious", "dangerous"
risk_score is 0.0 (completely safe) to 1.0 (extremely dangerous)"""

        raw_text = _ollama_chat('llama3.2:latest', prompt)

        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            result = json_lib.loads(json_match.group())
        else:
            result = {
                'risk_score': 0.2,
                'verdict': 'caution',
                'flags': [],
                'url_analysis': [],
                'reasoning': raw_text[:300],
            }

        result['urls_found'] = all_links
        result['domains_found'] = all_domains
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'skipped': True}), 500


# ── Text Content Analyzer (OCR.space + LLaVA + Llama) ─────────────────────

OCR_SPACE_URL = "https://api.ocr.space/parse/image"
OCR_SPACE_KEY = os.getenv('OCR_SPACE_KEY', 'K87999402988957')


def _ocr_space_extract(image_path: str) -> str:
    """Extract text via OCR.space API (eng + fre + ara)."""
    import base64 as _b64
    with open(image_path, 'rb') as f:
        b64 = _b64.b64encode(f.read()).decode('utf-8')
    ext = image_path.rsplit('.', 1)[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
            'webp': 'image/webp', 'gif': 'image/gif'}.get(ext, 'image/jpeg')
    b64_payload = f"data:{mime};base64,{b64}"
    results = []
    for lang, engine in [('eng', 2), ('fre', 2), ('ara', 1)]:
        try:
            payload = {
                'apikey': OCR_SPACE_KEY,
                'base64Image': b64_payload,
                'language': lang,
                'OCREngine': engine,
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'filetype': ext.upper(),
            }
            r = req_lib.post(OCR_SPACE_URL, data=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            if not data.get('IsErroredOnProcessing'):
                parsed = data.get('ParsedResults', [])
                if parsed:
                    text = parsed[0].get('ParsedText', '').strip()
                    if text and len(text) >= 3:
                        results.append(text)
        except Exception:
            pass
    return '\n'.join(dict.fromkeys(results)).strip() if results else ''


def run_text_content_analysis(image_path: str, caption: str = '') -> dict:
    """
    Text-image content analyzer:
      1. OCR.space  → extract raw text
      2. LLaVA      → visual full text reading
      3. llama3.2   → semantic analysis + AI generation check
    """
    # Step 1: OCR
    ocr_text = _ocr_space_extract(image_path)

    # Step 2: LLaVA visual reading (optional — OCR.space is primary)
    llava_prompt = """Read ALL visible text in this image exactly as it appears.
Include every word even if cursive, handwritten, stylized, or in Arabic/French.
Preserve line breaks. Reply ONLY with the text you read, no commentary."""
    llava_text = ''
    try:
        # _ollama_chat tries Groq vision first, then falls back to Ollama LLaVA
        llava_text = _ollama_chat('llava:latest', llava_prompt, image_path=image_path).strip()
    except Exception as e:
        print(f"   [text-content] Vision text reading skipped ({e}) — using OCR.space only")

    best_text = llava_text or ocr_text or caption or '[No text detected]'

    # Step 3: Llama semantic analysis + AI generation check
    import json as _json, re as _re
    analysis_prompt = f"""You are an expert content and AI-detection analyst.

IMAGE TEXT (extracted):
\"\"\"{best_text}\"\"\"

CAPTION (if any):
\"\"\"{caption[:500]}\"\"\"

Perform TWO analyses:

A) CONTENT ANALYSIS — Is the image text-only or does it contain other visual elements?
   - What type of content is this? (quote/meme/news/ad/screenshot/chart/other)
   - What language(s)? (english/french/arabic/mixed)
   - Is the text coherent and meaningful?
   - What is the message/intent?

B) AI GENERATION CHECK — Does this text-image show signs of AI generation?
   Common AI text-image tells:
   - Spelling errors, garbled characters, nonsensical words
   - Font inconsistencies within the same word
   - Text that bleeds into background or has halo artifacts
   - Unrealistic perfect typography for the claimed context
   - Prompt-like phrasing or generic inspirational quotes

Respond ONLY with valid JSON:
{{
  "is_text_only": true,
  "content_type": "quote|meme|news|ad|screenshot|chart|other",
  "language": "english|french|arabic|mixed",
  "is_coherent": true,
  "message": "What the text says/means in one sentence",
  "ai_text_probability": 0.0,
  "ai_tells": ["list of specific AI generation artifacts found, or empty"],
  "verdict": "likely_ai_generated|possibly_ai_generated|likely_authentic|uncertain",
  "reasoning": "2-3 sentence explanation"
}}"""

    result = {}
    try:
        raw = _ollama_chat('llama3.2:latest', analysis_prompt)
        m = _re.search(r'\{[\s\S]*\}', raw)
        if m:
            result = _json.loads(m.group())
    except Exception:
        pass

    return {
        'ocr_text': ocr_text,
        'llava_text': llava_text,
        'best_text': best_text,
        'is_text_only': result.get('is_text_only', True),
        'content_type': result.get('content_type', 'other'),
        'language': result.get('language', 'unknown'),
        'is_coherent': result.get('is_coherent', True),
        'message': result.get('message', ''),
        'ai_text_probability': result.get('ai_text_probability', 0.0),
        'ai_tells': result.get('ai_tells', []),
        'verdict': result.get('verdict', 'uncertain'),
        'reasoning': result.get('reasoning', ''),
    }


@app.route('/text-content', methods=['POST'])
def text_content_route():
    data = request.get_json()
    image_url = data.get('image_url')
    caption = data.get('caption', '')

    if not image_url:
        return jsonify({'error': 'image_url required'}), 400

    tmp_path = None
    try:
        tmp_path = download_image(image_url)

        # Quick OCR check first — if no text detected, skip the full pipeline
        ocr_text = _ocr_space_extract(tmp_path)
        if not ocr_text or len(ocr_text.strip()) < 10:
            return jsonify({'skipped': True, 'reason': 'No significant text detected in image'})

        result = run_text_content_analysis(tmp_path, caption)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Synthesis Agent (LLM-powered meta-reasoning) ──────────────────────────

SYNTHESIS_PROMPT = """You are the Synthesis Agent in a multi-agent misinformation detection pipeline for Instagram posts.

You receive structured outputs from 8 specialized agents organized into Blue Team (detection/forensics) and Red Team (context/verification). Your job: reconcile their findings into ONE final verdict with rigorous reasoning.

POST CONTEXT:
- Username: @{username}
- Caption: "{caption}"
- Likes: {likes} | Comments: {comments}
- Hashtags: {hashtags}
- Has image: {has_image}

AGENT RESULTS (with assigned reliability weights):
{agent_details}

DECISION RULES — follow these strictly:
1. If Image Forensics detected AI generation with HIGH confidence (>70%), this is STRONG evidence — the verdict should lean toward "suspicious" or "fake" unless other agents provide compelling counter-evidence.
2. If Reverse Image found pre-existing copies (verdict FAKE or HIGHLY_SUSPICIOUS), this is near-conclusive evidence of image reuse — heavily penalize.
3. If OCR + Claim Checker found CONTRADICTED claims, cap the confidence at 50% maximum.
4. Bot Detection and Source Credibility are CONTEXT signals — they inform trustworthiness but cannot alone prove content is fake.
5. If agents CONTRADICT each other, you MUST explain the contradiction and why you sided with one over the other.
6. Link Scanner with "clean" (no URLs found) is NEUTRAL — don't count it as positive evidence.
7. Text Content Analyzer "skipped" (no text in image) is NEUTRAL — don't count as positive or negative.

WEIGHTING GUIDANCE:
- Image Forensics (0.20) and Reverse Image (0.18) are the strongest signals — they analyze the actual media.
- OCR + Claim (0.15) and Caption Alignment (0.12) cross-reference claims against visual evidence.
- Bot Detection (0.10) and Source Credibility (0.08) assess the source, not the content.
- Link Scanner (0.07) and Text Content (0.10) are supplementary.

Respond ONLY with valid JSON, no markdown or preamble:
{{
  "verdict": "verified|suspicious|fake",
  "confidence": 0-100,
  "synthesis": "3-5 sentence reasoning covering key agreements, contradictions, and the decisive evidence. Be specific — reference actual agent outputs.",
  "key_evidence": ["list of 2-4 most decisive evidence points that drove your verdict"],
  "contradictions": ["list of any agent disagreements you identified, or empty array"],
  "decisive_factors": "1-2 sentence explanation of what single factor was most decisive"
}}"""


def _format_agent_for_synthesis(agent: dict, weight: float) -> str:
    """Format a single agent result for the synthesis prompt."""
    lines = []
    lines.append(f"  Agent: {agent.get('name', '?')} (Team: {agent.get('team', '?')}, Weight: {weight})")
    lines.append(f"  Score: {agent.get('score', '?')} | Real: {agent.get('real', False)}")
    lines.append(f"  Finding: {agent.get('finding', 'N/A')}")
    lines.append(f"  Reasoning: {agent.get('reasoning', 'N/A')}")

    # Include key raw data if available
    raw = agent.get('raw')
    if raw:
        # Only include the most relevant fields, skip large blobs
        compact_raw = {}
        for k, v in raw.items():
            if k in ('annotated_image_b64',):
                continue  # skip large binary
            if isinstance(v, str) and len(v) > 300:
                compact_raw[k] = v[:300] + '...'
            else:
                compact_raw[k] = v
        lines.append(f"  Raw data: {compact_raw}")

    return '\n'.join(lines)


@app.route('/synthesis', methods=['POST'])
def synthesis_route():
    """LLM-powered Synthesis Agent — meta-reasoning over all agent outputs."""
    data = request.get_json()
    agents = data.get('agents', [])
    post = data.get('post', {})
    weights = data.get('weights', {})

    if not agents:
        return jsonify({'error': 'agents array required'}), 400

    try:
        import json as _json, re as _re

        # Build detailed agent descriptions for the prompt
        agent_details = []
        for i, agent in enumerate(agents):
            name = agent.get('name', f'Agent {i}')
            weight = weights.get(name, 0.125)  # default equal weight
            agent_details.append(_format_agent_for_synthesis(agent, weight))

        prompt = SYNTHESIS_PROMPT.format(
            username=post.get('username', 'unknown'),
            caption=(post.get('caption', '') or '')[:800],
            likes=post.get('likes_count', '0'),
            comments=post.get('comments_count', '0'),
            hashtags=', '.join(post.get('hashtags', [])[:10]),
            has_image='Yes' if post.get('image_url') else 'No',
            agent_details='\n\n'.join(agent_details),
        )

        print(f"\n{'='*60}")
        print(f"[synthesis] Running LLM-powered Synthesis Agent...")
        print(f"[synthesis] {len(agents)} agents, post by @{post.get('username', '?')}")
        print(f"{'='*60}")

        raw_text = _groq_chat(prompt)
        print(f"[synthesis] Got {len(raw_text)} chars from Groq")

        # Parse JSON response
        json_match = _re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            result = _json.loads(json_match.group())
        else:
            print(f"[synthesis] WARNING: Failed to parse JSON, using fallback")
            result = {
                'verdict': 'suspicious',
                'confidence': 50,
                'synthesis': raw_text[:500],
                'key_evidence': [],
                'contradictions': [],
                'decisive_factors': 'LLM output could not be parsed.',
            }

        # Validate and clamp
        if result.get('verdict') not in ('verified', 'suspicious', 'fake'):
            result['verdict'] = 'suspicious'
        result['confidence'] = max(0, min(100, int(result.get('confidence', 50))))

        print(f"[synthesis] Verdict: {result['verdict']} ({result['confidence']}/100)")
        print(f"[synthesis] Synthesis: {result.get('synthesis', '')[:200]}...")

        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"[synthesis] ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PYTHON_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
