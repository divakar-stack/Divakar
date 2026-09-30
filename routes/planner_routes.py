import json
import re
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from auth import user_from_session
from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE
from database import get_db
from main_context import page_context
from models import RecommendationHistory
from schemas import HomePlannerInput, JewelryPlannerInput, PartyPlannerInput
from services import gemini_service, recommendation_service

router = APIRouter()


def _form_error(request: Request, db: Session, template: str, message: str):
    return page_context(request, template, db, status_code=422, error=message)


def _save_history(request: Request, db: Session, planner: str, inputs: dict, results: dict) -> None:
    user = user_from_session(request.session.get("user_id"), db)
    if not user:
        return
    db.add(RecommendationHistory(user_id=user.id, planner_type=planner,
        input_data=json.dumps(inputs, default=str), recommendation_data=json.dumps(results, default=str)))
    db.commit()


def _parse_home_items(value: str) -> list[dict]:
    items = []
    for line in value.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*(.{1,80}?)\s*(?::|,)\s*(-?\d+)\s*", line)
        if not match:
            raise ValueError("List each item as Item name: quantity, for example Sofa: 1.")
        items.append({"name": match.group(1).strip(), "quantity": int(match.group(2))})
    if not items:
        raise ValueError("Add at least one item and its quantity.")
    return items


@router.post("/generate-home", response_class=HTMLResponse)
async def generate_home(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        values = dict(form)
        values["items"] = _parse_home_items(str(values.pop("required_items", "")))
        data = HomePlannerInput.model_validate(values)
    except (ValidationError, ValueError) as exc:
        message = str(exc.errors()[0]["msg"]) if isinstance(exc, ValidationError) and exc.errors() else str(exc)
        return _form_error(request, db, "home_planner.html", message)
    inputs = data.model_dump(mode="json")
    results, ai_used = recommendation_service.generate_home_recommendations(data.model_dump(mode="python"))
    _save_history(request, db, "home", inputs, results)
    return page_context(request, "home_results.html", db, results=results, ai_used=ai_used)


@router.post("/generate-party", response_class=HTMLResponse)
async def generate_party(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    values = dict(form)
    values["accommodation_required"] = values.get("accommodation_required") in {"on", "true", "yes"}
    try:
        data = PartyPlannerInput.model_validate(values)
    except ValidationError as exc:
        return _form_error(request, db, "party_planner.html", str(exc.errors()[0]["msg"]))
    inputs = data.model_dump(mode="json")
    results, ai_used = recommendation_service.generate_party_recommendations(data.model_dump(mode="python"))
    _save_history(request, db, "party", inputs, results)
    return page_context(request, "party_results.html", db, results=results, ai_used=ai_used)


def _valid_image_signature(data: bytes, mime_type: str) -> bool:
    return ((mime_type == "image/jpeg" and data.startswith(b"\xff\xd8\xff"))
            or (mime_type == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
            or (mime_type == "image/webp" and len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"))


@router.post("/generate-jewelry", response_class=HTMLResponse)
async def generate_jewelry(request: Request, outfit_image: UploadFile | None = File(default=None), db: Session = Depends(get_db)):
    form = await request.form()
    values = dict(form)
    image_data = None
    mime_type = ""
    if outfit_image and outfit_image.filename:
        mime_type = outfit_image.content_type or ""
        extension = "." + outfit_image.filename.rsplit(".", 1)[-1].lower() if "." in outfit_image.filename else ""
        if extension not in ALLOWED_IMAGE_EXTENSIONS or mime_type not in ALLOWED_IMAGE_TYPES:
            return _form_error(request, db, "jewelry_planner.html", "Upload a JPG, JPEG, PNG, or WEBP image.")
        image_data = await outfit_image.read(MAX_IMAGE_SIZE + 1)
        if len(image_data) > MAX_IMAGE_SIZE:
            return _form_error(request, db, "jewelry_planner.html", "The outfit image must be 5 MB or smaller.")
        if not _valid_image_signature(image_data, mime_type):
            return _form_error(request, db, "jewelry_planner.html", "The image contents do not match the selected image type.")
    try:
        data = JewelryPlannerInput.model_validate(values)
    except ValidationError as exc:
        return _form_error(request, db, "jewelry_planner.html", str(exc.errors()[0]["msg"]))
    outfit_analysis = ""
    image_input = (image_data, mime_type) if image_data else None
    if image_input:
        outfit_analysis = gemini_service.analyze_outfit_image(image_data, mime_type, data.outfit_description)
    inputs = data.model_dump(mode="json")
    if image_data:
        inputs["outfit_image_uploaded"] = True
    results, ai_used = recommendation_service.generate_jewelry_recommendations(data.model_dump(mode="python"), outfit_analysis, image_input)
    _save_history(request, db, "jewelry", inputs, results)
    return page_context(request, "jewelry_results.html", db, results=results, ai_used=ai_used)