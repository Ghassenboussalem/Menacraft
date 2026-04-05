"""
Combined AI Image Detector — Main Entry Point

Merges two detection approaches:
  1. MobileViT Classifier  → Fast binary score (~1 sec)
  2. Groq Vision Pipeline  → Detailed findings with bboxes (~20 sec)

Final score = weighted combination of both.
"""

import time
import json
from pathlib import Path

from detector import detect_ai_image, get_quick_summary
from classifier import MobileViTClassifier
from annotator import annotate_image


# ── Weights for the final score ──
CLASSIFIER_WEIGHT = 0.30   # 30% — fast but less explainable
PIPELINE_WEIGHT = 0.70     # 70% — detailed and explainable


class CombinedDetector:
    """
    Unified AI image detector combining a classification model
    with a multi-stage vision pipeline.
    """

    def __init__(self):
        """Initialize both detection systems."""
        print("Initializing AI Image Detector...")
        self.classifier = MobileViTClassifier()
        print(f"   Classifier: {'enabled' if self.classifier.available else 'disabled (pipeline only)'}")
        print("   Pipeline: Groq Vision (Llama 4 Scout)")
        print("Ready.\n")

    def detect(
        self,
        image_source: str,
        annotate: bool = True,
        output_path: str = None,
    ) -> dict:
        """
        Run the full combined detection on an image.

        Args:
            image_source: Path to a local image file, URL, or data URL.
            annotate: If True, save an annotated image with findings.
            output_path: Custom path for the annotated image.

        Returns:
            Dict with combined verdict, scores from both systems,
            detailed findings, and path to annotated image.
        """
        start = time.time()
        is_local_file = (
            isinstance(image_source, str)
            and not image_source.startswith("http")
            and not image_source.startswith("data:")
        )

        # ── 1. Run MobileViT Classifier (fast) ──
        classifier_result = None
        if self.classifier.available and is_local_file:
            print("[1/3] Running MobileViT classifier...")
            classifier_result = self.classifier.predict(image_source)
            if classifier_result:
                print(f"      AI probability: {classifier_result['ai_probability']:.0%}")
                print(f"      Prediction: {classifier_result['predicted_class']}")
            else:
                print("      Classifier returned no result")
        else:
            print("[1/3] Classifier skipped (not available or non-local image)")

        # ── 2. Run Groq Vision Pipeline (detailed) ──
        print("[2/3] Running Groq vision pipeline...")
        pipeline_result = detect_ai_image(image_source)
        pipeline_confidence = pipeline_result.get("confidence", 0)
        print(f"      Pipeline verdict: {pipeline_result.get('verdict', '?')}")
        print(f"      Pipeline confidence: {pipeline_confidence:.0%}")

        # ── 3. Combine scores ──
        print("[3/3] Computing combined verdict...")
        combined = self._combine_results(classifier_result, pipeline_result)

        # ── 4. Annotate image ──
        annotated_path = None
        if annotate and is_local_file:
            try:
                annotated_path = annotate_image(
                    image_source,
                    combined,
                    output_path=output_path,
                )
                combined["annotated_image"] = annotated_path
            except Exception as e:
                print(f"      Annotation failed: {e}")

        elapsed = time.time() - start
        combined["elapsed_seconds"] = round(elapsed, 1)
        print(f"\nAnalysis complete in {elapsed:.1f}s")

        return combined

    def detect_quick(self, image_source: str) -> dict:
        """
        Quick detection — classifier only (if available), no annotations.
        Falls back to pipeline if classifier not available.
        """
        is_local = (
            isinstance(image_source, str)
            and not image_source.startswith("http")
            and not image_source.startswith("data:")
        )

        if self.classifier.available and is_local:
            result = self.classifier.predict(image_source)
            if result:
                verdict = self._score_to_verdict(result["ai_probability"])
                return {
                    "verdict": verdict,
                    "confidence": result["ai_probability"],
                    "summary": f"Quick classifier result: {result['ai_probability']:.0%} AI probability",
                    "method": "classifier_only",
                    "classifier_score": result["ai_probability"],
                }

        # Fallback to full pipeline
        full = detect_ai_image(image_source)
        return get_quick_summary(full)

    def _combine_results(self, classifier_result: dict | None, pipeline_result: dict) -> dict:
        """Combine classifier and pipeline results into a unified verdict."""
        pipeline_conf = pipeline_result.get("confidence", 0)
        pipeline_verdict = pipeline_result.get("verdict", "uncertain")

        if classifier_result and classifier_result.get("ai_probability") is not None:
            cls_score = classifier_result["ai_probability"]

            # Weighted average
            combined_score = (
                cls_score * CLASSIFIER_WEIGHT
                + pipeline_conf * PIPELINE_WEIGHT
            )

            method = "combined"
            scores = {
                "classifier_score": round(cls_score, 4),
                "classifier_weight": CLASSIFIER_WEIGHT,
                "pipeline_score": round(pipeline_conf, 4),
                "pipeline_weight": PIPELINE_WEIGHT,
                "combined_score": round(combined_score, 4),
            }
        else:
            combined_score = pipeline_conf
            method = "pipeline_only"
            scores = {
                "classifier_score": None,
                "pipeline_score": round(pipeline_conf, 4),
                "combined_score": round(combined_score, 4),
            }

        verdict = self._score_to_verdict(combined_score)

        return {
            "verdict": verdict,
            "confidence": round(combined_score, 4),
            "summary": pipeline_result.get("summary", ""),
            "method": method,
            "scores": scores,
            "key_findings": pipeline_result.get("key_findings", []),
            "overall_reasoning": pipeline_result.get("overall_reasoning", ""),
            "stages": pipeline_result.get("stages", {}),
        }

    @staticmethod
    def _score_to_verdict(score: float) -> str:
        """Map a 0-1 score to a verdict label."""
        if score >= 0.70:
            return "likely_ai_generated"
        elif score >= 0.45:
            return "possibly_ai_generated"
        elif score >= 0.25:
            return "uncertain"
        else:
            return "likely_authentic"


# ── Module-level convenience function ──
_detector_instance = None


def get_detector() -> CombinedDetector:
    """Get or create the singleton detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CombinedDetector()
    return _detector_instance


def combined_detect(image_source: str, annotate: bool = True, output_path: str = None) -> dict:
    """Convenience function: run combined detection."""
    return get_detector().detect(image_source, annotate=annotate, output_path=output_path)
