"""
MobileViT Classifier — Binary AI image classifier.

Uses a fine-tuned MobileViT model to quickly predict whether
an image is AI-generated or real. This is the "fast lane" of
the detection system (~1 second vs ~20 seconds for the full
Groq pipeline).

If PyTorch / transformers are not installed, this module
gracefully returns None so the rest of the pipeline still works.
"""

import os
from pathlib import Path

# ── Check if torch is available ──
_TORCH_AVAILABLE = False
torch = None
nn = None
transforms = None
Image = None
try:
    import torch
    import torch.nn as nn
    from torchvision import transforms
    from PIL import Image
    _TORCH_AVAILABLE = True
except ImportError:
    pass


# Model paths — try local copy first, then blue team directory
_LOCAL_MODEL = Path(__file__).parent / "models" / "mobilevit_best.pth"
_BLUE_TEAM_MODEL = Path(__file__).parent.parent.parent.parent / "blue team" / "ai_detection" / "models" / "mobilevit_best.pth"


def _find_model_path() -> str | None:
    """Find the MobileViT model checkpoint."""
    for p in [_LOCAL_MODEL, _BLUE_TEAM_MODEL]:
        if p.exists():
            return str(p)
    return None


class MobileViTClassifier:
    """
    Wrapper around a fine-tuned MobileViT model for AI image detection.

    Usage:
        classifier = MobileViTClassifier()
        result = classifier.predict("path/to/image.jpg")
        # result = {"ai_probability": 0.87, "real_probability": 0.13, ...}
    """

    def __init__(self, model_path: str = None, device: str = None):
        self.available = False
        self.model = None
        self.transform = None
        self.device = None

        if not _TORCH_AVAILABLE:
            print("   [classifier] PyTorch not installed — classifier disabled")
            print("   [classifier] Install with: pip install torch torchvision transformers")
            return

        model_path = model_path or _find_model_path()

        if not model_path or not os.path.exists(model_path):
            print(f"   [classifier] Model not found — classifier disabled")
            print(f"   [classifier] Searched: {_LOCAL_MODEL}")
            print(f"   [classifier] Searched: {_BLUE_TEAM_MODEL}")
            return

        try:
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            self._load_model(model_path)
            self.available = True
            print(f"   [classifier] MobileViT loaded on {self.device}")
            print(f"   [classifier] Model: {model_path}")
        except Exception as e:
            print(f"   [classifier] Failed to load model: {e}")
            self.available = False

    def _load_model(self, model_path: str):
        """Load the MobileViT model from checkpoint."""
        from transformers import MobileViTForImageClassification, MobileViTConfig

        # Torch 2.5.x backported the CVE-2025-32434 restriction from 2.6.
        import torch.serialization as _ts
        try:
            _ts.add_safe_globals([dict, list, set, tuple, int, float, str, bool])
        except AttributeError:
            pass  # torch < 2.4

        config = MobileViTConfig.from_pretrained("apple/mobilevit-small")
        config.num_labels = 2
        config.id2label = {0: "Real", 1: "AI"}
        config.label2id = {"Real": 0, "AI": 1}

        class _Wrapper(nn.Module):
            def __init__(self, cfg):
                super().__init__()
                self.mobilevit = MobileViTForImageClassification(cfg)
            def forward(self, x):
                return self.mobilevit(x).logits

        wrapper = _Wrapper(config)

        checkpoint = torch.load(
            model_path, map_location=self.device, weights_only=False
        )
        wrapper.load_state_dict(checkpoint["model_state_dict"])
        wrapper.to(self.device)
        wrapper.eval()

        self.model = wrapper
        self._is_wrapper = True

        # Image transforms (must match training)
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def predict(self, image_path: str) -> dict | None:
        """
        Predict whether an image is AI-generated.

        Returns:
            Dict with ai_probability, real_probability, confidence, predicted_class.
            Returns None if the classifier is not available.
        """
        if not self.available:
            return None

        try:
            img = Image.open(image_path).convert("RGB")
            tensor = self.transform(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(tensor)
                logits = outputs if isinstance(outputs, torch.Tensor) else outputs.logits
                probs = torch.softmax(logits, dim=1)
                predicted = torch.argmax(probs, dim=1).item()
                confidence = probs[0][predicted].item()

            return {
                "ai_probability": round(probs[0][1].item(), 4),
                "real_probability": round(probs[0][0].item(), 4),
                "confidence": round(confidence, 4),
                "predicted_class": "AI" if predicted == 1 else "Real",
                "is_ai": predicted == 1,
            }
        except Exception as e:
            print(f"   [classifier] Prediction error: {e}")
            return None

    def predict_from_bytes(self, image_bytes: bytes) -> dict | None:
        """Predict from raw image bytes."""
        if not self.available:
            return None

        try:
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                img.save(f, format="JPEG")
                tmp_path = f.name

            result = self.predict(tmp_path)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            print(f"   [classifier] Prediction error: {e}")
            return None
