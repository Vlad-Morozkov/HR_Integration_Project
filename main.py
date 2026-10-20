
import os
import uuid
import logging

from datetime import date, datetime
from uuid import UUID
from typing import List

import requests

# added gmail
import smtplib
from email.message import EmailMessage
#

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Form
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

from models import Base, Position, Application


from pydantic import BaseModel, field_validator
from datetime import date
from uuid import UUID


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
                    "email":        "alice@example.com",
                    "birth_date":   date(1990, 5, 15),
                    "status":       "New"
                },
                {
                    "lang":         "en",
                    "position_id":  "Frontend Engineer",
                    "educ":         "MBA",
                    "experience":   "3 years",
                    "full_name":    "Bob Jones",
                    "email":        "bob@example.com",
                    "birth_date":   date(1988, 8, 22),
                    "status":       "Hired"
                },
                {
                    "lang":         "en",
                    "position_id":  "HR Manager",
                    "educ":         "BA Psychology",
                    "experience":   "2 years",
                    "full_name":    "Charlie Brown",
                    "email":        "charlie@example.com",
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
                    "email":       "SPI94@example.com",
                    "birth_date":  date(1994, 6, 2),
                    "status":      "New"
                },
                {
                    "lang":        "ru",
                    "position_id": "Frontend Engineer",
                    "educ":        "Высшее. Магистр",
                    "experience":  "5 лет",
                    "full_name":   "Иванова Анна Сергеевна",
                    "email":       "IAA92@example.com",
                    "birth_date":  date(1992, 2, 29),
                    "status":      "Hired"
                },
                {
                    "lang":        "ru",
                    "position_id": "HR Manager",
                    "educ":        "Высшее. Кандидат технических наук",
                    "experience":  "7 лет",
                    "full_name":   "Петров Алексей Дмитриевич",
                    "email":       "PAD90@example.com",
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
    )
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
# API: RESET DEMO DATA
# ==========================================

@app.post(
    "/api/reset-demo",
    status_code=status.HTTP_200_OK
)
def reset_demo_data(
    db: Session = Depends(get_db)
):

    """
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

        # ----------------------------------
        # 1. Delete existing applications
        # ----------------------------------

        db.query(Application).delete(
            synchronize_session=False
        )

        # ----------------------------------
        # 2. Delete all existing positions
        # ----------------------------------

        db.query(Position).delete(
            synchronize_session=False
        )

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

        logging.info("Demo data successfully reset.")

        return {
            "message": "Success",
            "positions_created": len(demo_positions),
            "applications_created": sum(
                len(applications)
                for applications in APPLICATION_DEMO_COLLECTION.values()
            )
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

    return db.query(Position).all()

# added
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
#

# added 
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
#
