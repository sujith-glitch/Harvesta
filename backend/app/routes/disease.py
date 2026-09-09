"""
FastAPI Router for Crop Disease Vision Screening & Scan History.
Provides image upload, real-time ML diagnostic screening, user-isolated scan persistence,
and history management.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, Farm, Crop, CropDiseaseScan
from backend.app.services.auth_service import get_current_user
from backend.app.services.disease_service import DiseaseService
from backend.app.services.image_storage_service import ImageStorageService
from backend.app.services.notification_service import NotificationService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Crop Disease Vision AI"])


@router.post(
    "/api/ai/disease-scan",
    status_code=status.HTTP_200_OK,
    summary="Screen Crop Leaf Image for Disease Anomalies"
)
async def scan_crop_disease(
    file: UploadFile = File(..., description="Crop leaf photo (JPEG, PNG, WebP)"),
    farm_id: Optional[int] = Form(None, description="Optional Farm ID to link"),
    crop_id: Optional[int] = Form(None, description="Optional Crop ID to link"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts an uploaded crop leaf photograph, performs security validation, runs vision ML screening,
    persists scan record to database, generates optional alerts, and returns actionable recommendations.
    """
    # 1. Verify Farm / Crop ownership if provided
    farm = None
    if farm_id is not None:
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Farm with ID {farm_id} not found or does not belong to your account."
            )

    crop = None
    if crop_id is not None:
        crop_query = db.query(Crop).join(Farm, Crop.farm_id == Farm.id).filter(Crop.id == crop_id, Farm.user_id == current_user.id)
        crop = crop_query.first()
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crop with ID {crop_id} not found or does not belong to your account."
            )

    # 2. Read and validate uploaded file bytes
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Uploaded image file is empty.")
    except Exception as read_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(read_err)}"
        )

    # 3. Validate image integrity and save to local storage
    try:
        storage_key, pil_image = ImageStorageService.save_scan_image(
            file_bytes=file_bytes,
            filename=file.filename or "scan.jpg",
            content_type=file.content_type,
            owner_id=current_user.id,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as storage_err:
        logger.error(f"Image storage error: {storage_err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process and store uploaded image."
        )

    # 4. Execute ML Vision Inference
    try:
        prediction = DiseaseService.predict_image(pil_image)
    except Exception as infer_err:
        logger.error(f"Inference execution error: {infer_err}", exc_info=True)
        # Cleanup uploaded image on ML error
        ImageStorageService.delete_scan_image(storage_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Disease screening inference failed. Please try again with a clearer photograph."
        )

    # 5. Persist Scan Record in database
    scan_record = CropDiseaseScan(
        user_id=current_user.id,
        farm_id=farm.id if farm else None,
        crop_id=crop.id if crop else None,
        image_path=storage_key,
        predicted_crop=prediction["predicted_crop"],
        predicted_disease=prediction["predicted_disease"],
        confidence=prediction["confidence"],
        model_version=prediction["model_version"],
        recommendation=prediction["recommendation_summary"],
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    # 6. Dispatch Notification Alert if disease detected
    if prediction["screening_status"] == "candidate_match":
        try:
            NotificationService.generate_disease_alert(
                db=db,
                user=current_user,
                crop_name=prediction["predicted_crop"],
                disease_name=prediction["predicted_disease"],
                confidence=prediction["confidence"],
                farm_name=farm.name if farm else None,
                urgency=prediction["urgency"],
            )
        except Exception as notif_err:
            logger.warning(f"Non-blocking disease alert trigger failed: {notif_err}")

    # 7. Log Activity Telemetry
    try:
        AnalyticsService.log_activity_event(
            db=db,
            event_name="disease_scan",
            user_id=current_user.id,
            feature="crop_disease_ai",
            metadata={
                "scan_id": scan_record.id,
                "crop": prediction["predicted_crop"],
                "disease": prediction["predicted_disease"],
                "confidence": prediction["confidence"],
                "is_healthy": prediction["is_healthy"],
            },
        )
    except Exception:
        pass

    return {
        "id": scan_record.id,
        "scan_id": scan_record.id,
        "predicted_crop": prediction["predicted_crop"],
        "predicted_disease": prediction["predicted_disease"],
        "display_name": prediction["display_name"],
        "confidence": prediction["confidence"],
        "confidence_threshold": prediction["confidence_threshold"],
        "screening_status": prediction["screening_status"],
        "is_healthy": prediction["is_healthy"],
        "urgency": prediction["urgency"],
        "description": prediction["description"],
        "recommendations": prediction["recommendations"],
        "recommendation": prediction["recommendation_summary"],
        "top_predictions": prediction["top_predictions"],
        "model_version": prediction["model_version"],
        "disclaimer": prediction["disclaimer"],
        "image_path": storage_key,
        "created_at": scan_record.created_at.isoformat() if scan_record.created_at else None,
    }


@router.get(
    "/api/disease-scans",
    status_code=status.HTTP_200_OK,
    summary="Get Farmer's Crop Disease Scan History"
)
def get_disease_scans(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    farm_id: Optional[int] = Query(None),
    crop_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns paginated scan history for the authenticated farmer (newest first).
    """
    query = db.query(CropDiseaseScan).filter(CropDiseaseScan.user_id == current_user.id)
    if farm_id is not None:
        query = query.filter(CropDiseaseScan.farm_id == farm_id)
    if crop_id is not None:
        query = query.filter(CropDiseaseScan.crop_id == crop_id)

    total = query.count()
    items = query.order_by(CropDiseaseScan.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "scans": [s.to_dict() for s in items],
    }


@router.get(
    "/api/disease-scans/{scan_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Single Crop Disease Scan Record"
)
def get_single_disease_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns single scan details. Enforces strict user ownership isolation.
    """
    scan = (
        db.query(CropDiseaseScan)
        .filter(CropDiseaseScan.id == scan_id, CropDiseaseScan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop disease scan record not found."
        )
    return scan.to_dict()


@router.delete(
    "/api/disease-scans/{scan_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Crop Disease Scan Record"
)
def delete_disease_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes scan record and removes associated stored image from disk.
    """
    scan = (
        db.query(CropDiseaseScan)
        .filter(CropDiseaseScan.id == scan_id, CropDiseaseScan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop disease scan record not found."
        )

    # Delete local image file
    if scan.image_path:
        ImageStorageService.delete_scan_image(scan.image_path)

    db.delete(scan)
    db.commit()

    AuditService.log_audit_event(
        db=db,
        action="crop_disease_scan_deleted",
        entity_type="crop_disease_scan",
        user_id=current_user.id,
        entity_id=scan_id,
        status="SUCCESS",
    )

    return {
        "status": "success",
        "message": "Crop disease scan record deleted successfully.",
        "id": scan_id,
    }


@router.get(
    "/api/disease-scans/{scan_id}/image",
    summary="Retrieve Stored Crop Disease Scan Image File"
)
def get_scan_image(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Securely streams the stored JPEG leaf image for authenticated scan owners.
    """
    scan = (
        db.query(CropDiseaseScan)
        .filter(CropDiseaseScan.id == scan_id, CropDiseaseScan.user_id == current_user.id)
        .first()
    )
    if not scan or not scan.image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan image not found."
        )

    image_bytes = ImageStorageService.get_scan_image_bytes(scan.image_path)
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file is missing from storage."
        )

    return Response(content=image_bytes, media_type="image/jpeg")
