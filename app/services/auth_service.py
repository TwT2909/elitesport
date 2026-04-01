import bcrypt
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tariff import Tariff


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_initial_admin(db: Session) -> None:
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return
    admin = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        full_name="Администратор",
        role="admin",
    )
    db.add(admin)
    db.commit()


def create_default_tariffs(db: Session) -> None:
    if db.query(Tariff).count() > 0:
        return

    defaults = [
        Tariff(
            name="Trainee",
            description="Базовый доступ к тренажёрному залу. Идеально для начинающих.",
            duration_days=30,
            price=1990,
        ),
        Tariff(
            name="Athlete",
            description="Зал + все групповые занятия: йога, кардио, функциональный тренинг.",
            duration_days=30,
            price=3490,
        ),
        Tariff(
            name="Champion",
            description="Полный доступ + персональный тренер + SPA-зона. Максимум возможностей.",
            duration_days=30,
            price=5990,
        ),
    ]

    for tariff in defaults:
        db.add(tariff)
    db.commit()
