import json
import base64
import os
import re
import requests
from PIL import Image, ImageDraw, ImageFont
import httpx
from openai import OpenAI


class ImageContentAnalyzer:
    """
    Système hybride d'analyse d'image:
      1. OCR.space API  → extraction texte brut (remplace Tesseract, gère ara+fra+eng)
      2. LLaVA          → lecture visuelle COMPLÈTE (source principale, gère cursives/stylisées)
      3. Llama 3.1 70B  → analyse contextuelle approfondie + reconstruction
      4. PIL            → highlighting contextuel si nécessaire
    """

    OCR_SPACE_URL = "https://api.ocr.space/parse/image"

    # Codes de langue OCR.space
    # https://ocr.space/OCRAPI#postparameters
    OCR_LANG_MAP = {
        "ara": "ara",
        "fra": "fre",
        "eng": "eng",
    }

    def __init__(
        self,
        api_key: str,
        ocr_space_key: str = "K87999402988957",
        base_url: str = "https://tokenfactory.esprit.tn/api",
    ):
        self.ocr_space_key = ocr_space_key

        self.http_client = httpx.Client(verify=False)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=self.http_client,
        )

        self.llava_model = "hosted_vllm/llava-v1.6-mistral-7b-hf"
        self.llama_model = "hosted_vllm/Llama-3.1-70B-Instruct"

    # ──────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────

    def image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")



    def _get_mime_type(self, image_path: str) -> str:
        ext = image_path.lower().rsplit(".", 1)[-1]
        return {
            "jpg" : "image/jpeg",
            "jpeg": "image/jpeg",
            "png" : "image/png",
            "gif" : "image/gif",
            "bmp" : "image/bmp",
            "tiff": "image/tiff",
            "tif" : "image/tiff",
            "webp": "image/webp",
            "pdf" : "application/pdf",
        }.get(ext, "image/jpeg")

    # ──────────────────────────────────────────────
    # ÉTAPE 1 — OCR.space API (remplace Tesseract)
    # ──────────────────────────────────────────────

    def extract_text_ocr_space(self, image_path: str) -> str:
        """
        Extrait le texte via l'API OCR.space (ara + fra + eng).
        Envoie l'image en base64 pour éviter les problèmes de chemin.
        Tente d'abord l'anglais+français, puis l'arabe séparément si rien détecté.
        Fallback : message d'erreur lisible.
        """
        image_b64  = self.image_to_base64(image_path)
        mime_type  = self._get_mime_type(image_path)
        b64_payload = f"data:{mime_type};base64,{image_b64}"

        results = []

        # Tentative 1 : anglais (engine 2 = meilleur pour texte latin + stylisé)
        for lang in ["eng", "fre"]:
            try:
                payload = {
                    "apikey"             : self.ocr_space_key,
                    "base64Image"        : b64_payload,
                    "language"           : lang,
                    "OCREngine"          : 2,          # Engine 2 : plus précis
                    "isOverlayRequired"  : False,
                    "detectOrientation"  : True,
                    "scale"              : True,        # Améliore la lisibilité
                    "isTable"            : False,
                    "filetype"           : mime_type.split("/")[-1].upper(),
                }
                resp = requests.post(
                    self.OCR_SPACE_URL,
                    data=payload,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("IsErroredOnProcessing"):
                    err = data.get("ErrorMessage", ["Erreur inconnue"])
                    print(f"   ⚠️  OCR.space erreur ({lang}): {err}")
                    continue

                parsed = data.get("ParsedResults", [])
                if parsed:
                    text = parsed[0].get("ParsedText", "").strip()
                    if text and len(text) >= 3:
                        results.append(text)

            except requests.exceptions.Timeout:
                print(f"   ⚠️  OCR.space timeout pour lang={lang}")
            except Exception as e:
                print(f"   ⚠️  OCR.space erreur ({lang}): {str(e)}")

        # Tentative 2 : arabe (engine 1 car engine 2 ne supporte pas ara)
        try:
            payload_ara = {
                "apikey"            : self.ocr_space_key,
                "base64Image"       : b64_payload,
                "language"          : "ara",
                "OCREngine"         : 1,
                "isOverlayRequired" : False,
                "detectOrientation" : True,
                "scale"             : True,
                "filetype"          : mime_type.split("/")[-1].upper(),
            }
            resp = requests.post(
                self.OCR_SPACE_URL,
                data=payload_ara,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("IsErroredOnProcessing"):
                parsed = data.get("ParsedResults", [])
                if parsed:
                    text_ara = parsed[0].get("ParsedText", "").strip()
                    if text_ara and len(text_ara) >= 3:
                        results.append(text_ara)

        except Exception as e:
            print(f"   ⚠️  OCR.space arabe: {str(e)}")

        if not results:
            return "[ERREUR: Aucun texte détecté par OCR.space]"

        # Fusionner les résultats uniques
        combined = "\n".join(dict.fromkeys(results))
        return combined.strip()

    # ──────────────────────────────────────────────
    # ÉTAPE 2a — LLaVA : lecture visuelle COMPLÈTE (source principale)
    # ──────────────────────────────────────────────

    def read_full_text_llava(self, image_path: str) -> str:
        """
        LLaVA lit TOUT le texte visible dans l'image directement.
        Gère polices cursives, manuscrites, stylisées, arabe, etc.
        C'est la SOURCE PRINCIPALE du texte (prioritaire sur OCR.space).
        """
        image_b64 = self.image_to_base64(image_path)

        prompt = """Lis TOUT le texte visible dans cette image, exactement tel qu'il apparaît.
Inclus chaque mot, même s'il est en police cursive, manuscrite, stylisée ou en arabe.
Conserve la structure (sauts de ligne si plusieurs lignes).
Réponds UNIQUEMENT avec le texte lu, sans commentaire ni explication."""

        try:
            response = self.client.chat.completions.create(
                model=self.llava_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                temperature=0.0,
                max_tokens=500,
            )
            result = response.choices[0].message.content.strip()
            return result if result else ""

        except Exception as e:
            print(f"   ⚠️  LLaVA (lecture complète) indisponible: {str(e)}")
            return ""



    # ──────────────────────────────────────────────
    # ÉTAPE 3 — Llama : analyse sémantique
    # ──────────────────────────────────────────────

    def analyze_content_llama(
        self, best_text: str, ocr_text: str = "", llava_text: str = ""
    ) -> dict:
        """
        Analyse sémantique avancée avec Llama 3.1 70B.
        Utilise best_text (LLaVA si dispo, sinon OCR.space) comme source principale.
        Focus sur le contexte et la compréhension du message.
        """
        context = f'TEXTE PRINCIPAL (source la plus fiable):\n"{best_text}"'

        if ocr_text and ocr_text != best_text:
            context += f'\n\nTEXTE OCR.space (pour comparaison):\n"{ocr_text}"'

        if llava_text and llava_text != best_text:
            context += f'\n\nTEXTE LU PAR LLAVA:\n"{llava_text}"'

        prompt = f"""{context}

Fais une analyse PROFESSIONNELLE axée sur le CONTEXTE et le MESSAGE:

ÉTAPE 1 — RECONSTRUCTION:
Corrige les erreurs éventuelles pour obtenir un texte propre et cohérent.

ÉTAPE 2 — ANALYSE CONTEXTUELLE APPROFONDIE:
- Type de contenu (marketing / motivationnel / éducatif / technique / publicité / etc.)
- Objectif principal (motiver / vendre / informer / convaincre / alerter / etc.)
- Audience cible (grand public / entreprises / jeunes / professionnels / etc.)
- Ton et style du message (formel / informel / inspirant / urgent / etc.)
- Message clé et valeur ajoutée
- Contexte d'utilisation probable (réseaux sociaux / affiche / site web / etc.)

Réponds UNIQUEMENT en JSON valide (sans markdown ni backticks):
{{
  "description_avancee": {{
    "type_contenu": "...",
    "objectif": "...",
    "audience_cible": "...",
    "ton_style": "...",
    "message_cle": "...",
    "contexte_utilisation": "...",
    "resume": "Description détaillée du contenu et de son contexte (3-4 phrases)"
  }},
  "langue": "arabe / français / anglais / mixte",
  "est_logique": "OUI / NON / PARTIELLEMENT",
  "explication": "Explication claire du résultat et de la cohérence du message",
  "texte_reconstruit": "..."
}}

RÈGLES IMPORTANTES:
- Focus sur la COMPRÉHENSION du message et son CONTEXTE
- Si le texte est clair et cohérent → est_logique = "OUI"
- Si le message est compréhensible malgré quelques imperfections → "PARTIELLEMENT"
- Si incohérent ou incompréhensible → "NON"
- Analyse approfondie du contexte et de l'intention du message"""

        try:
            response = self.client.chat.completions.create(
                model=self.llama_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un expert en analyse de contenu et correction d'erreurs OCR. "
                            "Sois précis et objectif. Si le texte est propre, dis-le clairement. "
                            "Réponds toujours en JSON valide sans markdown."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )

            result_text = response.choices[0].message.content
            start = result_text.find("{")
            end   = result_text.rfind("}") + 1

            if start != -1 and end > start:
                result = json.loads(result_text[start:end])
                return result

            raise ValueError("JSON invalide")

        except Exception as e:
            print(f"   ⚠️  Erreur Llama: {str(e)}")
            return self._fallback_analysis(best_text)

    # ──────────────────────────────────────────────
    # Analyse de secours (sans LLM)
    # ──────────────────────────────────────────────

    def _fallback_analysis(self, text: str) -> dict:
        if re.search(r"[\u0600-\u06FF]", text):
            langue = "arabe"
        elif re.search(r"[àâäéèêëïîôùûüÿç]", text, re.IGNORECASE):
            langue = "français"
        else:
            langue = "anglais"

        return {
            "description_avancee": {
                "type_contenu"       : "général",
                "objectif"           : "informer",
                "audience_cible"     : "général",
                "ton_style"          : "neutre",
                "message_cle"        : "Contenu textuel",
                "contexte_utilisation": "général",
                "resume"             : "Analyse de secours. Le texte a été extrait mais l'analyse contextuelle complète n'est pas disponible.",
            },
            "langue"             : langue,
            "est_logique"        : "PARTIELLEMENT",
            "explication"        : "Analyse contextuelle limitée (mode de secours).",
            "texte_reconstruit"  : text,
        }

    # ──────────────────────────────────────────────
    # ÉTAPE 4 — PIL : highlighting
    # ──────────────────────────────────────────────

    def highlight_problems(
        self,
        image_path: str,
        est_logique: str,
        description: dict,
        output_path: str = "image_highlighted.jpg",
    ) -> str | None:
        if est_logique == "OUI":
            print("   ℹ️  Contenu cohérent, pas de highlighting nécessaire")
            return None

        img = Image.open(image_path).convert("RGBA")

        # Overlay léger selon le niveau de cohérence
        if est_logique == "NON":
            overlay_color = (220, 50, 50, 35)
        else:  # PARTIELLEMENT
            overlay_color = (255, 165, 0, 25)
        
        overlay = Image.new("RGBA", img.size, overlay_color)
        img = Image.alpha_composite(img, overlay)

        banner_h = 140
        banner   = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bd       = ImageDraw.Draw(banner)
        bd.rectangle([(0, 0), (img.width, banner_h)], fill=(15, 15, 15, 210))
        img  = Image.alpha_composite(img, banner)
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arial.ttf", 28)
            font_body  = ImageFont.truetype("arial.ttf", 18)
            font_small = ImageFont.truetype("arial.ttf", 15)
        except Exception:
            font_title = ImageFont.load_default()
            font_body  = font_title
            font_small = font_title

        draw.text((20, 14), "📊  ANALYSE DE CONTENU", fill=(255, 220, 50, 255), font=font_title)

        type_contenu = description.get('type_contenu', 'N/A')
        objectif = description.get('objectif', 'N/A')
        draw.text((20, 56), f"Type: {type_contenu} | Objectif: {objectif}", fill=(255, 255, 255, 255), font=font_body)

        status_color = (220, 50, 50, 255) if est_logique == "NON" else (255, 165, 0, 255)
        draw.text((20, 88), f"Cohérence: {est_logique}", fill=status_color, font=font_body)

        message_cle = description.get('message_cle', '')[:60]
        if message_cle:
            draw.text((20, 112), f"Message: {message_cle}...", fill=(180, 180, 180, 255), font=font_small)

        img = img.convert("RGB")
        img.save(output_path, quality=95)
        print(f"   ✅ Image avec analyse contextuelle sauvegardée : {output_path}")
        return output_path

    # ──────────────────────────────────────────────
    # Pipeline principal
    # ──────────────────────────────────────────────

    def analyze_image_complete(self, image_path: str) -> dict:
        """
        Pipeline complet :
          1.  OCR.space  → texte brut (fallback / complément)
          2.  LLaVA      → lecture COMPLÈTE de l'image (source principale)
          3.  Llama      → analyse contextuelle approfondie sur le meilleur texte
          4.  PIL        → highlighting contextuel si nécessaire
        """
        if not os.path.exists(image_path):
            print(f"❌ Image introuvable : {image_path}")
            return {}

        # ── Étape 1 : OCR.space ──
        print("📸 ÉTAPE 1 : Extraction via OCR.space API...")
        ocr_text = self.extract_text_ocr_space(image_path)
        print(f"   → {len(ocr_text)} caractères extraits")
        print(f"   → Aperçu : {repr(ocr_text[:100])}")

        # ── Étape 2a : LLaVA lecture complète (SOURCE PRINCIPALE) ──
        print("\n👁  ÉTAPE 2a : LLaVA — lecture visuelle complète...")
        llava_full_text = self.read_full_text_llava(image_path)

        if llava_full_text:
            print(f"   ✅ LLaVA a lu : {repr(llava_full_text[:120])}")
            best_text = llava_full_text
            llava_ok  = True
        else:
            print("   ⚠️  LLaVA indisponible → utilisation du texte OCR.space")
            best_text = ocr_text
            llava_ok  = False

        # ── Étape 2b : Ignorée (focus sur le contexte) ──
        print(f"\n✅ ÉTAPE 2b : Focus sur l'analyse contextuelle")

        # ── Étape 3 : Llama ──
        print(f"\n🧠 ÉTAPE 3 : Analyse contextuelle approfondie avec Llama 3.1 70B...")
        analyse = self.analyze_content_llama(best_text, ocr_text, llava_full_text)

        if llava_ok and not analyse.get("explication"):
            analyse["explication"] = (
                "Le texte a été lu correctement par LLaVA. "
                "Analyse contextuelle complète effectuée."
            )

        desc = analyse.get("description_avancee", {})
        print(f"   → Type              : {desc.get('type_contenu', 'N/A')}")
        print(f"   → Objectif          : {desc.get('objectif', 'N/A')}")
        print(f"   → Audience          : {desc.get('audience_cible', 'N/A')}")
        print(f"   → Ton/Style         : {desc.get('ton_style', 'N/A')}")
        print(f"   → Message clé       : {desc.get('message_cle', 'N/A')}")
        print(f"   → Contexte          : {desc.get('contexte_utilisation', 'N/A')}")
        print(f"   → Langue            : {analyse.get('langue', 'N/A')}")
        print(f"   → Cohérence         : {analyse.get('est_logique', 'N/A')}")

        # ── Étape 4 : Highlighting contextuel ──
        image_highlighted = None
        if analyse.get("est_logique") in ["NON", "PARTIELLEMENT"]:
            print(f"\n🎨 ÉTAPE 4 : Génération image avec analyse contextuelle...")
            image_highlighted = self.highlight_problems(
                image_path,
                analyse.get("est_logique"),
                desc,
                output_path="image_highlighted.jpg",
            )
        else:
            print(f"\n✅ ÉTAPE 4 : Contenu cohérent, pas de highlighting nécessaire")

        return {
            "texte_ocr_space"        : ocr_text,
            "texte_llava"            : llava_full_text,
            "texte_utilise"          : best_text,
            "texte_reconstruit"      : analyse.get("texte_reconstruit", best_text),
            "description_avancee"    : analyse.get("description_avancee", {}),
            "langue"                 : analyse.get("langue", "N/A"),
            "est_logique"            : analyse.get("est_logique", "N/A"),
            "explication"            : analyse.get("explication", ""),
            "source_principale"      : "LLaVA" if llava_ok else "OCR.space",
            "image_highlighted"      : image_highlighted,
        }

    def __del__(self):
        if hasattr(self, "http_client"):
            self.http_client.close()


# ──────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    API_KEY        = "sk-f90b3b0c49044060b61a6dd33aa6b827"
    OCR_SPACE_KEY  = "K87999402988957"
    BASE_URL       = "https://tokenfactory.esprit.tn/api"
    IMAGE_PATH     = "hack5.jpg"

    analyzer = ImageContentAnalyzer(
        api_key=API_KEY,
        ocr_space_key=OCR_SPACE_KEY,
        base_url=BASE_URL,
    )

    print("🚀 Analyse hybride : OCR.space + LLaVA (source principale) + Llama (analyse contextuelle)\n")
    print("=" * 65)

    resultat = analyzer.analyze_image_complete(IMAGE_PATH)

    if not resultat:
        print("❌ Analyse échouée.")
        exit(1)

    print("\n" + "=" * 65)
    print("📋 RÉSULTATS FINAUX")
    print("=" * 65)

    print(f"\n🔧 SOURCE PRINCIPALE : {resultat['source_principale']}")
    print(f"\n📝 TEXTE OCR.space :\n{resultat['texte_ocr_space']}")

    if resultat.get("texte_llava"):
        print(f"\n👁  TEXTE LU PAR LLAVA :\n{resultat['texte_llava']}")

    print(f"\n⭐ TEXTE UTILISÉ POUR L'ANALYSE :\n{resultat['texte_utilise']}")

    if (
        resultat.get("texte_reconstruit")
        and resultat["texte_reconstruit"] != resultat["texte_utilise"]
    ):
        print(f"\n✨ TEXTE RECONSTRUIT (CORRIGÉ) :\n{resultat['texte_reconstruit']}")

    desc = resultat.get("description_avancee", {})
    print(f"\n📊 ANALYSE CONTEXTUELLE APPROFONDIE :")
    print(f"   Type de contenu       : {desc.get('type_contenu', 'N/A')}")
    print(f"   Objectif              : {desc.get('objectif', 'N/A')}")
    print(f"   Audience cible        : {desc.get('audience_cible', 'N/A')}")
    print(f"   Ton et style          : {desc.get('ton_style', 'N/A')}")
    print(f"   Message clé           : {desc.get('message_cle', 'N/A')}")
    print(f"   Contexte d'utilisation: {desc.get('contexte_utilisation', 'N/A')}")
    print(f"\n📄 RÉSUMÉ :\n{desc.get('resume', 'N/A')}")

    print(f"\n🌍 LANGUE      : {resultat['langue']}")
    print(f"✅ COHÉRENCE   : {resultat['est_logique']}")
    print(f"\n💡 EXPLICATION :\n{resultat['explication']}")

    if resultat.get("image_highlighted"):
        print(f"\n🖼  IMAGE GÉNÉRÉE : {resultat['image_highlighted']}")

    output_json = {
        "texte_ocr_space"        : resultat["texte_ocr_space"],
        "texte_llava"            : resultat.get("texte_llava"),
        "texte_utilise"          : resultat["texte_utilise"],
        "texte_reconstruit"      : resultat.get("texte_reconstruit"),
        "description_avancee"    : resultat.get("description_avancee"),
        "langue"                 : resultat["langue"],
        "est_logique"            : resultat["est_logique"],
        "explication"            : resultat["explication"],
        "source_principale"      : resultat["source_principale"],
        "image_highlighted"      : resultat.get("image_highlighted"),
    }

    with open("analyse_complete.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Résultats sauvegardés dans : analyse_complete.json")
    print("=" * 65)