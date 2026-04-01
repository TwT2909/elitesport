from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from itsdangerous import URLSafeSerializer

from app.database import get_db
from app.config import SECRET_KEY
from app.services.auth_service import authenticate_user
from app.models.user import User
from app.i18n import get_translations

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")
serializer = URLSafeSerializer(SECRET_KEY)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.cookies.get("session")
    if not user_id:
        return None
    try:
        uid = serializer.loads(user_id)
    except Exception:
        return None
    return db.query(User).filter(User.id == uid, User.is_active == True).first()


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise RedirectException()
    return user


class RedirectException(Exception):
    pass


@router.get("/login")
def login_page(request: Request):
    lang = request.cookies.get("lang", "en")
    t = get_translations(lang)
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "t": t, "lang": lang})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    lang = request.cookies.get("lang", "en")
    t = get_translations(lang)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": t["wrong_credentials"], "t": t, "lang": lang},
        )
    response = RedirectResponse(url="/dashboard", status_code=302)
    token = serializer.dumps(user.id)
    response.set_cookie("session", token, httponly=True, max_age=86400)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response
