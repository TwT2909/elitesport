from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.tariff import Tariff
from app.models.payment import Payment
from app.routers.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])
templates = Jinja2Templates(directory="app/templates")


def ctx(request: Request, **kwargs):
    return {"request": request, "t": request.state.t, "lang": request.state.lang, **kwargs}


@router.get("")
def payment_list(
    request: Request,
    page: int = Query(1, ge=1),
    client_id: int = Query(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    per_page = 20
    query = db.query(Payment)
    if client_id:
        query = query.filter(Payment.client_id == client_id)

    total = query.count()
    payments = query.order_by(Payment.payment_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "payments/list.html",
        ctx(request, user=user, payments=payments, page=page, total_pages=total_pages, client_id=client_id),
    )


@router.get("/create")
def payment_create_form(request: Request, client_id: int = Query(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    clients = db.query(Client).filter(Client.is_active == True).order_by(Client.last_name).all()
    tariffs = db.query(Tariff).filter(Tariff.is_active == True).order_by(Tariff.name).all()

    return templates.TemplateResponse(
        "payments/create.html",
        ctx(request, user=user, clients=clients, tariffs=tariffs, selected_client_id=client_id, error=None),
    )


@router.post("/create")
def payment_create(
    request: Request,
    client_id: int = Form(...),
    tariff_id: int = Form(...),
    valid_from: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
    if not tariff:
        return RedirectResponse(url="/payments/create")

    start_date = datetime.strptime(valid_from, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=tariff.duration_days)

    payment = Payment(
        client_id=client_id, tariff_id=tariff_id, amount=tariff.price,
        valid_from=start_date, valid_until=end_date, created_by=user.id,
    )
    db.add(payment)
    db.commit()
    return RedirectResponse(url="/payments", status_code=302)
