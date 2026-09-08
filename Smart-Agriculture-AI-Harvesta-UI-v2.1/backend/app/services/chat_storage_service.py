"""
AI Chat Storage and Conversation Management Service.
Handles conversational thread persistence, role-based message storage, and history querying.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models import AIChatConversation, AIChatMessage


class ChatStorageService:
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: int,
        title: str = "New Conversation",
        farm_id: Optional[int] = None,
        commit: bool = True,
    ) -> AIChatConversation:
        """
        Initializes a new conversational session.
        """
        conversation = AIChatConversation(
            user_id=user_id,
            farm_id=farm_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(conversation)
        if commit:
            db.commit()
            db.refresh(conversation)
        else:
            db.flush()
        return conversation

    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: int,
        limit: int = 20,
    ) -> List[AIChatConversation]:
        """
        Retrieves a user's recent conversations ordered by last update.
        """
        return (
            db.query(AIChatConversation)
            .filter(AIChatConversation.user_id == user_id)
            .order_by(AIChatConversation.updated_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int,
        user_id: int,
    ) -> Optional[AIChatConversation]:
        """
        Fetches a conversation by ID ensuring user ownership.
        """
        return (
            db.query(AIChatConversation)
            .filter(
                AIChatConversation.id == conversation_id,
                AIChatConversation.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
        model_name: Optional[str] = None,
        conversation: Optional[AIChatConversation] = None,
        commit: bool = True,
    ) -> AIChatMessage:
        """
        Appends a message ('user', 'assistant', 'system') to a conversation
        and updates the parent conversation's updated_at timestamp.
        """
        now = datetime.utcnow()
        message = AIChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_name=model_name,
            created_at=now,
        )
        db.add(message)

        # Update conversation updated_at
        if conversation is None:
            conversation = db.query(AIChatConversation).filter(AIChatConversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = now

        if commit:
            db.commit()
            db.refresh(message)
        return message

    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: int,
        limit: int = 100,
    ) -> List[AIChatMessage]:
        """
        Retrieves ordered messages for a conversation thread.
        """
        # Read the newest bounded window, then return it in conversational order.
        rows = (
            db.query(AIChatMessage)
            .filter(AIChatMessage.conversation_id == conversation_id)
            .order_by(AIChatMessage.created_at.desc(), AIChatMessage.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: int,
        user_id: int,
    ) -> bool:
        """
        Deletes a conversation and cascades deletion to all its messages.
        """
        conversation = (
            db.query(AIChatConversation)
            .filter(
                AIChatConversation.id == conversation_id,
                AIChatConversation.user_id == user_id,
            )
            .first()
        )
        if not conversation:
            return False
        db.delete(conversation)
        db.commit()
        return True
