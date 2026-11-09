from __future__ import annotations

import os
import uuid
import logging
import random

from datetime import date, datetime, timedelta
from uuid import UUID
from typing import List

import requests

# added gmail
import smtplib
from email.message import EmailMessage
#

import json

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Form,
    Request
)

from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    func,
    Index,
    text
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from models import Base, Position, Application, Interview


from pydantic import BaseModel, field_validator
from datetime import date
from uuid import UUID

from datetime import timezone

import hmac
import hashlib

CALCOM_WEBHOOK_SECRET = os.getenv("CALCOM_WEBHOOK_SECRET")


class CalcomWebhookPayload(BaseModel):
    triggerEvent: str
    payload: dict


def verify_calcom_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not CALCOM_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        CALCOM_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature_header, expected)

# ----------------------------------
# Timezone naive-UTC datetime return for SQLite и Postgres
# ----------------------------------

def parse_calcom_datetime(value: str) -> datetime:
    """
    Безопасный парсинг ISO-8601 для Python 3.8.
    Отрезает миллисекунды (например, .000Z), которые старый Python не понимает.
    """
    if "." in value:
        parts = value.split(".")
        if "Z" in parts[1]:
            value = parts[0] + "Z"
        elif "+" in parts[1]:
            value = parts[0] + "+" + parts[1].split("+")[1]
        elif "-" in parts[1] and parts[1].find("-") > 0:
            value = parts[0] + parts[1][parts[1].find("-"):]
        else:
            value = parts[0]

    value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

def cancel_calcom_booking(booking_uid: str) -> bool:
    """
    Отменяет бронь в Cal.com.
    Возвращает True при успехе (200/204), иначе False.
    """
    if not CALCOM_API_KEY:
        logging.warning("CALCOM_API_KEY missing, cannot cancel booking.")
        return False

    url = f"https://api.cal.com/v2/bookings/{booking_uid}/cancel"
    headers = {
        "Authorization":   f"Bearer {CALCOM_API_KEY}",
        "Content-Type":    "application/json",
        "cal-api-version": "2024-08-13",
    }
    body = {
        "cancellationReason": "Demo reset",
        # cancelSubsequentBookings только для повторяющихся броней,
        # для обычной интервью-брони оставляем False или не передаём.
    }

    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        if r.status_code in (200, 204):
            logging.info(f"Cal.com booking {booking_uid} cancelled.")
            return True
        logging.warning(
            f"Cal.com cancel failed for {booking_uid}: "
            f"{r.status_code} {r.text[:200]}"
        )
        return False
    except requests.RequestException as e:
        logging.exception(f"Cal.com cancel request error: {e}")
        return False

def prune_old_interviews(db: Session, keep_last: int = 20):
    """
    Оставляет в БД только `keep_last` самых свежих записей.
    Перед удалением старых броней отменяет их в Cal.com.
    """
    try:
        # Получаем все брони, сортируя от новых к старым (по дате создания)
        interviews = db.query(Interview).order_by(Interview.created_at.desc()).all()

        if len(interviews) > keep_last:
            to_delete = interviews[keep_last:] # Берем всё, что идет после 10-й записи

            for old_int in to_delete:
                # Если бронь еще активна, отменяем её в Cal.com
                if old_int.status == "confirmed":
                    cancel_calcom_booking(old_int.calcom_uid)

                # Удаляем из локальной БД
                db.delete(old_int)

            db.commit()
            logging.info(f"Pruned {len(to_delete)} old interviews. Kept last {keep_last}.")
            
    except Exception as e:
        db.rollback()
        logging.exception("Error pruning old interviews.")        

# ----------------------------------
# Interview tablesqlite3 hr_project.db ".schema interviews"
# ----------------------------------

class InterviewResponse(BaseModel):
    id:             str
    application_id: str
    calcom_uid:     str
    booking_start:  datetime
    booking_end:    datetime
    attendee_email: str
    attendee_name:  str
    attendee_tz:    str
    support_email:  str
    status:         str
    created_at:     datetime

    class Config:
        from_attributes = True


class BookedSlotResponse(BaseModel):
    start:          str
    end:            str
    booking_uid:    str
    application_id: str


# ----------------------------------
# Common demo applications
# ----------------------------------

APPLICATION_DEMO_COLLECTION = {
        # ----------------------------------
        # English examples
        # ----------------------------------
        
            "en": [
            
                {
                    "lang":         "en",
                    "position_id":  "Senior Backend Developer",
                    "educ":         "BSc Computer Science",
                    "experience":   "5 years",
                    "full_name":    "Alice Smith",
                    "email":        "aspanseric+alice@gmail.com",
                    "birth_date":   date(1990, 5, 15),
                    "status":       "New"
                },
                {
                    "lang":         "en",
                    "position_id":  "Frontend Engineer",
                    "educ":         "MBA",
                    "experience":   "3 years",
                    "full_name":    "Bob Jones",
                    "email":        "aspanseric+bob@gmail.com",
                    "birth_date":   date(1988, 8, 22),
                    "status":       "Hired"
                },
                {
                    "lang":         "en",
                    "position_id":  "HR Manager",
                    "educ":         "BA Psychology",
                    "experience":   "2 years",
                    "full_name":    "Charlie Brown",
                    "email":        "aspanseric+charlie@gmail.com",
                    "birth_date":   date(1995, 1, 10),
                    "status":       "Canceled"
                },
                # --- НОВЫЕ АНГЛИЙСКИЕ ПРИМЕРЫ ---
                {
                    "lang":         "en",
                    "position_id":  "Frontend Engineer",
                    "educ":         "MSc Software Engineering",
                    "experience":   "6 years",
                    "full_name":    "David Miller",
                    "email":        "aspanseric+david@gmail.com",
                    "birth_date":   date(1985, 11, 20),
                    "status":       "New"
                },
                {
                    "lang":         "en",
                    "position_id":  "HR Manager",
                    "educ":         "BSc Human Resources",
                    "experience":   "4 years",
                    "full_name":    "Eva Green",
                    "email":        "aspanseric+eva@gmail.com",
                    "birth_date":   date(1993, 3, 8),
                    "status":       "New"
                }
            ],

        # ----------------------------------
        # Russian examples
        # ----------------------------------
        
            "ru": [
        
                {
                    "lang":        "ru",
                    "position_id": "Senior Backend Developer",
                    "educ":        "Высшее. Бакалавр",
                    "experience":  "3 года",
                    "full_name":   "Синицын Пётр Игоревич",
                    "email":       "aspanseric+SPI94@gmail.com",
                    "birth_date":  date(1994, 6, 2),
                    "status":      "New"
                },
                {
                    "lang":        "ru",
                    "position_id": "Frontend Engineer",
                    "educ":        "Высшее. Магистр",
                    "experience":  "5 лет",
                    "full_name":   "Иванова Анна Сергеевна",
                    "email":       "aspanseric+IAA92@gmail.com",
                    "birth_date":  date(1992, 2, 29),
                    "status":      "Hired"
                },
                {
                    "lang":        "ru",
                    "position_id": "HR Manager",
                    "educ":        "Высшее. Кандидат технических наук",
                    "experience":  "7 лет",
                    "full_name":   "Петров Алексей Дмитриевич",
                    "email":       "aspanseric+PAD90@gmail.com",
                    "birth_date":  date(1990, 1, 10),
                    "status":      "Canceled"
                },
                # --- НОВЫЕ РУССКИЕ ПРИМЕРЫ ---
                {
                    "lang":        "ru",
                    "position_id": "Frontend Engineer",
                    "educ":        "Высшее. Бакалавр",
                    "experience":  "4 года",
                    "full_name":   "Захаров Михаил Олегович",
                    "email":       "aspanseric+ZHRV@gmail.com",
                    "birth_date":  date(1997, 7, 14),
                    "status":      "New"
                },
                {
                    "lang":        "ru",
                    "position_id": "Senior Backend Developer",
                    "educ":        "Высшее. Магистр",
                    "experience":  "6 лет",
                    "full_name":   "Черепанова Мария Петровна",
                    "email":       "aspanseric+CHMP@gmail.com",
                    "birth_date":  date(1991, 9, 30),
                    "status":      "New"
                }

            ]
        }



# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./hr_project.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if "sqlite" in DATABASE_URL
        else {}
    ),
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

Base.metadata.create_all(bind=engine)

# ==========================================
# FASTAPI INITIALIZATION
# ==========================================

app = FastAPI(
    title="HR Hiring System API",
    version="1.1.0"
)


# ==========================================
# DATABASE DEPENDENCY
# ==========================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class PositionResponse(BaseModel):
    id: str
    pos_name: str
    is_free: bool

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    id: str
    position_id: str
    position_name: str
    app_date: datetime
    educ: str
    experience: str
    full_name: str
    email: str
    birth_date: date
    status: str

    class Config:
        from_attributes = True

class PositionCreate(BaseModel):
    pos_name: str
    is_free: bool = True

class ApplicationCreate(BaseModel):
    position_id: UUID
    educ: str
    experience: str
    full_name: str
    email: str
    birth_date: date

    @field_validator(
        "educ",
        "experience",
        "full_name",
        "email"
    )

    # Сначала объявляется список полей "@field_validator" для которых нужна проверка,
    # а сразу после пишется сама проверка, т.к. она идёт сразу после значит это прверка 
    # (метод/функця) предназначена для полей выше. Проходит построчно: сначала "educ", 
    # потом "experience" и т.д.

    @classmethod
    def field_must_not_be_empty(cls, value: str) -> str:
        # "-> str" подсказывает программе, что раз в "value" пришёл ": str", то и на выходе будет "str".
        # Это не ограничение, а подсказка, если в итоге будет число, то прога просто подчеркнёт красным,
        # код при этом не обязательно сломается - питон гибкий) Так же подсказка "->" нужна чтоб
        # IDE подсказывал какие методы можно использоавть для этого типа данных.
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value

    # Из особенностей: обычно функции работают с уже существующими экземплярами класса,
    # а тут проверка: "можно ли вообще создать экз.?" поэтому в метод @classmethod 
    # передаётся "cls", это означает, что нужно сметреть состав атрибутов 
    # класса "ApplicationCreate", а не конкретного экземпляра (которог ещё и нет).    
        
    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, value: str) -> str:
        value = value.strip()

        if "@" not in value:
            raise ValueError("Invalid email address.")

        return value


class StatusUpdateRequest(BaseModel):
    status: str
    email: str
    support_email: str = ""


class EmailUpdateRequest(BaseModel):
    email: str
# was "send_brevo_email"
def send_email(
    to_email: str,
    subject: str,
    message: str
) -> bool:

    if "@" not in to_email:
        logging.warning("Invalid email. Skipping email.")
        return False

    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_password:
        logging.error("Gmail settings are missing.")
        return False

    email_message = EmailMessage()
    email_message["From"] = gmail_address
    email_message["To"] = to_email
    email_message["Subject"] = subject
    email_message.set_content(message, subtype="html")

    try:
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=10
        ) as server:
            server.login(gmail_address, gmail_password)
            server.send_message(email_message)

        logging.info(f"Email successfully sent to {to_email}")
        return True

    except Exception:
        logging.exception("Gmail sending failed.")
        return False

def normalize_email(email: str) -> str:
    """
    Normalize email for consistent duplicate checking.
    """
    return email.strip().lower() 
    # Функция которая нормализует имэй, чтоб при проверке не было сложностей 
    # с заглавными буквами - всё нормализуется до строчных

# ==========================================
# CAL.COM CONFIG
# ==========================================

CALCOM_API_KEY    = os.getenv("CALCOM_API_KEY")
CALCOM_EVENT_TYPE = os.getenv("CALCOM_EVENT_TYPE")

if CALCOM_EVENT_TYPE:
    try:
        CALCOM_EVENT_TYPE = int(CALCOM_EVENT_TYPE)
    except ValueError:
        logging.warning(
            "CALCOM_EVENT_TYPE must be an integer (e.g. 123456). "
            "Calendar integration will be disabled."
        )
        CALCOM_EVENT_TYPE = None


class InterviewRequest(BaseModel):
    application_id: str
    email:          str
    full_name:      str
    booking_start:  str          # ISO 8601, e.g. "2026-10-30T04:00:00.000Z"
    booking_end:    str          # ISO 8601
    support_email:  str = ""
    timezone:       str = "UTC"  # TODO: populate from browser detection later
    language:       str = "en"   # TODO: populate from browser detection later

# ==========================================
# API: Webhook cal.com
# ==========================================

@app.post("/api/webhooks/calcom")
async def calcom_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Принимает события от Cal.com.
    Проверяет подпись X-Cal-Signature-256.
    На BOOKING_CANCELLED помечает бронь как отменённую.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Cal-Signature-256")

    if not verify_calcom_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = CalcomWebhookPayload(**json.loads(raw_body))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    trigger = event.triggerEvent
    data = event.payload

    if trigger == "BOOKING_CANCELLED":
        booking_uid = data.get("uid")
        if not booking_uid:
            raise HTTPException(status_code=400, detail="Missing booking uid")

        interview = db.query(Interview).filter(
            Interview.calcom_uid == booking_uid,
            Interview.status == "confirmed",
        ).first()

        if interview:
            interview.status = "cancelled"
            interview.cancelled_at = datetime.utcnow()
            db.commit()
            logging.info(f"Interview {interview.id} cancelled via webhook (cal.com uid={booking_uid})")
        else:
            logging.warning(f"Webhook cancellation for unknown/ already-cancelled uid={booking_uid}")

    # BOOKING_CREATED / RESCHEDULED можно обработать позже
    return {"status": "ok"}

# ==========================================
# API: CREATE APPLICATION
# ==========================================

@app.post(
    "/api/applications",
    status_code=status.HTTP_201_CREATED
)

def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db)
):

    try:

        # ----------------------------------
        # 1. Validate position UUID
        # ----------------------------------
        
        valid_position_id = str(application_data.position_id)

        # ----------------------------------
        # 2. Normalize email
        # ----------------------------------
        
        normalized_email = normalize_email(application_data.email)

        # ----------------------------------
        # 3. Check whether position exists
        # ----------------------------------

        position = db.query(Position).filter(
            Position.id == valid_position_id
        ).first()

        if not position:
            raise HTTPException(
                status_code=404,
                detail="Position not found."
            )

        # ----------------------------------
        # 4. Check active duplicate
        # ----------------------------------

        existing_app = db.query(Application).filter(                # проверка на соовпадение по:
            func.lower(Application.email)   == normalized_email,    # - имеющемуся email
            Application.position_id         == valid_position_id,   # - имеющейся позицией
            Application.status.in_          (["New", "Hired"])      # - только статус Новый или Принят
        ).first()

        if existing_app:

            logging.warning(
                f"Duplicate application rejected: "
                f"email={normalized_email}, "
                f"position_id={valid_position_id}"
            )

            raise HTTPException(
                status_code=409,
                detail="You have already applied for this position."
            )

        # ----------------------------------
        # 5. Create application
        # ----------------------------------

        new_app = Application(
            id          =str(uuid.uuid4()),
            position_id =valid_position_id,
            app_date    =datetime.utcnow(),
            educ        =application_data.educ,
            experience  =application_data.experience,
            full_name   =application_data.full_name,
            email       =normalized_email,
            birth_date  =application_data.birth_date,
            status      ="New"
        )

        db.add(new_app)

        db.commit()
        db.refresh(new_app)

        logging.info(
            f"Application created: {new_app.id}"
        )

        return {
            "message": "Created",
            "id": new_app.id
        }

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        logging.warning(
            "Database rejected duplicate application."
        )

        raise HTTPException(
            status_code=409,
            detail="You have already applied for this position."
        )

    except Exception as e:
        db.rollback()

        logging.exception(
            f"Error creating application: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error during database operation."
        )


# ==========================================
# API: UPDATE APPLICATION STATUS
# ==========================================

@app.patch(
    "/api/applications/{app_id}/status",
    status_code=status.HTTP_200_OK
)
def update_application_status(
    app_id: str,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates application status.

    Hiring:
    - Application status becomes Hired.
    - Linked position becomes unavailable.
    - Candidate receives a hiring email.
    - Support receives a workplace notification.

    Cancellation:
    - Application status becomes Canceled.
    - Candidate receives a rejection email.

    Изменение статуса заявки - Принят/Отклонена.

    Принять:
        Статус становится   - Принят
        Позиция             - недоступна
        Кандидуту и Поддежке- по указанным адресам отправляются имэйлы

    Отказать:
        Статус становится   - Отклонена
        Кандидат получает   - по указанному адресу получает отказ

    """

    if request.status not in ["Hired", "Canceled"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be 'Hired' or 'Canceled'."
        )

    try:

        # 1. Find application
        application = db.query(Application).filter(
            Application.id == app_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found."
            )

        # 2. Application must be New
        if application.status != "New":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Application cannot be changed because "
                    f"its current status is '{application.status}'."
                )
            )

        # 3. Find linked position
        position = db.query(Position).filter(
            Position.id == application.position_id
        ).first()

        if request.status == "Hired" and not position:
            raise HTTPException(
                status_code=404,
                detail="Linked position not found."
            )

        # 4. Update status
        application.status = request.status

        # 5. Make position unavailable after hiring
        if request.status == "Hired":
            position.is_free = False

        db.commit()
        db.refresh(application)

        logging.info(
            f"Application {application.id} status updated "
            f"to {application.status}"
        )

        # 6. Send emails
        candidate_email_sent = False
        support_email_sent = False

        if "@" in request.email:

            if request.status == "Hired":
                candidate_email_sent = send_email(
                    request.email,
                    "Congratulations! You are hired",
                    "Congratulations, you are hired! Come work with us."
                )

            elif request.status == "Canceled":
                candidate_email_sent = send_email(
                    request.email,
                    "Application update",
                    "Sorry, your application is not a fit for us. "
                    "Have a good day."
                )

        if (
            request.status == "Hired"
            and request.support_email
            and "@" in request.support_email
        ):
            support_email_sent = send_email(
                request.support_email,
                "New employee hired",
                f"New employee {application.full_name} hired. "
                "Please prepare a workplace."
            )

        # 7. Return result
        response = {
            "message": "OK",
            "application_id": application.id,
            "status": application.status,
            "candidate_email_sent": candidate_email_sent
        }

        if request.status == "Hired":
            response["support_email_sent"] = support_email_sent

        if "@" not in request.email:
            response["warning"] = (
                "Candidate email is invalid. "
                "Application status was updated, but no candidate email was sent."
            )

        return response

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Status update conflicts with existing application data."
        )

    except Exception as e:
        db.rollback()

        logging.exception(
            f"Error updating application status: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error during status update."
        )
#


# aded
class EmailUpdateRequest(BaseModel):
    email: str


@app.patch(
    "/api/applications/{app_id}/email",
    status_code=status.HTTP_200_OK
)
def update_application_email(
    app_id: str,
    request: EmailUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        application = db.query(Application).filter(
            Application.id == app_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found."
            )

        new_email = normalize_email(request.email)

        if "@" not in new_email:
            raise HTTPException(
                status_code=422,
                detail="Invalid email address."
            )

        application.email = new_email

        db.commit()
        db.refresh(application)

        return {
            "message": "Email updated successfully.",
            "application_id": application.id,
            "email": application.email
        }

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "This email is already used for an active "
                "application to this position."
            )
        )

    except Exception:
        db.rollback()

        logging.exception(
            "Error updating application email."
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error during email update."
        )

# ==========================================
# API: BOOK INTERVIEW (Cal.com)
# ==========================================

@app.post(
    "/api/interviews",
    status_code=status.HTTP_201_CREATED
)
def create_interview(
    request: InterviewRequest,
    db: Session = Depends(get_db)
):
    """
    Creates an interview booking on Cal.com.

    Принимает подготовленные данные из фронтенда,
    создаёт бронь в Cal.com, возвращает uid брони.
    """

    # 1. Server configuration
    if not CALCOM_API_KEY or not CALCOM_EVENT_TYPE:
        raise HTTPException(
            status_code=503,
            detail="Calendar integration is not configured on the server."
        )

    # 2. Validate the application exists
    application = db.query(Application).filter(
        Application.id == request.application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )

    # 3. Вычисляем длительность
    try:
        start_dt = parse_calcom_datetime(request.booking_start)
        end_dt = parse_calcom_datetime(request.booking_end)
    except Exception as e:
        logging.error(f"Error parsing dates: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Нарезаем на куски по 30 минут
    chunks = []
    current = start_dt
    while current < end_dt:
        next_chunk = current + timedelta(minutes=30)
        if next_chunk > end_dt:
            next_chunk = end_dt
        chunks.append((current, next_chunk))
        current = next_chunk

    # 4. Отправляем каждый кусок в Cal.com
    created_uids = []
    calcom_headers = {
        "Authorization":   f"Bearer {CALCOM_API_KEY}",
        "Content-Type":    "application/json",
        "cal-api-version": "2024-08-13",
    }

    for chunk_start, chunk_end in chunks:
        # Округляем до минут, чтобы Cal.com не ругался
        start_str = chunk_start.strftime("%Y-%m-%dT%H:%M:00.000Z")
        
        calcom_body = {
            "start": start_str,
            "eventTypeId": CALCOM_EVENT_TYPE,
            "attendee": {
                "name":     request.full_name or application.full_name,
                "email":    request.email     or application.email,
                "timeZone": request.timezone,
                "language": request.language,
            },
            "metadata": {
                "application_id": str(application.id),
                "support_email":  request.support_email or "",
            },
        }

        try:
            response = requests.post(
                "https://api.cal.com/v2/bookings",
                json=calcom_body,
                headers=calcom_headers,
                timeout=15,
            )
        except requests.RequestException as e:
            # Если сеть упала, отменяем то, что уже успели создать
            for uid in created_uids:
                cancel_calcom_booking(uid)
            raise HTTPException(status_code=502, detail=f"Calendar service unavailable: {e}")

        if response.status_code not in (200, 201):
            # Если Cal.com отклонил один кусок — отменяем предыдущие (откат)
            for uid in created_uids:
                cancel_calcom_booking(uid)
            
            detail = response.json().get("message", response.text[:200])
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Cal.com rejected: {detail}"
            )

        # 5. Сохраняем успешный кусок в БД
        data = response.json().get("data", {})
        booking_uid = data.get("uid")
        created_uids.append(booking_uid)

        interview = Interview(
            application_id = application.id,
            calcom_uid     = booking_uid,
            booking_start  = chunk_start,
            booking_end    = chunk_end,
            attendee_email = request.email     or application.email,
            attendee_name  = request.full_name or application.full_name,
            attendee_tz    = request.timezone,
            support_email  = request.support_email or "",
            status         = "confirmed",
        )
        db.add(interview)
    
    db.commit()

    # 6. Очищаем старые, если превысили лимит
    prune_old_interviews(db, keep_last=20)

    logging.info(f"Booked {len(chunks)} chunks for application {application.id}")

    return {
        "message":        "Interview booked.",
        "application_id": application.id,
        "booking_uid":    created_uids[0] if created_uids else "",
        "booking_start":  request.booking_start,
        "booking_end":    request.booking_end,
    }

@app.get(
    "/api/interviews/booked-slots",
    response_model=List[BookedSlotResponse]
)
def get_booked_slots(
    db: Session = Depends(get_db)
):
    """
    Возвращает все подтверждённые брони в форме, которую ждёт FullCalendar.
    """
    try:
        interviews = (
            db.query(Interview)
              .filter(Interview.status == "confirmed")
              .order_by(Interview.booking_start)
              .all()
        )
    except SQLAlchemyError:
        logging.exception("Error fetching booked slots.")
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable."
        )

    return [
        {
            "start":          i.booking_start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "end":            i.booking_end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "booking_uid":    i.calcom_uid,
            "application_id": i.application_id,
        }
        for i in interviews
    ]


@app.post("/api/interviews/{booking_uid}/cancel")
def cancel_interview(
    booking_uid: str,
    db: Session = Depends(get_db)
):
    # 1. Find the booking in our database
    interview = db.query(Interview).filter(
        Interview.calcom_uid == booking_uid
    ).first()

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Booking not found."
        )

    # 2. Check that the booking is still active
    if interview.status != "confirmed":
        raise HTTPException(
            status_code=409,
            detail="Booking is not active."
        )

    # 3. Cancel the booking in Cal.com
    success = cancel_calcom_booking(booking_uid)

    if not success:
        raise HTTPException(
            status_code=502,
            detail="Could not cancel booking in Cal.com."
        )

    # 4. Update our local database
    try:
        interview.status = "cancelled"
        interview.cancelled_at = datetime.utcnow()
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        logging.exception("Error updating cancelled interview.")
        raise HTTPException(
            status_code=500,
            detail="Booking was cancelled in Cal.com, but database update failed."
        )

    return {
        "message": "Booking cancelled successfully.",
        "booking_uid": booking_uid,
        "status": "cancelled"
    }


# для отладки полный список

@app.get(
    "/api/interviews",
    response_model=List[InterviewResponse]
)
def get_interviews(
    status_filter: str = "confirmed",
    db: Session = Depends(get_db)
):
    query = db.query(Interview)
    if status_filter:
        query = query.filter(Interview.status == status_filter)
    return query.order_by(Interview.booking_start).all()    

# ==========================================
# API: CREATE DEMO DATA IF DATABASE IS EMPTY
# ==========================================

@app.post(
    "/api/initialize-demo",
    status_code=status.HTTP_200_OK
)
def initialize_demo_data(
    db: Session = Depends(get_db)
):
    try:
        # Do not overwrite existing data
        if db.query(Position).first():
            return {
                "message": "Database already contains positions. No changes made."
            }

        demo_positions = [
            "Senior Backend Developer",
            "Frontend Engineer",
            "HR Manager"
        ]

        positions_by_name = {}

        # Create demo positions
        for position_name in demo_positions:
            position = Position(
                id=str(uuid.uuid4()),
                pos_name=position_name,
                is_free=True
            )
            db.add(position)
            positions_by_name[position_name] = position

        db.flush()

        # Create demo applications using the existing collection
        applications_created = 0

        for language in APPLICATION_DEMO_COLLECTION:
            for app_data in APPLICATION_DEMO_COLLECTION[language]:
                app_data = app_data.copy()
                app_data.pop("lang", None)

                position_name = app_data.pop("position_id")
                position = positions_by_name.get(position_name)

                if not position:
                    raise ValueError(
                        f"Unknown demo position: {position_name}"
                    )

                db.add(
                    Application(
                        id=str(uuid.uuid4()),
                        app_date=datetime.utcnow(),
                        position_id=position.id,
                        **app_data
                    )
                )

                applications_created += 1

        # Match the existing demo setup
        positions_by_name["Frontend Engineer"].is_free = False

        db.commit()

        logging.info("Demo data initialized.")

        return {
            "message": "Demo data created successfully.",
            "positions_created": len(demo_positions),
            "applications_created": applications_created
        }

    except Exception:
        db.rollback()
        logging.exception("Error initializing demo data.")

        raise HTTPException(
            status_code=500,
            detail="Unable to initialize demo data."
        )

# ==========================================
# API: RESET DEMO DATA
# ==========================================

def generate_demo_interviews(db: Session, applications: list, tz_offset: float = 0.0):
    logging.info(f"DEBUG: Генерация демо. Получен tz_offset = {tz_offset}")
    
    if not CALCOM_API_KEY or not CALCOM_EVENT_TYPE:
        logging.warning("Cal.com not configured, skipping demo interviews.")
        return 0

    # Безопасный выбор кандидата (чтобы не выйти за пределы списка, если кандидатов мало)
    def get_app(idx):
        return applications[idx % len(applications)]

    # ЖЕСТКИЙ ГРАФИК: (день от сегодня, час, минута, длительность, индекс_кандидата)
    demo_schedule = [
        # --- Кандидат 1 (Индекс 0): 3 встречи, всего 2.5 часа ---
        (0, 10, 0, 30, 0),   # День 1: 10:00 - 10:30
        (2, 14, 0, 60, 0),   # День 3: 14:00 - 15:00
        (4, 11, 0, 60, 0),   # День 5: 11:00 - 12:00

        # --- Кандидат 2 (Индекс 1): 2 встречи, всего 2 часа (0.5 + 1.5) ---
        (0, 10, 30, 30, 1),  # День 1: 10:30 - 11:00 (Встык к Кандидату 1!)
        (6, 14, 30, 90, 1),  # День 7: 14:30 - 16:00 (1.5 часа)

        # --- Остальные кандидаты: по 1 встрече (максимум 1 час) ---
        (2, 9, 0, 60, 2),    # Кандидат 3, День 3: 09:00 - 10:00 (1 час)
        (4, 15, 0, 30, 3),   # Кандидат 4, День 5: 15:00 - 15:30 (30 мин)
        (6, 9, 0, 60, 4),    # Кандидат 5, День 7: 09:00 - 10:00 (1 час)
        (8, 12, 0, 30, 5),   # Кандидат 6, День 9: 12:00 - 12:30 (30 мин)
    ]

    bookings_created = 0
    
    def send_booking(attendee, start_dt, end_dt):
        safe_email = attendee.email.replace("example.com", "gmail.com")
        calcom_body = {
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:00.000Z"),
            "eventTypeId": CALCOM_EVENT_TYPE,
            "attendee": {
                "name": attendee.full_name,
                "email": safe_email,
                "timeZone": "UTC",
                "language": "en",
            },
        }
        try:
            r = requests.post(
                "https://api.cal.com/v2/bookings",
                json=calcom_body,
                headers={
                    "Authorization": f"Bearer {CALCOM_API_KEY}",
                    "Content-Type": "application/json",
                    "cal-api-version": "2024-08-13",
                },
                timeout=5
            )
            if r.status_code in (200, 201):
                data = r.json().get("data", {})
                db.add(Interview(
                    application_id=attendee.id,
                    calcom_uid=data.get("uid"),
                    booking_start=start_dt,
                    booking_end=end_dt,
                    attendee_email=safe_email,
                    attendee_name=attendee.full_name,
                    attendee_tz="UTC",
                    status="confirmed"
                ))
                return True
            else:
                logging.error(f"Demo rejected: {r.text}")
                return False
        except Exception as e:
            logging.error(f"Demo booking failed: {e}")
            return False

    base_date = datetime.utcnow().date()
    if datetime.utcnow().hour >= 15:
        base_date += timedelta(days=1)

    # Проходим по нашему жесткому графику
    for day_offset, local_hour, local_minute, duration, app_index in demo_schedule:
        # Пропускаем выходные
        target_date = base_date + timedelta(days=day_offset)
        while target_date.weekday() >= 5:
            target_date += timedelta(days=1)

        # Переводим локальное время в UTC
        utc_hour = local_hour - int(tz_offset)
        start_dt = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=utc_hour, minutes=local_minute)
        end_dt = start_dt + timedelta(minutes=duration)

        # Получаем нужного кандидата по индексу
        attendee = get_app(app_index)
        
        current_chunk_start = start_dt
        is_success = True
        
        # Нарезаем длинные встречи на куски по 30 минут для Cal.com
        while current_chunk_start < end_dt:
            next_chunk_end = current_chunk_start + timedelta(minutes=30)
            if next_chunk_end > end_dt:
                next_chunk_end = end_dt
                
            if not send_booking(attendee, current_chunk_start, next_chunk_end):
                is_success = False
                break
                
            current_chunk_start = next_chunk_end
            
        if is_success:
            bookings_created += 1

    db.commit()
    return bookings_created

@app.post(
    "/api/reset-demo",
    status_code=status.HTTP_200_OK
)
def reset_demo_data(
    db: Session = Depends(get_db),
    tz_offset: float = 0.0   
):

    """
    0.
    Clears all interviews.
    Очищает бронирование собеседований.
    1. 
    Clears all applications.          
    Удаляет все отклики.
    2. 
    Ensures 3 demo positions exist.   
    Создаёт 3 demo должности.
    3. 
    Resets position availability.     
    Сбрасывает статусы занятости должностей.
    4. 
    Seeds 3 demo applications.        
    Загружает 3 demo отклика
    5.
    Ensures 6 demo booking slots.
    Создаёт 6 demo бронирований.
    """

    try:

        # 0a. Cancel all confirmed bookings in Cal.com BEFORE deleting locally
        confirmed_interviews = db.query(Interview).filter(
            Interview.status == "confirmed"
        ).all()

        cancelled_ok = 0
        cancelled_fail = 0

        for interview in confirmed_interviews:
            if cancel_calcom_booking(interview.calcom_uid):
                cancelled_ok += 1
            else:
                cancelled_fail += 1

        if cancelled_fail:
            logging.warning(
                f"Reset demo: {cancelled_fail} Cal.com bookings "
                f"could not be cancelled (they may still exist)."
            )

        # 0b. Delete interviews locally
        db.query(Interview).delete(synchronize_session=False)

        # 1. Delete existing applications
        db.query(Application).delete(synchronize_session=False)

        # 2. Delete all existing positions
        db.query(Position).delete(synchronize_session=False)

        # ----------------------------------
        # 3. Create 3 demo positions
        # ----------------------------------

        demo_positions = [
            "Senior Backend Developer",
            "Frontend Engineer",
            "HR Manager"
        ]

        for position_name in demo_positions:

            new_position = Position(
                id=str(uuid.uuid4()),
                pos_name=position_name,
                is_free=True
            )

            db.add(new_position)

        db.flush()

        # Retrieve the three demo positions
        positions = []

        for position_name in demo_positions:

            position = db.query(Position).filter(
                Position.pos_name == position_name
            ).first()

            positions.append(position)
        
        # ----------------------------------
        # 5. Insert demo applications
        # ----------------------------------

        for language in APPLICATION_DEMO_COLLECTION:

            for app_data in APPLICATION_DEMO_COLLECTION[language]:

                app_data = app_data.copy()

                # Remove demo-only metadata
                app_data.pop("lang", None)

                # position_id in demo data contains the position name.
                position_name = app_data.pop("position_id")

                # Find the real database position by name
                position = db.query(Position).filter(
                    Position.pos_name == position_name
                ).first()

                if not position:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Position not found: {position_name}"
                    )

                # Use the real UUID from the database
                new_app = Application(
                    id=str(uuid.uuid4()),
                    app_date=datetime.utcnow(),
                    position_id=position.id,
                    **app_data
                )

                db.add(new_app)

        # ----------------------------------
        # 6. Update hired position
        # ----------------------------------

        positions[1].is_free = False

        db.commit()

        # ----------------------------------
        # 7. Создаем демо-брони на 2 недели
        # ----------------------------------
        new_apps = db.query(Application).filter(Application.status == "New").all()
        
        created_interviews = 0
        if new_apps:
            # ПЕРЕДАЕМ tz_offset В ФУНКЦИЮ
            created_interviews = generate_demo_interviews(db, new_apps, tz_offset)
            logging.info(f"Created {created_interviews} demo interviews.")

        logging.info("Demo data successfully reset.")

        return {
            "message": "Success",
            "positions_created": len(demo_positions),
            "applications_created": sum(
                len(applications)
                for applications in APPLICATION_DEMO_COLLECTION.values()
            ),
            "interviews_created": created_interviews  # <-- Добавили в ответ
        }

    except Exception as e:
        db.rollback()

        logging.exception(
            f"Error resetting demo data: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error during demo reset."
        )

@app.get("/api/demo-application")
def get_demo_application(lang: str = "en"):

    if lang not in APPLICATION_DEMO_COLLECTION:
        raise HTTPException(
            status_code=400,
            detail="Language must be 'en' or 'ru'."
        )

    return APPLICATION_DEMO_COLLECTION[lang][0]

# ==========================================
# API: GET POSITIONS
# ==========================================

@app.get(
    "/api/positions",
    response_model=List[PositionResponse]
)
def get_positions(
    db: Session = Depends(get_db)
):
    try:
        return db.query(Position).all()

    except SQLAlchemyError:
        logging.exception(
            "Database error while retrieving positions"
        )

        raise HTTPException(
            status_code=503,
            detail="The database is temporarily unavailable. Please try again later."
        )


@app.post(
    "/api/positions",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_position(
    position_data: PositionCreate,
    db: Session = Depends(get_db)
):
    new_position = Position(
        pos_name=position_data.pos_name,
        is_free=position_data.is_free
    )

    db.add(new_position)
    db.commit()
    db.refresh(new_position)

    return new_position

@app.get(
    "/api/applications",
    response_model=List[ApplicationResponse]
)
def get_applications(
    position: str = None,
    full_name: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Application,
        Position.pos_name.label("position_name")
    ).join(
        Position,
        Application.position_id == Position.id
    )

    if position:
        query = query.filter(
            Position.pos_name.ilike(f"%{position}%")
        )

    if full_name:
        query = query.filter(
            Application.full_name.ilike(f"%{full_name}%")
        )

    results = query.all()

    return [
        ApplicationResponse(
            id=application.id,
            position_id=application.position_id,
            position_name=position_name,
            app_date=application.app_date,
            educ=application.educ,
            experience=application.experience,
            full_name=application.full_name,
            email=application.email,
            birth_date=application.birth_date,
            status=application.status
        )
        for application, position_name in results
    ]