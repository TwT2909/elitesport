import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Form, Query, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.client import Client, Gender
from app.models.tariff import Tariff
from app.models.payment import Payment
from app.routers.auth import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = os.path.join("app", "static", "uploads")


async def save_photo(photo: UploadFile) -> str | None:
    if not photo or not photo.filename:
        return None
    ext = os.path.splitext(photo.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        return None
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await photo.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return filename


def ctx(request: Request, **kwargs):
    return {"request": request, "t": request.state.t, "lang": request.state.lang, **kwargs}


@router.get("")
def client_list(
    request: Request,
    search: str = Query("", alias="q"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    per_page = 20
    query = db.query(Client).filter(Client.is_active == True)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Client.last_name.ilike(pattern),
                Client.first_name.ilike(pattern),
                Client.phone.ilike(pattern),
                Client.email.ilike(pattern),
            )
        )

    total = query.count()
    clients = query.order_by(Client.last_name).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "clients/list.html",
        ctx(request, user=user, clients=clients, search=search, page=page, total_pages=total_pages, total=total),
    )


@router.get("/create")
def client_create_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    tariffs = db.query(Tariff).filter(Tariff.is_active == True).order_by(Tariff.name).all()
    return templates.TemplateResponse("clients/create.html", ctx(request, user=user, tariffs=tariffs, error=None))


@router.post("/create")
async def client_create(
    request: Request,
    last_name: str = Form(...),
    first_name: str = Form(...),
    patronymic: str = Form(""),
    phone: str = Form(...),
    email: str = Form(""),
    birth_date: str = Form(""),
    gender: str = Form("male"),
    notes: str = Form(""),
    tariff_id: int = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    photo_filename = await save_photo(photo)

    client = Client(
        last_name=last_name,
        first_name=first_name,
        patronymic=patronymic or None,
        phone=phone,
        email=email or None,
        birth_date=datetime.strptime(birth_date, "%Y-%m-%d").date() if birth_date else None,
        gender=Gender(gender),
        photo=photo_filename,
        notes=notes or None,
    )
    db.add(client)
    db.flush()

    if tariff_id:
        tariff = db.query(Tariff).filter(Tariff.id == tariff_id, Tariff.is_active == True).first()
        if tariff:
            from datetime import timedelta
            start = datetime.today().date()
            payment = Payment(
                client_id=client.id,
                tariff_id=tariff.id,
                amount=tariff.price,
                valid_from=start,
                valid_until=start + timedelta(days=tariff.duration_days),
                created_by=user.id,
            )
            db.add(payment)

    db.commit()
    return RedirectResponse(url="/clients", status_code=302)


@router.get("/{client_id}")
def client_detail(client_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return RedirectResponse(url="/clients")

    return templates.TemplateResponse("clients/edit.html", ctx(request, user=user, client=client, error=None))


@router.post("/{client_id}")
async def client_update(
    client_id: int,
    request: Request,
    last_name: str = Form(...),
    first_name: str = Form(...),
    patronymic: str = Form(""),
    phone: str = Form(...),
    email: str = Form(""),
    birth_date: str = Form(""),
    gender: str = Form("male"),
    notes: str = Form(""),
    is_active: bool = Form(True),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    if user.role == "operator":
        return RedirectResponse(url="/clients")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return RedirectResponse(url="/clients")

    photo_filename = await save_photo(photo)
    if photo_filename:
        if client.photo:
            old_path = os.path.join(UPLOAD_DIR, client.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        client.photo = photo_filename

    client.last_name = last_name
    client.first_name = first_name
    client.patronymic = patronymic or None
    client.phone = phone
    client.email = email or None
    client.birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date() if birth_date else None
    client.gender = Gender(gender)
    client.notes = notes or None
    client.is_active = is_active
    db.commit()
    return RedirectResponse(url="/clients", status_code=302)
