import streamlit as st
import requests
import re
import pandas as pd

from timezone_component import detect_timezone

# added streamlit_calendar
from streamlit_calendar import calendar

from datetime import date, datetime, timedelta


import html
import json
import streamlit.components.v1 as components

from validators import (
    normalize_email,
    is_valid_email,
    is_valid_birth_date,
    has_email_duplicate,
)

# 1. САМАЯ ПЕРВАЯ КОМАНДА STREAMLIT
st.set_page_config(
    page_title="HR Hiring System",
    layout="wide"
)

# Detect user's browser timezone
timezone_data = detect_timezone()

if timezone_data:
    st.session_state["user_tz_name"] = timezone_data["timezone"]
    st.session_state["user_tz_offset"] = timezone_data["offset"] / 60.0
else:
    st.session_state.setdefault("user_tz_name", "UTC")
    st.session_state.setdefault("user_tz_offset", 0.0)

# =========================================================
# AUTOMATIC TIMEZONE DETECTION
# =========================================================

timezone_data = components.html(
    """
    <script>
        const timezone =
            Intl.DateTimeFormat().resolvedOptions().timeZone;

        const offset =
            new Date().getTimezoneOffset();

        const data = {
            timezone: timezone,
            offset: -offset
        };

        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: JSON.stringify(data)
        }, "*");
    </script>
    """,
    height=0
)

# =========================================================
# AUTOMATIC LANGUAGE DETECTION
# =========================================================

accept_lang = st.context.headers.get(
    "Accept-Language", "en"
)

browser_lang = "en"

for item in accept_lang.split(","):

    code = item.split(";")[0].strip()
    code = code.split("-")[0].lower()

    if code in ("en", "ru"):
        browser_lang = code
        break

default_index = 1 if browser_lang == "ru" else 0


def show_duplicate_email_notice(
    message_template,
    email,
    cancel_hint,
    copied_message,
    copy_hint
):
    before, after = message_template.split("{email}", 1)

    safe_email = html.escape(str(email))
    safe_before = html.escape(before)
    safe_after = html.escape(after)
    safe_copy_hint = html.escape(copy_hint)
    safe_copied = html.escape(copied_message)

    js_email = json.dumps(str(email))
    js_copied = json.dumps(copied_message)

    html_content = f"""
    <div style="
        background-color: #fff3cd;
        border: 1px solid #ffe69c;
        border-radius: 0.5rem;
        padding: 0.9rem 1rem;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 16px;
        color: #664d03;
        line-height: 1.5;
    ">
        <div style="margin-bottom: 0.4rem;">
            <span style="font-weight: 700;">⚠️</span>
            {safe_before}<span
                id="email-link"
                title="{safe_copy_hint}"
                style="
                    color: #0d6efd;
                    text-decoration: underline;
                    cursor: pointer;
                    font-weight: 600;
                "
            >{safe_email}</span>{safe_after}<span
                id="copy-feedback"
                style="
                    display: none;
                    margin-left: 8px;
                    color: #198754;
                    font-weight: 600;
                    font-size: 14px;
                "
            ></span>
        </div>
        <div style="font-style: italic; opacity: 0.75; font-size: 14px;">{safe_copy_hint}</div>
    </div>
    <script>
        const emailValue = {js_email};
        const copiedText = {js_copied};

        function copyToClipboard(text) {{
            if (navigator.clipboard && window.isSecureContext) {{
                return navigator.clipboard.writeText(text);
            }} else {{
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.opacity = '0';
                document.body.appendChild(ta);
                ta.select();
                try {{ document.execCommand('copy'); }} catch (e) {{}}
                document.body.removeChild(ta);
                return Promise.resolve();
            }}
        }}

        document.getElementById('email-link').addEventListener('click', async function() {{
            try {{
                await copyToClipboard(emailValue);
            }} catch (e) {{}}

            const fb = document.getElementById('copy-feedback');
            fb.textContent = copiedText;
            fb.style.display = 'inline-block';
            setTimeout(function() {{ fb.style.display = 'none'; }}, 2000);
        }});
    </script>
    """

    components.html(html_content, height=110)

# Local
API_URL = "http://127.0.0.1:8000" 

# Prod
# API_URL = "https://hr-integration-project-swart.vercel.app"


# =========================================================
# КЭШИРУЕМЫЕ ЗАГРУЗКИ (Способ Б)
# =========================================================

@st.cache_data(ttl=15, show_spinner=False)
def load_all_applications(api_url: str) -> list:
    """Все заявки. Кэш живет 15 секунд."""
    response = requests.get(f"{api_url}/api/applications", timeout=10)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=30, show_spinner=False)
def load_positions(api_url: str) -> list:
    """Справочник должностей. Кэш живет 30 секунд."""
    response = requests.get(f"{api_url}/api/positions", timeout=10)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=15, show_spinner=False)
def load_booked_slots(api_url: str) -> list:
    """Занятые слоты собеседований. Кэш живет 15 секунд."""
    response = requests.get(f"{api_url}/api/interviews/booked-slots", timeout=10)
    response.raise_for_status()
    return response.json()

# =========================================================
# LANGUAGE
# =========================================================

LANGUAGES = ["English", "Русский"]

# Устанавливаем язык по умолчанию на основе браузера
default_index = 1 if browser_lang == "ru" else 0

# Если пользователь еще не трогал селектор, ставим дефолт
if "language_selector" not in st.session_state:
    st.session_state["language_selector"] = LANGUAGES[default_index]

max_language_length = max(
    len(language_name)
    for language_name in LANGUAGES
)

selector_width = max_language_length + 5

st.markdown(
    """
    <style>
    div[data-testid="stSelectbox"] {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

col_empty, col_language = st.columns(
    [100 - selector_width, selector_width]
)

with col_language:
    language = st.selectbox(
        "Language",
        LANGUAGES,
        label_visibility    ="collapsed",
        key                 ="language_selector"
    )

lang = "ru" if language == "Русский" else "en"


TEXTS = {
    "en": {
        "title":                 "HR Hiring System",
        "mode":                  "Select mode",
        "candidate":             "Candidate",
        "hr":                    "HR",

        #----------
        # Candidate Mode
        #----------

        "fill_test_data":        "Fill with test data",
        "clear_fields":          "Clear fields",
        "position":              "Position",
        "full_name":             "Full Name",
        "email":                 "Email",
        "education":             "Education",
        "experience":            "Experience",
        "birth_date":            "Birth Date",
        "submit_application":    "Submit Application",

        #----------
        # Booking review
        #----------

        "my_bookings": "My Bookings",
        "select_candidate_booking": "Select Candidate (with active bookings)",
        "no_active_bookings": "No candidates with active upcoming bookings found.",
        "date": "Date",
        "time": "Time",
        "select_booking":           "Select",
        "reschedule_booking":       "Reschedule",
        "cancel_booking":           "Cancel Booking",
        "booking_url_missing":      "URL not provided by backend",
        "cancel_booking_for_reason": "Cancel booking for candidate",
        "dismiss":                  "Dismiss",
        "has_booking_at":           "has a booking at",
        "cancellation_ask":         "Do you need to cancel it?",     
        "bookings_cancelled_successfully":  "All bookings cancelled successfully.",           
     
        #----------
        # Notiffications
        #----------

        "empty_db":              "The database is empty. Would you like to create demo data?",
        "success":               "Data submitted successfully.",
        "birth_date_error":      "Birth date cannot be today or in the future.",
        "empty_bdate_field":     "Fill birth date field.",
        "no_positions":          "No positions available.",
        "connection_error":      "Could not connect to the HR system.",
        "duplicate_application": "You have already applied for this position.",
        "invalid_email":         "Please enter a valid email address.",
        "invalid_email_for_candidate": "For {name} ({position}) {error_text}",        

        #----------
        # HR Mode
        #----------

        "refresh":               "Refresh",
        "filters":               "Filters",
        "clear_filters":         "Clear filters",
        "apply_filters":         "Apply",
        "applications":          "Applications",
        "support_email":         "Support Email",
        "positions":             "Positions",
        "available":             "Available",
        "new_position":          "New Position",
        "add_position":          "Add Position",

        #----------
        # Notiffications
        #----------

        "position_empty":        "Position name cannot be empty.",
        "position_added":        "Position added successfully.",
        "position_add_error":    "Could not add position.",
        
        # Buttons

        "reset_demo":            "Reset & Load Demo Data",
        "system_locked_message": 
                "The system is updating. Another user is currently loading data. Please wait 1-2 minutes.",
        #----------
        # Notiffications
        #----------

        "demo_loaded":           "Demo data loaded successfully.",
        "DemoData&BookingGeneration": 
                "Demo data is being loaded and booking via Cal.com is being set up. Please wait...",
        "demo_load_error":       "Could not load demo data.",
        "demo_load_error_check_connection":
               "Please check the connection and try again.",
        "no_applications":       "No applications found.",
        "select_one":            "Select one application.",
        "select_only_one":       "Please select only one application.",
        "candidate_already_hired":      "This candidate is already hired",
        "position_occupied_warning":    
                    "Position is already occupied. You can hire the candidate, but you need to check the number of slots.",
        "hire_anyway":  "Hire candidate anyway",
        "cancel":       "Cancel",     

        # Headers

        "email_help":            "Candidate email",

        #----------
        # Notiffications
        #----------

        "email_duplicate_active": 
            "This email {email} is already used for an active application to this position.",
        "click_email_to_copy":   "Click email to copy",
        "cancel_email_changes":  "Click Refresh to cancel email changes",
        "email_copied":          "Email copied!",
        "email_updated":         "Email updated successfully.",
        "email_update_error":    "Could not update email.",
        "same_email_hire_prompt": 
            "⚠️ A candidate with this email {email} is already hired for «{hired_position}». Do you want to hire them again for «{current_position}»?",
        "click_value_to_copy":   "Click value to copy",

        # Buttons

        "review":                "Review",
        "Interview":             "Interview",
        "hire":                  "Hire",
        "reject":                "Reject",

        # Calendar

        "collapse_calendar":    "Collapse calendar",
        "expand_calendar":      "Expand calendar",
        "calendar":         "Calendar",
        "calendar_booked":  "Booked",
        "today":            "today",
        "week":             "week",
        "day":              "day",
        "all_day":          "all-day",
        "locale_code":      "en",
        "booked":           "Booked",
        "cancel_booking":   "Cancel Booking",
        "booking_cancelled":    "Interview booking cancelled successfully.",
        "canceling_booking":    "Canceling booking. Please wait...",
        "selected_booking": "Selected booking",

        # Application's notiffications

        "select_slot_first":     "Please select a free time slot on the calendar.",
        "slot_already_booked":   "That slot is already booked.",
        "slot_unavailable":      "Selected unavailable time (set at Cal.com)",
        "interview_ready":       "Booked",
        "slot_in_past":          "You select a slot in the past.",
        "selected_slot":         "Selected slot",
        "application_hired":     "Application hired.",
        "application_rejected":  "Application rejected.",
        "hire_error":            "Could not hire application.",
        "reject_error":          "Could not reject application.",
        "request_failed":        "Request failed",

        # Headers

        "candidate_name":        "Full Name",
        "education":             "Education",
        "experience":            "Experience",
        "application_date":      "Application Date",
        "status":                "Status",
        "select":                "Select",

        "submit_error":          "Data not submitted. Please try again later. Error code: {code}.",
        "fill_field":            "Fill {field_name}",

        "status_new":            "New",
        "status_hired":          "Hired",
        "status_canceled":       "Canceled",
        "status_all":            "All",            
    },

    "ru": {
        "title":                 "Система найма сотрудников",
        "mode":                  "Выберите режим",
        "candidate":             "Кандидат",
        "hr":                    "HR",

        #----------
        # Candidate Mode
        #----------

        "fill_test_data":        "Заполнить Demo данными",
        "clear_fields":          "Очистить поля",
        "position":              "Должность",
        "full_name":             "ФИО",
        "email":                 "Email",
        "education":             "Образование",
        "experience":            "Опыт работы",
        "birth_date":            "Дата рождения",
        "submit_application":    "Отправить заявку",

        #----------
        # Booking review
        #----------

        "my_bookings":              "Мои собеседования",
        "select_candidate_booking": "Выберите кандидата (с активными записями)",
        "no_active_bookings":       "Не найдено кандидатов с активными предстоящими записями.",
        "date":                     "Дата",
        "time":                     "Время",
        "select_booking":           "Выбрать",
        "reschedule_booking":       "Изменить встречу",
        "cancel_booking":           "Отменить",
        "booking_url_missing":      "backend не предоставил URL",
        "cancel_booking_for_reason": "Отменить записи для кандидата",
        "dismiss":                  "Закрыть",
        "has_booking_at":           "имеет запись на",
        "cancellation_ask":         "Хотите отменить?",
        "bookings_cancelled_successfully":  "Все записи для кандидата отменены.",         

        #----------
        # Notiffications
        #----------


        "empty_db":              "База данных пуста. Хотите заполнить demo данными?",
        "success":               "Данные успешно отправлены.",
        "birth_date_error":      "Дата рождения не может быть сегодня или в будущем.",
        "empty_bdate_field":     "Заполните дату рождения.",
        "no_positions":          "Нет доступных вакансий.",
        "connection_error":      "Не удалось подключиться к системе найма.",
        "duplicate_application": "Вы уже подавали заявку на эту должность.",
        "invalid_email":         "Пожалуйста, введите корректный адрес электронной почты.",
        "invalid_email_for_candidate": "Для {name} ({position}) {error_text}",

        #----------
        # HR Mode
        #----------

        "refresh":               "Обновить",
        "filters":               "Фильтры",
        "clear_filters":         "Очистить фильтры",
        "apply_filters":         "Применить",
        "applications":          "Заявки",
        "support_email":         "Email службы поддержки",
        "positions":             "Должности",
        "available":             "Доступна",
        "new_position":          "Новая должность",
        "add_position":          "Добавить должность",

        #----------
        # Notiffications
        #----------

        "position_empty":        "Название должности не может быть пустым.",
        "position_added":        "Должность успешно добавлена.",
        "position_add_error":    "Не удалось добавить должность.",

        # Buttons

        "reset_demo":            "Сбросить и загрузить Demo-данные",
        "system_locked_message": 
            "Система обновляется. Другой пользователь выполняет загрузку данных. Пожалуйста, подождите 1-2 минуты.",


        #----------
        # Notiffications
        #----------

        "demo_loaded":           "Demo-данные успешно загружены.",
        "DemoData&BookingGeneration": 
                "Идёт генерация демо-данных и записей в Cal.com. Пожалуйста, подождите...",        
        "demo_load_error":       "Не удалось загрузить Demo-данные.",
        "demo_load_error_check_connection":
               "Пожалуйста проверьте соединение и повторите запрос снова.",
        "no_applications":       "Заявки не найдены.",
        "select_one":            "Выберите одну заявку.",
        "select_only_one":       "Пожалуйста, выберите только одну заявку.",
        "candidate_already_hired":"Этот кандидат уже принят на работу",
        "position_occupied_warning":    
                "Позиция уже занята. Кандидата можно принять, но нужно проверить количество ставок.",
        "hire_anyway":  "Принять кандидата всё равно",
        "cancel":       "Отмена",


        # Email buttons

        "email_help":            "Email кандидата",

        # Email notifs

        "email_duplicate_active":
            "Почта {email} уже используется в активной заявке на ту же должность.",
        "cancel_email_changes":  "Нажмите Обновить, чтобы отменить изменение email",
        "click_email_to_copy":   "Нажмите, чтобы скопировать",
        "email_copied":          "Email скопирован!",
        "email_updated":         "Email успешно обновлён.",
        "email_update_error":    "Не удалось обновить email.",
        "same_email_hire_prompt": 
            "⚠️ Кандидат с этим email {email} уже принят на должность «{hired_position}». Хотите ли принять его повторно на должность «{current_position}»?",
        "click_value_to_copy":   "Click value to copy",

        # Кнопки
        
        "review":                "Рассмотреть",
        "Interview":             "Собеседовать",
        "hire":                  "Принять на работу",
        "reject":                "Отклонить",



        # Calendar

        "collapse_calendar":    "Скрыть календарь",
        "expand_calendar":      "Показать календарь",
        "calendar":         "Календарь",
        "calendar_booked":  "Занято",
        "today":            "Сегодня",
        "week":             "Неделя",
        "day":              "День",
        "all_day":          "Весь день",
        "locale_code":      "ru",
        "booked":           "Забронировано",
        "cancel_booking":   "Отменить собеседование",
        "booking_cancelled":    "Собеседование успешно отменено.",
        "canceling_booking":    "Отмена собеседования. Подождите подалуйста.",        
        "selected_booking":     "Выбранная запись",
        # Сообщения 
        
        "interview_ready":       "Собеседование запланировано в календаре.",
        "slot_in_past":          "Вы выбрали прошедше время",
        "selected_slot":         "Выбрано время",        
        "select_slot_first":     "Выберите свободный слот в календаре",
        "slot_already_booked":   "Этот слот забронирован.",
        "slot_unavailable":      "Выбрано нерабочее время (настроено в Cal.com)",
        "application_hired":     "Кандидат принят на работу.",
        "application_rejected":  "Заявка отклонена.",
        "hire_error":            "Не удалось принять кандидата на работу.",
        "reject_error":          "Не удалось отклонить заявку.",
        "request_failed":        "Ошибка запроса",

        "candidate_name":        "ФИО",
        "education":             "Образование",
        "experience":            "Опыт работы",
        "application_date":      "Дата заявки",
        "status":                "Статус",
        "select":                "Выбрать",

        "submit_error":          "Не удалось отправить данные. Попробуйте позже. Код ошибки: {code}.",
        "fill_field":            "Заполните поле «{field_name}»",

        "status_new":            "Новая",
        "status_hired":          "Принят",
        "status_canceled":       "Отклонена",
        "status_all":            "Все",        
    }

}


t = TEXTS[lang]


# =========================================================
# TITLE
# =========================================================

st.title(t["title"])


# =========================================================
# MODE
# =========================================================

if "mode" not in st.session_state:
    st.session_state["mode"] = "Candidate"


mode_options = {
    "Candidate": t["candidate"],
    "HR": t["hr"]
}


selected_mode = st.radio(
    t["mode"],
    list(mode_options.values()),
    index=(
        0
        if st.session_state["mode"] == "Candidate"
        else 1
    ),
    horizontal=True
)


if selected_mode == t["candidate"]:
    st.session_state["mode"] = "Candidate"
else:
    st.session_state["mode"] = "HR"


mode = selected_mode


# =========================================================
# CANDIDATE FORM STATE (постоянное хранилище введённых данных)
# =========================================================

# Эти ключи НЕ привязаны к виджетам, поэтому Streamlit
# не удаляет их при смене языка или смены формы.
if "store_full_name" not in st.session_state:
    st.session_state["store_full_name"] = ""
if "store_email" not in st.session_state:
    st.session_state["store_email"] = ""
if "store_educ" not in st.session_state:
    st.session_state["store_educ"] = ""
if "store_experience" not in st.session_state:
    st.session_state["store_experience"] = ""
if "store_birth_date" not in st.session_state:
    st.session_state["store_birth_date"] = date.today()
if "bdate_touched" not in st.session_state:          # <-- new
    st.session_state["bdate_touched"] = False        # <-- new
if "store_position_id" not in st.session_state:
    st.session_state["store_position_id"] = None

# Счётчик версии формы: при увеличении все ключи виджетов
# меняются → Streamlit создаёт их заново и берёт значения
# из store_*. Это единственный надёжный способ визуально
# очистить/обновить поля.
if "candidate_form_version" not in st.session_state:
    st.session_state["candidate_form_version"] = 0


# =========================================================
# CANDIDATE MODE
# =========================================================

if mode == t["candidate"]:

    st.header(t["candidate"])

    form_version = st.session_state["candidate_form_version"]

    # -----------------------------------------------------
    # Fill demo data + Clear fields
    # -----------------------------------------------------

    col_fill, col_clear = st.columns(
        [0.2, 0.8],
        vertical_alignment="bottom"
    )

    with col_fill:
        fill_clicked = st.button(
            t["fill_test_data"],
            key="fill_demo_candidate"
        )

    with col_clear:
        clear_label = (t["clear_fields"])
        clear_clicked = st.button(
            clear_label,
            key="clear_candidate_fields"
        )

    if clear_clicked:

        # Очистка постоянного хранилища (должность НЕ трогаем)
        st.session_state["store_full_name"] = ""
        st.session_state["store_email"] = ""
        st.session_state["store_educ"] = ""
        st.session_state["store_experience"] = ""
        st.session_state["store_birth_date"] = date.today()
        st.session_state["bdate_touched"] = False            # <-- new

        # Новая версия формы — все виджеты создаются заново
        st.session_state["candidate_form_version"] += 1

        st.rerun()

    if fill_clicked:

        response = requests.get(
            f"{API_URL}/api/demo-application",
            params={"lang": lang},
            timeout=5
        )

        if response.status_code == 200:

            demo_data = response.json()

            st.session_state["store_full_name"] = demo_data["full_name"]
            st.session_state["store_email"] = demo_data["email"]
            st.session_state["store_educ"] = demo_data["educ"]
            st.session_state["store_experience"] = demo_data["experience"]
            st.session_state["store_birth_date"] = date.fromisoformat(
                demo_data["birth_date"]
            )

            st.session_state["bdate_touched"] = True              # <-- new

            # Новая версия формы — виджеты подхватят демо-данные
            st.session_state["candidate_form_version"] += 1

            st.rerun()

        else:

            st.error(
                f"Could not load test data. "
                f"Error code: {response.status_code}"
            )

    # -----------------------------------------------------
    # Load positions
    # -----------------------------------------------------

    try:
        positions = load_positions(API_URL)

        if not positions:

            st.warning(t["empty_db"])

            if st.button(t["fill_test_data"], key="initialize_demo"):

                try:
                    init_response = requests.post(
                        f"{API_URL}/api/initialize-demo",
                        timeout=15
                    )

                    init_response.raise_for_status()

                    st.success(t["demo_loaded"])

                    st.rerun()

                except requests.RequestException:
                    st.error(
                        t["demo_load_error"] + " "
                        + t["demo_load_error_check_connection"]
                    )

        else:

            # Берем только свободные позиции и сортируем по названию (pos_name)
            available_positions = sorted(
                [
                    position
                    for position in positions
                    if position["is_free"]
                ],
                key=lambda p: p["pos_name"].lower()  # .lower() чтобы регистр не влиял (А и а)
            )

            if not available_positions:

                st.warning(t["no_positions"])

            else:

                # Индекс сохранённой должности в текущем списке
                position_ids = [p["id"] for p in available_positions]

                if st.session_state["store_position_id"] in position_ids:
                    pos_index = position_ids.index(
                        st.session_state["store_position_id"]
                    )
                else:
                    pos_index = 0

                # Ключ должности — БЕЗ версии: должность не сбрасывается
                selected_position = st.selectbox(
                    t["position"],
                    available_positions,
                    index=pos_index,
                    format_func=lambda position: position["pos_name"],
                    key=f"widget_position_{lang}"
                )

                selected_position_id = selected_position["id"]
                st.session_state["store_position_id"] = selected_position_id

                # -----------------------------------------
                # Поля формы (ключи с версией формы)
                # -----------------------------------------

                st.text_input(
                    t["full_name"],
                    value=st.session_state["store_full_name"],
                    key=f"widget_full_name_{lang}_{form_version}"
                )
                st.session_state["store_full_name"] = st.session_state[
                    f"widget_full_name_{lang}_{form_version}"
                ]

                st.text_input(
                    t["email"],
                    value=st.session_state["store_email"],
                    key=f"widget_email_{lang}_{form_version}"
                )
                st.session_state["store_email"] = st.session_state[
                    f"widget_email_{lang}_{form_version}"
                ]

                st.text_input(
                    t["education"],
                    value=st.session_state["store_educ"],
                    key=f"widget_educ_{lang}_{form_version}"
                )
                st.session_state["store_educ"] = st.session_state[
                    f"widget_educ_{lang}_{form_version}"
                ]

                st.text_input(
                    t["experience"],
                    value=st.session_state["store_experience"],
                    key=f"widget_experience_{lang}_{form_version}"
                )
                st.session_state["store_experience"] = st.session_state[
                    f"widget_experience_{lang}_{form_version}"
                ]

                birth_date_widget_key = (
                    f"widget_birth_date_{lang}_{form_version}"
                )

                if birth_date_widget_key not in st.session_state:
                    st.session_state[birth_date_widget_key] = (
                        st.session_state["store_birth_date"]
                    )

                def _sync_birth_date():
                    st.session_state["store_birth_date"] = (
                        st.session_state[birth_date_widget_key]
                    )
                    st.session_state["bdate_touched"] = True          # <-- new

                st.date_input(
                    t["birth_date"],
                    key=birth_date_widget_key,
                    on_change=_sync_birth_date,
                    format="DD/MM/YYYY",
                    min_value=date(1900, 1, 1)   # нижняя граница
                    # max_value=date.today()        # будущие даты выбрать нельзя
                )

                # -----------------------------------------
                # Birth date validation (only after the user touched it)
                # -----------------------------------------

                birth_date_invalid = not is_valid_birth_date(st.session_state["store_birth_date"])

                show_bdate_error = (
                    st.session_state["bdate_touched"] and birth_date_invalid
                )

                if show_bdate_error:

                    if st.session_state["store_birth_date"] is None:

                        st.error(t["empty_bdate_field"])

                    else:

                        st.markdown(
                            f'<p style="color:red;">'
                            f'{t["birth_date_error"]}'
                            f'</p>',
                            unsafe_allow_html=True
                        )

                # -----------------------------------------
                # Submit application
                # -----------------------------------------

                if st.button(
                    t["submit_application"],
                    disabled=show_bdate_error
                ):

                    # If the user is submitting an untouched (still default) invalid
                    # birth date, mark it touched and re-render so the error appears.
                    st.session_state["bdate_touched"] = True

                    if birth_date_invalid:
                        st.rerun()

                    required_fields = {
                        "store_full_name": t["full_name"],
                        "store_email": t["email"],
                        "store_educ": t["education"],
                        "store_experience": t["experience"],
                    }
                    
                    validation_error = None

                    for field_key, field_name in required_fields.items():
                        field_value = st.session_state[field_key].strip()

                        # 1. Проверка на пустоту
                        if not field_value:
                            validation_error = t["fill_field"].format(field_name=field_name)
                            break

                        # 2. Проверка email сразу после того, как убедились, что он не пустой
                        if field_key == "store_email" and not is_valid_email(field_value):
                            validation_error = t["invalid_email"]
                            break

                    if validation_error:
                        st.error(validation_error)

                    else:

                        application_data = {
                            "position_id": selected_position_id,
                            "educ": st.session_state["store_educ"],
                            "experience": st.session_state["store_experience"],
                            "full_name": st.session_state["store_full_name"],
                            "email": st.session_state["store_email"],
                            "birth_date": st.session_state[
                                "store_birth_date"
                            ].isoformat()
                        }

                        response = requests.post(
                            f"{API_URL}/api/applications",
                            json=application_data,
                            timeout=5
                        )

                        if response.status_code == 201:
                            load_all_applications.clear() # <-- Очищаем кэш
                            st.session_state["show_success"] = True

                            # Очистка постоянного хранилища
                            st.session_state["store_full_name"] = ""
                            st.session_state["store_email"] = ""
                            st.session_state["store_educ"] = ""
                            st.session_state["store_experience"] = ""
                            st.session_state["store_birth_date"] = date.today()
                            st.session_state["bdate_touched"] = False            # <-- new

                            # Новая версия формы — поля визуально очистятся
                            st.session_state["candidate_form_version"] += 1

                            st.rerun()

                        elif response.status_code == 409:
                            st.error(t["duplicate_application"])
                        elif response.status_code == 422:
                            st.error(t["submit_error"])
                        elif response.status_code == 503:
                            # <-- ДОБАВИТЬ ЭТО
                            st.error(t["system_locked_message"])
                        else:
                            st.error(
                                f'{t["submit_error"]} '
                                f'Error code: {response.status_code}.'
                            )

                if st.session_state.pop("show_success", False):
                    st.success(t["success"])

    except requests.RequestException:

        st.error(t["connection_error"])

    # =========================================================
    # CANDIDATE BOOKINGS TABLE
    # =========================================================
    st.divider()
    st.subheader(t.get("my_bookings", "My Bookings"))

    try:
        # Fetch all applications and booked slots
        all_apps = load_all_applications(API_URL)
        all_slots = load_booked_slots(API_URL)

        # Use the existing timezone offset from your app's session state
        tz_offset = st.session_state.get("user_tz_offset", 0.0)
        now_utc = datetime.utcnow()

        valid_candidates = {}
        candidate_bookings = {}

        # Filter and match applications with upcoming slots
        for slot in all_slots:
            app_id = slot.get("application_id")
            
            # Parse date safely as UTC
            try:
                s_dt_utc = datetime.fromisoformat(slot["start"].replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue

            # Check if booking is in the future
            if s_dt_utc >= now_utc:
                app = next((a for a in all_apps if a["id"] == app_id), None)
                
                # Check if application status is 'New'
                if app and app["status"] == "New":
                    valid_candidates[app_id] = f"{app['full_name']} ({app['email']}). {app.get('position_name', '')}"
                    if app_id not in candidate_bookings:
                        candidate_bookings[app_id] = []
                    candidate_bookings[app_id].append(slot)

        if not valid_candidates:
            st.info(t.get("no_active_bookings", "No candidates with active upcoming bookings found."))
        else:
            # Dropdown ahead of table
            selected_app_id = st.selectbox(
                t.get("select_candidate_booking", "Select Candidate"),
                options=list(valid_candidates.keys()),
                format_func=lambda x: valid_candidates[x],
                key="candidate_booking_selector"
            )

            if selected_app_id:
                bookings = candidate_bookings[selected_app_id]

                # Prepare table data
                table_data = []
                for b in bookings:
                    try:
                        s_dt_utc = datetime.fromisoformat(b["start"].replace("Z", "+00:00")).replace(tzinfo=None)
                        e_dt_utc = datetime.fromisoformat(b["end"].replace("Z", "+00:00")).replace(tzinfo=None)

                        # Apply the local time offset
                        s_dt_local = s_dt_utc + timedelta(hours=tz_offset)
                        e_dt_local = e_dt_utc + timedelta(hours=tz_offset)
                    except Exception:
                        continue
                        
                    # Select column is first
                    table_data.append({
                        t.get("select_booking", "Select"): False,
                        "_id": b["booking_uid"],
                        t.get("date", "Date"): s_dt_local.strftime("%d-%m-%Y"),
                        t.get("time", "Time"): f"{s_dt_local.strftime('%H:%M')} - {e_dt_local.strftime('%H:%M')}",
                        # Check multiple possible backend keys for links
                        "cancel_url": b.get("cancel_url", b.get("cancel_link", "#")),
                        "reschedule_url": b.get("reschedule_url", b.get("reschedule_link", "#"))
                    })

                # Table with Checkbox
                edited_df = st.data_editor(
                    table_data,
                    hide_index=True,
                    width="stretch",
                    disabled=[
                        "_id", 
                        t.get("date", "Date"), 
                        t.get("time", "Time"), 
                        "cancel_url", 
                        "reschedule_url"
                    ],
                    column_config={
                        "_id": None,
                        "cancel_url": None, 
                        "reschedule_url": None, 
                        t.get("select_booking", "Select"): st.column_config.CheckboxColumn(
                            t.get("select_booking", "Select"),
                            width="small" 
                        )
                    },
                    key=f"candidate_booking_table_{selected_app_id}"
                )

                # Safe selection logic for both List and DataFrame (Fixes crash & disabled buttons)
                select_col = t.get("select_booking", "Select")
                if hasattr(edited_df, "iloc"):
                    selected_rows = edited_df[edited_df[select_col] == True].to_dict("records")
                else:
                    selected_rows = [row for row in edited_df if row.get(select_col) is True]

                # Инициализируем значения по умолчанию
                final_cancel_url = "#"
                final_reschedule_url = "#"
                system_locked = False  # <-- Значение по умолчанию (переменная существует ВСЕГДА)

                if len(selected_rows) == 1:
                    final_cancel_url = selected_rows[0].get("cancel_url", "#")
                    final_reschedule_url = selected_rows[0].get("reschedule_url", "#")
                elif len(selected_rows) > 1:
                    st.warning(t.get("select_only_one", "Please select only one booking at a time."))

                # Проверяем статус блокировки на сервере
                try:
                    status_resp = requests.get(f"{API_URL}/api/system-status", timeout=2)
                    if status_resp.status_code == 200:
                        system_locked = status_resp.json().get("locked", False)
                except Exception:
                    system_locked = False

                if system_locked:
                    st.warning(t["system_locked_message"])

                # Buttons under the table
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button(
                        t.get("reschedule_booking", "Reschedule"),
                        disabled=(len(selected_rows) != 1 or final_reschedule_url == "#"),
                        use_container_width=True,
                        key="reschedule_btn"
                    ):
                        # Проверяем статус системы перед переходом
                        try:
                            status_resp = requests.get(f"{API_URL}/api/system-status", timeout=2)
                            is_locked = status_resp.json().get("locked", False) if status_resp.status_code == 200 else False
                        except Exception:
                            is_locked = False
                        
                        if is_locked:
                            st.warning(t["system_locked_message"])
                        else:
                            # Редирект через JS
                            st.markdown(
                                f'<script>window.open("{final_reschedule_url}", "_blank");</script>',
                                unsafe_allow_html=True
                            )
                            st.stop()
                    
                with btn_col2:
                    if st.button(
                        t.get("cancel_booking", "Cancel Booking"),
                        disabled=(len(selected_rows) != 1 or final_cancel_url == "#"),
                        use_container_width=True,
                        key="cancel_btn"
                    ):
                        # Проверяем статус системы перед переходом
                        try:
                            status_resp = requests.get(f"{API_URL}/api/system-status", timeout=2)
                            is_locked = status_resp.json().get("locked", False) if status_resp.status_code == 200 else False
                        except Exception:
                            is_locked = False
                        
                        if is_locked:
                            st.warning(t["system_locked_message"])
                        else:
                            # Редирект через JS
                            st.markdown(
                                f'<script>window.open("{final_cancel_url}", "_blank");</script>',
                                unsafe_allow_html=True
                            )
                            st.stop()
                    
    except requests.RequestException as e:
        st.error(f"Could not load bookings: {e}")    

# =========================================================
# HR MODE
# =========================================================

else:

    # -----------------------------------------------------
    # HELPER: собрать будущие брони кандидата для промпта отмены
    # -----------------------------------------------------

    def _collect_candidate_bookings(application_id: int) -> list:
        try:
            slots = load_booked_slots(API_URL)
        except Exception:
            return []
        return [
            s for s in slots
            if s.get("application_id") == application_id
        ]

    def _schedule_bookings_cancel_prompt(application_id: int, candidate_name: str) -> None:
        """
        Если у кандидата есть будущие брони — сохраняет их в session_state,
        чтобы промпт отрисовался на следующем рендере.
        Ничего не делает, если броней нет.
        """
        bookings = _collect_candidate_bookings(application_id)
        if bookings:
            st.session_state["bookings_to_cancel"] = {
                "name": candidate_name,
                "bookings": bookings,
            }

    def _handle_stale_data_or_lock():
        """
        Вызывается, когда данные на сервере изменились (другой пользователь сделал сброс),
        или когда система заблокирована (монопольный режим).
        Принудительно сбрасывает интерфейс, чтобы HR не нанял "фантомного" кандидата.
        """
        # 1. Полностью очищаем кэш, чтобы при следующем рендере скачались новые данные
        load_all_applications.clear()
        load_positions.clear()
        load_booked_slots.clear()

        # 2. Снимаем выделение со строки таблицы
        st.session_state["selected_row_app_id"] = None
        st.session_state["active_application_id"] = None

        # 3. Очищаем выбранные слоты в календаре
        st.session_state.pop("booking_start", None)
        st.session_state.pop("booking_end", None)
        st.session_state.pop("selected_booking_uid", None)
        st.session_state.pop("selected_booking_start", None)
        st.session_state.pop("selected_booking_end", None)
        st.session_state.pop("selected_booking_name", None)
        
        # 4. Меняем версию таблицы, чтобы она перерисовалась с нуля
        st.session_state["editor_version"] = st.session_state.get("editor_version", 0) + 1            

    # -----------------------------------------------------
    # HR Header and Refresh
    # -----------------------------------------------------

    header_col, refresh_col = st.columns(
        [0.05, 0.65],
        vertical_alignment="bottom"
    )

    with header_col:
        st.header(t["hr"])

    
    with refresh_col:
        if st.button(t["refresh"]):
            load_all_applications.clear()
            load_positions.clear()
            load_booked_slots.clear()
            st.session_state["editor_version"] = (
                st.session_state.get("editor_version", 0) + 1
            )
            st.rerun() 

    # ---------------------------------------------
    # Applications
    # ---------------------------------------------

    st.subheader(t["applications"])

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    if "position_filter" not in st.session_state:
        st.session_state["position_filter"] = ""

    if "email_filter" not in st.session_state:
        st.session_state["email_filter"] = "" 
        
    if "full_name_filter" not in st.session_state:
        st.session_state["full_name_filter"] = ""    

    if "status_filter" not in st.session_state:
        st.session_state["status_filter"] = ""          

    if "selected_row_app_id" not in st.session_state:
        st.session_state["selected_row_app_id"] = None             

    filter_header_col, clear_filter_col = st.columns(
        [0.90, 0.10],
        vertical_alignment="center"
    )

    with filter_header_col:
        filters_expanded = st.expander(
            f" **{t['filters']}**",
            expanded=False
        )

    with clear_filter_col:
        if st.button(t["clear_filters"]):
            st.session_state["position_filter"] = ""
            st.session_state["email_filter"] = ""
            st.session_state["full_name_filter"] = ""
            st.session_state["status_filter"] = ""            
            st.session_state.pop("email_duplicate_active", None)
            st.session_state["selected_row_app_id"] = None   # Снимает галочку с выделенной в предыдущем действии строки           
            st.session_state["editor_version"] = (
                st.session_state.get("editor_version", 0) + 1
            )
            st.rerun()

    with filters_expanded:
        # --- 1. Фильтр по статусу (из прошлого шага) ---
        status_options = ["", "New", "Hired", "Canceled"]
        
        def _fmt_status(s):
            if s == "": return t.get("status_all", "All")
            if s == "New": return t.get("status_new", "New")
            if s == "Hired": return t.get("status_hired", "Hired")
            if s == "Canceled": return t.get("status_canceled", "Canceled")
            return s

        current_status_idx = status_options.index(st.session_state["status_filter"]) if st.session_state["status_filter"] in status_options else 0
        status_filter_input = st.selectbox(
            t.get("status", "Status"),
            options=status_options,
            index=current_status_idx,
            format_func=_fmt_status
        )

        # --- 2. Фильтр по позиции (умный выпадающий список) ---
        # Загружаем список должностей из кэша (функция load_positions уже есть в коде)
        try:
            _all_positions = load_positions(API_URL)
            pos_names = [p["pos_name"] for p in _all_positions]
        except Exception:
            pos_names = []

        # Чтобы текущий фильтр не терялся, если такой позиции больше нет в базе
        _current_pos = st.session_state["position_filter"]
        if _current_pos and _current_pos not in pos_names:
            pos_names.insert(0, _current_pos)

        _pos_index = pos_names.index(_current_pos) if _current_pos in pos_names else None
        
        position_filter_input = st.selectbox(
            t["position"],
            options=pos_names,
            index=_pos_index,
            accept_new_options=True,  # Позволяет вводить свои значения
            placeholder="Введите для поиска или выберите...",
        )

        # --- 3. Остальные фильтры ---
        email_filter_input = st.text_input(
            t["email"],
            value=st.session_state["email_filter"]
        )

        full_name_filter_input = st.text_input(
            t["full_name"],
            value=st.session_state["full_name_filter"]
        )

        # --- 4. Применение фильтров ---
        if st.button(t["apply_filters"]):
            # Если пользователь стер все в selectbox, Streamlit присылает None, 
            # поэтому заменяем на пустую строку для безопасного сохранения.
            st.session_state["position_filter"] = position_filter_input if position_filter_input else ""
            st.session_state["email_filter"] = email_filter_input
            st.session_state["full_name_filter"] = full_name_filter_input
            st.session_state["status_filter"] = status_filter_input
            st.rerun()



    # -----------------------------------------------------
    # Support Email
    # -----------------------------------------------------

    if "support_email" not in st.session_state:
        st.session_state["support_email"] = ""

    support_email = st.session_state["support_email"] 


    # -----------------------------------------------------
    # Load applications
    # -----------------------------------------------------

    try:
        # Теперь скачиваем ВСЕ заявки один раз и фильтруем на клиенте
        all_applications = load_all_applications(API_URL)

        position_q = st.session_state["position_filter"].strip().casefold()
        full_name_q = st.session_state["full_name_filter"].strip().casefold()
        email_q = st.session_state["email_filter"].strip().casefold()
        status_q = st.session_state["status_filter"].strip()  # <-- Забираем статус        

        applications = all_applications

        if position_q:
            applications = [a for a in applications if position_q in str(a.get("position_name", "")).casefold()]
        if full_name_q:
            applications = [a for a in applications if full_name_q in str(a.get("full_name", "")).casefold()]
        if email_q:
            applications = [a for a in applications if email_q in str(a.get("email", "")).casefold()]
        if status_q:
            applications = [a for a in applications if a.get("status") == status_q]

        # =========================================
        # СОРТИРОВКА
        # Сортируем по дате подачи заявки (app_date) от новых к старым.
        # Если даты одинаковые, сортируем по ID (от большего к меньшему).
        # =========================================
        applications = sorted(
            applications, 
            key=lambda x: (x.get("app_date", ""), x.get("id", 0)), 
            reverse=True
        )            

        # -------------------------------------------------
        # No applications
        # -------------------------------------------------

        if not applications:

            st.info(t["no_applications"])


        else:

            # ---------------------------------------------
            # Prepare table data
            # ---------------------------------------------

            display_data = []

            # FIX: single-select — галочка только у сохранённой строки
            _selected_id = st.session_state.get("selected_row_app_id")

            for application in applications:
                  
                display_data.append({
                    "_app_id": application["id"],
                    t["select"]: (application["id"] == _selected_id),  # <-- было: False
                    t["position"]: application["position_name"],
                    t["education"]: application["educ"],
                    t["experience"]: application["experience"],
                    t["full_name"]: application["full_name"],
                    t["email"]: application["email"],
                    t["application_date"]: datetime.fromisoformat(
                        application["app_date"]
                    ).strftime("%d-%m-%Y"),
                    t["status"]: {
                        "New": t["status_new"],
                        "Hired": t["status_hired"],
                        "Canceled": t["status_canceled"]
                    }.get(application["status"], application["status"])
                })



            # ---------------------------------------------
            # Editable applications table
            # ---------------------------------------------

            
            edited_data = st.data_editor(
                display_data,
                key=f"edited_data_{st.session_state.get('editor_version', 0)}",
                width="stretch",
                hide_index=True,
                disabled=[
                    t["position"],
                    t["education"],
                    t["experience"],
                    t["full_name"],
                    t["application_date"],
                    t["status"]
                ],
                column_config={
                    "_app_id": None,  # <-- ДОБАВИТЬ (скрывает колонку из интерфейса)
                    t["select"]: st.column_config.CheckboxColumn(
                        t["select"],
                        help=t["select_one"]
                    ),
                    t["email"]: st.column_config.TextColumn(
                    t["email"],
                    help=t["email_help"]
                )
                }
            )


            # -------------------------------------------------
            # Deferred duplicate-email notice (shown after rerun)
            # -------------------------------------------------
            if st.session_state.pop("email_duplicate_show", False):
                pending_email = st.session_state.pop("email_duplicate_email", None)
                if pending_email is not None:
                    show_duplicate_email_notice(
                        t["email_duplicate_active"],
                        pending_email,
                        t["cancel_email_changes"],
                        t["email_copied"],
                        t["click_email_to_copy"]
                    )
                    
            # -------------------------------------------------
            # Detect and save changed emails
            # -------------------------------------------------

            email_updated_flag = False
            force_ui_reset = False

            # FIX 1.3:
            # Снимаем блокировку email_duplicate_active в начале каждого запуска.
            # Логика: дубликат обнаруживается в ТЕКУЩЕМ запуске → ставится флаг →
            # st.rerun() → таблица перерисовывается с оригинальными email →
            # на следующем запуске дубликата уже нет, и блокировать кнопки нечем.
            # Флаг при этом выставляется заново только если дубликат снова обнаружен
            # именно в этом запуске (см. блок `if duplicate_exists` ниже).
            # st.session_state.pop("email_duplicate_active", None) # Избыточна

            for row in edited_data:
                app_id = row.get("_app_id")
                if not app_id:
                    continue
                    
                # Находим оригинальную заявку строго по ID
                original_app = next((a for a in applications if a["id"] == app_id), None)
                if not original_app:
                    continue

                original_email = original_app["email"]
                edited_email = row[t["email"]]


                if normalize_email(edited_email) != normalize_email(original_email):
                    
                    # Проверка на валидность формата email
                    if not is_valid_email(edited_email):
                        # Сохраняем структуру данных для кастомного вывода с кликабельными полями
                        st.session_state["current_action_message"] = {
                            "type": "invalid_email",
                            "name": original_app['full_name'],
                            "position": original_app['position_name'],
                            "error_text": t["invalid_email"]
                        }
                        st.session_state["current_action_message_type"] = "error"
                        break # Прерываем цикл, не отправляя запрос на сервер

                    # Проверка на дубликат в этой же должности
                    duplicate_exists = has_email_duplicate(
                        email=edited_email,
                        current_app_id=app_id,
                        applications=all_applications,
                        same_position_only=True,
                        target_position_id=original_app["position_id"],
                    )

                    # if duplicate_exists:
                    #     st.session_state["email_duplicate_active"] = app_id
                    #     show_duplicate_email_notice(
                    #         t["email_duplicate_active"],
                    #         edited_email,
                    #         t["cancel_email_changes"],
                    #         t["email_copied"],
                    #         t["click_email_to_copy"]
                    #     )
                    #     force_ui_reset = True
                    #     break # Выходим из цикла, чтобы не сохранять остальные

                    if duplicate_exists:
                        st.session_state["email_duplicate_email"] = edited_email
                        st.session_state["email_duplicate_show"] = True
                        force_ui_reset = True
                        break

                    st.session_state.pop("email_duplicate_active", None)

                    # Сохраняем в базу
                    email_response = requests.patch(
                        f"{API_URL}/api/applications/{app_id}/email",
                        json={"email": edited_email},
                        timeout=5
                    )

                    if email_response.status_code == 200:
                        load_all_applications.clear() # <-- Очищаем кэш
                        email_updated_flag = True
                    
                    elif email_response.status_code == 409:
                        detail = email_response.json().get("detail", t["email_duplicate_active"])
                        if "already used for an active application" in detail:
                            st.session_state["email_duplicate_email"] = edited_email
                            st.session_state["email_duplicate_show"] = True
                        else:
                            st.error(detail)
                        force_ui_reset = True
                        break

                    else:
                        detail = email_response.json().get("detail", "")
                        st.error(f'{t["email_update_error"]} {detail} (Error code: {email_response.status_code})')
                        force_ui_reset = True
                        break

            # Если была ошибка (дубликат или сбой) — жестко сбрасываем UI
            if force_ui_reset:
                st.session_state["editor_version"] = (
                    st.session_state.get("editor_version", 0) + 1
                )
                st.rerun()

            # Если успешно сохранили — тоже перезапускаем, чтобы подтянуть чистые данные
            if email_updated_flag:
                st.session_state.pop("current_action_message", None) # <-- Убираем старую ошибку
                st.session_state["email_updated_message"] = True
                st.session_state["editor_version"] = (
                    st.session_state.get("editor_version", 0) + 1
                )
                st.rerun()                      

            # Показываем отложенное сообщение об успехе
            if st.session_state.pop("email_updated_message", False):
                st.success(t["email_updated"])

            # -------------------------------------------------
            # FIX: single-select.
            # Клик по новой строке автоматически снимает галочку
            # с предыдущей. Никогда не бывает двух отмеченных.
            # -------------------------------------------------
            _checked_ids = [
                row["_app_id"]
                for row in edited_data
                if row.get(t["select"]) and row.get("_app_id") is not None
            ]
            _stored_id = st.session_state.get("selected_row_app_id")

            if len(_checked_ids) == 0:
                _new_id = None
            elif len(_checked_ids) == 1:
                _new_id = _checked_ids[0]
            else:
                # Пользователь кликнул новую строку, старая осталась отмеченной.
                # Оставляем ту, что НЕ совпадает с сохранённой.
                _new_id = next(
                    (i for i in _checked_ids if i != _stored_id),
                    _checked_ids[0]
                )

            if _new_id != _stored_id:
                st.session_state["selected_row_app_id"] = _new_id
                # Меняем ключ виджета, чтобы Streamlit перерисовал таблицу
                # с правильными галочками (без нашего сброса он сохранит
                # старую отмеченную строку визуально).
                st.session_state["editor_version"] = (
                    st.session_state.get("editor_version", 0) + 1
                )
                st.rerun()
                  
            # =========================================
            # Calendar expand/collapse state (default: collapsed)
            # =========================================
            if "calendar_expanded" not in st.session_state:
                st.session_state["calendar_expanded"] = False
            if "calendar_version" not in st.session_state:
                st.session_state["calendar_version"] = 0                


            # Определяем локаль
            calendar_locale = "ru" if lang == "ru" else "en"

            # =========================================
            # Find selected rows
            # =========================================
            selected_rows = [
                index
                for index, row
                in enumerate(edited_data)
                if row[t["select"]]
            ]

            # Safe defaults — handlers below always have something to read
            review_clicked = False
            interview_clicked = False
            hire_clicked = False
            reject_clicked = False
            selected_application = None
            selected_application_id = None
            edited_email = None
            email_is_valid = False
            can_process = False
            email_duplicate_for_selected = False
            same_email_hired_app = None    # <-- NEW
            same_email_hired = False       # <-- NEW            

            # =========================================
            # Selection state
            # =========================================
            if len(selected_rows) == 0:
                st.info(t["select_one"])

            elif len(selected_rows) > 1:
                st.warning(t["select_only_one"])

            else:
                selected_index = selected_rows[0]
                selected_application = applications[selected_index]
                selected_application_id = selected_application["id"]

                # Блок стирания сооббщения при смене состояния
                if st.session_state.get("last_selected_app_for_hire") != selected_application_id:
                    st.session_state["last_selected_app_for_hire"] = selected_application_id
                    st.session_state["show_hire_warning"] = False
                    st.session_state.pop("pending_hire_app_id", None)

                    # При смене кандидата сбрасываем и same-email warning
                    st.session_state["show_same_email_hire_warning"] = False
                    st.session_state.pop("pending_same_email_app_id", None)
                    st.session_state.pop("pending_same_email_info", None)

                    # Стираем объединенное сообщение при смене кандидата
                    st.session_state.pop("current_action_message", None) # <-- ЗАМЕНА

                # ---------------------------

                # New selection → clear old slot, AUTO-EXPAND calendar
                if st.session_state.get("active_application_id") != selected_application_id:
                    st.session_state["active_application_id"] = selected_application_id
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)
                    st.session_state["calendar_expanded"] = True

                edited_email = edited_data[selected_index][t["email"]]
                email_is_valid = is_valid_email(edited_email)

                can_process = selected_application["status"] == "New"

                # FIX 1.3 (robust):
                # Считаем дубликат заново на каждом рендере по актуальным данным.
                # Никаких сохранённых флагов в session_state — только «правда момента».
                # Если редактирование уже откатилось (таблица перерисована с
                # оригинальными email), дубликата не будет → кнопки разблокированы.
                email_duplicate_for_selected = has_email_duplicate(
                    email=edited_email,
                    current_app_id=selected_application_id,
                    applications=all_applications,
                    same_position_only=True,
                    target_position_id=selected_application["position_id"],
                )

                # NEW: тот же email, но Hired на ДРУГОЙ должности
                # (не блокирует кнопки — покажет подтверждение при клике на «Принять»).
                same_email_hired_app = None
                if is_valid_email(edited_email):
                    _norm = normalize_email(edited_email)
                    same_email_hired_app = next(
                        (
                            app for app in all_applications
                            if app["id"] != selected_application_id
                            and app["status"] == "Hired"
                            and normalize_email(app["email"]) == _norm
                        ),
                        None
                    )
                same_email_hired = (
                    selected_application["status"] == "New"
                    and same_email_hired_app is not None
                )

                # Needed for Interview button — enabled only if a slot is picked
                slot_selected = bool(
                    st.session_state.get("booking_start")
                    and st.session_state.get("booking_end")
                )

                # -----------------------------------------
                # Action buttons
                # -----------------------------------------
                col1, col2, col3 = st.columns(3)

                with col1:
                    interview_clicked = st.button(
                        t["Interview"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                            or not slot_selected        # <-- NEW: requires a slot
                        )
                    )

                with col2:
                    hire_clicked = st.button(
                        t["hire"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                        )
                    )

                with col3:
                    reject_clicked = st.button(
                        t["reject"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                        )
                    )

                # FIX 3: Предупреждение о занятой позиции — ПРЯМО ПОД КНОПКАМИ,
                # выше календаря. НЕ сбрасываем show_hire_warning внутри блока —
                # только по явному выбору пользователя. Так предупреждение
                # остаётся при любых перерисовках (свернуть календарь, сменить
                # фильтр и т.п.).
                if (
                    st.session_state.get("show_hire_warning")
                    and st.session_state.get("pending_hire_app_id") == selected_application_id
                ):
                    st.warning(t.get(
                        "position_occupied_warning",
                        "Позиция уже занята. Кандидата можно принять, но нужно проверить количество ставок."
                    ))
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button(
                            t.get("hire_anyway", "Принять кандидата всё равно"),
                            type="primary"
                        ):
                            st.session_state["force_hire_clicked"] = True
                            st.session_state["show_hire_warning"] = False
                            st.session_state.pop("pending_hire_app_id", None)
                            st.rerun()
                    with col_no:
                        if st.button(t.get("cancel", "Отмена")):
                            st.session_state["show_hire_warning"] = False
                            st.session_state.pop("pending_hire_app_id", None)
                            st.rerun()

                # NEW: промпт «уже принят на другую должность»
                if (
                    st.session_state.get("show_same_email_hire_warning")
                    and st.session_state.get("pending_same_email_app_id") == selected_application_id
                ):
                    _info = st.session_state.get("pending_same_email_info", {})
                    
                    # 1. Готовим шаблон для HTML-функции: подставляем должности,
                    # но оставляем {email}, чтобы функция сама заменила его на кликабельный
                    _template = t.get(
                        "same_email_hire_prompt",
                        "A candidate with this email {email} is already hired for «{hired_position}». Do you want to hire them again for «{current_position}»?"
                    )
                    _formatted_template = _template.replace(
                        "{hired_position}", _info.get("hired_position", "")
                    ).replace(
                        "{current_position}", _info.get("current_position", "")
                    )

                    # 2. Отрисовываем красивый HTML-блок (как на скриншоте 2)
                    show_duplicate_email_notice(
                        message_template=_formatted_template,
                        email=_info.get("email", ""),
                        cancel_hint="", # В этой функции не используется, но требуется по сигнатуре
                        copied_message=t.get("email_copied", "Скопировано!"),
                        copy_hint=t.get("click_email_to_copy", "Нажмите на email, чтобы скопировать")
                    )

                    # 3. Кнопки под блоком
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button(
                            t.get("hire_anyway", "Принять кандидата всё равно"),
                            type="primary",
                            key="same_email_hire_anyway",
                        ):
                            st.session_state["force_hire_clicked"] = True
                            st.session_state["show_same_email_hire_warning"] = False
                            st.session_state.pop("pending_same_email_app_id", None)
                            st.session_state.pop("pending_same_email_info", None)
                            st.rerun()
                    with col_no:
                        if st.button(
                            t.get("cancel", "Отмена"),
                            key="same_email_hire_cancel",
                        ):
                            st.session_state["show_same_email_hire_warning"] = False
                            st.session_state.pop("pending_same_email_app_id", None)
                            st.session_state.pop("pending_same_email_info", None)
                            st.rerun()

            # =========================================
            # ЕДИНОЕ ОКНО СООБЩЕНИЙ (Успех / Ошибки) РЯМО ПОД КНОПКАМИ (до календаря).
            # =========================================
            # Забираем флаги успеха и превращаем их в единое сообщение

            if st.session_state.pop("application_hired_message", False):
                st.session_state["current_action_message"] = t.get("application_hired", t.get("status_hired", "Кандидат принят"))
                st.session_state["current_action_message_type"] = "success"
            if st.session_state.pop("application_rejected_message", False):
                st.session_state["current_action_message"] = t["application_rejected"]
                st.session_state["current_action_message_type"] = "success"
            if st.session_state.pop("interview_ready_message", False):
                st.session_state["current_action_message"] = t.get("interview_ready", "Interview booked successfully.")
                st.session_state["current_action_message_type"] = "success"
            if st.session_state.pop("booking_cancelled_message", False):
                st.session_state["current_action_message"] = t.get("booking_cancelled", "Interview booking cancelled successfully.")
                st.session_state["current_action_message_type"] = "success"

            # Отрисовываем сообщение, если оно есть в памяти. 
            # Оно не исчезнет, пока не будет перезаписано новым или пока не сменим кандидата.
            if st.session_state.get("current_action_message"):
                _msg_type = st.session_state.get("current_action_message_type", "success")
                _msg_text = st.session_state["current_action_message"]
                
                if _msg_type == "success":
                    st.success(_msg_text)
                elif _msg_type == "error":
                    # Если это ошибка невалидного email (словарь, а не строка)
                    if isinstance(_msg_text, dict) and _msg_text.get("type") == "invalid_email":
                        _name = _msg_text["name"]
                        _pos = _msg_text["position"]
                        _err = _msg_text["error_text"]
                        
                        # Берем текущий шаблон и текст подсказки из словаря
                        _tpl = t.get("invalid_email_for_candidate", "For {name} ({position}) {error_text}")
                        _hint = t.get("click_value_to_copy", "Click value to copy")
                        
                        # Заменяем {name}, {position} на HTML-спаны
                        _html_msg = _tpl.replace(
                            "{name}", 
                            f'<span class="copy-txt" data-copy="{html.escape(_name)}" style="color: #0d6efd; text-decoration: underline; cursor: pointer; font-weight: 600;" title="{html.escape(_hint)}">{html.escape(_name)}</span>'
                        ).replace(
                            "{position}", 
                            f'<span class="copy-txt" data-copy="{html.escape(_pos)}" style="color: #0d6efd; text-decoration: underline; cursor: pointer; font-weight: 600;" title="{html.escape(_hint)}">{html.escape(_pos)}</span>'
                        ).replace(
                            "{error_text}", 
                            html.escape(_err)
                        )
                        
                        # Добавляем подсказку внизу
                        _html = f"""
                        <div style="background-color: #ffebee; color: #c62828; padding: 0.9rem 1rem; border-radius: 0.5rem; border: 1px solid #ef9a9a; font-family: 'Source Sans Pro', sans-serif; font-size: 16px; line-height: 1.5;">
                            <div style="margin-bottom: 0.4rem;">{_html_msg}</div>
                            <div style="font-style: italic; opacity: 0.75; font-size: 14px;">{html.escape(_hint)}</div>
                        </div>
                        <script>
                            document.querySelectorAll('.copy-txt').forEach(function(el) {{
                                el.addEventListener('click', function() {{
                                    navigator.clipboard.writeText(this.getAttribute('data-copy'));
                                }});
                            }});
                        </script>
                        """
                        # Выводим через components.html, чтобы работал JS. Высоту увеличили до 110.
                        components.html(_html, height=110)
                    else:
                        # Обычная ошибка текстом (например, "Позиция занята" от сервера)
                        st.error(_msg_text)

            # =========================================
            # Промпт «Отменить брони кандидата»
            # =========================================
            # FIX: перенесено сюда из конца try:, чтобы пользователь видел
            # его сразу под кнопками, а не под календарём.
            # Срабатывает после найма ИЛИ отклонения, если у кандидата
            # были будущие брони.
            if "bookings_to_cancel" in st.session_state:
                prompt_info = st.session_state["bookings_to_cancel"]
                candidate_name = prompt_info["name"]
                bookings_list = prompt_info["bookings"]

                tz_offset = st.session_state.get("user_tz_offset", 0.0)

                # 1. Собираем все интервалы в локальном времени и сортируем их
                intervals = []
                for b in bookings_list:
                    try:
                        s = datetime.fromisoformat(
                            b["start"].replace("Z", "+00:00")
                        ).replace(tzinfo=None) + timedelta(hours=tz_offset)
                        e = datetime.fromisoformat(
                            b["end"].replace("Z", "+00:00")
                        ).replace(tzinfo=None) + timedelta(hours=tz_offset)
                        intervals.append([s, e])
                    except Exception:
                        pass

                intervals.sort(key=lambda x: x[0])

                # 2. Объединяем последовательные слоты (только в один день)
                merged_intervals = []
                for current in intervals:
                    if not merged_intervals:
                        merged_intervals.append(current)
                    else:
                        last = merged_intervals[-1]
                        is_same_day = current[0].date() == last[1].date()
                        is_consecutive = current[0] <= last[1]
                        if is_same_day and is_consecutive:
                            last[1] = max(last[1], current[1])
                        else:
                            merged_intervals.append(current)

                # 3. Форматируем объединенные интервалы в красивую строку
                formatted_times = []
                for s, e in merged_intervals:
                    if s.date() == e.date():
                        formatted_times.append(
                            f"{s.strftime('%H:%M')} → {e.strftime('%H:%M %d.%m.%Y')}"
                        )
                    else:
                        formatted_times.append(
                            f"{s.strftime('%H:%M %d.%m.%Y')} → {e.strftime('%H:%M %d.%m.%Y')}"
                        )

                time_str = ", ".join(formatted_times)

                # Само уведомление
                st.warning(
                    f"⚠️ **{candidate_name}** {t['has_booking_at']} "
                    f"**{time_str}**. {t['cancellation_ask']}"
                )

                # Функции-коллбеки для кнопок
                def _cancel_all_bookings():
                    for b in bookings_list:
                        requests.post(
                            f"{API_URL}/api/interviews/{b['booking_uid']}/cancel",
                            timeout=10
                        )
                    del st.session_state["bookings_to_cancel"]
                    st.session_state["calendar_version"] += 1
                    st.session_state["hired_cancelled_msg"] = True

                def _dismiss_booking_prompt():
                    del st.session_state["bookings_to_cancel"]

                col_btn, col_empty = st.columns([1, 1])
                with col_btn:
                    st.button(
                        t.get("cancel_booking_for_reason", "Cancel booking for candidate"),
                        type="primary",
                        on_click=_cancel_all_bookings
                    )
                with col_empty:
                    st.button(
                        t.get("dismiss", "Dismiss"),
                        on_click=_dismiss_booking_prompt
                    )

            # Показываем сообщение об успешной отмене
            if st.session_state.pop("hired_cancelled_msg", False):
                st.success(t["bookings_cancelled_successfully"])

            # =========================================
            # Calendar toggle + guard
            # =========================================
            if "calendar_version" not in st.session_state:
                st.session_state["calendar_version"] = 0

            def _toggle_cal():
                new_state = not st.session_state.get("calendar_expanded", False)
                st.session_state["calendar_expanded"] = new_state
                if not new_state:
                    # Очищаем свободный слот
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)
                    
                    # Очищаем выбранную бронь (синюю рамку)
                    st.session_state.pop("selected_booking_uid", None)
                    st.session_state.pop("selected_booking_start", None)
                    st.session_state.pop("selected_booking_end", None)
                    st.session_state.pop("selected_booking_name", None)
                    
                # Убиваем кэш календаря, чтобы он не вернул старый dateClick
                st.session_state["calendar_version"] += 1

            toggle_label = (
                f"▲ {t.get('collapse_calendar', 'Collapse calendar')}"
                if st.session_state.get("calendar_expanded", False)
                else f"▼ {t.get('expand_calendar', 'Expand calendar')}"
            )

            # Если календарь развернут — показываем две колонки (Развернуть/Свернуть + Отменить)
            if st.session_state.get("calendar_expanded", False):

                col_calendar, col_cancel = st.columns(2)

                with col_calendar:
                    st.button(
                        toggle_label,
                        key="calendar_toggle_button",
                        on_click=_toggle_cal
                    )

                with col_cancel:
                    cancel_booking_clicked = st.button(
                        t.get("cancel_booking", "Cancel Booking"),
                        key="cancel_booking_button",
                        disabled=not bool(
                            st.session_state.get("selected_booking_uid")
                        )
                    )
            # Если календарь свернут — показываем только кнопку развернуть
            else:
                st.button(
                    toggle_label,
                    key="calendar_toggle_button",
                    on_click=_toggle_cal
                )
                cancel_booking_clicked = False  # Важно! Чтобы код ниже не упал с ошибкой

            # ГАРД (оставляем)
            if not st.session_state.get("calendar_expanded", False):
                st.session_state.pop("booking_start", None)
                st.session_state.pop("booking_end", None)

                # Очищаем выбранную бронь
                st.session_state.pop("selected_booking_uid", None)
                st.session_state.pop("selected_booking_start", None)
                st.session_state.pop("selected_booking_end", None)
                st.session_state.pop("selected_booking_name", None)                
            
            # =========================================
            # Calendar — rendered only when expanded
            # =========================================

            # Берем настройки локализации из словаря t
            cal_locale    = t.get("locale_code", "en")
            cal_today     = t.get("today", "today")
            cal_week      = t.get("week", "week")
            cal_day       = t.get("day", "day")
            cal_all_day   = t.get("all_day", "all-day")


            if st.session_state["calendar_expanded"]:
                calendar_options = {
                    "initialView": "timeGridWeek",
                    "selectable": True,
                    "selectOverlap": False,
                    "slotMinTime": "09:00:00",
                    "slotMaxTime": "18:00:00",
                    "slotDuration": "00:30:00",
                    "snapDuration": "00:30:00",
                    # Первый день недели: 1 для РФ (Пн), 0 для США (Вс)
                    "firstDay": 1 if cal_locale == "ru" else 0, 
                    # Когда закоменчено можно листать в прошлое
                    # "validRange": {                           
                    #     "start": date.today().isoformat()
                    # },
                    "headerToolbar": {
                        "left": "prev,next today",
                        "center": "title",
                        "right": "timeGridWeek,timeGridDay",
                    },
                    "height": 500,

                    # --- ЛОКАЛИЗАЦИЯ ---
                    "locale": cal_locale,
                    "buttonText": {
                        "today": cal_today,
                        "week": cal_week,
                        "day": cal_day
                    },
                    "allDayText": cal_all_day,

                    # --- ФОРМАТЫ ОТОБРАЖЕНИЯ ---
                    "locale": calendar_locale,
                    "titleFormat": {
                        "year": "numeric",
                        "month": "long"
                    },
                    "dayHeaderFormat": {
                        "weekday": "short",
                        "month": "numeric",
                        "day": "numeric",
                        "omitCommas": True
                    },
                    "slotLabelFormat": {
                        "hour": "2-digit",
                        "minute": "2-digit",
                        "hour12": False
                    },
                    "eventTimeFormat": {
                        "hour": "2-digit",
                        "minute": "2-digit",
                        "hour12": False
                    },
                    # ----------------------
                }

                # Fetch booked slots from backend
                try:
                    booked_slots = load_booked_slots(API_URL)
                except Exception as e:
                    st.warning(f"Could not load booked slots: {e}")
                    booked_slots = []

                # Use no chunks split

                # 1 ver - use no 30 min chunks-------------
                # Build events
                calendar_events = []
                color_palette = [
                                "#e74c3c", "#43abf1", "#08e021", "#f1c40f", "#9b59b6",
                                "#f07000", "#1abc9c", "#004d9a", "#e84393", "#e75c11b6"
                                ]

                app_color_map = {}

                booked_title = t.get("booked", "Booked")
                selected_booking_uid = st.session_state.get("selected_booking_uid")

                # 1. Собираем все уникальные ID заявок, у которых есть брони, и сортируем их
                unique_booked_app_ids = sorted(list({
                    slot.get("application_id") for slot in booked_slots 
                    if slot.get("application_id") is not None
                }))
                
                # 2. Раздаем цвета строго по порядку (0, 1, 2, 3...)
                # Кандидат с самым маленьким ID получит первый цвет, следующий - второй и т.д.
                app_color_map = {
                    app_id: color_palette[idx % len(color_palette)] 
                    for idx, app_id in enumerate(unique_booked_app_ids)
                }

                for slot in booked_slots:
                    app_id = slot.get("application_id", "")
                    
                    # 3. Просто берем закрепленный цвет из словаря
                    slot_color = app_color_map.get(app_id, "#cccccc") # серый по умолчанию

                    is_selected = (selected_booking_uid == slot["booking_uid"])
                    
                    # Ищем имя кандидата и позицию по ID заявки
                    app = next((a for a in all_applications if a["id"] == app_id), None)
                    if app:
                        candidate_name = f"{app['full_name']} ({app['position_name']})"
                    else:
                        candidate_name = booked_title

                    # Pass the slot natively as ONE block (no more 30-min chunks)
                    # Форматируем время для подсказки (в локальном времени)
                    tz_offset = st.session_state.get("user_tz_offset", 0.0)
                    try:
                        s_dt = datetime.fromisoformat(slot["start"].replace("Z", "+00:00")).replace(tzinfo=None)
                        e_dt = datetime.fromisoformat(slot["end"].replace("Z", "+00:00")).replace(tzinfo=None)
                        s_local = s_dt + timedelta(hours=tz_offset)
                        e_local = e_dt + timedelta(hours=tz_offset)
                        
                        # Берем данные для красивой подсказки
                        if app:
                            t_name = app["full_name"]
                            t_pos = app.get("position_name", "No position")
                        else:
                            t_name = booked_title
                            t_pos = ""
                            
                        time_str = f"{s_local.strftime('%H:%M')} - {e_local.strftime('%H:%M, %d.%m.%Y')}"
                        
                        # Собираем все в одну подсказку с переносами строк (\n)
                        tooltip_text = f"{t_name}\n{t_pos}\n{time_str}"
                    except Exception:
                        tooltip_text = candidate_name

                    event = {
                        "id": slot["booking_uid"],
                        "title": candidate_name,
                        "start": slot["start"],
                        "end": slot["end"],
                        "backgroundColor": slot_color,
                        "tooltip": tooltip_text,  # <-- Всплывающая подсказка
                    }

                    if is_selected:
                        # Assign a CSS class (FullCalendar will use this to apply the thick border)
                        event["classNames"] = ["selected-booking-frame"]
                        # Убрали backgroundColor и textColor, чтобы фон остался прежним
                        
                    calendar_events.append(event)

                # Define the thick CSS frame
                bold_frame_css = """
                .fc-event.selected-booking-frame {
                    border: 3px solid #093445 !important; /* Темно-синяя рамка 3px */
                    box-shadow: 0 0 8px rgba(9, 52, 69, 0.8) !important; /* Свечение в тон рамки */
                    z-index: 10 !important;
                }
                """

                # Call the calendar function
                calendar_result = calendar(
                    events=calendar_events,
                    options=calendar_options,
                    custom_css=bold_frame_css,  # <--- This is the magic line
                    key=f"booking_calendar_v{st.session_state['calendar_version']}",
                )
                # ----- Handle drag-select -----
                if calendar_result and calendar_result.get("callback") == "select":
                    if st.session_state.pop("ignore_next_calendar_callback", False):
                        pass  # Игнорируем старый клик
                    else:
                        sel = calendar_result["select"] # <-- ВОЗВРАЩАЕМ
                        sel_start = datetime.fromisoformat(sel["start"].replace("Z", "+00:00")) # <-- ВОЗВРАЩАЕМ
                        
                        if sel_start.replace(tzinfo=None) < datetime.utcnow():
                            st.warning(t["slot_in_past"])
                        else:
                            st.session_state.pop("selected_booking_uid", None)
                            st.session_state.pop("selected_booking_start", None)
                            st.session_state.pop("selected_booking_end", None)

                            if (
                                st.session_state.get("booking_start") != sel["start"]
                                or st.session_state.get("booking_end") != sel["end"]
                            ):
                                st.session_state["booking_start"] = sel["start"]
                                st.session_state["booking_end"] = sel["end"]
                                st.rerun()

                # ----- Handle single-click -----
                if calendar_result and calendar_result.get("callback") == "dateClick":
                    # ДОБАВИТЬ ПРОВЕРКУ:
                    if st.session_state.pop("ignore_next_calendar_callback", False):
                        pass  # Игнорируем старый клик
                    else:
                        date_str = calendar_result["dateClick"]["date"]
                        try:
                            start_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            if start_dt.replace(tzinfo=None) < datetime.utcnow():
                                st.warning(t["slot_in_past"])
                                st.stop()

                            end_dt = start_dt + timedelta(minutes=30)
                            
                            # Convert local time to UTC using the existing offset
                            tz_offset = st.session_state.get("user_tz_offset", 0.0)
                            
                            if start_dt.tzinfo is None:
                                start_utc = start_dt - timedelta(hours=tz_offset)
                            else:
                                start_utc = start_dt.replace(tzinfo=None)
                                
                            if end_dt.tzinfo is None:
                                end_utc = end_dt - timedelta(hours=tz_offset)
                            else:
                                end_utc = end_dt.replace(tzinfo=None)

                            start_iso = start_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                            end_iso = end_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

                            overlaps_booked = any(
                                start_iso < slot["end"] and end_iso > slot["start"]
                                for slot in booked_slots
                            )

                            if overlaps_booked:
                                st.info(t["slot_already_booked"])
                            else:

                                st.session_state.pop("selected_booking_uid", None)
                                st.session_state.pop("selected_booking_start", None)
                                st.session_state.pop("selected_booking_end", None)

                                if (
                                    st.session_state.get("booking_start") != start_iso
                                    or st.session_state.get("booking_end") != end_iso
                                ):
                                    st.session_state["booking_start"] = start_iso
                                    st.session_state["booking_end"] = end_iso
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Could not parse slot: {e}")

                # ----- Handle clicks on booked events -----
                if calendar_result and calendar_result.get("callback") == "eventClick":
                    clicked_event = calendar_result["eventClick"]["event"]
                    booking_uid = clicked_event.get("id")

                    # Guard: only act if this is a *new* booking selection.
                    # Prevents the cached eventClick payload from looping st.rerun().
                    if booking_uid and st.session_state.get("selected_booking_uid") != booking_uid:
                        st.session_state["selected_booking_uid"] = booking_uid

                        # СОХРАНЯЕМ ИМЯ ИЗ КАЛЕНДАРЯ
                        st.session_state["selected_booking_name"] = clicked_event.get("title", "Candidate")                        

                        # Clear any previously selected free slot
                        st.session_state.pop("booking_start", None)
                        st.session_state.pop("booking_end", None)

                        st.session_state["selected_booking_start"] = clicked_event.get("start")
                        st.session_state["selected_booking_end"] = clicked_event.get("end")

                        st.rerun()

            # =========================================
            # Cancel interview booking
            # =========================================

            if cancel_booking_clicked:

                booking_uid = st.session_state.get("selected_booking_uid")

                if not booking_uid:
                    st.warning("Please select a booked interview first.")

                else:

                    try:
                        with st.spinner(t["canceling_booking"]):

                            cancel_response = requests.post(
                                f"{API_URL}/api/interviews/{booking_uid}/cancel",
                                timeout=15
                            )

                        if cancel_response.status_code == 200:
                            load_booked_slots.clear() # <-- Очищаем кэш
                            load_all_applications.clear() # <-- Очищаем кэш
                            # Clear selected booking
                            st.session_state.pop("selected_booking_uid", None)
                            st.session_state.pop("selected_booking_start", None)
                            st.session_state.pop("selected_booking_end", None)

                            # Clear free-slot selection too
                            st.session_state.pop("booking_start", None)
                            st.session_state.pop("booking_end", None)

                            # Refresh calendar
                            st.session_state["calendar_version"] += 1

                            st.session_state["booking_cancelled_message"] = True

                            st.rerun()

                        else:
                            if cancel_response.status_code == 503:
                                st.session_state["current_action_message"] = t["system_locked_message"]
                                _handle_stale_data_or_lock()
                            else:
                                try:
                                    detail = cancel_response.json().get("detail", cancel_response.text)
                                except Exception:
                                    detail = cancel_response.text[:300]
                                st.session_state["current_action_message"] = f"Cancellation failed: {detail}"
                            
                            st.session_state["current_action_message_type"] = "error"
                            st.rerun()

                            # Booking no longer active — clear stale selection
                            if cancel_response.status_code in (404, 409):

                                st.session_state.pop("selected_booking_uid", None)
                                st.session_state.pop("selected_booking_start", None)
                                st.session_state.pop("selected_booking_end", None)

                                st.session_state["calendar_version"] += 1
                                st.rerun()

                    except requests.RequestException as e:
                        st.error(f"Cancellation request failed: {e}")


            # =========================================
            # Handlers — only fire when their button was clicked
            # (buttons only render when one app is selected)
            # =========================================

            # ----- Interview -----
            if interview_clicked:
                booking_start = st.session_state.get("booking_start")
                booking_end = st.session_state.get("booking_end")

                if not booking_start or not booking_end:
                    if st.session_state.get("calendar_expanded", False):
                        st.error(t["select_slot_first"])
                else:
                    interview_payload = {
                        "application_id": selected_application_id,
                        "email": edited_email,
                        "full_name": selected_application["full_name"],
                        "booking_start": booking_start,
                        "booking_end": booking_end,
                        "support_email": support_email,
                        "timezone": st.session_state.get("user_tz_name", "UTC"),
                        "language": lang
                    }

                    try:
                        resp = requests.post(
                            f"{API_URL}/api/interviews",
                            json=interview_payload,
                            timeout=15,
                        )
                    except requests.RequestException as e:
                        st.session_state["current_action_message"] = f"{t['request_failed']}: {e}"
                        st.session_state["current_action_message_type"] = "error"
                        st.rerun()

                    if resp.status_code not in (200, 201):
                        try:
                            detail = resp.json().get("detail", "")
                        except Exception:
                            detail = resp.text[:300]

                        detail_lower = str(detail).lower()
                        
                        if resp.status_code == 409:
                            st.session_state["current_action_message"] = t["slot_unavailable"]
                        elif resp.status_code == 400 and "past" in detail_lower:
                            st.session_state["current_action_message"] = t["slot_in_past"]
                        elif resp.status_code == 503:
                            st.session_state["current_action_message"] = t["system_locked_message"]
                            _handle_stale_data_or_lock() # <-- ДОБАВИТЬ ЭТО
                        elif resp.status_code == 404:
                            st.session_state["current_action_message"] = "Заявка не найдена. Возможно, база данных была обновлена."
                            _handle_stale_data_or_lock() # <-- ДОБАВИТЬ ЭТО
                        else:
                            st.session_state["current_action_message"] = t["system_locked_message"] or f"Error {resp.status_code}"
                            
                        st.session_state["current_action_message_type"] = "error"
                        st.rerun()

                    result = resp.json()
                    load_booked_slots.clear() # <-- Очищаем кэш
                    load_all_applications.clear() # <-- Очищаем кэш
                    st.session_state["interview_booking_uid"] = result.get("booking_uid", "")
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)
                    st.session_state["interview_ready_message"] = True
                    st.session_state["calendar_version"] += 1  # <--- ВАЖНО
                    st.session_state["ignore_next_calendar_callback"] = True                     
                    st.rerun()

            # ----- Reject -----
            if reject_clicked:
                response = requests.patch(
                    f"{API_URL}/api/applications/{selected_application_id}/status",
                    json={
                        "status": "Canceled",
                        "email": edited_email
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    load_all_applications.clear() # <-- Очищаем кэш
                    st.session_state["application_rejected_message"] = True
                    # NEW: та же логика, что и при найме — предложить
                    # отменить будущие брони кандидата.
                    _schedule_bookings_cancel_prompt(
                        selected_application_id,
                        selected_application["full_name"],
                    )
                    st.rerun()
                else:
                    try:
                        # Пытаемся достать текст ошибки от сервера (наш detail про монопольный режим)
                        detail = response.json().get("detail", "")
                    except Exception:
                        detail = ""
                        
                    if response.status_code == 503:
                        # Если это блокировка базы, показываем её напрямую
                        st.session_state["current_action_message"] = t["system_locked_message"]
                        _handle_stale_data_or_lock() # <-- ДОБАВИТЬ ЭТО
                    elif response.status_code == 404:
                        # Если заявку удалили (устаревшие данные)
                        st.session_state["current_action_message"] = "Заявка не найдена. Возможно, база данных была обновлена другим пользователем."
                        _handle_stale_data_or_lock() # <-- ДОБАВИТЬ ЭТО
                    else:
                        st.session_state["current_action_message"] = f'... (Error: {response.status_code})'
                        
                    st.session_state["current_action_message_type"] = "error"
                    st.rerun()

            # ----- Hire -----
            if hire_clicked or st.session_state.get("force_hire_clicked"):
                force_hire = st.session_state.pop("force_hire_clicked", False)
                
                if not force_hire:
                    # Проверка 1: позиция занята?
                    is_free = True
                    try:
                        positions_list = load_positions(API_URL)
                        pos = next((p for p in positions_list if p["id"] == selected_application["position_id"]), None)
                        if pos:
                            is_free = pos["is_free"]
                    except Exception:
                        pass

                    if not is_free:
                        st.session_state["pending_hire_app_id"] = selected_application_id
                        st.session_state["show_hire_warning"] = True
                        st.rerun()

                    # Проверка 2 (NEW): тот же email уже нанят на другую должность?
                    if same_email_hired_app is not None:
                        st.session_state["pending_same_email_app_id"] = selected_application_id
                        st.session_state["pending_same_email_info"] = {
                            "email": same_email_hired_app["email"],
                            "hired_position": same_email_hired_app["position_name"],
                            "current_position": selected_application["position_name"],
                        }
                        st.session_state["show_same_email_hire_warning"] = True
                        st.rerun()
                        
                # Сам процесс найма (сработает и для обычной кнопки, и для "Всё равно")
                response = requests.patch(
                    f"{API_URL}/api/applications/{selected_application_id}/status",
                    json={"status": "Hired", "email": edited_email, "support_email": support_email},
                    timeout=10
                )

                if response.status_code == 200:
                    load_all_applications.clear() # <-- Очищаем кэш
                    load_positions.clear()         # <-- Очищаем кэш (позиция стала занята)
                    st.session_state["application_hired_message"] = True
                    _schedule_bookings_cancel_prompt(
                        selected_application_id,
                        selected_application["full_name"],
                    )
                    st.rerun()
                else:
                    try:
                        # Пытаемся достать текст ошибки от сервера (наш detail про монопольный режим)
                        detail = response.json().get("detail", "")
                    except Exception:
                        detail = ""
                        
                    if response.status_code == 503:
                        # Если это блокировка базы, показываем её напрямую
                        st.session_state["current_action_message"] = t["system_locked_message"]
                        _handle_stale_data_or_lock() # <-- ДОБАВИТЬ ЭТО
                    elif response.status_code == 404:
                        # Если заявку удалили (устаревшие данные)
                        st.session_state["current_action_message"] = "Заявка не найдена. Возможно, база данных была обновлена другим пользователем."
                        _handle_stale_data_or_lock() # <-- ДОБАВИТЬ ЭТО
                    else:
                        st.session_state["current_action_message"] = f'... (Error: {response.status_code})'
                        
                    st.session_state["current_action_message_type"] = "error"
                    st.rerun()

    except requests.RequestException as e:

        st.error(
            f'{t["request_failed"]}: {e}'
        )

    # =========================================
    # Show current selection (always visible)
    # =========================================
    _bs = st.session_state.get("booking_start")
    _be = st.session_state.get("booking_end")
    
    _sel_b_start = st.session_state.get("selected_booking_start")
    _sel_b_end = st.session_state.get("selected_booking_end")
    _sel_b_name = st.session_state.get("selected_booking_name")

    if _bs and _be:
        # Это если выбран СВОБОДНЫЙ слот
        try:
            bs_dt = datetime.fromisoformat(_bs.replace("Z", "+00:00")).replace(tzinfo=None)
            be_dt = datetime.fromisoformat(_be.replace("Z", "+00:00")).replace(tzinfo=None)
            
            tz_offset = st.session_state.get("user_tz_offset", 0.0)
            bs_dt_local = bs_dt + timedelta(hours=tz_offset)
            be_dt_local = be_dt + timedelta(hours=tz_offset)
            
            if bs_dt_local.date() == be_dt_local.date():
                display_str = f"{bs_dt_local.strftime('%H:%M')} → {be_dt_local.strftime('%H:%M %d.%m.%Y')}"
            else:
                display_str = f"{bs_dt_local.strftime('%H:%M %d.%m.%Y')} → {be_dt_local.strftime('%H:%M %d.%m.%Y')}"
        except Exception:
            display_str = f"{_bs} → {_be}"

        _msg_col, _clear_col = st.columns([6, 1])
        with _msg_col:
            st.success(f"{t['selected_slot']}: {display_str}")
        with _clear_col:
            def _clear_slot():
                st.session_state.pop("booking_start", None)
                st.session_state.pop("booking_end", None)
                st.session_state["calendar_version"] += 1

            st.button("✕", key="clear_slot_btn", on_click=_clear_slot, help=t.get("clear_slot", "Clear selection"))

    elif _sel_b_start and _sel_b_end:
        # Это если выбран ЗАНЯТЫЙ слот (для отмены)
        try:
            bs_dt = datetime.fromisoformat(_sel_b_start.replace("Z", "+00:00")).replace(tzinfo=None)
            be_dt = datetime.fromisoformat(_sel_b_end.replace("Z", "+00:00")).replace(tzinfo=None)
            
            tz_offset = st.session_state.get("user_tz_offset", 0.0)
            bs_dt_local = bs_dt + timedelta(hours=tz_offset)
            be_dt_local = be_dt + timedelta(hours=tz_offset)
            
            if bs_dt_local.date() == be_dt_local.date():
                display_str = f"{bs_dt_local.strftime('%H:%M')} → {be_dt_local.strftime('%H:%M %d.%m.%Y')}"
            else:
                display_str = f"{bs_dt_local.strftime('%H:%M %d.%m.%Y')} → {be_dt_local.strftime('%H:%M %d.%m.%Y')}"
        except Exception:
            display_str = f"{_sel_b_start} → {_sel_b_end}"

        _msg_col, _clear_col = st.columns([6, 1])
        with _msg_col:
            # Используем синий цвет (st.info) для занятого слота
            st.info(f"{t.get('selected_booking', 'Selected booking')}: {display_str} - {_sel_b_name}")
        with _clear_col:
            def _clear_booked_slot():
                st.session_state.pop("selected_booking_uid", None)
                st.session_state.pop("selected_booking_start", None)
                st.session_state.pop("selected_booking_end", None)
                st.session_state.pop("selected_booking_name", None)
                st.session_state["calendar_version"] += 1

            st.button("✕", key="clear_booked_slot_btn", on_click=_clear_booked_slot, help=t.get("clear_slot", "Clear selection"))

    else:
        if st.session_state.get("calendar_expanded", False):
            st.info(t["select_slot_first"])

    # -----------------------------------------------------
    # Support Email
    # -----------------------------------------------------

    support_email = st.text_input(
        t["support_email"],
        key="support_email"
    )

    # -----------------------------------------------------
    # Positions
    # -----------------------------------------------------

    st.subheader(t["positions"])

    try:
        positions = load_positions(API_URL)

        if positions:
            positions_data = []

            for position in positions:
                positions_data.append({
                    t["position"]: position["pos_name"],
                    t["available"]: "✔" if position["is_free"] else ""
                })

            df = pd.DataFrame(positions_data)

            available_column = t["available"]


            # old
            #styled_df = df.style.applymap(

            # actual
            styled_df = df.style.map(    
                lambda value: (
                    "color: green; font-weight: bold; font-size: 24px;"
                    if value == "✔" else ""
                ),
                subset=[available_column]
            )

            st.dataframe(
                styled_df,
                width="stretch",
                hide_index=True
            )

    except requests.RequestException as e:
        st.error(f"Error loading positions: {e}")

    # -----------------------------------------------------
    # Add position
    # -----------------------------------------------------

    # 1. Функция-колбэк. Срабатывает ДО перерисовки страницы,
    # поэтому может безопасно менять значение текстового поля.
    def _add_position_callback():
        pos_name = st.session_state.get("new_position_input", "").strip()

        if not pos_name:
            st.session_state["position_error_message"] = t["position_empty"]
            return

        try:
            response = requests.post(
                f"{API_URL}/api/positions",
                json={
                    "pos_name": pos_name,
                    "is_free": True
                },
                timeout=5
            )

            if response.status_code == 201:
                load_positions.clear() # <-- Очищаем кэш
                st.session_state["position_added_message"] = True
                st.session_state["new_position_input"] = ""   # Очищаем поле
            elif response.status_code == 503:
                # <-- ДОБАВИТЬ ЭТОТ БЛОК
                st.session_state["position_error_message"] = t["system_locked_message"]
            else:
                st.session_state["position_error_message"] = (
                    f'{t["position_add_error"]} '
                    f'Error code: {response.status_code}.'
                )
        except requests.RequestException:
            st.session_state["position_error_message"] = t["request_failed"]

    # 2. Текстовое поле с фиксированным ключом
    st.text_input(
        t["new_position"],
        key="new_position_input"
    )

    # 3. Кнопка вызывает колбэк
    st.button(t["add_position"], on_click=_add_position_callback)

    # 4. Вывод сообщений (после кнопки)
    if "position_error_message" in st.session_state:
        st.error(st.session_state.pop("position_error_message"))

    if st.session_state.pop("position_added_message", False):
        st.success(t["position_added"])

    # -----------------------------------------------------
    # Reset demo
    # -----------------------------------------------------

    is_demo_loading = st.query_params.get("demo_loading") == "1"

    if is_demo_loading:
        st.info(t["DemoData&BookingGeneration"])

    if st.button(t["reset_demo"], disabled=is_demo_loading):
        st.query_params["demo_loading"] = "1"
        st.rerun()

    if is_demo_loading and not st.session_state.get("demo_post_sent"):
        st.session_state["demo_post_sent"] = True
        
        tz_offset = st.session_state.get("user_tz_offset", 0.0)
        
        try:
            with st.spinner(t["DemoData&BookingGeneration"]):
                response = requests.post(
                    f"{API_URL}/api/reset-demo",
                    params={"tz_offset": tz_offset},
                    timeout=90
                )
                
            if response.status_code == 200:
                load_all_applications.clear()
                load_positions.clear()
                load_booked_slots.clear()
                st.session_state["demo_loaded_message"] = True
            elif response.status_code == 503:
                # <-- ЛОВИМ МОНОПОЛЬНЫЙ РЕЖИМ
                try:
                    detail = response.json().get("detail", "Сброс уже выполняется другим пользователем.")
                except Exception:
                    detail = "Сброс уже выполняется другим пользователем."
                st.error(f"⚠️ {detail}")
            else:
                st.error(f'{t["demo_load_error"]} Error code: {response.status_code}.')
                
        except requests.RequestException as e:
            # Если сервер недоступен или таймаут — показываем ошибку
            st.error(f'{t["request_failed"]}: {e}')
            
        finally:
            # В ЛЮБОМ СЛУЧАЕ (успех или ошибка) очищаем флаги, 
            # чтобы кнопка разблокировалась и пользователь мог попробовать снова
            st.session_state.pop("demo_post_sent", None)
            st.query_params.pop("demo_loading", None)
            
        st.rerun()

    if st.session_state.pop("demo_loaded_message", False):
        st.success(t["demo_loaded"])