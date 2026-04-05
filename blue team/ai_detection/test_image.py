"""
CLI tool to test the AI image detector on local images.

Usage:
  python test_image.py path/to/image.jpg
  python test_image.py path/to/image.png --verbose
  python test_image.py path/to/image.jpg --no-annotate
  python test_image.py path/to/image.jpg --json
"""

import sys
import json
import argparse
import os

from combined_detector import CombinedDetector


def main():
    parser = argparse.ArgumentParser(
        description="AI Image Detector - Combined classifier + vision pipeline"
    )
    parser.add_argument(
        "image",
        help="Path to a local image file or a public image URL",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full stage-by-stage output",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON instead of formatted text",
    )
    parser.add_argument(
        "--no-annotate",
        action="store_true",
        help="Skip generating annotated image",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for annotated image",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  AI IMAGE DETECTION — Combined Analysis")
    print("=" * 60)
    print(f"Image: {args.image}")
    print("-" * 60)

    # Create detector and run
    detector = CombinedDetector()
    result = detector.detect(
        args.image,
        annotate=not args.no_annotate,
        output_path=args.output,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    # -- Formatted output --
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    verdict = result["verdict"]
    confidence = result["confidence"]
    method = result.get("method", "?")

    verdict_map = {
        "likely_ai_generated": "[!!] LIKELY AI-GENERATED",
        "possibly_ai_generated": "[!]  POSSIBLY AI-GENERATED",
        "likely_authentic": "[OK] LIKELY AUTHENTIC",
        "uncertain": "[??] UNCERTAIN",
    }
    print(f"\nVerdict:    {verdict_map.get(verdict, verdict)}")
    print(f"Confidence: {confidence:.0%}")
    print(f"Method:     {method}")
    print(f"Time:       {result.get('elapsed_seconds', 0)}s")

    # Show individual scores
    scores = result.get("scores", {})
    if scores:
        print(f"\n  Score Breakdown:")
        cls_score = scores.get("classifier_score")
        pipe_score = scores.get("pipeline_score")
        combined = scores.get("combined_score")

        if cls_score is not None:
            cls_w = scores.get("classifier_weight", 0.3)
            print(f"    Classifier (MobileViT): {cls_score:.0%}  (weight: {cls_w:.0%})")
        else:
            print(f"    Classifier (MobileViT): not available")

        if pipe_score is not None:
            pipe_w = scores.get("pipeline_weight", 0.7)
            print(f"    Pipeline (Groq Vision): {pipe_score:.0%}  (weight: {pipe_w:.0%})")

        if combined is not None:
            print(f"    Combined Score:         {combined:.0%}")

    print(f"\nSummary:")
    print(f"   {result.get('summary', 'N/A')}")

    if result.get("key_findings"):
        print(f"\nKey Findings:")
        for finding in result["key_findings"]:
            severity = finding.get("severity", "none")
            marker = {
                "critical": "[CRITICAL]",
                "moderate": "[MODERATE]",
                "minor":    "[MINOR]",
                "none":     "[NONE]",
            }.get(severity, "[?]")
            print(f"   {marker} {finding.get('feature', '?')}")
            print(f"     {finding.get('finding', '')}")

    if args.verbose:
        print(f"\nOverall Reasoning:")
        print(f"   {result.get('overall_reasoning', 'N/A')}")

        print(f"\nStage Details:")
        stages = result.get("stages", {})

        if "scene_analysis" in stages:
            print(f"\n   Stage 1 -- Scene Analysis:")
            scene = stages["scene_analysis"]
            print(f"     Subject: {scene.get('subject', '?')}")
            print(f"     Style: {scene.get('style', '?')}")
            print(f"     Setting: {scene.get('setting', '?')}")
            elements = scene.get("notable_elements", [])
            if elements:
                print(f"     Elements: {', '.join(str(e) for e in elements)}")

        if "features_identified" in stages:
            print(f"\n   Stage 2 -- Features Checked:")
            for feat in stages["features_identified"]:
                print(f"     * [{feat.get('priority', '?')}] {feat.get('category', '?')}")

        if "feature_inspections" in stages:
            print(f"\n   Stage 3 -- Inspection Results:")
            for insp in stages["feature_inspections"]:
                cat = insp.get("category", "?")
                conf = insp.get("confidence_ai", 0)
                artifacts = insp.get("artifacts_detected", [])
                print(f"     * {cat}: {conf:.0%} AI confidence")
                if artifacts:
                    for a in artifacts:
                        if isinstance(a, dict):
                            label = a.get("label", "?")
                            desc = a.get("description", "")
                            sev = a.get("severity", "?")
                            bbox = a.get("bbox", [])
                            bbox_str = ""
                            if bbox:
                                try:
                                    bbox_str = f" @ [{','.join(str(int(b)) for b in bbox)}]"
                                except (ValueError, TypeError):
                                    pass
                            print(f"       - [{sev}] {label}: {desc}{bbox_str}")
                        else:
                            print(f"       - {a}")

    print("\n" + "=" * 60)

    # Show annotated image path
    if result.get("annotated_image"):
        print(f"\nAnnotated image: {result['annotated_image']}")

    print()


if __name__ == "__main__":
    main()
