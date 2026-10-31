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

    # 3. Build Cal.com payload
    #    Cal.com calculates "end" from the event type duration,
    #    so only "start" is sent here.
    
    # Вычисляем длительность в минутах (защищено от падения)
    try:
        start_dt = parse_calcom_datetime(request.booking_start)
        end_dt = parse_calcom_datetime(request.booking_end)
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
    except Exception as e:
        logging.error(f"Error parsing dates for duration: {e}")
        duration_minutes = 30  # Дефолт (30 минут), если дата пришла кривой

    calcom_body = {
        "start":       request.booking_start,
        "lengthInMinutes": duration_minutes,
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

    calcom_headers = {
        "Authorization":   f"Bearer {CALCOM_API_KEY}",
        "Content-Type":    "application/json",
        "cal-api-version": "2024-08-13",
    }

    # 4. Call Cal.com
    try:
        response = requests.post(
            "https://api.cal.com/v2/bookings",
            json=calcom_body,
            headers=calcom_headers,
            timeout=15,
        )
    except requests.RequestException as e:
        logging.exception("Cal.com request failed.")
        raise HTTPException(
            status_code=502,
            detail=f"Calendar service unavailable: {e}"
        )

    # 5. Translate Cal.com errors into clean HTTP responses
    if response.status_code not in (200, 201):
        detail = ""
        try:
            payload = response.json()
            detail = payload.get("message") or payload.get("error") or ""
        except Exception:
            detail = response.text[:300]

        # Preserve 4xx if Cal.com said "slot taken", "invalid", etc.
        http_status = (
            response.status_code
            if 400 <= response.status_code < 500
            else 502
        )

        logging.warning(
            f"Cal.com rejected booking for application {application.id}: "
            f"{response.status_code} {detail}"
        )

        raise HTTPException(
            status_code=http_status,
            detail=f"Cal.com rejected the booking: {detail or 'unknown error'}"
        )

    # 6. Persist to DB
    try:
        data = response.json().get("data", {})
    except Exception:
        data = {}

    booking_uid  = data.get("uid", "")
    actual_start = data.get("start", request.booking_start)
    actual_end   = data.get("end",   request.booking_end)

    if not booking_uid:
        raise HTTPException(
            status_code=502,
            detail="Cal.com did not return a booking uid."
        )

    try:
        interview = Interview(
            application_id = application.id,
            calcom_uid     = booking_uid,
            booking_start  = parse_calcom_datetime(actual_start),
            booking_end    = parse_calcom_datetime(actual_end),
            attendee_email = request.email     or application.email,
            attendee_name  = request.full_name or application.full_name,
            attendee_tz    = request.timezone,
            support_email  = request.support_email or "",
            status         = "confirmed",
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
    except IntegrityError:
        db.rollback()
        # calcom_uid уже есть в БД (например, дубль по вебхуку)
        raise HTTPException(
            status_code=409,
            detail="This booking already exists in our system."
        )
    except Exception as e:
        db.rollback()
        logging.exception("Failed to persist interview.")
        # Внимание: бронь в Cal.com уже создана, но локально не сохранена.
        # Для pet-проекта оставляем как 500, в продакшене нужна компенсация.
        raise HTTPException(
            status_code=500,
            detail=f"Booking created in Cal.com but not saved locally: {e}"
        )

    logging.info(
        f"Interview booked: application={application.id}, "
        f"cal.com_uid={booking_uid}, "
        f"start={actual_start}, end={actual_end}"
    )

    prune_old_interviews(db, keep_last=20)

    return {
        "message":        "Interview booked.",
        "application_id": application.id,
        "booking_uid":    booking_uid,
        "booking_start":  actual_start,
        "booking_end":    actual_end,
        "interview_id":   interview.id,
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

def generate_demo_interviews(db: Session, applications: list):
    """
    Создает демо-брони в Cal.com и сохраняет их в БД.
    Бронирует раз в 2 рабочих дня, начиная с сегодня, на 2 недели вперед.
    """
    if not CALCOM_API_KEY or not CALCOM_EVENT_TYPE:
        logging.warning("Cal.com not configured, skipping demo interviews.")
        return 0

    # Ищем пользователя, чтобы проверить рабочие часы (упрощенно берем с 9 до 16 UTC)
    start_date = datetime.utcnow().date()
    end_date = start_date + timedelta(days=14)
    
    created_count = 0
    current_date = start_date
    durations = [30, 60, 90] # 30 мин, 1 час, 1.5 часа

    while current_date <= end_date:
        # 5 - это суббота, 6 - воскресенье
        if current_date.weekday() < 5: 
            
            # Выбираем случайное время с 09:00 до 16:00 UTC
            random_hour = random.randint(9, 16)
            random_minute = random.choice([0, 30])
            
            # Если это сегодня, убеждаемся, что время еще не прошло
            start_dt = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=random_hour, minutes=random_minute)
            
            if start_dt > datetime.utcnow() + timedelta(hours=1): # хотя бы за час до брони
                duration = random.choice(durations)
                end_dt = start_dt + timedelta(minutes=duration)
                
                # Берем случайного кандидата из демо-заявок
                attendee = random.choice(applications)
                
                calcom_body = {
                    "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "lengthInMinutes": duration,
                    "eventTypeId": CALCOM_EVENT_TYPE,
                    "attendee": {
                        "name": attendee.full_name,
                        "email": attendee.email,
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
                            attendee_email=attendee.email,
                            attendee_name=attendee.full_name,
                            attendee_tz="UTC",
                            status="confirmed"
                        ))
                        created_count += 1
                except Exception as e:
                    logging.error(f"Demo booking failed: {e}")

            # Пропускаем один рабочий день (как просили - раз в два дня)
            current_date += timedelta(days=2)
        else:
            # Если попали на выходной, сдвигаемся на понедельник
            current_date += timedelta(days=1)

    db.commit()
    return created_count

@app.post(
    "/api/reset-demo",
    status_code=status.HTTP_200_OK
)
def reset_demo_data(
    db: Session = Depends(get_db)
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
            created_interviews = generate_demo_interviews(db, new_apps)
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