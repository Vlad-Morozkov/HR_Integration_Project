# PROJECT CONTEXT: HR Hiring System

## 1. Tech Stack
- Language: Python 3.x
- Backend: FastAPI + SQLAlchemy + Uvicorn
- Frontend: Streamlit
- Database: SQLite (local) / PostgreSQL (production)
- Environment: Variables loaded via python-dotenv
- Email: Gmail SMTP using `smtplib`, `EmailMessage`, and SMTP_SSL (`smtp.gmail.com:465`)
- Email credentials: `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`
- API URL: `http://127.0.0.1:8000`
- API title: `HR Hiring System API`
- API version: `1.1.0`

## 2. Database Schema
- Positions Table:
    `id`           (UUID, PK),
    `pos_name`     (String),
    `is_free`      (Boolean, default True).

- Applications Table:
    `id`           (UUID, PK),
    `position_id`  (UUID, FK to Positions),
    `app_date`     (DateTime, stored in UTC),
    `educ`         (String),
    `experience`   (String),
    `full_name`    (String),
    `email`        (String, normalized by trimming whitespace and converting to lowercase),
    `birth_date`   (Date),
    `status`       (String: "New", "Hired", "Canceled").

- Application API Response:
    Includes `position_name` (String), obtained from the related Positions record, in addition to the application fields.

## 3. Core Business Rules
- Duplicate Check:
    Cannot apply if the same normalized Email + Position_ID exists with status "New" or "Hired".
    If the previous application has status "Canceled", re-application is allowed. The previous record is retained for history, and the new application receives a new UUID.

- Application Validation:
    All application fields are required.
    Text fields `educ`, `experience`, `full_name`, and `email` cannot be empty or contain only whitespace.
    Email validation checks for the presence of "@".
    The birth date must be earlier than the current date.
    The frontend sends application data as a JSON body to `POST /api/applications`.

- Hiring Logic:
    Only applications with status "New" can be processed.
    When status changes to "Hired", the linked Position's `is_free` becomes False.
    The backend attempts to send a hiring notification to the candidate and a workplace-preparation notification to Support Email.
    Email delivery may fail even if the application status has already been updated in the database.

- Rejection Logic:
    When status changes to "Canceled", the application record is retained in the database.
    The backend attempts to send a rejection notification to the candidate.
    The candidate can reapply for the same position.
    Applications with status "Hired" or "Canceled" cannot be processed again through the Hire/Reject actions.

- Email Update Logic:
    HR can edit an application's email through the frontend.
    The backend normalizes the email and validates that it contains "@".
    Email updates can return HTTP 404 if the application is not found, HTTP 422 if the email is invalid, or HTTP 409 if a conflict occurs.

- Positions Management:
    HR can create a position through `POST /api/positions`.
    The position name cannot be empty.
    New positions are created with `is_free = True` by default.

- Application Filtering:
    HR can filter applications by position name and candidate full name through `GET /api/applications`.
    Email filtering is performed on the frontend.
    Position and full-name filters support partial matches.

- Demo Data:
    The system provides three demo positions:
        "Senior Backend Developer"
        "Frontend Engineer"
        "HR Manager"

    The demo collection contains six applications:
        Three English examples.
        Three Russian examples.

    Each language collection contains applications with statuses "New", "Hired", and "Canceled".

    The `POST /api/reset-demo` endpoint deletes existing Applications and Positions, recreates the three demo positions, and seeds six demo applications.
    The Frontend Engineer position is set to `is_free = False` because a demo application for this position has status "Hired".
    Existing records are deleted when demo data is reset.

    The `GET /api/demo-application?lang=en|ru` endpoint returns a demo application for the selected language.
    Supported language values are "en" and "ru".

- Frontend UI:
    Candidate and HR forms are displayed in the same browser tab.
    The user can switch between Candidate and HR modes.
    English and Russian interface text is stored in the `TEXTS` dictionary and selected manually.
    The Candidate form displays only available positions.
    The HR interface provides application filtering, email editing, application selection, Hire/Reject actions, position management, and demo data reset.
    Hire and Reject actions are available only when exactly one application with status "New" is selected and the relevant validation conditions are met.
    Position availability is displayed using a green check mark when the position is available.