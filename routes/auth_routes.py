from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import hash_password, user_from_session, verify_password
from database import get_db
from main_context import page_context
from models import User
from schemas import LoginInput, RegisterInput

router = APIRouter()


@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        data = RegisterInput.model_validate(dict(form))
    except ValidationError:
        return page_context(request, "register.html", db, status_code=422, error="Please enter a valid name, email, and password of at least 8 characters.")
    if db.scalar(select(User).where(User.email == data.email)):
        return page_context(request, "register.html", db, status_code=409, error="An account with that email already exists.")
    user = User(username=data.username, email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        data = LoginInput.model_validate(dict(form))
    except ValidationError:
        return page_context(request, "login.html", db, status_code=422, error="Enter your email and password.")
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        return page_context(request, "login.html", db, status_code=401, error="Email or password is incorrect.")
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@router.get("/session-info")
async def session_info(request: Request, db: Session = Depends(get_db)):
    user = user_from_session(request.session.get("user_id"), db)
    return {"authenticated": bool(user), "user": {"id": user.id, "username": user.username, "email": user.email} if user else None}


@router.get("/session-data")
async def session_data(request: Request, db: Session = Depends(get_db)):
    user = user_from_session(request.session.get("user_id"), db)
    return {"user_id": user.id if user else None, "authenticated": bool(user)}