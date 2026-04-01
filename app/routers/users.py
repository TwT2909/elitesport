from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="app/templates")


def ctx(request: Request, **kwargs):
    return {"request": request, "t": request.state.t, "lang": request.state.lang, **kwargs}


@router.get("")
def user_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/dashboard")

    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse("users/list.html", ctx(request, user=user, users=users))


@router.get("/create")
def user_create_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("users/form.html", ctx(request, user=user, edit_user=None, error=None))


@router.post("/create")
def user_create(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/dashboard")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return templates.TemplateResponse(
            "users/form.html", ctx(request, user=user, edit_user=None, error="Username already taken"),
        )

    new_user = User(username=username, hashed_password=hash_password(password), full_name=full_name, role=UserRole(role))
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/users", status_code=302)


@router.get("/{user_id}")
def user_edit_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/dashboard")

    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        return RedirectResponse(url="/users")

    return templates.TemplateResponse("users/form.html", ctx(request, user=user, edit_user=edit_user, error=None))


@router.post("/{user_id}")
def user_update(
    user_id: int,
    request: Request,
    full_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/dashboard")

    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        return RedirectResponse(url="/users")

    edit_user.full_name = full_name
    edit_user.role = UserRole(role)
    edit_user.is_active = is_active
    if password:
        edit_user.hashed_password = hash_password(password)
    db.commit()
    return RedirectResponse(url="/users", status_code=302)
