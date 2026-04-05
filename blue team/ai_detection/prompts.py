"""
Multi-stage prompts for the AI image detection pipeline.

Pipeline stages:
  1. Scene Analysis — Understand what's in the image
  2. Feature Identification — Based on the scene, decide what AI-telltale features to check
  3. Feature Inspection — For each feature, do a focused deep inspection
  4. Final Verdict — Aggregate findings into a confidence score
"""

# ──────────────────────────────────────────────
# STAGE 1: Scene Analysis
# ──────────────────────────────────────────────
SCENE_ANALYSIS_PROMPT = """You are an expert image forensics analyst. Analyze this image and provide a detailed description of:

1. **Subject**: What is the main subject? (person, animal, landscape, object, etc.)
2. **Setting**: Where does this appear to be? (indoor, outdoor, studio, etc.)
3. **Composition**: How is the image composed? (close-up, wide shot, portrait, etc.)
4. **Style**: What style is this? (photograph, illustration, 3D render, painting, etc.)
5. **Notable elements**: List all notable visual elements (text, reflections, shadows, hands, faces, backgrounds, etc.)

Respond in the following JSON format ONLY — no extra text:
{
  "subject": "...",
  "subject_type": "person|animal|landscape|object|food|vehicle|building|abstract|other",
  "setting": "...",
  "composition": "...",
  "style": "photograph|illustration|3d_render|painting|digital_art|other",
  "notable_elements": ["element1", "element2", ...],
  "contains_people": true/false,
  "contains_text": true/false,
  "contains_reflections": true/false
}"""

# ──────────────────────────────────────────────
# STAGE 2: Feature Identification
# ──────────────────────────────────────────────
FEATURE_IDENTIFICATION_PROMPT = """You are an expert AI-generated image forensics analyst. Based on the following scene analysis, determine which specific visual features should be inspected for signs of AI generation.

Scene Analysis:
{scene_analysis}

For each category below, decide if it's RELEVANT to check in this specific image. Only include categories that are actually present in the image.

Possible categories:
- **hands_fingers**: Check if there are hands/fingers visible — AI often produces extra fingers, fused fingers, inconsistent nail count
- **face_anatomy**: Check facial features — asymmetric eyes, misaligned pupils, uncanny valley expressions, smooth/plastic skin
- **text_writing**: Check any visible text — AI misspells words, produces nonsensical characters, inconsistent fonts
- **reflections_mirrors**: Check reflections — AI fails at consistent reflections in mirrors, glasses, water
- **background_consistency**: Check background — AI produces blurry, morphing, or inconsistent backgrounds
- **lighting_shadows**: Check lighting — AI produces inconsistent shadow directions, missing shadows, wrong lighting angles
- **skin_texture**: Check skin — AI produces overly smooth, plastic-looking, or pattern-repetitive skin
- **hair_detail**: Check hair — AI produces hair that merges into background, impossible strands, uniform textures
- **clothing_fabric**: Check clothing — AI produces warped patterns, impossible folds, dissolving edges
- **symmetry_geometry**: Check geometric symmetry — AI often produces too-perfect or warped symmetry
- **edges_boundaries**: Check object boundaries — AI produces soft bleeding edges, object merging
- **depth_perspective**: Check perspective — AI produces impossible vanishing points, scale inconsistencies
- **teeth_mouth**: Check teeth/mouth — AI produces extra teeth, asymmetric teeth, gums that blend
- **jewelry_accessories**: Check accessories — AI produces warped earrings, melting glasses frames
- **overall_coherence**: Always check — overall visual coherence and consistency

Respond in JSON format ONLY:
{{
  "features_to_check": [
    {{
      "category": "category_name",
      "reason": "Why this is relevant for this image",
      "priority": "high|medium|low"
    }}
  ]
}}"""

# ──────────────────────────────────────────────
# STAGE 3: Feature Inspection (per feature)
# ──────────────────────────────────────────────
FEATURE_INSPECTION_PROMPT = """You are an expert AI-generated image forensics analyst performing a FOCUSED inspection.

You are checking for ONE specific category of AI artifacts: **{category}**

Context about the image: {scene_summary}
Reason for this check: {reason}

INSPECTION GUIDELINES for "{category}":
{inspection_guidelines}

Examine this specific aspect of the image very carefully. Look for subtle artifacts that indicate AI generation.

IMPORTANT: Be objective. Many real photos can have unusual features too. Only flag issues that are genuinely suspicious.

For EACH artifact you detect, provide the approximate BOUNDING BOX as percentage coordinates of the image (0-100).
Think of the image as a grid: x=0 is the left edge, x=100 is the right edge, y=0 is the top, y=100 is the bottom.
The bounding box should tightly surround the specific area where you see the artifact.

Respond in JSON format ONLY:
{{
  "category": "{category}",
  "findings": "Detailed description of what you found",
  "artifacts_detected": [
    {{
      "label": "Short name of the artifact",
      "description": "What is wrong in this area",
      "bbox": [x_min, y_min, x_max, y_max],
      "severity": "critical|moderate|minor"
    }}
  ],
  "confidence_ai": 0.0 to 1.0,
  "reasoning": "Step-by-step reasoning for your confidence score"
}}"""

# ──────────────────────────────────────────────
# STAGE 4: Final Verdict
# ──────────────────────────────────────────────
FINAL_VERDICT_PROMPT = """You are an expert AI-generated image forensics analyst. You have completed a multi-stage analysis of an image. Review all findings below and provide a FINAL VERDICT.

## Scene Analysis
{scene_analysis}

## Feature Inspections
{feature_inspections}

Consider the following when making your judgment:
1. How many features showed AI artifacts?
2. How severe are the artifacts? (subtle vs. obvious)
3. Could any "artifacts" be explained by camera quality, compression, lighting, or editing?
4. What is the overall coherence of the image?
5. The style — is this meant to look like digital art (which is OK) or a photograph (where AI tells are more suspicious)?

Respond in JSON format ONLY:
{{
  "verdict": "likely_ai_generated" | "possibly_ai_generated" | "likely_authentic" | "uncertain",
  "confidence": 0.0 to 1.0,
  "summary": "2-3 sentence summary for a non-technical user",
  "key_findings": [
    {{
      "feature": "feature_name",
      "finding": "what was found",
      "severity": "critical|moderate|minor|none"
    }}
  ],
  "overall_reasoning": "Detailed reasoning for the final verdict"
}}"""

# ──────────────────────────────────────────────
# Inspection guidelines per category
# ──────────────────────────────────────────────
INSPECTION_GUIDELINES = {
    "hands_fingers": """
- Count the fingers on each visible hand. Humans have exactly 5 fingers per hand.
- Check if fingers are fused, split, or have extra joints.
- Look for impossible bending angles.
- Check fingernails — are they consistent in size and shape?
- Look for hands that fade into objects or clothing.
- Check thumb positioning — is the thumb on the correct side?
""",
    "face_anatomy": """
- Check eye alignment — are both eyes at the same height and angle?
- Look at pupil shape and consistency between eyes.
- Check ear symmetry and shape.
- Look for the "uncanny valley" — does the face look subtly wrong?
- Check if eyebrows are natural or painted-on looking.
- Look for skin that appears too smooth or plastic-like (poreless).
- Check if facial features proportions are anatomically correct.
""",
    "text_writing": """
- Read any visible text — does it make sense? Are words spelled correctly?
- Check for nonsensical characters or symbols mixed in.
- Look for inconsistent font sizes or styles within the same text block.
- Check if text follows proper orientation and perspective.
- Look for characters that morph or blend into the background.
""",
    "reflections_mirrors": """
- If there are reflective surfaces, does the reflection match the scene?
- Check glasses — do the reflections make sense?
- Look at water reflections — are they geometrically correct?
- Check mirror reflections — does the reflected image match?
""",
    "background_consistency": """
- Look for repeating patterns in the background.
- Check for objects that morph or blend into each other.
- Look for inconsistent levels of detail (sharp foreground, melting background).
- Check for impossible architectural features.
- Look for floating or disconnected objects.
""",
    "lighting_shadows": """
- Check if shadows all point in a consistent direction.
- Look for missing shadows where they should exist.
- Check if lighting on the subject matches the environment lighting.
- Look for impossible light sources or reflections.
- Check for inconsistent brightness across the image.
""",
    "skin_texture": """
- Look for overly smooth, airbrushed skin with no pores.
- Check for repeating texture patterns.
- Look for skin that transitions oddly at edges (neck, wrists).
- Check for inconsistent skin tones or plastic-looking appearance.
- Look for micro-patterns or grid artifacts in skin areas.
""",
    "hair_detail": """
- Check individual hair strands — do they look natural?
- Look for hair that merges into the background.
- Check for uniform blob-like hair textures.
- Look for impossible hair physics (defying gravity unnaturally).
- Check hair vs. skin boundaries.
""",
    "clothing_fabric": """
- Check fabric patterns — do they warp or stretch impossibly?
- Look for clothing edges that dissolve into the background.
- Check folds and wrinkles — are they physically plausible?
- Look for buttons, zippers, or fasteners that look melted.
- Check pattern consistency across the garment.
""",
    "symmetry_geometry": """
- Check if the image has unnaturally perfect symmetry.
- Look for geometric shapes that warp or distort.
- Check if architectural lines are straight and consistent.
- Look for impossible geometry or Escher-like artifacts.
""",
    "edges_boundaries": """
- Check object boundaries — are they clean or do they bleed?
- Look for objects that merge into each other.
- Check for haloing effects around subjects.
- Look for soft, undefined boundaries where sharp edges should exist.
""",
    "depth_perspective": """
- Check if the perspective is consistent throughout the image.
- Look for objects at wrong scales relative to their distance.
- Check vanishing points — are parallel lines consistent?
- Look for impossible spatial relationships between objects.
""",
    "teeth_mouth": """
- Count visible teeth — is the number reasonable?
- Check for asymmetric or oddly shaped teeth.
- Look for gums that blend into teeth or lips.
- Check if the mouth opening is anatomically correct.
- Look for teeth that appear to merge or float.
""",
    "jewelry_accessories": """
- Check earrings — are they consistent between ears?
- Look for glasses frames that warp or disconnect.
- Check necklaces and chains — do links look consistent?
- Look for watches or bracelets with impossible designs.
""",
    "overall_coherence": """
- Step back and look at the overall image — does anything feel "off"?
- Check if the image style is consistent throughout.
- Look for areas that seem more detailed than others for no reason.
- Check if the image has that characteristic AI "dreamlike" quality.
- Look for micro-artifacts: tiny areas of noise, color bleeding, or distortion.
- Check if the image looks like it could exist in reality.
"""
}
