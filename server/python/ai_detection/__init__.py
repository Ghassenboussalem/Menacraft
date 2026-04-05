"""
AI Image Detection Package — local copy of blue team/ai_detection.

Combines MobileViT classifier (fast) + Groq Vision pipeline (detailed)
for AI-generated image detection with annotated output.
"""

from .combined_detector import CombinedDetector, get_detector, combined_detect

__all__ = ["CombinedDetector", "get_detector", "combined_detect"]
