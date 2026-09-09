"""Farmer-owned reports with in-app preview and PDF/CSV exports."""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ActivityEvent, CropDiseaseScan, Farm, FieldAnalysisHistory, User
from backend.app.services.auth_service import get_current_user
from backend.app.services.report_service import build_report_pdf


router = APIRouter(prefix="/api/reports", tags=["Farmer Reports"])

REPORTS = {
    "farm-overview": {
        "title": "Farm Overview",
        "description": "Registered fields, crops, land size, soil type, and farming method.",
    },
    "field-analysis": {
        "title": "Field Analysis",
        "description": "Saved soil, crop, weather, recommendation, and priority readings.",
    },
    "irrigation-history": {
        "title": "Irrigation History",
        "description": "Field analyses where irrigation action was recommended.",
    },
    "disease-screening": {
        "title": "Disease Screening",
        "description": "Crop image screening results and preliminary guidance.",
    },
    "activity-history": {
        "title": "Activity History",
        "description": "A privacy-safe record of features used in your Harvesta account.",
    },
}


def _date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y, %I:%M %p")
    return str(value or "Not available")


def _report(db: Session, user: User, key: str) -> Dict[str, Any]:
    if key not in REPORTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]

    if key == "farm-overview":
        columns = [
            {"key": "farm", "label": "Farm"}, {"key": "location", "label": "Location"},
            {"key": "size", "label": "Size (ha)"}, {"key": "soil", "label": "Soil type"},
            {"key": "method", "label": "Method"}, {"key": "crops", "label": "Crops"},
        ]
        farms = db.query(Farm).filter(Farm.user_id == user.id).order_by(Farm.created_at.desc()).all()
        rows = [{
            "farm": farm.name,
            "location": ", ".join(filter(None, [farm.location, farm.district, farm.state, farm.country])),
            "size": farm.size,
            "soil": farm.soil_type,
            "method": farm.farming_method,
            "crops": ", ".join(crop.name for crop in farm.crops) or "No crops added",
        } for farm in farms]
    elif key in {"field-analysis", "irrigation-history"}:
        columns = [
            {"key": "date", "label": "Date"}, {"key": "crop", "label": "Crop"},
            {"key": "moisture", "label": "Moisture"}, {"key": "ph", "label": "Soil pH"},
            {"key": "status", "label": "Recommendation"}, {"key": "priority", "label": "Priority"},
        ]
        query = db.query(FieldAnalysisHistory).filter(FieldAnalysisHistory.user_id == user.id)
        if key == "irrigation-history":
            query = query.filter(FieldAnalysisHistory.recommendation_status.ilike("%IRRIGATION%"))
        items = query.order_by(FieldAnalysisHistory.created_at.desc()).limit(500).all()
        rows = [{
            "date": _date(item.created_at), "crop": item.crop_type,
            "moisture": f"{item.current_soil_moisture:.1f}%", "ph": item.soil_ph,
            "status": item.recommendation_status.replace("_", " ").title(), "priority": item.priority.title(),
        } for item in items]
    elif key == "disease-screening":
        columns = [
            {"key": "date", "label": "Date"}, {"key": "crop", "label": "Crop"},
            {"key": "condition", "label": "Screening result"}, {"key": "confidence", "label": "Confidence"},
            {"key": "guidance", "label": "Preliminary guidance"},
        ]
        items = db.query(CropDiseaseScan).filter(
            CropDiseaseScan.user_id == user.id
        ).order_by(CropDiseaseScan.created_at.desc()).limit(500).all()
        rows = [{
            "date": _date(item.created_at), "crop": item.predicted_crop,
            "condition": item.predicted_disease,
            "confidence": f"{(item.confidence or 0) * 100:.1f}%",
            "guidance": item.recommendation,
        } for item in items]
    else:
        columns = [
            {"key": "date", "label": "Date"}, {"key": "event", "label": "Activity"},
            {"key": "feature", "label": "Feature"},
        ]
        items = db.query(ActivityEvent).filter(
            ActivityEvent.user_id == user.id
        ).order_by(ActivityEvent.created_at.desc()).limit(500).all()
        rows = [{
            "date": _date(item.created_at),
            "event": item.event_name.replace("_", " ").title(),
            "feature": (item.feature or "Account").replace("_", " ").title(),
        } for item in items]

    return {
        "key": key,
        **REPORTS[key],
        "record_count": len(rows),
        "columns": columns,
        "rows": rows,
        "generated_at": datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC"),
    }


@router.get("")
def list_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"reports": [_report(db, current_user, key) | {"rows": []} for key in REPORTS]}


@router.get("/{report_key}")
def view_report(
    report_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _report(db, current_user, report_key)


@router.get("/{report_key}/download")
def download_report(
    report_key: str,
    format: str = Query("pdf", pattern="^(pdf|csv)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _report(db, current_user, report_key)
    filename = f"harvesta-{report_key}.{format}"
    if format == "pdf":
        content = build_report_pdf(report, current_user.full_name)
        media_type = "application/pdf"
    else:
        text_buffer = io.StringIO(newline="")
        writer = csv.DictWriter(text_buffer, fieldnames=[column["key"] for column in report["columns"]])
        writer.writeheader()
        writer.writerows(report["rows"])
        content = text_buffer.getvalue().encode("utf-8-sig")
        media_type = "text/csv; charset=utf-8"
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
