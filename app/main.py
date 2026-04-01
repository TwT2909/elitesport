from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.database import engine, Base, SessionLocal
from app.services.auth_service import create_initial_admin, create_default_tariffs
from app.routers import auth, clients, tariffs, payments, dashboard, users
from app.i18n import get_translations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EliteSport: Client Management")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.middleware("http")
async def add_translations(request: Request, call_next):
    lang = request.cookies.get("lang", "en")
    request.state.lang = lang
    request.state.t = get_translations(lang)
    response = await call_next(request)
    return response


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(clients.router)
app.include_router(tariffs.router)
app.include_router(payments.router)
app.include_router(users.router)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        create_initial_admin(db)
        create_default_tariffs(db)
    finally:
        db.close()


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")


@app.get("/set-lang")
def set_language(lang: str = Query(...), redirect: str = Query("/dashboard")):
    response = RedirectResponse(url=redirect, status_code=302)
    response.set_cookie("lang", lang, max_age=365 * 24 * 3600)
    return response
