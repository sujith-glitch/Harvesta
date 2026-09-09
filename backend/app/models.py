"""
SQLAlchemy ORM Models for Smart Agriculture AI Harvesta Platform.

Includes Core Domain Models:
- User
- FieldAnalysisHistory
- Farm
- Crop

Supabase Platform Foundation Models (Phase A):
- UserSession
- ActivityEvent
- Notification
- NotificationPreference
- AIChatConversation
- AIChatMessage
- CropDiseaseScan
- WeatherSnapshot
- AuditLog
- SensorDevice
- SensorReading
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


# =====================================================================
# CORE DOMAIN MODELS
# =====================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="farmer", nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Token verification fields
    verification_token_hash = Column(String(255), nullable=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    verification_sent_at = Column(DateTime, nullable=True)
    verification_attempts = Column(Integer, default=0, nullable=False)

    # Password reset fields (only SHA-256 token hashes are stored, never raw tokens)
    reset_token_hash = Column(String(255), nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    reset_sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Core Relationships
    field_analyses = relationship("FieldAnalysisHistory", back_populates="user", cascade="all, delete-orphan")
    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")

    # Supabase Platform Foundation Relationships (Cascade Delete)
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan", uselist=False)
    chat_conversations = relationship("AIChatConversation", back_populates="user", cascade="all, delete-orphan")
    disease_scans = relationship("CropDiseaseScan", back_populates="user", cascade="all, delete-orphan")
    sensor_devices = relationship("SensorDevice", back_populates="user", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("FarmerProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    app_preferences = relationship("AppPreference", back_populates="user", cascade="all, delete-orphan", uselist=False)
    inventory_items = relationship("InventoryItem", back_populates="user", cascade="all, delete-orphan")

    # Nullable FK Relationships (SET NULL)
    activity_events = relationship("ActivityEvent", back_populates="user")
    weather_snapshots = relationship("WeatherSnapshot", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class FieldAnalysisHistory(Base):
    __tablename__ = "field_analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    crop_type = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    current_soil_moisture = Column(Float, nullable=False)
    soil_ph = Column(Float, nullable=False)
    soil_temperature = Column(Float, nullable=False)
    weather_temperature = Column(Float, nullable=False)
    weather_humidity = Column(Float, nullable=False)
    weather_precipitation = Column(Float, nullable=False)
    weather_wind_speed = Column(Float, nullable=False)
    recommendation_status = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    factors = Column(Text, nullable=False)  # Stored as JSON string list
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="field_analyses")

    def get_factors_list(self):
        """Helper to parse JSON factors string back to a list of strings."""
        if not self.factors:
            return []
        try:
            return json.loads(self.factors)
        except Exception:
            return [self.factors]

    def to_dict(self):
        """Convert ORM model to dictionary output."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop_type": self.crop_type,
            "location": {},
            "weather": {
                "temperature": self.weather_temperature,
                "humidity": self.weather_humidity,
                "precipitation": self.weather_precipitation,
                "wind_speed": self.weather_wind_speed
            },
            "soil": {
                "current_soil_moisture": self.current_soil_moisture,
                "soil_ph": self.soil_ph,
                "soil_temperature": self.soil_temperature
            },
            "analysis": {
                "status": self.recommendation_status,
                "priority": self.priority,
                "reason": self.reason,
                "factors": self.get_factors_list()
            },
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at)
        }


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    size = Column(Float, nullable=True)
    soil_type = Column(String(100), nullable=True)
    farming_method = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="farms")
    crops = relationship("Crop", back_populates="farm", cascade="all, delete-orphan")
    sensor_devices = relationship("SensorDevice", back_populates="farm", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="farm")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)
    planting_date = Column(DateTime, nullable=True)
    expected_harvest_date = Column(DateTime, nullable=True)
    growth_stage = Column(String(100), nullable=True)
    health_status = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    farm = relationship("Farm", back_populates="crops")


class FarmerProfile(Base):
    """Optional farmer account details stored separately from login credentials."""
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=True)
    address = Column(String(500), nullable=True)
    district = Column(String(150), nullable=True)
    state = Column(String(150), nullable=True)
    country = Column(String(150), nullable=True)
    bio = Column(Text, nullable=True)
    primary_crop = Column(String(150), nullable=True)
    experience_years = Column(Integer, nullable=True)
    avatar_color = Column(String(20), default="#A6BC12", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "phone": self.phone,
            "address": self.address,
            "district": self.district,
            "state": self.state,
            "country": self.country,
            "bio": self.bio,
            "primary_crop": self.primary_crop,
            "experience_years": self.experience_years,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AppPreference(Base):
    """Cross-device language, appearance, accessibility, and voice settings."""
    __tablename__ = "app_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    compact_mode = Column(Boolean, default=False, nullable=False)
    reduce_motion = Column(Boolean, default=False, nullable=False)
    voice_enabled = Column(Boolean, default=True, nullable=False)
    voice_auto_speak = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="app_preferences")

    def to_dict(self):
        return {
            "language": self.language,
            "theme": self.theme,
            "compact_mode": self.compact_mode,
            "reduce_motion": self.reduce_motion,
            "voice_enabled": self.voice_enabled,
            "voice_auto_speak": self.voice_auto_speak,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InventoryItem(Base):
    """Farmer-owned supplies, seed, fertilizer, tools, and equipment stock."""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), default="Other", index=True, nullable=False)
    quantity = Column(Float, default=0, nullable=False)
    unit = Column(String(50), default="units", nullable=False)
    low_stock_threshold = Column(Float, default=0, nullable=False)
    supplier = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="inventory_items")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "unit": self.unit,
            "low_stock_threshold": self.low_stock_threshold,
            "is_low_stock": self.quantity <= self.low_stock_threshold,
            "supplier": self.supplier,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =====================================================================
# SUPABASE PLATFORM FOUNDATION MODELS (PHASE A)
# =====================================================================

class UserSession(Base):
    """
    Tracks authenticated user sessions for security auditing and engagement analytics.
    Does NOT store raw passwords, plain JWT tokens, or raw IPs.
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    login_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    logout_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    device_type = Column(String(100), nullable=True)  # 'desktop', 'mobile', 'tablet'
    platform = Column(String(100), nullable=True)     # 'Windows', 'iOS', 'Android', 'macOS', 'Linux'
    user_agent = Column(String(500), nullable=True)
    ip_hash = Column(String(255), nullable=True)      # Privacy-safe SHA-256 hashed network ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "login_at": self.login_at.isoformat() if self.login_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "logout_at": self.logout_at.isoformat() if self.logout_at else None,
            "duration_seconds": self.duration_seconds,
            "device_type": self.device_type,
            "platform": self.platform,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ActivityEvent(Base):
    """
    Records platform feature usage and analytics events.
    Metadata is stored in a cross-engine JSON column (native JSONB on PostgreSQL, JSON-Text on SQLite).
    """
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    session_id = Column(String(255), index=True, nullable=True)
    event_name = Column(String(100), index=True, nullable=False)  # 'login', 'farm_created', 'analysis_run', etc.
    feature = Column(String(100), index=True, nullable=True)       # 'dashboard', 'irrigation_ai', 'farms', etc.
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="activity_events")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "event_name": self.event_name,
            "feature": self.feature,
            "event_metadata": self.event_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Notification(Base):
    """
    Stores user in-app and delivery-tracked notifications.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type = Column(String(50), nullable=False)  # 'IRRIGATION_ALERT', 'DISEASE_ALERT', 'SECURITY', 'WEATHER', 'SYSTEM'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True, nullable=False)
    delivery_channel = Column(String(50), default="IN_APP", nullable=False)  # 'IN_APP', 'EMAIL', 'BOTH'
    delivery_status = Column(String(50), default="DELIVERED", nullable=False)  # 'PENDING', 'DELIVERED', 'FAILED'
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    read_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "delivery_channel": self.delivery_channel,
            "delivery_status": self.delivery_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }


class NotificationPreference(Base):
    """
    User notification preferences per alert category.
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    irrigation_alerts = Column(Boolean, default=True, nullable=False)
    disease_alerts = Column(Boolean, default=True, nullable=False)
    security_alerts = Column(Boolean, default=True, nullable=False)
    weather_alerts = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notification_preferences")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_enabled": self.email_enabled,
            "irrigation_alerts": self.irrigation_alerts,
            "disease_alerts": self.disease_alerts,
            "security_alerts": self.security_alerts,
            "weather_alerts": self.weather_alerts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AIChatConversation(Base):
    """
    Stores conversational AI context sessions associated with a farmer and optional farm.
    """
    __tablename__ = "ai_chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), index=True, nullable=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_conversations")
    farm = relationship("Farm", backref="chat_conversations")
    messages = relationship("AIChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIChatMessage.created_at")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AIChatMessage(Base):
    """
    Individual chat messages in an AI Conversation.
    Roles: 'user', 'assistant', 'system'
    """
    __tablename__ = "ai_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_chat_conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    conversation = relationship("AIChatConversation", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CropDiseaseScan(Base):
    """
    Stores image-based crop disease scan records and diagnosis outputs.
    Image path references Supabase Storage object keys or secure local filepaths.
    """
    __tablename__ = "crop_disease_scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), index=True, nullable=True)
    crop_id = Column(Integer, ForeignKey("crops.id", ondelete="SET NULL"), index=True, nullable=True)
    image_path = Column(String(500), nullable=False)  # Storage path or object key
    predicted_crop = Column(String(100), nullable=True)
    predicted_disease = Column(String(150), nullable=True)
    confidence = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="disease_scans")
    farm = relationship("Farm", backref="disease_scans")
    crop = relationship("Crop", backref="disease_scans")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "crop_id": self.crop_id,
            "image_path": self.image_path,
            "predicted_crop": self.predicted_crop,
            "predicted_disease": self.predicted_disease,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class WeatherSnapshot(Base):
    """
    Stores historical meteorological snapshots for farm locations.
    """
    __tablename__ = "weather_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), index=True, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    precipitation = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    weather_code = Column(Integer, nullable=True)
    source = Column(String(100), default="open-meteo", nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="weather_snapshots")
    farm = relationship("Farm", backref="weather_snapshots")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "precipitation": self.precipitation,
            "wind_speed": self.wind_speed,
            "weather_code": self.weather_code,
            "source": self.source,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(Base):
    """
    Security and administrative audit trail.
    Does NOT log raw passwords, JWTs, or SMTP secrets.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action = Column(String(100), index=True, nullable=False)       # 'account_created', 'email_verified', 'password_reset_requested', 'farm_deleted', etc.
    entity_type = Column(String(100), index=True, nullable=False)  # 'user', 'farm', 'crop', 'auth'
    entity_id = Column(Integer, nullable=True)
    status = Column(String(50), default="SUCCESS", nullable=False) # 'SUCCESS', 'FAILED', 'BLOCKED'
    audit_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="audit_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status,
            "audit_metadata": self.audit_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =====================================================================
# SENSOR / IOT FOUNDATION
# =====================================================================

class SensorDevice(Base):
    """Registered farm sensor gateway. Only a SHA-256 device-key hash is stored."""
    __tablename__ = "sensor_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    device_uid = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    device_type = Column(String(100), default="esp32_gateway", nullable=False)
    status = Column(String(50), default="registered", index=True, nullable=False)
    api_key_hash = Column(String(64), unique=True, nullable=False)
    firmware_version = Column(String(100), nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sensor_devices")
    farm = relationship("Farm", back_populates="sensor_devices")
    readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "device_uid": self.device_uid,
            "name": self.name,
            "device_type": self.device_type,
            "status": self.status,
            "firmware_version": self.firmware_version,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SensorReading(Base):
    """Timestamped readings received from a registered farm sensor gateway."""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("sensor_devices.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), index=True, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    soil_moisture = Column(Float, nullable=True)
    soil_temperature = Column(Float, nullable=True)
    air_temperature = Column(Float, nullable=True)
    air_humidity = Column(Float, nullable=True)
    soil_ph = Column(Float, nullable=True)
    nitrogen = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    battery_level = Column(Float, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    source = Column(String(50), default="device", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("SensorDevice", back_populates="readings")
    user = relationship("User", back_populates="sensor_readings")
    farm = relationship("Farm", back_populates="sensor_readings")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "soil_moisture": self.soil_moisture,
            "soil_temperature": self.soil_temperature,
            "air_temperature": self.air_temperature,
            "air_humidity": self.air_humidity,
            "soil_ph": self.soil_ph,
            "nitrogen": self.nitrogen,
            "phosphorus": self.phosphorus,
            "potassium": self.potassium,
            "rainfall": self.rainfall,
            "battery_level": self.battery_level,
            "raw_payload": self.raw_payload,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
