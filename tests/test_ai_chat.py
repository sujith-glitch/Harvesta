"""
Unit & Integration Tests for Phase E Real AI Agronomist Chat.
Covers conversation management, user isolation, message exchange,
context injection, failure handling, and telemetry.
"""

import os
import sys
import uuid
import asyncio
from time import perf_counter
from datetime import datetime
from unittest.mock import AsyncMock, patch

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import (
    User,
    Farm,
    Crop,
    FieldAnalysisHistory,
    CropDiseaseScan,
    WeatherSnapshot,
    AIChatConversation,
    AIChatMessage,
    ActivityEvent,
)
from backend.app.services.auth_service import AuthService
from backend.app.services.chat_ai_service import ChatAIService
from backend.app.services.llm.base import LLMProvider, LLMProviderError
from backend.app.services.llm import set_llm_provider, get_llm_provider
from backend.app.services.local_ai_service import LocalAIService
from backend.app.services.chat_storage_service import ChatStorageService

client = TestClient(app)


class MockSuccessLLMProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock_ollama"

    @property
    def default_model(self) -> str:
        return "qwen2.5-coder:7b"

    async def generate_chat_response(self, messages, temperature=0.7, max_tokens=None):
        return {
            "content": "For your tomato crop, maintain 60% soil moisture and water early in the morning.",
            "model": "qwen2.5-coder:7b",
            "eval_count": 28,
        }


class MockFailingLLMProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock_failing_ollama"

    @property
    def default_model(self) -> str:
        return "qwen2.5-coder:7b"

    async def generate_chat_response(self, messages, temperature=0.7, max_tokens=None):
        raise LLMProviderError("Local AI assistant is currently unreachable at http://127.0.0.1:11434.")


def create_test_farmer(email_prefix: str = "farmer"):
    """Helper to create a verified user and return (user_obj, auth_headers)."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name=f"Farmer {email_prefix.capitalize()}",
            hashed_password=AuthService.hash_password("password123"),
            role="farmer",
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = AuthService.create_access_token(user.id, user.email)
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_mock_llm():
    """Default each test to using MockSuccessLLMProvider."""
    original_provider = get_llm_provider()
    set_llm_provider(MockSuccessLLMProvider())
    yield
    set_llm_provider(original_provider)


# =====================================================================
# 1. AUTHENTICATION & ACCESS CONTROL
# =====================================================================

def test_unauthenticated_conversations_rejected():
    """Unauthenticated chat requests must return 401."""
    res = client.get("/api/chat/conversations")
    assert res.status_code == 401

    res = client.post("/api/chat/conversations", json={"title": "Test"})
    assert res.status_code == 401

    res = client.get("/api/chat/conversations/1")
    assert res.status_code == 401

    res = client.delete("/api/chat/conversations/1")
    assert res.status_code == 401

    res = client.post("/api/chat/conversations/1/messages", json={"message": "Hello"})
    assert res.status_code == 401

    assert client.get("/api/chat/status").status_code == 401


def test_authenticated_user_can_check_local_ai_readiness():
    _, headers = create_test_farmer("chat_status")
    expected = {
        "mode": "auto",
        "provider": "offline-knowledge",
        "ready": True,
        "model": "harvesta-offline-v1",
        "message": "Offline fallback is ready.",
    }
    with patch.object(LocalAIService, "get_status", return_value=expected):
        response = client.get("/api/chat/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == expected


# =====================================================================
# 2. CONVERSATION MANAGEMENT & USER ISOLATION
# =====================================================================

def test_conversation_creation_and_listing():
    """Farmer creates and lists their own conversations."""
    user, headers = create_test_farmer("chat_create")

    # Create conversation
    res = client.post("/api/chat/conversations", json={"title": "Tomato Irrigation Planning"}, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None
    assert data["title"] == "Tomato Irrigation Planning"
    conv_id = data["id"]

    # List conversations
    list_res = client.get("/api/chat/conversations", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(c["id"] == conv_id for c in list_data["conversations"])


def test_conversation_list_and_thread_isolation():
    """User A cannot view or access User B's conversation thread."""
    user1, headers1 = create_test_farmer("chat_u1")
    user2, headers2 = create_test_farmer("chat_u2")

    # User 1 creates conversation
    res1 = client.post("/api/chat/conversations", json={"title": "User1 Private Chat"}, headers=headers1)
    conv1_id = res1.json()["id"]

    # User 2 list should not contain conv1
    list2 = client.get("/api/chat/conversations", headers=headers2)
    assert all(c["id"] != conv1_id for c in list2.json()["conversations"])

    # User 2 direct query for conv1 should return 404
    thread2 = client.get(f"/api/chat/conversations/{conv1_id}", headers=headers2)
    assert thread2.status_code == 404


def test_cross_user_delete_blocked():
    """User B cannot delete User A's conversation."""
    user1, headers1 = create_test_farmer("del_u1")
    user2, headers2 = create_test_farmer("del_u2")

    res1 = client.post("/api/chat/conversations", json={"title": "Owner Chat"}, headers=headers1)
    conv1_id = res1.json()["id"]

    del_res = client.delete(f"/api/chat/conversations/{conv1_id}", headers=headers2)
    assert del_res.status_code == 404

    # Verify conversation still exists for owner
    owner_get = client.get(f"/api/chat/conversations/{conv1_id}", headers=headers1)
    assert owner_get.status_code == 200


def test_delete_owned_conversation_cascades_messages():
    """Deleting conversation deletes conversation and all child messages."""
    user, headers = create_test_farmer("cascade_user")

    res = client.post("/api/chat/conversations", json={"title": "To Delete"}, headers=headers)
    conv_id = res.json()["id"]

    # Add message
    msg_res = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"message": "Hello agronomist"}, headers=headers)
    assert msg_res.status_code == 200

    # Delete conversation
    del_res = client.delete(f"/api/chat/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(AIChatConversation).filter(AIChatConversation.id == conv_id).first() is None
        assert db.query(AIChatMessage).filter(AIChatMessage.conversation_id == conv_id).count() == 0
    finally:
        db.close()


def test_farm_ownership_validated_on_creation():
    """Farmer cannot link another user's farm ID to a conversation."""
    user1, _ = create_test_farmer("farm_u1")
    user2, headers2 = create_test_farmer("farm_u2")

    db = SessionLocal()
    try:
        farm = Farm(user_id=user1.id, name="User 1 Farm", size=5.0)
        db.add(farm)
        db.commit()
        farm_id = farm.id
    finally:
        db.close()

    res = client.post("/api/chat/conversations", json={"title": "Intruder", "farm_id": farm_id}, headers=headers2)
    assert res.status_code == 404
    assert "not found or does not belong" in res.json()["detail"]


# =====================================================================
# 3. MESSAGE EXCHANGE & AGENT EXECUTION
# =====================================================================

def test_empty_chat_message_rejected():
    """Sending empty or whitespace message returns 400 Bad Request."""
    user, headers = create_test_farmer("empty_msg_user")
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    res = client.post(f"/api/chat/conversations/{conv['id']}/messages", json={"message": "   "}, headers=headers)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_oversized_chat_message_rejected():
    """Sending message exceeding max length returns 422 Unprocessable Entity."""
    user, headers = create_test_farmer("large_msg_user")
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    huge_msg = "A" * 2500
    res = client.post(f"/api/chat/conversations/{conv['id']}/messages", json={"message": huge_msg}, headers=headers)
    assert res.status_code == 422


def test_user_message_and_mocked_assistant_response_saved():
    """Sending a message saves user message, queries mock provider, and saves assistant response."""
    user, headers = create_test_farmer("exchange_user")
    conv = client.post("/api/chat/conversations", json={"title": "Crop Advisory"}, headers=headers).json()
    conv_id = conv["id"]

    res = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"message": "What is the optimal soil moisture for my potato field?"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["user_message"]["role"] == "user"
    assert "optimal soil moisture" in data["user_message"]["content"]
    assert data["assistant_message"]["role"] == "assistant"
    assert "maintain 60% soil moisture" in data["assistant_message"]["content"]
    assert data["assistant_message"]["model_name"] == "qwen2.5-coder:7b"


def test_first_message_auto_generates_title():
    """If title was default 'New Conversation', first user message updates the title."""
    user, headers = create_test_farmer("autotitle_user")
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()
    conv_id = conv["id"]
    assert conv["title"] == "New Conversation"

    res = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"message": "How do I prevent tomato leaf blight during rainy seasons?"},
        headers=headers,
    )
    assert res.status_code == 200
    updated_conv = res.json()["conversation"]
    assert "How do I prevent tomato leaf blight" in updated_conv["title"]


def test_ollama_failure_uses_safe_offline_fallback():
    """When Ollama is unavailable, the local rules engine keeps chat usable."""
    set_llm_provider(MockFailingLLMProvider())

    user, headers = create_test_farmer("fail_user")
    conv = client.post("/api/chat/conversations", json={"title": "Failing Chat"}, headers=headers).json()
    conv_id = conv["id"]

    res = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"message": "Hello agronomist!"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["assistant_message"]["role"] == "assistant"
    assert data["assistant_message"]["model_name"] == "harvesta-offline-v1"
    assert data["assistant_message"]["content"].strip()

    # The offline response remains part of the farmer's saved chat history.
    db = SessionLocal()
    try:
        asst_msgs = (
            db.query(AIChatMessage)
            .filter(AIChatMessage.conversation_id == conv_id, AIChatMessage.role == "assistant")
            .all()
        )
        assert len(asst_msgs) == 1
    finally:
        db.close()


def test_common_farming_questions_are_supported_by_instant_local_knowledge():
    assert LocalAIService.can_answer_instantly("Hello Harvesta") is True
    assert LocalAIService.can_answer_instantly("Should I irrigate my dry tomato soil?") is True
    assert LocalAIService.can_answer_instantly("Can you check this leaf disease photo?") is True
    assert LocalAIService.can_answer_instantly("Write a detailed business plan for my farm") is False
    assert LocalAIService.can_answer_instantly("What is the crop status?") is True
    assert LocalAIService.can_answer_instantly("What is the crip status") is True
    assert LocalAIService.can_answer_instantly("Which type of crop can we plant today?") is True
    assert LocalAIService.is_crop_selection_question("What disease affects my crop?") is False
    assert LocalAIService.is_crop_selection_question("What fertilizer is best for tomato crop?") is False
    assert LocalAIService.is_crop_selection_question("How should I plant tomato seedlings?") is False
    assert LocalAIService.is_crop_selection_question("Suggest irrigation for my crop") is False


def test_fast_crop_selection_reply_is_detailed_structured_and_context_aware():
    reply = LocalAIService.generate_offline_reply(
        "Which crop can I plant today?",
        {
            "crops": ["Tomato"],
            "latest_field_analysis": {
                "crop_type": "Tomato",
                "soil_moisture": 35,
                "soil_ph": 6.5,
                "recorded_at": "2026-09-08T10:00",
            },
        },
        language="en",
    )["content"]

    assert len(reply) >= 800
    assert "Useful starting groups" in reply
    assert "Check before buying seed" in reply
    assert "Registered crops: Tomato" in reply
    assert "soil moisture 35.0%" in reply
    assert "Next step" in reply


def test_detailed_model_output_cap_is_configurable_and_bounded(monkeypatch):
    monkeypatch.setenv("CHAT_MAX_RESPONSE_TOKENS", "520")
    assert ChatAIService.max_response_tokens() == 520
    monkeypatch.setenv("CHAT_MAX_RESPONSE_TOKENS", "9999")
    assert ChatAIService.max_response_tokens() == 600
    monkeypatch.setenv("CHAT_MAX_RESPONSE_TOKENS", "invalid")
    assert ChatAIService.max_response_tokens() == 360


def test_tanglish_crop_selection_reply_is_detailed_and_keeps_roman_script():
    reply = LocalAIService.generate_offline_reply(
        "ennaku innaikku enna crop podanum suggest pannu",
        {},
        language="ta",
    )["content"]
    assert len(reply) >= 700
    assert "Seed vaangurathukku munadi" in reply
    assert "Next step" in reply
    assert not any("\u0B80" <= char <= "\u0BFF" for char in reply)


def test_detailed_turn_passes_configured_output_budget(monkeypatch):
    _, headers = create_test_farmer("response_budget")
    provider = get_llm_provider(force_new=True)
    monkeypatch.setenv("LOCAL_AI_MODE", "auto")
    monkeypatch.setenv("CHAT_MAX_RESPONSE_TOKENS", "420")
    with patch.object(
        provider,
        "generate_chat_response",
        new_callable=AsyncMock,
        return_value={"content": "Structured answer", "model": provider.default_model},
    ) as llm:
        response = client.post(
            "/api/chat/messages",
            json={"message": "Explain crop rotation planning in detail"},
            headers=headers,
        )
    assert response.status_code == 200
    assert llm.await_args.kwargs["max_tokens"] == 420


def test_first_turn_is_one_request_and_one_commit_with_local_status(monkeypatch):
    _, headers = create_test_farmer("quick_status")
    provider = get_llm_provider(force_new=True)
    monkeypatch.setenv("LOCAL_AI_MODE", "auto")
    with patch.object(provider, "generate_chat_response", new_callable=AsyncMock) as llm:
        from sqlalchemy import event
        from backend.app.database import engine
        from sqlalchemy.orm import Session
        commits, statements = [], []
        def committed(session): commits.append(True)
        def executed(conn, cursor, statement, params, context, many): statements.append(statement)
        event.listen(Session, "after_commit", committed)
        event.listen(engine, "before_cursor_execute", executed)
        try:
            started = perf_counter()
            response = client.post("/api/chat/messages", json={"message": "What is the crip status"}, headers=headers)
            elapsed = perf_counter() - started
        finally:
            event.remove(Session, "after_commit", committed)
            event.remove(engine, "before_cursor_execute", executed)
    assert response.status_code == 200
    data = response.json()
    assert data["response_mode"] == "instant-local-knowledge"
    assert "No crops are registered" in data["assistant_message"]["content"]
    llm.assert_not_awaited()
    assert len(commits) == 1
    assert sum(statement.lstrip().upper().startswith("SELECT") for statement in statements) <= 4
    print(f"\nFirst crop-status turn: {elapsed:.3f}s, {len(statements)} SQL statements, one commit (isolated test DB)")
    thread = client.get(f"/api/chat/conversations/{data['conversation']['id']}", headers=headers).json()
    assert [message['role'] for message in thread['messages']] == ['user', 'assistant']


def test_new_turn_endpoint_enforces_ownership_and_validation():
    _, owner = create_test_farmer("turn_owner")
    _, other = create_test_farmer("turn_other")
    conversation = client.post("/api/chat/conversations", json={}, headers=owner).json()
    payload = {"conversation_id": conversation["id"], "message": "hello"}
    assert client.post("/api/chat/messages", json=payload).status_code == 401
    assert client.post("/api/chat/messages", json=payload, headers=other).status_code == 404
    assert client.post("/api/chat/messages", json={"message": " "}, headers=owner).status_code == 400
    assert client.post("/api/chat/messages", json={"message": "x" * 2001}, headers=owner).status_code == 422


def test_slow_model_is_cancelled_and_fallback_saved(monkeypatch):
    _, headers = create_test_farmer("slow_model")
    cancelled = []
    async def slow_model(**kwargs):
        try:
            await asyncio.sleep(60)
        finally:
            cancelled.append(True)
    provider = get_llm_provider()
    monkeypatch.setattr(provider, "generate_chat_response", slow_model)
    monkeypatch.setattr(ChatAIService, "model_timeout_seconds", staticmethod(lambda: 0.02))
    response = client.post("/api/chat/messages", json={"message": "Explain crop rotation planning in detail"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["fallback_reason"] == "model_timeout"
    assert response.json()["assistant_message"]["model_name"] == "harvesta-offline-v1"
    assert cancelled == [True]


def test_latest_history_window_not_first_messages():
    user, _ = create_test_farmer("recent_context")
    with SessionLocal() as db:
        conversation = ChatStorageService.create_conversation(db, user.id)
        for number in range(12):
            ChatStorageService.add_message(db, conversation.id, "user", str(number), conversation=conversation, commit=False)
        db.commit()
        messages = ChatStorageService.get_conversation_messages(db, conversation.id, limit=4)
        assert [message.content for message in messages] == ["8", "9", "10", "11"]


def test_offline_status_context_excludes_other_farmers():
    user, _ = create_test_farmer("status_owner")
    other, _ = create_test_farmer("status_other")
    with SessionLocal() as db:
        farm = Farm(user_id=user.id, name="Own field")
        private_farm = Farm(user_id=other.id, name="Private field")
        db.add_all([farm, private_farm])
        db.flush()
        db.add_all([Crop(farm_id=farm.id, name="Tomato", health_status="Needs inspection"),
                    Crop(farm_id=private_farm.id, name="Secret crop")])
        db.commit()
        context = ChatAIService.build_offline_context(db, user)
        reply = LocalAIService.generate_offline_reply("crop status", context)["content"]
        assert "Tomato" in reply and "Needs inspection" in reply
        assert "not a live health check" in reply
        assert "Secret crop" not in reply


# =====================================================================
# 4. CONTEXT INJECTION & TELEMETRY
# =====================================================================

def test_farmer_context_builder_includes_agronomic_data():
    """Context builder includes user's farm, crop, analysis, and disease scan without leaking secrets."""
    user, _ = create_test_farmer("context_farmer")

    db = SessionLocal()
    try:
        # Add farm
        farm = Farm(user_id=user.id, name="Green Valley Farm", size=15.5, location="Nashik")
        db.add(farm)
        db.commit()

        # Add crop
        crop = Crop(farm_id=farm.id, name="Tomato", growth_stage="Flowering")
        db.add(crop)
        db.commit()

        # Add field analysis
        analysis = FieldAnalysisHistory(
            user_id=user.id,
            crop_type="Tomato",
            current_soil_moisture=52.4,
            soil_ph=6.5,
            soil_temperature=26.0,
            weather_temperature=28.0,
            weather_humidity=65.0,
            weather_precipitation=2.0,
            weather_wind_speed=8.0,
            recommendation_status="NO_IRRIGATION_NEEDED",
            priority="LOW",
            reason="Current field conditions are within the target range.",
            factors="[]",
            created_at=datetime.utcnow(),
        )
        db.add(analysis)

        # Add disease scan
        scan = CropDiseaseScan(
            user_id=user.id,
            farm_id=farm.id,
            crop_id=crop.id,
            image_path="uploads/disease_scans/scan_test.jpg",
            predicted_crop="Tomato",
            predicted_disease="Early Blight",
            confidence=0.88,
            model_version="v1.0",
            recommendation="Prune lower leaves.",
            created_at=datetime.utcnow(),
        )
        db.add(scan)
        db.commit()

        # Build context
        context_str = ChatAIService.build_farmer_context(db, user, farm_id=farm.id)

        assert "Green Valley Farm" in context_str
        assert "Tomato" in context_str
        assert "52.4%" in context_str
        assert "Early Blight" in context_str
        assert "password" not in context_str.lower()
        assert "secret" not in context_str.lower()
    finally:
        db.close()


def test_activity_telemetry_logged_without_full_body():
    """Chat message logs an activity_event without storing the raw text in metadata."""
    user, headers = create_test_farmer("telemetry_chat_user")
    conv = client.post("/api/chat/conversations", json={"title": "Telemetry Test"}, headers=headers).json()

    res = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"message": "A secret agricultural question that should not be in audit"},
        headers=headers,
    )
    assert res.status_code == 200

    db = SessionLocal()
    try:
        act = (
            db.query(ActivityEvent)
            .filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.event_name == "ai_chat_message",
            )
            .first()
        )
        assert act is not None
        assert act.feature == "ai_agronomist_chat"
        assert act.event_metadata["conversation_id"] == conv["id"]
        assert "secret agricultural question" not in str(act.event_metadata)
    finally:
        db.close()
