import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import user_from_session
from database import get_db
from main_context import page_context
from models import RecommendationHistory

router = APIRouter()


@router.get("/history")
async def history(request: Request, db: Session = Depends(get_db)):
    user = user_from_session(request.session.get("user_id"), db)
    if not user:
        if "application/json" in request.headers.get("accept", ""):
            raise HTTPException(status_code=401, detail="Authentication required.")
        return RedirectResponse("/login", status_code=303)
    rows = db.scalars(select(RecommendationHistory).where(RecommendationHistory.user_id == user.id).order_by(RecommendationHistory.created_at.desc())).all()
    entries = [{"id": row.id, "planner_type": row.planner_type, "created_at": row.created_at,
                "inputs": json.loads(row.input_data), "results": json.loads(row.recommendation_data)} for row in rows]
    if "application/json" in request.headers.get("accept", ""):
        return {"history": entries}
    return page_context(request, "history.html", db, entries=entries, user=user)


@router.get("/recommendations-details")
async def recommendations_details(request: Request, id: int | None = None, db: Session = Depends(get_db)):
    user = user_from_session(request.session.get("user_id"), db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    query = select(RecommendationHistory).where(RecommendationHistory.user_id == user.id)
    if id is not None:
        query = query.where(RecommendationHistory.id == id)
    else:
        query = query.order_by(RecommendationHistory.created_at.desc()).limit(20)
    rows = db.scalars(query).all()
    return {"recommendations": [{"id": row.id, "planner_type": row.planner_type,
        "created_at": row.created_at.isoformat(), "input_data": json.loads(row.input_data),
        "recommendation_data": json.loads(row.recommendation_data)} for row in rows]}


@router.get("/startup")
async def startup_status():
    from config import GEMINI_API_KEY

    return {"status": "ok", "gemini_configured": bool(GEMINI_API_KEY), "fallback_available": True}