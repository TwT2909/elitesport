from datetime import datetime, date

from sqlalchemy import DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date] = mapped_column(Date)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    client = relationship("Client", back_populates="payments")
    tariff = relationship("Tariff")
    creator = relationship("User")
