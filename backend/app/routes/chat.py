"""
FastAPI Router for Real AI Agronomist Chat.
Provides authenticated conversation management, message exchange,
and contextual precision agricultural intelligence.
"""

import asyncio
import logging
from time import perf_counter
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, Farm, AIChatConversation, AIChatMessage
from backend.app.services.auth_service import get_current_user
from backend.app.services.chat_storage_service import ChatStorageService
from backend.app.services.chat_ai_service import ChatAIService, MAX_USER_MESSAGE_LENGTH, MAX_HISTORY_MESSAGES
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.audit_service import AuditService
from backend.app.services.local_ai_service import LocalAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["AI Agronomist Chat"])


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Optional conversation topic title")
    farm_id: Optional[int] = Field(None, description="Optional Farm ID for targeted agronomic context")


class MessageCreate(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_USER_MESSAGE_LENGTH,
        description="Farmer's question or agricultural query",
    )


class ChatTurnCreate(MessageCreate):
    conversation_id: Optional[int] = Field(None, gt=0)


@router.get("/status", status_code=status.HTTP_200_OK, summary="Get Local AI Readiness")
def get_chat_status(current_user: User = Depends(get_current_user)):
    return LocalAIService.get_status()


# ==========================================
# CONVERSATION ENDPOINTS
# ==========================================

@router.post(
    "/conversations",
    status_code=status.HTTP_201_CREATED,
    summary="Create a New AI Chat Conversation"
)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initializes a new persistent chat session for the authenticated farmer.
    Validates farm ownership if farm_id is provided.
    """
    if payload.farm_id is not None:
        farm = db.query(Farm).filter(Farm.id == payload.farm_id, Farm.user_id == current_user.id).first()
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Farm with ID {payload.farm_id} not found or does not belong to your account."
            )

    title = (payload.title or "").strip() or "New Conversation"
    conversation = ChatStorageService.create_conversation(
        db=db,
        user_id=current_user.id,
        title=title,
        farm_id=payload.farm_id,
    )

    AnalyticsService.log_activity_event(
        db=db,
        event_name="ai_chat_conversation_created",
        user_id=current_user.id,
        feature="ai_agronomist_chat",
        metadata={"conversation_id": conversation.id, "farm_id": payload.farm_id},
    )

    return conversation.to_dict()


@router.get(
    "/conversations",
    status_code=status.HTTP_200_OK,
    summary="List Authenticated Farmer's Chat Conversations"
)
def get_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns user-scoped conversations ordered newest/most recently updated first.
    """
    query = (
        db.query(AIChatConversation)
        .filter(AIChatConversation.user_id == current_user.id)
        .order_by(AIChatConversation.updated_at.desc())
    )
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "conversations": [c.to_dict() for c in items],
    }


@router.get(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Single Conversation and Message Thread"
)
def get_conversation_thread(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns single conversation details and ordered message thread. Enforces ownership.
    """
    conversation = ChatStorageService.get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or does not belong to your account."
        )

    messages = ChatStorageService.get_conversation_messages(db, conversation_id, limit=150)

    return {
        "conversation": conversation.to_dict(),
        "messages": [m.to_dict() for m in messages],
    }


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a Conversation and its Messages"
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes conversation and cascade-deletes its messages. Enforces ownership.
    """
    deleted = ChatStorageService.delete_conversation(db, conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or does not belong to your account."
        )

    AuditService.log_audit_event(
        db=db,
        action="ai_chat_conversation_deleted",
        entity_type="ai_chat_conversation",
        user_id=current_user.id,
        entity_id=conversation_id,
        status="SUCCESS",
    )

    return {
        "status": "success",
        "message": "Conversation deleted successfully.",
        "id": conversation_id,
    }


# ==========================================
# MESSAGE EXCHANGE ENDPOINT
# ==========================================

@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_200_OK,
    summary="Send Message to AI Agronomist"
)
def send_chat_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _exchange_message(conversation_id, payload, current_user, db)


@router.post("/messages", summary="Send a chat turn, creating a conversation if needed")
def send_chat_turn(
    payload: ChatTurnCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _exchange_message(payload.conversation_id, payload, current_user, db)


def _exchange_message(conversation_id, payload, current_user, db):
    # A synchronous route runs in FastAPI's worker pool: remote synchronous
    # database calls must not block the event loop used by other farmers.
    started = perf_counter()
    raw_message = payload.message.strip()
    if not raw_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat message cannot be empty or contain only whitespace."
        )

    user_id = current_user.id
    if conversation_id is None:
        conversation = ChatStorageService.create_conversation(
            db, user_id, title=raw_message[:45], commit=False,
        )
        conversation_id = conversation.id
        existing_messages = []
        AnalyticsService.log_activity_event(
            db, "ai_chat_conversation_created", user_id=user_id,
            feature="ai_agronomist_chat",
            metadata={"conversation_id": conversation_id, "farm_id": None}, commit=False,
        )
    else:
        conversation = ChatStorageService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or does not belong to your account."
            )
        existing_messages = ChatStorageService.get_conversation_messages(
            db, conversation_id, limit=MAX_HISTORY_MESSAGES,
        )

    if len(existing_messages) == 0 and (conversation.title == "New Conversation" or not conversation.title):
        # Auto-title: first 45 chars sanitized
        auto_title = raw_message[:45].strip()
        if len(raw_message) > 45:
            auto_title += "…"
        conversation.title = auto_title

    # 3. Store user message in database
    user_msg = ChatStorageService.add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=raw_message,
        conversation=conversation,
        commit=False,
    )

    # 4. Generate Assistant Response via ChatAIService
    res = asyncio.run(ChatAIService.generate_assistant_response(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
        farm_id=conversation.farm_id,
        user_message=raw_message,
        recent_messages=existing_messages,
    ))

    if res.get("error"):
        db.rollback()
        # Provider unavailable / failed — Return 503 without storing fake response
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=res["error"],
        )

    # 5. Store Assistant Message in database
    assistant_msg = ChatStorageService.add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=res["content"],
        model_name=res["model_name"],
        conversation=conversation,
        commit=False,
    )

    # 6. Log telemetry event (without storing full chat body in metadata)
    AnalyticsService.log_activity_event(
        db=db,
        event_name="ai_chat_message",
        user_id=user_id,
        feature="ai_agronomist_chat",
        metadata={
            "conversation_id": conversation_id,
            "model": res["model_name"],
            "provider": res.get("provider", "ollama"),
            "msg_len": len(raw_message),
        },
        commit=False,
    )

    # Persist the whole turn and telemetry together. Serialize after flush,
    # before commit expiry; avoid extra SELECT/refresh round trips to Supabase.
    db.flush()
    result = {
        "user_message": user_msg.to_dict(),
        "assistant_message": assistant_msg.to_dict(),
        "conversation": conversation.to_dict(),
        "response_mode": res.get("provider"),
        "fallback_reason": res.get("fallback_reason"),
    }
    db.commit()
    result["response_time_ms"] = round((perf_counter() - started) * 1000)
    return result
