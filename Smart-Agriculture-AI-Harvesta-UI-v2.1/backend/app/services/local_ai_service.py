"""Local-first conversational agriculture assistant.

The preferred provider is a locally running Ollama server. When Ollama is not
installed or a model is not available, the service falls back to a small,
deterministic agriculture knowledge assistant so the chat surface still works
without an internet connection or paid API key.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib import error, request

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are Harvesta, a cautious local-first farming assistant.
Use the farmer's supplied farm context when it is relevant. Give short,
practical answers with observations, next checks, and clear uncertainty.
Never claim that an image prediction or sensor estimate is a confirmed
diagnosis. Do not invent pesticide names, dosages, legal approvals, weather
facts, or sensor readings. Recommend a qualified local agronomist for severe,
fast-spreading, or uncertain crop problems. Ask for the crop, growth stage,
location, and recent observations when important details are missing.
"""


class LocalAIService:
    """Generates chat replies with local Ollama and a zero-network fallback."""

    _INSTANT_TOPIC_TERMS = (
        "disease",
        "leaf",
        "spot",
        "blight",
        "photo",
        "image",
        "irrig",
        "water",
        "moisture",
        "dry",
        "soil",
        "ph",
        "npk",
        "nitrogen",
        "phosph",
        "potassium",
        "weather",
        "rain",
        "temperature",
        "wind",
        "climate",
        "நோய்",
        "இலை",
        "தண்ணீர்",
        "மண்",
        "வானிலை",
        "நீர்ப்பாசனம்",
        "payanir",
        "thanni",
        "mannu",
        "ilai",
        "noi",
        "mazhai",
    )

    _LANGUAGE_NAMES = {
        "en": "English",
        "ta": "Tamil",
        "hi": "Hindi",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
    }

    @classmethod
    def detect_language(cls, message: str, fallback: str = "en") -> str:
        """Detect supported Indian scripts and common romanized Tamil phrases."""
        text = message or ""
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"
        if re.search(r"[\u0C80-\u0CFF]", text):
            return "kn"
        if re.search(r"[\u0D00-\u0D7F]", text):
            return "ml"
        lower = re.sub(r"[^a-z ]", " ", text.lower())
        tamil_markers = {
            "ennaku", "enakku", "epadi", "eppadi", "pananum", "pannanum",
            "iruku", "irukku", "venum", "enna", "mari", "marii", "athu",
            "inga", "anga", "solu", "sollu", "pannu", "nalatha", "mazhai",
        }
        if len(set(lower.split()) & tamil_markers) >= 2:
            return "ta"
        return fallback if fallback in cls._LANGUAGE_NAMES else "en"

    @staticmethod
    def _base_url() -> str:
        return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")

    @staticmethod
    def _model_name() -> str:
        return os.getenv("OLLAMA_MODEL", "gemma3:4b").strip() or "gemma3:4b"

    @staticmethod
    def _mode() -> str:
        mode = os.getenv("LOCAL_AI_MODE", "auto").strip().lower()
        return mode if mode in {"auto", "ollama", "offline"} else "auto"

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns provider readiness without exposing host credentials."""
        mode = cls._mode()
        if mode == "offline":
            return {
                "mode": mode,
                "provider": "offline-knowledge",
                "ready": True,
                "model": "harvesta-offline-v1",
                "message": "Offline agriculture knowledge assistant is ready.",
            }

        try:
            req = request.Request(f"{cls._base_url()}/api/tags", method="GET")
            with request.urlopen(req, timeout=2.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
            installed = [item.get("name", "") for item in payload.get("models", [])]
            configured = cls._model_name()
            ready = configured in installed or any(
                name.split(":")[0] == configured.split(":")[0] for name in installed
            )
            return {
                "mode": mode,
                "provider": "ollama",
                "ready": ready,
                "model": configured,
                "installed_models": installed,
                "message": (
                    "Local Ollama model is ready."
                    if ready
                    else f"Ollama is running, but model '{configured}' is not installed."
                ),
            }
        except Exception:
            return {
                "mode": mode,
                "provider": "offline-knowledge",
                "ready": True,
                "model": "harvesta-offline-v1",
                "message": "Ollama is unavailable; the offline agriculture assistant will be used.",
            }

    @classmethod
    def generate_reply(
        cls,
        messages: List[Dict[str, str]],
        farm_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Returns content, provider, and model for a conversation turn."""
        if cls._mode() != "offline":
            try:
                latest = messages[-1].get("content", "") if messages else ""
                language = cls.detect_language(latest)
                return cls._generate_with_ollama(messages, farm_context or {}, language)
            except Exception as exc:
                logger.info("Local Ollama chat unavailable; using offline fallback: %s", exc)
                if cls._mode() == "ollama":
                    logger.warning("LOCAL_AI_MODE=ollama requested but provider call failed.")

        latest = messages[-1].get("content", "") if messages else ""
        language = cls.detect_language(latest)
        return {
            "content": cls._offline_reply(latest, farm_context or {}, language),
            "provider": "offline-knowledge",
            "model": "harvesta-offline-v1",
        }

    @classmethod
    def generate_offline_reply(
        cls,
        message: str,
        farm_context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        """Forces the built-in zero-network fallback after a provider failure."""
        return {
            "content": cls._offline_reply(
                message,
                farm_context or {},
                language or cls.detect_language(message),
            ),
            "provider": "offline-knowledge",
            "model": "harvesta-offline-v1",
        }

    @classmethod
    def can_answer_instantly(cls, message: str) -> bool:
        """Use the zero-wait knowledge path for short, common farming questions."""
        clean = re.sub(r"\s+", " ", (message or "").strip()).lower()
        if not clean or len(clean) > 320:
            return False

        if re.search(r"\b(hi|hello|hey)\b", clean):
            return True
        if any(phrase in clean for phrase in ("what can you do", "how can you help", "help me")):
            return True
        if cls.is_crop_status_question(clean):
            return True
        return any(term in clean for term in cls._INSTANT_TOPIC_TERMS)

    @staticmethod
    def is_crop_status_question(message: str) -> bool:
        # Include the common phone dictation/typing mistake in "crip status".
        clean = (message or "").lower()
        return bool(re.search(r"\b(crop|crops|crip|farm|field)\b", clean) and
                    re.search(r"\b(status|doing|condition|health|update)\b", clean))

    @classmethod
    def _generate_with_ollama(
        cls,
        messages: List[Dict[str, str]],
        farm_context: Dict[str, Any],
        language: str = "en",
    ) -> Dict[str, str]:
        context_text = json.dumps(farm_context, ensure_ascii=True, default=str)
        ollama_messages = [
            {
                "role": "system",
                "content": (
                    f"{SYSTEM_PROMPT}\nReply only in {cls._LANGUAGE_NAMES.get(language, 'English')}. "
                    "Match the farmer's writing style, including romanized Tamil when used.\n"
                    f"Farmer context: {context_text}"
                ),
            }
        ]
        for item in messages[-16:]:
            role = item.get("role", "user")
            if role not in {"user", "assistant", "system"}:
                role = "user"
            ollama_messages.append({"role": role, "content": item.get("content", "")[:6000]})

        body = json.dumps(
            {
                "model": cls._model_name(),
                "messages": ollama_messages,
                "stream": False,
                "options": {"temperature": 0.2},
            }
        ).encode("utf-8")
        req = request.Request(
            f"{cls._base_url()}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, error.HTTPError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        content = str(payload.get("message", {}).get("content", "")).strip()
        if not content:
            raise RuntimeError("Ollama returned an empty response.")
        return {"content": content, "provider": "ollama", "model": cls._model_name()}

    @staticmethod
    def _latest_soil_moisture(context: Dict[str, Any]) -> Optional[float]:
        value = context.get("latest_field_analysis", {}).get("soil_moisture")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _offline_reply(cls, message: str, context: Dict[str, Any], language: str = "en") -> str:
        """Small deterministic fallback for common farmer questions."""
        clean = re.sub(r"\s+", " ", message.strip())
        lower = clean.lower()
        crops = [str(c) for c in context.get("crops", []) if c]
        crop_text = ", ".join(crops[:5]) if crops else "your crop"

        if not clean:
            return "Please type a question about irrigation, soil, crop health, weather, or a leaf photo."

        # Localized zero-network guidance keeps voice and text chat useful even
        # when the larger local model is not running.
        if language == "ta":
            if any(term in lower for term in ("disease", "leaf", "spot", "photo", "image", "noi", "ilai", "நோய்", "இலை")):
                return (
                    "நோய் கண்டறிதல் பகுதியில் பகல் வெளிச்சத்தில் எடுத்த தெளிவான இலையின் படத்தை பதிவேற்றுங்கள். "
                    "இது முதற்கட்ட AI பரிசோதனை மட்டுமே. பாதிப்பு வேகமாகப் பரவினால் உள்ளூர் வேளாண் நிபுணரை அணுகுங்கள்."
                )
            if any(term in lower for term in ("water", "moisture", "irrig", "thanni", "mazhai", "தண்ணீர்", "நீர்ப்பாசனம்")):
                moisture = cls._latest_soil_moisture(context)
                saved = f"கடைசியாக சேமித்த மண் ஈரப்பதம் {moisture:.1f}%. " if moisture is not None else "சமீபத்திய மண் ஈரப்பதத் தகவல் இல்லை. "
                return saved + "பயிரின் வளர்ச்சி நிலை, மண்ணின் தன்மை, சமீபத்திய மழை மற்றும் வேர் ஆழ ஈரப்பதத்தைச் சரிபார்த்து பின்னர் நீர்ப்பாசனம் செய்யுங்கள்."
            return (
                f"{crop_text} பற்றி உதவ முடியும். பயிர், வளர்ச்சி நிலை, நீங்கள் கவனித்த அறிகுறி, "
                "சமீபத்திய வானிலை மற்றும் மண் அளவீட்டைச் சொல்லுங்கள். நீங்கள் Tanglish-ல் கேட்டாலும் அதே மொழியில் பதிலளிப்பேன்."
            )
        localized_generic = {
            "hi": "मैं आपकी फसल, सिंचाई, मिट्टी और पौधों के स्वास्थ्य में मदद कर सकता हूँ। कृपया फसल, विकास चरण, लक्षण, हाल का मौसम और उपलब्ध मिट्टी रीडिंग बताइए।",
            "te": "పంట, నీటిపారుదల, నేల మరియు మొక్కల ఆరోగ్యం గురించి నేను సహాయం చేయగలను. పంట, పెరుగుదల దశ, లక్షణం, ఇటీవలి వాతావరణం మరియు నేల రీడింగ్ చెప్పండి.",
            "kn": "ಬೆಳೆ, ನೀರಾವರಿ, ಮಣ್ಣು ಮತ್ತು ಸಸ್ಯ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಬೆಳೆ, ಬೆಳವಣಿಗೆಯ ಹಂತ, ಲಕ್ಷಣ, ಇತ್ತೀಚಿನ ಹವಾಮಾನ ಮತ್ತು ಮಣ್ಣಿನ ಓದುವಿಕೆಯನ್ನು ತಿಳಿಸಿ.",
            "ml": "വിള, ജലസേചനം, മണ്ണ്, സസ്യാരോഗ്യം എന്നിവയിൽ എനിക്ക് സഹായിക്കാം. വിള, വളർച്ചാഘട്ടം, ലക്ഷണം, സമീപകാല കാലാവസ്ഥ, മണ്ണിന്റെ അളവ് എന്നിവ പറയുക.",
        }
        if language in localized_generic:
            return localized_generic[language]

        if any(term in lower for term in ("hello", "hi ", "hey", "what can you do")):
            return (
                "I can help interpret your saved field readings, explain irrigation results, "
                "suggest crop-health checks, and guide you through a leaf Disease Scan. "
                f"Your current crop context is: {crop_text}. What would you like to check?"
            )

        if cls.is_crop_status_question(clean):
            records = context.get("crop_details", [])
            if records:
                summary = "Saved crop records (not a live health check):\n" + "\n".join(
                    f"- {crop['name']}: stage {crop.get('growth_stage') or 'not recorded'}; "
                    f"recorded health {crop.get('health_status') or 'not recorded'}."
                    for crop in records[:6]
                )
            elif crops:
                summary = f"Registered crops: {crop_text}. No current crop-health reading is available."
            else:
                summary = "No crops are registered in your account yet. Open Fields → Add crop to record your crop."
            analysis = context.get("latest_field_analysis", {})
            moisture = cls._latest_soil_moisture(context)
            if moisture is not None:
                recorded = analysis.get("recorded_at") or "date not recorded"
                summary += (
                    f"\nLatest saved field analysis ({recorded}): "
                    f"{analysis.get('crop_type') or 'crop not recorded'}, soil moisture {moisture:.1f}%. "
                    "This is saved analysis data, not a live sensor reading."
                )
            return summary + "\nRun a fresh Field Analysis or use Disease Scan to check a leaf problem."

        if any(term in lower for term in ("disease", "leaf", "spot", "blight", "photo", "image")):
            return (
                "Open Disease Scan and upload a clear photo of one leaf in daylight, including "
                "both the affected area and some healthy tissue. The result is a screening signal, "
                "not a confirmed diagnosis. Isolate fast-spreading symptoms, avoid moving wet tools "
                "between plants, and confirm severe cases with a local agronomist before treatment."
            )

        if any(term in lower for term in ("irrig", "water", "moisture", "dry")):
            moisture = cls._latest_soil_moisture(context)
            saved = (
                f"Your latest saved soil-moisture value is {moisture:.1f}%. "
                if moisture is not None
                else "I do not have a recent saved soil-moisture reading. "
            )
            return (
                saved
                + "Check moisture at the active root depth, recent rain, soil texture, crop stage, "
                "and forecast before irrigating. Use the Field Analysis tool for a recorded recommendation; "
                "do not irrigate from a single uncalibrated sensor reading alone."
            )

        if any(term in lower for term in ("ph", "npk", "nitrogen", "phosph", "potassium", "soil")):
            return (
                "Use a calibrated soil test and record the sample depth and field location. Compare pH and "
                "nutrients with the specific crop and growth stage; a single generic target can be misleading. "
                "Correct unusual readings only after repeating the test or confirming with a laboratory."
            )

        if any(term in lower for term in ("weather", "rain", "temperature", "wind", "climate")):
            return (
                "Use the live Field Analysis for the saved farm location. Check rainfall, temperature, humidity, "
                "and wind together: high heat and wind can increase water loss, while rain may justify delaying "
                "irrigation. I will not invent live weather when the weather service is unavailable."
            )

        return (
            f"I can help with {crop_text}, but I need a little more detail. Tell me the crop, growth stage, "
            "symptom or question, recent weather, and any soil/sensor reading you have. For a visible leaf "
            "problem, use Disease Scan and share a clear photo."
        )
