from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from auth import user_from_session
from main_context import page_context

router = APIRouter()


@router.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    return page_context(request, "index.html", db)


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = user_from_session(request.session.get("user_id"), db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return page_context(request, "dashboard.html", db, user=user)


@router.get("/home-planner")
async def home_planner(request: Request, db: Session = Depends(get_db)):
    return page_context(request, "home_planner.html", db)


@router.get("/party-planner")
async def party_planner(request: Request, db: Session = Depends(get_db)):
    return page_context(request, "party_planner.html", db)


@router.get("/jewelry-planner")
async def jewelry_planner(request: Request, db: Session = Depends(get_db)):
    return page_context(request, "jewelry_planner.html", db)


@router.get("/login")
async def login_page(request: Request, db: Session = Depends(get_db)):
    return page_context(request, "login.html", db)


@router.get("/register")
async def register_page(request: Request, db: Session = Depends(get_db)):
    return page_context(request, "register.html", db)