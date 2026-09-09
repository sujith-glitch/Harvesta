"""Database-backed inventory management scoped to the current farmer."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import InventoryItem, User
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.auth_service import get_current_user


router = APIRouter(prefix="/api/inventory", tags=["Farm Inventory"])

ALLOWED_CATEGORIES = {"Seeds", "Fertilizer", "Crop protection", "Tools", "Equipment", "Other"}


class InventoryPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field("Other", max_length=100)
    quantity: float = Field(0, ge=0, le=1_000_000_000)
    unit: str = Field("units", min_length=1, max_length=50)
    low_stock_threshold: float = Field(0, ge=0, le=1_000_000_000)
    supplier: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("name", "unit")
    @classmethod
    def clean_required_text(cls, value):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned

    @field_validator("category")
    @classmethod
    def validate_category(cls, value):
        cleaned = value.strip()
        return cleaned if cleaned in ALLOWED_CATEGORIES else "Other"

    @field_validator("supplier", "notes")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


def _owned_item(db: Session, user_id: int, item_id: int) -> InventoryItem:
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.user_id == user_id,
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found.")
    return item


@router.get("", status_code=status.HTTP_200_OK)
def list_inventory(
    category: Optional[str] = Query(None, max_length=100),
    low_stock_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(InventoryItem).filter(InventoryItem.user_id == current_user.id)
    if category:
        query = query.filter(InventoryItem.category == category)
    items = query.order_by(InventoryItem.updated_at.desc()).all()
    if low_stock_only:
        items = [item for item in items if item.quantity <= item.low_stock_threshold]
    return {
        "total": len(items),
        "low_stock_count": sum(1 for item in items if item.quantity <= item.low_stock_threshold),
        "items": [item.to_dict() for item in items],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = InventoryItem(user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    AnalyticsService.log_activity_event(
        db=db,
        event_name="inventory_item_created",
        user_id=current_user.id,
        feature="inventory",
        metadata={"item_id": item.id, "category": item.category},
    )
    return item.to_dict()


@router.put("/{item_id}", status_code=status.HTTP_200_OK)
def update_inventory_item(
    item_id: int,
    payload: InventoryPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _owned_item(db, current_user.id, item_id)
    for field_name, value in payload.model_dump().items():
        setattr(item, field_name, value)
    db.commit()
    db.refresh(item)
    return item.to_dict()


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
def delete_inventory_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _owned_item(db, current_user.id, item_id)
    db.delete(item)
    db.commit()
    return {"status": "success", "id": item_id}
