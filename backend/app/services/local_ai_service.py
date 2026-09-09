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
Use the farmer's supplied farm context when it is relevant. Give a direct answer,
practical recommendations, reasons, important checks, and one useful next step.
For agricultural questions, provide enough detail to be genuinely useful instead
of stopping after one or two sentences. Prefer short headings and bullet points
that are easy to read on a phone.
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
        "pest",
        "insect",
        "weed",
        "fertil",
        "compost",
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
        return os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b").strip() or "qwen2.5-coder:7b"

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
        if cls.is_crop_selection_question(clean):
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

    @staticmethod
    def is_crop_selection_question(message: str) -> bool:
        """Recognize common requests for choosing what to sow or plant."""
        clean = (message or "").lower()
        patterns = (
            r"\b(?:which|what|best)\s+(?:type\s+of\s+)?(?:crop|crops|seed|seeds|vegetable|vegetables)\b",
            r"\b(?:recommend|suggest|choose)\s+(?:a\s+|some\s+)?(?:crop|crops|seed|seeds|vegetable|vegetables)\b",
            r"\b(?:crop|crops|seed|seeds|vegetable|vegetables)\b.{0,35}\b(?:should|can|to)\b.{0,15}\b(?:plant|sow|grow)\b",
            r"\b(?:what|which)\b.{0,25}\b(?:plant|sow|grow)\b.{0,25}\b(?:today|now|this season)\b",
            r"\b(?:plant|sow|grow)\b.{0,25}\b(?:today|now|this season)\b",
            r"\b(?:enna|entha|endha)\s+(?:crop|seed)\b",
            r"\b(?:crop|seed)\b.{0,25}\b(?:podalam|podanum|vidaikalam|vidhaikalam)\b",
            r"(?:என்ன|எந்த)\s+(?:பயிர்|விதை)",
        )
        return any(re.search(pattern, clean) for pattern in patterns)

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
    def _saved_context_summary(cls, context: Dict[str, Any]) -> str:
        """Build a compact, factual summary without inventing live readings."""
        crops = [str(c) for c in context.get("crops", []) if c]
        analysis = context.get("latest_field_analysis", {}) or {}
        lines: List[str] = []
        if crops:
            lines.append(f"- Registered crops: {', '.join(crops[:5])}.")

        analysis_parts: List[str] = []
        if analysis.get("crop_type"):
            analysis_parts.append(f"crop {analysis['crop_type']}")
        for label, key, suffix in (
            ("soil moisture", "soil_moisture", "%"),
            ("soil pH", "soil_ph", ""),
            ("soil temperature", "soil_temperature", "°C"),
            ("air temperature", "weather_temperature", "°C"),
            ("humidity", "weather_humidity", "%"),
        ):
            value = analysis.get(key)
            try:
                if value is not None:
                    analysis_parts.append(f"{label} {float(value):.1f}{suffix}")
            except (TypeError, ValueError):
                continue
        if analysis.get("recommendation_status"):
            analysis_parts.append(f"result {analysis['recommendation_status']}")
        if analysis_parts:
            recorded = analysis.get("recorded_at") or "date not recorded"
            lines.append(f"- Latest saved analysis ({recorded}): {', '.join(analysis_parts)}.")

        latitude = analysis.get("latitude")
        longitude = analysis.get("longitude")
        if latitude is not None and longitude is not None:
            try:
                lines.append(f"- Saved analysis location: {float(latitude):.4f}, {float(longitude):.4f}.")
            except (TypeError, ValueError):
                pass

        return "\n".join(lines) if lines else "- No recent farm, crop, or sensor data is saved yet."

    @classmethod
    def _offline_reply(cls, message: str, context: Dict[str, Any], language: str = "en") -> str:
        """Fast structured fallback for common farmer questions."""
        clean = re.sub(r"\s+", " ", message.strip())
        lower = clean.lower()
        crops = [str(c) for c in context.get("crops", []) if c]
        crop_text = ", ".join(crops[:5]) if crops else "your crop"

        if not clean:
            return "Please type a question about irrigation, soil, crop health, weather, or a leaf photo."

        saved_context = cls._saved_context_summary(context)

        # Localized zero-network guidance keeps voice and text chat useful even
        # when the larger local model is not running.
        if language == "ta":
            uses_tamil_script = bool(re.search(r"[\u0B80-\u0BFF]", clean))
            if cls.is_crop_selection_question(clean):
                if not uses_tamil_script:
                    return (
                        "Indhaikku enna crop podalam — preliminary guidance\n"
                        "Date mattum vachu best crop select panna safe illa. District, season/rain, soil type, water availability, crop duration, market ellame consider pannanum.\n\n"
                        "Start panna koodiya groups\n"
                        "- Water kammi na local millet illa maize varieties-a check pannunga.\n"
                        "- Drainage correct-a irundha green gram, black gram, groundnut sowing window-a local-a confirm pannunga.\n"
                        "- Small irrigated plot-ku okra, chilli, tomato, keerai/coriander consider pannalam; nursery and weather protection crop-ku crop maarum.\n\n"
                        "Seed vaangurathukku munadi\n"
                        "1. District agriculture office/local trusted seed supplier-kitta current sowing window confirm pannunga.\n"
                        "2. Soil drainage, reliable water, expected rain, crop duration, market demand compare pannunga.\n"
                        "3. Pudhu crop/variety-na small plot-la first trial pannunga.\n\n"
                        f"Harvesta-la save aana data\n{saved_context}\n\n"
                        "Next step\nUnga district/state, soil type, rain-fed illa irrigated, land size, harvest eppo venum-nu sollunga. Appo naan 2–3 suitable crops shortlist panni reason-oda solren."
                    )
                return (
                    "இன்று எந்தப் பயிரைத் தேர்வு செய்வது — முதற்கட்ட வழிகாட்டல்\n"
                    "தேதி மட்டும் வைத்து சிறந்த பயிரைத் தேர்வு செய்வது பாதுகாப்பானது அல்ல. மாவட்டம், பருவமழை, மண் வகை, நீர் வசதி, பயிர் காலம் மற்றும் சந்தை தேவையை சேர்த்து பார்க்க வேண்டும்.\n\n"
                    "தொடக்கத் தேர்வுகள்\n"
                    "- நீர் குறைவாக இருந்தால் உள்ளூருக்கு ஏற்ற சிறுதானியம் அல்லது மக்காச்சோளம் பற்றி விசாரிக்கவும்.\n"
                    "- நல்ல வடிகால் இருந்தால் பாசிப்பயறு, உளுந்து அல்லது நிலக்கடலையின் விதைப்பு காலத்தை உள்ளூரில் உறுதிசெய்யவும்.\n"
                    "- சிறிய பாசன நிலத்திற்கு வெண்டை, மிளகாய், தக்காளி அல்லது கீரை வகைகளை பரிசீலிக்கலாம்.\n\n"
                    "அடுத்த படி\nஉங்கள் மாவட்டம், மண் வகை, பாசன வசதி, நில அளவு மற்றும் விரும்பும் அறுவடை காலத்தை கூறுங்கள். 2–3 பொருத்தமான பயிர்களை காரணத்துடன் குறுக்கிக் கூறுவேன்."
                )
            if any(term in lower for term in ("disease", "leaf", "spot", "photo", "image", "noi", "ilai", "நோய்", "இலை")):
                if not uses_tamil_script:
                    return (
                        "Leaf problem check\n"
                        "Disease Scan-la daylight-la clear close photo-um, whole leaf/plant pattern theriyura wide photo-um upload pannunga. Blur, filter, heavy shadow avoid pannunga.\n\n"
                        "Field-la check pannunga\n"
                        "- Old leaf-la start aacha illa young leaf-la start aacha?\n"
                        "- Leaf backside, stem, insects, recent rain, irrigation, spray/fertilizer history note pannunga.\n"
                        "- Fast-a spread aana affected plant/tools-a healthy row-kku move pannama careful-a handle pannunga.\n\n"
                        "Important\nAI result preliminary screening mattum; confirmed diagnosis illa. Severe/fast spread-na local agronomist-a contact pannunga. Crop, growth stage, affected percentage, symptoms eppo start aachu-nu sollunga."
                    )
                return (
                    "இலை அல்லது நோய் பரிசோதனை\n"
                    "நோய் கண்டறிதல் பகுதியில் பகல் வெளிச்சத்தில் எடுத்த நெருக்கப் படத்தையும், முழு இலை/செடியைக் காட்டும் படத்தையும் பதிவேற்றுங்கள்.\n\n"
                    "கவனிக்க வேண்டியது\n- அறிகுறி பழைய இலையிலா அல்லது இளம் இலையிலா தொடங்கியது?\n- இலையின் பின்பக்கம், தண்டு, பூச்சி, சமீபத்திய மழை மற்றும் தெளிப்பு வரலாற்றைப் பாருங்கள்.\n\n"
                    "AI முடிவு முதற்கட்ட பரிசோதனை மட்டுமே; உறுதி செய்யப்பட்ட நோயறிதல் அல்ல. பாதிப்பு வேகமாகப் பரவினால் உள்ளூர் வேளாண் நிபுணரை அணுகுங்கள்."
                )
            if any(term in lower for term in ("water", "moisture", "irrig", "thanni", "mazhai", "தண்ணீர்", "நீர்ப்பாசனம்")):
                moisture = cls._latest_soil_moisture(context)
                if not uses_tamil_script:
                    saved = f"Latest saved soil moisture {moisture:.1f}%. " if moisture is not None else "Recent soil-moisture reading save aagala. "
                    return (
                        "Irrigation guidance\n"
                        f"{saved}Idha mattum vachu water panna koodathu.\n\n"
                        "Water panna munadi\n"
                        "- Root depth-la moisture check pannunga; surface mattum paaka vendam.\n"
                        "- Crop/stage, soil drainage, last rain, heat/wind, last irrigation time compare pannunga.\n"
                        "- Unusual sensor value-na repeat check pannunga.\n\n"
                        "Next step\nField Analysis-la latest values use pannunga. Crop, growth stage, soil type, moisture, last irrigation and rainfall details anuppunga; appo specific recommendation solren."
                    )
                saved = f"கடைசியாக சேமித்த மண் ஈரப்பதம் {moisture:.1f}%. " if moisture is not None else "சமீபத்திய மண் ஈரப்பதத் தகவல் இல்லை. "
                return (
                    "நீர்ப்பாசன வழிகாட்டல்\n"
                    f"{saved}இந்த ஒரு அளவை மட்டும் வைத்து நீர்ப்பாசனம் செய்ய வேண்டாம்.\n\n"
                    "நீர் விடுவதற்கு முன்\n- வேர் ஆழத்தில் ஈரப்பதத்தை அளவிடுங்கள்.\n- பயிர் வளர்ச்சி நிலை, மண் வடிகால், சமீபத்திய மழை, வெப்பம் மற்றும் கடைசியாக நீர் விட்ட நேரத்தை ஒப்பிடுங்கள்.\n- மாறுபட்ட சென்சார் மதிப்பை மீண்டும் சரிபார்க்கவும்.\n\n"
                    "பயிர், வளர்ச்சி நிலை, மண் வகை மற்றும் சமீபத்திய அளவுகளை கூறினால் குறிப்பிட்ட வழிகாட்டல் தர முடியும்."
                )
            if not uses_tamil_script:
                return (
                    "Detailed farm guidance kudukka indha details venum\n"
                    "- crop and growth stage;\n- district/location;\n- exact symptom illa decision;\n- recent rain/weather;\n- moisture, pH, NPK or temperature reading.\n\n"
                    f"Harvesta-la save aana data\n{saved_context}\n\n"
                    "Neenga Tanglish-la ketta naan Tanglish-la reply pannuven. Visible leaf problem-na Disease Scan use pannunga."
                )
            return (
                "விரிவான விவசாய வழிகாட்டலுக்கு கீழ்கண்ட தகவல்களை கூறுங்கள்:\n"
                "- பயிர் மற்றும் வளர்ச்சி நிலை;\n- மாவட்டம்/இடம்;\n- துல்லியமான அறிகுறி அல்லது முடிவு;\n- சமீபத்திய மழை/வானிலை;\n- ஈரப்பதம், pH, NPK அல்லது வெப்பநிலை அளவு.\n\n"
                "காணக்கூடிய இலைப் பிரச்சினைக்கு நோய் கண்டறிதல் பகுதியைப் பயன்படுத்தவும்."
            )
        localized_generic = {
            "hi": "मैं आपकी फसल, सिंचाई, मिट्टी और पौधों के स्वास्थ्य में मदद कर सकता हूँ। कृपया फसल, विकास चरण, लक्षण, हाल का मौसम और उपलब्ध मिट्टी रीडिंग बताइए।",
            "te": "పంట, నీటిపారుదల, నేల మరియు మొక్కల ఆరోగ్యం గురించి నేను సహాయం చేయగలను. పంట, పెరుగుదల దశ, లక్షణం, ఇటీవలి వాతావరణం మరియు నేల రీడింగ్ చెప్పండి.",
            "kn": "ಬೆಳೆ, ನೀರಾವರಿ, ಮಣ್ಣು ಮತ್ತು ಸಸ್ಯ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಬೆಳೆ, ಬೆಳವಣಿಗೆಯ ಹಂತ, ಲಕ್ಷಣ, ಇತ್ತೀಚಿನ ಹವಾಮಾನ ಮತ್ತು ಮಣ್ಣಿನ ಓದುವಿಕೆಯನ್ನು ತಿಳಿಸಿ.",
            "ml": "വിള, ജലസേചനം, മണ്ണ്, സസ്യാരോഗ്യം എന്നിവയിൽ എനിക്ക് സഹായിക്കാം. വിള, വളർച്ചാഘട്ടം, ലക്ഷണം, സമീപകാല കാലാവസ്ഥ, മണ്ണിന്റെ അളവ് എന്നിവ പറയുക.",
        }
        if language in localized_generic:
            return localized_generic[language]

        if cls.is_crop_selection_question(clean):
            return (
                "Crop choice for today — preliminary guidance\n"
                "I can shortlist crops, but the date alone is not enough to safely choose the best one. "
                "District, current rainfall, soil type, irrigation supply, and the time available before harvest can change the answer.\n\n"
                "Useful starting groups\n"
                "- Cereals: maize or a locally suitable millet when water is limited; paddy only where the season and water supply support it.\n"
                "- Pulses: green gram, black gram, or groundnut can be considered where drainage and the local sowing window fit.\n"
                "- Vegetables: okra, chilli, tomato, leafy greens, or coriander may suit smaller irrigated plots, but nursery and heat/rain protection needs differ.\n\n"
                "Check before buying seed\n"
                "1. Confirm the local sowing window with your district agriculture office or a trusted local seed supplier.\n"
                "2. Match the crop to soil drainage, reliable water, expected rain, market access, and crop duration.\n"
                "3. Start with a small plot if the crop or variety is new to your farm.\n\n"
                "Your saved Harvesta data\n"
                f"{saved_context}\n\n"
                "Next step\n"
                "Send your district/state, soil type, irrigated or rain-fed condition, land size, and preferred harvest time. I can then narrow this to 2–3 crops and explain the best option."
            )

        if any(term in lower for term in ("hello", "hi ", "hey", "what can you do")):
            return (
                "Hello — I am Harvesta AI. I can give detailed, practical help with:\n"
                "- choosing crops using season, location, soil, and water availability;\n"
                "- interpreting saved moisture, pH, weather, and field-analysis results;\n"
                "- irrigation planning and crop-health checks;\n"
                "- preparing a clear Disease Scan and explaining its screening result.\n\n"
                "I separate saved measurements from general advice and I will tell you when important data is missing. "
                f"Current crop context: {crop_text}. Ask a complete question such as, “Which crop should I plant?” or “Does my tomato field need irrigation?”"
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
            return (
                f"Crop status summary\n{summary}\n\n"
                "What this means\n"
                "- A saved crop name or health label is not the same as a live field diagnosis.\n"
                "- Use a fresh Field Analysis for soil/weather-based irrigation guidance.\n"
                "- Use Disease Scan for visible leaf symptoms, and include the whole plant pattern when describing the problem.\n\n"
                "Next step\nTell me which crop you want to inspect and what changed today—colour, spots, wilting, growth, pests, or soil moisture."
            )

        if any(term in lower for term in ("disease", "leaf", "spot", "blight", "photo", "image")):
            return (
                "Leaf or disease check\n"
                "Use Disease Scan with a clear daylight photo. Include one close photo of the affected area and one wider photo showing the leaf or plant pattern. Avoid blur, filters, heavy shadow, and a wet leaf surface.\n\n"
                "While checking the crop\n"
                "- Note whether symptoms began on old or young leaves and whether they are spreading plant-to-plant.\n"
                "- Check the leaf underside, stem, nearby insects, recent rain, irrigation, and any recent spray or fertilizer.\n"
                "- Isolate rapidly worsening plants when practical and clean tools before moving to healthy rows.\n\n"
                "Important\n"
                "The image result is preliminary AI screening, not a confirmed diagnosis or chemical prescription. "
                "For rapid spread, severe wilting, stem rot, or major crop loss, contact a local agronomist before treatment.\n\n"
                "Next step\nTell me the crop, growth stage, affected plant percentage, how long the symptom has been present, and what the spots or damage look like."
            )

        if any(term in lower for term in ("irrig", "water", "moisture", "dry")):
            moisture = cls._latest_soil_moisture(context)
            saved = (
                f"Your latest saved soil-moisture value is {moisture:.1f}%. "
                if moisture is not None
                else "I do not have a recent saved soil-moisture reading. "
            )
            return (
                "Irrigation guidance\n"
                f"{saved}Treat it as one input, not the full decision.\n\n"
                "Check before watering\n"
                "- Measure moisture at the crop’s active root depth, not only at the surface.\n"
                "- Consider crop and growth stage, soil texture and drainage, recent rain, heat, wind, and the next reliable forecast.\n"
                "- Repeat an unusual sensor value or compare it with a simple hand/field check.\n\n"
                "Practical next action\n"
                "Run Field Analysis with the latest moisture, pH, soil temperature, and correct location. If irrigation is recommended, apply it in a controlled cycle and recheck the root zone rather than flooding from one reading.\n\n"
                "Send the crop, growth stage, soil type, latest moisture value, last irrigation time, and recent rainfall for a more specific recommendation."
            )

        if any(term in lower for term in ("ph", "npk", "nitrogen", "phosph", "potassium", "soil")):
            return (
                "Soil and nutrient guidance\n"
                "Use a calibrated test and record the sample depth, field location, date, and whether fertilizer was recently applied. A single pH or NPK value without crop stage and sampling details can be misleading.\n\n"
                "Recommended checks\n"
                "- Take several representative samples instead of relying on one edge or wet spot.\n"
                "- Compare pH and nutrients with the exact crop, variety, growth stage, and local soil recommendation.\n"
                "- Repeat an unusual sensor result or confirm it through a soil laboratory before making a major correction.\n"
                "- Record the change in Harvesta so later analyses can be compared.\n\n"
                f"Saved context\n{saved_context}\n\n"
                "Next step\nSend the crop, stage, soil type, pH, N-P-K readings with units, and last fertilizer date. I can explain which result needs attention first without inventing a dosage."
            )

        if any(term in lower for term in ("pest", "insect", "weed", "fertil", "compost")):
            return (
                "Crop management guidance\n"
                "First identify the crop, growth stage, affected area, and exact symptom or pest. Check several plants across the field so one damaged plant does not represent the whole crop.\n\n"
                "Safe next steps\n"
                "- Photograph the damage, leaf underside, stem, and any visible insect.\n"
                "- Record recent rain, irrigation, fertilizer, and spray history.\n"
                "- Prefer prevention and locally approved integrated pest-management steps after identification.\n"
                "- Do not mix or increase products from a chatbot suggestion; labels and local approvals vary.\n\n"
                "For fast spread or heavy loss, take the photos and field history to a qualified local agronomist. Send me the crop, stage, symptom, affected percentage, and location for a more focused checklist."
            )

        if any(term in lower for term in ("weather", "rain", "temperature", "wind", "climate")):
            return (
                "Weather-based farm guidance\n"
                "Use Live Weather Field Analysis with the correct farm location. Temperature, humidity, rainfall, and wind should be read together: heat and wind can increase water loss; high humidity can slow drying; reliable rain may justify delaying irrigation.\n\n"
                "Before acting\n"
                "- Confirm that the displayed location and observation time are correct.\n"
                "- Compare the forecast with soil moisture at root depth and the crop’s growth stage.\n"
                "- Avoid spraying in unsuitable wind or immediately before expected rain, and follow the product label.\n\n"
                f"Saved context\n{saved_context}\n\n"
                "I will not invent live weather when the weather service is unavailable. Send your district, crop/stage, and the weather values shown in Harvesta for a specific interpretation."
            )

        return (
            "I can give a detailed farm recommendation, but the question needs a little more context.\n\n"
            "Please send\n"
            "- crop and growth stage;\n"
            "- district/location and whether the field is irrigated or rain-fed;\n"
            "- the exact symptom or decision you need help with;\n"
            "- recent rain/weather and any moisture, pH, NPK, or temperature reading;\n"
            "- how long the condition has been present and what you have already tried.\n\n"
            f"Current saved context\n{saved_context}\n\n"
            "For a visible leaf problem, use Disease Scan and share a clear photo. For crop selection, tell me your soil type, water availability, land size, and desired harvest period."
        )
