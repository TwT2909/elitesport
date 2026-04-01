from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tariff import Tariff
from app.routers.auth import get_current_user

router = APIRouter(prefix="/tariffs", tags=["tariffs"])
templates = Jinja2Templates(directory="app/templates")


def ctx(request: Request, **kwargs):
    return {"request": request, "t": request.state.t, "lang": request.state.lang, **kwargs}


@router.get("")
def tariff_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    tariffs = db.query(Tariff).order_by(Tariff.name).all()
    return templates.TemplateResponse("tariffs/list.html", ctx(request, user=user, tariffs=tariffs))


@router.get("/create")
def tariff_create_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role == "operator":
        return RedirectResponse(url="/tariffs")
    return templates.TemplateResponse("tariffs/form.html", ctx(request, user=user, tariff=None, error=None))


@router.post("/create")
def tariff_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    duration_days: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role == "operator":
        return RedirectResponse(url="/tariffs")

    tariff = Tariff(name=name, description=description or None, duration_days=duration_days, price=price)
    db.add(tariff)
    db.commit()
    return RedirectResponse(url="/tariffs", status_code=302)


@router.get("/{tariff_id}")
def tariff_edit_form(tariff_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role == "operator":
        return RedirectResponse(url="/tariffs")

    tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
    if not tariff:
        return RedirectResponse(url="/tariffs")

    return templates.TemplateResponse("tariffs/form.html", ctx(request, user=user, tariff=tariff, error=None))


@router.post("/{tariff_id}")
def tariff_update(
    tariff_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    duration_days: int = Form(...),
    price: float = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role == "operator":
        return RedirectResponse(url="/tariffs")

    tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
    if not tariff:
        return RedirectResponse(url="/tariffs")

    tariff.name = name
    tariff.description = description or None
    tariff.duration_days = duration_days
    tariff.price = price
    tariff.is_active = is_active
    db.commit()
    return RedirectResponse(url="/tariffs", status_code=302)
