"""
Smart Agriculture AI Chat Coordination Service.
Builds agricultural system prompts, injects bounded farmer context,
manages conversation history limits, and calls configured LLM provider.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models import (
    User,
    Farm,
    Crop,
    FieldAnalysisHistory,
    CropDiseaseScan,
    WeatherSnapshot,
    Notification,
    AIChatMessage,
    SensorReading,
    AppPreference,
)
from backend.app.services.llm import get_llm_provider, LLMProviderError
from backend.app.services.local_ai_service import LocalAIService

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 8
MAX_USER_MESSAGE_LENGTH = 2000

AGRONOMIST_SYSTEM_PROMPT = """You are the Harvesta AI Agronomist, an expert precision agricultural intelligence assistant designed to help farmers optimize crop yields, conserve water, and manage plant health.

Your core operating principles:
1. FOCUS: Focus strictly on agronomy, irrigation, crop health, soil moisture management, pest/disease prevention, and sustainable farming practices.
2. FARMER-FIRST & PRACTICAL: Provide clear, concise, actionable guidance tailored to the farmer's specific crops and field conditions. Use farmer-friendly language with clear bullet points.
3. GROUNDED IN KNOWN DATA: Ground your responses in the farmer's real data provided in the context below. Distinguish observed telemetry from general agricultural principles.
4. NO SENSOR FABRICATION: Do NOT invent unmeasured telemetry (e.g. do not fabricate NPK, electrical conductivity, or satellite NDVI values that are not present in the context).
5. NON-PRESCRIPTIVE SCREENING: Treat all crop disease vision scan results as preliminary AI screening, not an authoritative chemical prescription or certification. For severe infestations or uncertain blights, explicitly encourage on-site consultation with a local agricultural extension specialist.
6. CONCISE: Keep explanations focused, practical, and under 250-300 words unless the farmer asks for an in-depth breakdown."""


class ChatAIService:
    @staticmethod
    def build_offline_context(db: Session, user: User, farm_id: Optional[int] = None) -> Dict[str, Any]:
        crop_query = (
            db.query(Crop)
            .join(Farm, Crop.farm_id == Farm.id)
            .filter(Farm.user_id == user.id)
        )
        if farm_id is not None:
            crop_query = crop_query.filter(Farm.id == farm_id)
        crops = crop_query.order_by(Crop.id).limit(6).all()
        latest = (
            db.query(FieldAnalysisHistory)
            .filter(FieldAnalysisHistory.user_id == user.id)
            .order_by(FieldAnalysisHistory.created_at.desc())
            .first()
        )
        return {
            "crops": [crop.name for crop in crops],
            "crop_details": [
                {"name": crop.name, "growth_stage": crop.growth_stage, "health_status": crop.health_status}
                for crop in crops
            ],
            "latest_field_analysis": {
                "soil_moisture": latest.current_soil_moisture if latest else None,
                "crop_type": latest.crop_type if latest else None,
                "recorded_at": latest.created_at.isoformat(timespec="minutes") if latest and latest.created_at else None,
            },
        }

    @staticmethod
    def model_timeout_seconds() -> float:
        """Bound interactive model waiting independently of bulk/model timeouts."""
        try:
            return max(1.0, min(15.0, float(os.getenv("CHAT_MODEL_TIMEOUT_SECONDS", "6"))))
        except ValueError:
            return 6.0

    @staticmethod
    def build_farmer_context(
        db: Session,
        user: User,
        farm_id: Optional[int] = None,
    ) -> str:
        """
        Constructs a concise, safe agricultural context block for the prompt.
        Includes only non-sensitive agronomic data belonging to the authenticated user.
        """
        context_parts = []
        user_name = user.full_name or "Farmer"
        context_parts.append(f"Farmer: {user_name}")

        # 1. Registered Farms & Target Farm
        farms_query = db.query(Farm).filter(Farm.user_id == user.id)
        farms = farms_query.all()

        target_farm = None
        if farm_id is not None:
            target_farm = next((f for f in farms if f.id == farm_id), None)

        if target_farm:
            context_parts.append(
                f"Selected Farm Context: {target_farm.name} "
                f"({target_farm.size or 'Unknown'} ha, Location: {target_farm.location or 'Default'})"
            )
        elif farms:
            farm_names = [f"{f.name} ({f.size or '?'} ha)" for f in farms[:4]]
            context_parts.append(f"Registered Farms: {', '.join(farm_names)}")
        else:
            context_parts.append("Registered Farms: None recorded yet.")

        # 2. Registered Crops
        if target_farm:
            crops = db.query(Crop).filter(Crop.farm_id == target_farm.id).all()
        else:
            crops = db.query(Crop).join(Farm, Crop.farm_id == Farm.id).filter(Farm.user_id == user.id).limit(6).all()

        if crops:
            crop_summaries = [f"{c.name} (Stage: {c.growth_stage or 'Planted'})" for c in crops[:5]]
            context_parts.append(f"Active Crops: {', '.join(crop_summaries)}")
        else:
            context_parts.append("Active Crops: None recorded yet.")

        # 3. Latest Field Analysis & Soil Moisture
        analysis_query = db.query(FieldAnalysisHistory).filter(FieldAnalysisHistory.user_id == user.id)
        latest_analysis = analysis_query.order_by(FieldAnalysisHistory.created_at.desc()).first()

        if latest_analysis:
            context_parts.append(
                f"Latest Field Analysis ({latest_analysis.crop_type or 'General'}): "
                f"Soil Moisture={latest_analysis.current_soil_moisture:.1f}%, "
                f"Weather Temp={latest_analysis.weather_temperature:.1f}°C, "
                f"Humidity={latest_analysis.weather_humidity:.1f}%, "
                f"Recommendation={latest_analysis.recommendation_status}, "
                f"Priority={latest_analysis.priority}"
            )

        # 4. Recent Weather Snapshot
        latest_weather = (
            db.query(WeatherSnapshot)
            .filter(WeatherSnapshot.user_id == user.id)
            .order_by(WeatherSnapshot.created_at.desc())
            .first()
        )
        if latest_weather:
            context_parts.append(
                f"Recent Microclimate ({latest_weather.source}): "
                f"Temp={latest_weather.temperature}°C, "
                f"Humidity={latest_weather.humidity}%, "
                f"Precipitation={latest_weather.precipitation}mm, "
                f"Wind={latest_weather.wind_speed}km/h"
            )

        # 5. Latest Physical Sensor Reading (when hardware is connected)
        latest_sensor = (
            db.query(SensorReading)
            .filter(SensorReading.user_id == user.id)
            .order_by(SensorReading.recorded_at.desc())
            .first()
        )
        if latest_sensor:
            sensor_values = []
            for label, value, unit in (
                ("Soil moisture", latest_sensor.soil_moisture, "%"),
                ("Soil temperature", latest_sensor.soil_temperature, "°C"),
                ("Air temperature", latest_sensor.air_temperature, "°C"),
                ("Air humidity", latest_sensor.air_humidity, "%"),
                ("Soil pH", latest_sensor.soil_ph, ""),
            ):
                if value is not None:
                    sensor_values.append(f"{label}={value}{unit}")
            if sensor_values:
                context_parts.append(f"Latest physical sensor reading: {', '.join(sensor_values)}")

        # 6. Latest Crop Disease Screening Result
        latest_scan = (
            db.query(CropDiseaseScan)
            .filter(CropDiseaseScan.user_id == user.id)
            .order_by(CropDiseaseScan.created_at.desc())
            .first()
        )
        if latest_scan:
            conf_pct = int(round((latest_scan.confidence or 0.8) * 100))
            context_parts.append(
                f"Latest Disease Vision Scan: Crop={latest_scan.predicted_crop}, "
                f"Condition={latest_scan.predicted_disease} ({conf_pct}% confidence). "
                f"Guidance={latest_scan.recommendation or 'Inspect foliage regularly.'}"
            )

        # 7. Active High-Priority Alerts
        active_alerts = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.is_read == False,
                Notification.type.in_(["IRRIGATION_ALERT", "DISEASE_ALERT", "WEATHER"]),
            )
            .order_by(Notification.created_at.desc())
            .limit(2)
            .all()
        )
        if active_alerts:
            alert_texts = [f"[{a.type}] {a.title}" for a in active_alerts]
            context_parts.append(f"Active Farm Alerts: {'; '.join(alert_texts)}")

        return "\n".join(context_parts)

    @classmethod
    async def generate_assistant_response(
        cls,
        db: Session,
        user: User,
        conversation_id: int,
        farm_id: Optional[int],
        user_message: str,
        recent_messages: List[AIChatMessage],
    ) -> Dict[str, Any]:
        """
        Coordinates full prompt construction, context building, history truncation,
        and LLM execution.
        """
        preference = db.query(AppPreference).filter(AppPreference.user_id == user.id).first()
        preferred_language = preference.language if preference else "en"
        reply_language = LocalAIService.detect_language(user_message, preferred_language)

        # Common short questions use the built-in agriculture knowledge path.
        # This avoids loading the large local model for greetings and routine
        # disease, irrigation, soil, or weather guidance.
        provider = get_llm_provider()
        if provider.provider_name == "ollama" and (
            LocalAIService._mode() == "offline" or LocalAIService.can_answer_instantly(user_message)
        ):
            fallback = LocalAIService.generate_offline_reply(
                user_message,
                cls.build_offline_context(db, user, farm_id),
                language=reply_language,
            )
            return {
                "content": fallback["content"],
                "model_name": fallback["model"],
                "provider": "instant-local-knowledge",
                "error": None,
            }

        # 1. Build Farmer Context Block
        farmer_context = cls.build_farmer_context(db, user, farm_id)

        full_system_prompt = (
            f"{AGRONOMIST_SYSTEM_PROMPT}\n\n"
            f"LANGUAGE: Reply only in {LocalAIService._LANGUAGE_NAMES.get(reply_language, 'English')}. "
            "Match the farmer's writing style; if they use romanized Tamil (Tanglish), reply in clear Tanglish.\n\n"
            f"--- CURRENT FARMER CONTEXT ---\n"
            f"{farmer_context}\n"
            f"-----------------------------"
        )

        # 2. Build Bounded Message History (Last N messages)
        prompt_messages: List[Dict[str, str]] = [
            {"role": "system", "content": full_system_prompt}
        ]

        # Truncate to recent bounded history
        bounded_history = recent_messages[-MAX_HISTORY_MESSAGES:]
        for msg in bounded_history:
            if msg.role in ("user", "assistant"):
                prompt_messages.append({"role": msg.role, "content": msg.content})

        # Append current user message
        prompt_messages.append({"role": "user", "content": user_message})

        # 3. Call LLM Provider
        try:
            response_dict = await asyncio.wait_for(
                provider.generate_chat_response(
                    messages=prompt_messages,
                    temperature=0.2,
                    max_tokens=160,
                ),
                timeout=cls.model_timeout_seconds(),
            )
            return {
                "content": response_dict["content"],
                "model_name": response_dict.get("model", provider.default_model),
                "provider": provider.provider_name,
                "error": None,
            }
        except (LLMProviderError, asyncio.TimeoutError) as pe:
            logger.warning(f"LLM Provider Error during chat: {pe}")
            fallback = LocalAIService.generate_offline_reply(
                user_message,
                cls.build_offline_context(db, user, farm_id),
                language=reply_language,
            )
            return {
                "content": fallback["content"],
                "model_name": fallback["model"],
                "provider": fallback["provider"],
                "fallback_reason": "model_timeout" if isinstance(pe, asyncio.TimeoutError) else "model_unavailable",
                "error": None,
            }
        except Exception as e:
            logger.error(f"Unexpected chat generation error: {e}", exc_info=True)
            fallback = LocalAIService.generate_offline_reply(
                user_message,
                cls.build_offline_context(db, user, farm_id),
                language=reply_language,
            )
            return {
                "content": fallback["content"],
                "model_name": fallback["model"],
                "provider": fallback["provider"],
                "fallback_reason": "model_unavailable",
                "error": None,
            }
