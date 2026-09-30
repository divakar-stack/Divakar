from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import user_from_session
from config import BASE_DIR

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def page_context(request: Request, template: str, db: Session, status_code: int = 200, **extra):
    user = extra.pop("user", None) or user_from_session(request.session.get("user_id"), db)
    context = {"request": request, "user": user, **extra}
    return templates.TemplateResponse(request, template, context, status_code=status_code)