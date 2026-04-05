import os
import json
import google.generativeai as genai
from PIL import Image


class UniversalCaptionVerifier:
    """
    Adaptive image-caption verification system.
    
    Uses a compact, principle-driven prompt that adapts to any content type:
    news, memes, ads, personal posts, political content, disaster photos, etc.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    # ───────────────────────────────────────────────
    # THE UNIVERSAL PROMPT
    # ───────────────────────────────────────────────
    PROMPT = """You are a forensic image-caption verifier. Your ONLY job: determine whether the caption accurately represents what the image shows.

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
  "score": 0-100
}}"""

    def verify(self, image_path: str, caption: str) -> dict:
        """Verify a caption against an image. Works with any content type."""
        image = Image.open(image_path)
        prompt = self.PROMPT.format(caption=caption)

        response = self.model.generate_content([prompt, image])
        return self._parse(response.text)

    def _parse(self, raw: str) -> dict:
        """Parse JSON response with fallback handling."""
        cleaned = raw.strip()

        # Strip markdown fences if present
        if cleaned.startswith('```'):
            cleaned = '\n'.join(cleaned.split('\n')[1:])
        if cleaned.endswith('```'):
            cleaned = '\n'.join(cleaned.split('\n')[:-1])
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from mixed content
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                try:
                    parsed = json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError:
                    return self._fallback(raw)
            else:
                return self._fallback(raw)

        # Normalize and fill defaults
        return {
            'visual_description': parsed.get('visual_description', ''),
            'claims': parsed.get('claims', []),
            'content_type': parsed.get('content_type', 'other'),
            'commercial_signals': parsed.get('commercial_signals', []),
            'manipulation_type': parsed.get('manipulation_type', 'NONE'),
            'red_flags': parsed.get('red_flags', []),
            'reasoning': parsed.get('reasoning', ''),
            'verdict': parsed.get('verdict', 'UNKNOWN'),
            'score': parsed.get('score', 0),
            'raw': raw
        }

    def _fallback(self, raw: str) -> dict:
        """Return a structured fallback when parsing fails."""
        return {
            'visual_description': '',
            'claims': [],
            'content_type': 'other',
            'commercial_signals': [],
            'manipulation_type': 'NONE',
            'red_flags': ['PARSE_FAILURE: Model did not return valid JSON'],
            'reasoning': 'Could not parse model response.',
            'verdict': 'UNKNOWN',
            'score': 0,
            'raw': raw
        }


# ─────────────────────────────────────────────────
# Usage examples — works across all content types
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    api_key = os.getenv('GEMINI_API_KEY', 'YOUR_KEY_HERE')
    v = UniversalCaptionVerifier(api_key=api_key)

    # Works with ANY image + caption combination:
    # - News photo + headline
    # - Meme + claim
    # - Product ad + testimonial
    # - War photo + political caption
    # - Selfie + story
    # - Screenshot + context
    # - Video thumbnail + description

    result = v.verify("image.jpg", "Your caption here")

    print(f"Verdict:       {result['verdict']} ({result['score']}%)")
    print(f"Content Type:  {result['content_type']}")
    print(f"Manipulation:  {result['manipulation_type']}")
    print(f"Red Flags:     {', '.join(result['red_flags']) or 'None'}")
    print(f"Commercial:    {', '.join(result['commercial_signals']) or 'None'}")
    print()
    for c in result['claims']:
        icon = {'VERIFIED': '✅', 'UNVERIFIABLE': '❓', 'CONTRADICTED': '❌', 'METADATA': '🏷️'}.get(c['status'], '•')
        print(f"  {icon} [{c['status']}] {c['text']}")
        print(f"     ↳ {c['evidence']}")
    print()
    print(f"Reasoning:     {result['reasoning']}")