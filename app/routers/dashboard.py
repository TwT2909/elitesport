from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.client import Client
from app.models.payment import Payment
from app.routers.auth import get_current_user

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    total_clients = db.query(func.count(Client.id)).filter(Client.is_active == True).scalar()

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    payments_this_month = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.payment_date >= month_start)
        .scalar()
    )
    payments_count = (
        db.query(func.count(Payment.id))
        .filter(Payment.payment_date >= month_start)
        .scalar()
    )

    week_later = (now + timedelta(days=7)).date()
    expiring = (
        db.query(Payment)
        .filter(Payment.valid_until <= week_later, Payment.valid_until >= now.date())
        .all()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "t": request.state.t,
            "lang": request.state.lang,
            "total_clients": total_clients,
            "payments_this_month": float(payments_this_month),
            "payments_count": payments_count,
            "expiring": expiring,
        },
    )
