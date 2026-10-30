import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pos_name = Column(String, nullable=False)
    is_free = Column(Boolean, default=True, nullable=False)

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Strict ForeignKey referencing Position.id
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=False)
    app_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    educ = Column(String, nullable=False)
    experience = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    status = Column(String, default="New", nullable=False) # "New", "Hired", "Canceled"

class Interview(Base):
    __tablename__ = "interviews"

    id              = Column(String,   primary_key=True,
                              default=lambda: str(uuid.uuid4()))
    application_id  = Column(String,   ForeignKey("applications.id"),
                              nullable=False, index=True)
    calcom_uid      = Column(String,   unique=True, index=True,
                              nullable=False)
    booking_start   = Column(DateTime, nullable=False)
    booking_end     = Column(DateTime, nullable=False)
    attendee_email  = Column(String,   nullable=False)
    attendee_name   = Column(String,   nullable=False)
    attendee_tz     = Column(String,   default="UTC")
    support_email   = Column(String,   default="")
    status          = Column(String,   default="confirmed", index=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    cancelled_at    = Column(DateTime, nullable=True)