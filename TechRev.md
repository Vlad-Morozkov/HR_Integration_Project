# PROJECT CONTEXT: HR Hiring System

## 1. Tech Stack
- Language: Python 3.x
- Backend: FastAPI + SQLAlchemy + Uvicorn
- Frontend: Streamlit
- Database: SQLite (local) / PostgreSQL (production)
- Environment: Variables loaded via python-dotenv

## 2. Database Schema
- **Positions Table:** 
    `id`        (UUID, PK), 
    `pos_name`  (String), 
    `is_free`   (Boolean, default True).

- **Applications Table:** 
    `id`            (UUID, PK), 
    `position_id`   (UUID, FK to Positions), 
    `app_date`      (DateTime), 
    `educ`          (String), 
    `experience`    (String), 
    `full_name`     (String), 
    `email`         (String), 
    `birth_date`    (Date), 
    `status`        (String: "New", "Hired", "Canceled").

## 3. Core Business Rules
- **Duplicate Check:** 
    Cannot apply if Email + Position_ID exists with status "New" or "Hired". If "Canceled", allow re-application.
- **Hiring Logic:** 
    When status changes to "Hired", the linked Position's `is_free` must become False.
- **Demo Data:** 
    Reset endpoint clears Applications, ensures 3 Positions exist, and seeds 3 dummy Applications.

## 4. Current Project State
- [x] Environment setup (venv, FastAPI, Streamlit installed).
- [x] Database models defined.
- [ ] Backend endpoints fully tested.
- [ ] Frontend UI connected to Backend.