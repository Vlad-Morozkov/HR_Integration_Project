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
    safe_cancel_hint = html.escape(cancel_hint)
    safe_copy_hint = html.escape(copy_hint)

    js_email = json.dumps(str(email))
    js_copied = json.dumps(copied_message)


# Local
# API_URL = "http://127.0.0.1:8000" 

# Prod
API_URL = "https://hr-integration-project-swart.vercel.app"


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
        "select_booking": "Select",
        "reschedule_booking": "Reschedule",
        "cancel_booking": "Cancel Booking",
        "booking_url_missing": "URL not provided by backend",
        "cancel_booking_for_hired": "Cancel booking for Hired candidate",
        "dismiss": "Dismiss",
        "has_booking_at": "has a booking at",        
     
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
        "candidate_already_hired":"This candidate is already hired",  

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

        # Buttons

        "review":                "Review",
        "Interview":             "Interview",
        "hire":                  "Hire",
        "reject":                "Reject",

        # Calendar

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
        "interview_ready":       "ТЕХНИЧЕСКОЕ Invitation data prepared. Ready for next step.",
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
        "cancel_booking_for_hired": "Отменить запись для нанятого кандидата",
        "dismiss": "Закрыть",
        "has_booking_at": "имеет запись на",
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

        # Email buttons

        "email_help":            "Email кандидата",

        # Email notifs

        "email_duplicate_active":
            "Этот email {email} уже используется в активной заявке на эту должность.",
        "cancel_email_changes":  "Нажмите Обновить, чтобы отменить изменение email",
        "click_email_to_copy":   "Нажмите, чтобы скопировать",
        "email_copied":          "Email скопирован!",
        "email_updated":         "Email успешно обновлён.",
        "email_update_error":    "Не удалось обновить email.",
        
        # Кнопки
        
        "review":                "Рассмотреть",
        "Interview":             "Собеседовать",
        "hire":                  "Принять на работу",
        "reject":                "Отклонить",



        # Calendar

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
        
        "interview_ready":       "ТЕХНИЧЕСКОЕ Invitation data prepared. Ready for next step.",
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
        "status_canceled":       "Отклонена"
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

        response = requests.get(
            f"{API_URL}/api/positions",
            timeout=15
        )

        response.raise_for_status()

        positions = response.json()

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

            available_positions = [
                position
                for position in positions
                if position["is_free"]
            ]

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

                birth_date_invalid = (
                    st.session_state["store_birth_date"] is None
                    or st.session_state["store_birth_date"] >= date.today()
                )

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
                    
                    empty_field = None

                    for field_key, field_name in required_fields.items():

                        if not st.session_state[field_key].strip():
                            empty_field = field_name
                            break

                    if empty_field:

                        st.error(
                            t["fill_field"].format(
                                field_name=empty_field
                            )
                        )

                    elif not re.fullmatch(
                        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                        st.session_state["store_email"].strip()
                    ):

                        st.error(t["invalid_email"])

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
        apps_resp = requests.get(f"{API_URL}/api/applications", timeout=5)
        slots_resp = requests.get(f"{API_URL}/api/interviews/booked-slots", timeout=5)

        if apps_resp.status_code == 200 and slots_resp.status_code == 200:
            all_apps = apps_resp.json()
            all_slots = slots_resp.json()

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
                        valid_candidates[app_id] = f"{app['full_name']} ({app['email']})"
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
                        use_container_width=True,
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

                    final_cancel_url = "#"
                    final_reschedule_url = "#"

                    if len(selected_rows) == 1:
                        final_cancel_url = selected_rows[0].get("cancel_url", "#")
                        final_reschedule_url = selected_rows[0].get("reschedule_url", "#")
                    elif len(selected_rows) > 1:
                        st.warning(t.get("select_only_one", "Please select only one booking at a time."))

                    # Buttons under the table
                    btn_col1, btn_col2 = st.columns(2)
                    
                    with btn_col1:
                        st.link_button(
                            t.get("reschedule_booking", "Reschedule"),
                            url=final_reschedule_url,
                            disabled=(len(selected_rows) != 1 or final_reschedule_url == "#"),
                            use_container_width=True
                        )
                        
                    with btn_col2:
                        st.link_button(
                            t.get("cancel_booking", "Cancel Booking"),
                            url=final_cancel_url,
                            disabled=(len(selected_rows) != 1 or final_cancel_url == "#"),
                            use_container_width=True
                        )
                        
    except requests.RequestException as e:
        st.error(f"Could not load bookings: {e}")    

# =========================================================
# HR MODE
# =========================================================

else:

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
            st.session_state.pop("email_duplicate_active", None)
            st.session_state["editor_version"] = (
                st.session_state.get("editor_version", 0) + 1
            )
            st.rerun()

    with filters_expanded:
        position_filter_input = st.text_input(
            t["position"],
            value=st.session_state["position_filter"]
        )

        email_filter_input = st.text_input(
            t["email"],
            value=st.session_state["email_filter"]
        )

        full_name_filter_input = st.text_input(
            t["full_name"],
            value=st.session_state["full_name_filter"]
        )

        if st.button(t["apply_filters"]):
            st.session_state["position_filter"] = position_filter_input
            st.session_state["email_filter"] = email_filter_input
            st.session_state["full_name_filter"] = full_name_filter_input
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

        response = requests.get(
            f"{API_URL}/api/applications",
            params={
                "position":
                    st.session_state[
                        "position_filter"
                    ],

                "full_name":
                    st.session_state[
                        "full_name_filter"
                    ]
            },
            timeout=10
        )

        
        response.raise_for_status()


        applications = response.json()

        # Filter applications by email
        email_query = st.session_state["email_filter"].strip().casefold()

        if email_query:
            applications = [
                application
                for application in applications
                if email_query in str(
                    application.get("email", "")
                ).casefold()
            ]


        all_applications_response = requests.get(
            f"{API_URL}/api/applications",
            timeout=5
        )
        
        all_applications_response.raise_for_status()

        all_applications = all_applications_response.json()

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


            for application in applications:
                  
                display_data.append({
                    "_app_id": application["id"],  # <-- ДОБАВИТЬ СКРЫТЫЙ ID
                    t["select"]: False,
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
                use_container_width=True,
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
            # Detect and save changed emails
            # -------------------------------------------------

            email_updated_flag = False
            force_ui_reset = False

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

                if edited_email != original_email:
                    edited_email_normalized = str(edited_email).strip().casefold()

                    # Проверка на дубликат в этой же должности
                    duplicate_exists = any(
                        application["id"] != app_id
                        and application["position_id"] == original_app["position_id"]
                        and application["status"] in ("New", "Hired")
                        and str(application["email"]).strip().casefold() == edited_email_normalized
                        for application in all_applications
                    )

                    if duplicate_exists:
                        st.session_state["email_duplicate_active"] = app_id
                        show_duplicate_email_notice(
                            t["email_duplicate_active"],
                            edited_email,
                            t["cancel_email_changes"],
                            t["email_copied"],
                            t["click_email_to_copy"]
                        )
                        force_ui_reset = True
                        break # Выходим из цикла, чтобы не сохранять остальные

                    st.session_state.pop("email_duplicate_active", None)

                    # Сохраняем в базу
                    email_response = requests.patch(
                        f"{API_URL}/api/applications/{app_id}/email",
                        json={"email": edited_email},
                        timeout=5
                    )

                    if email_response.status_code == 200:
                        email_updated_flag = True
                    elif email_response.status_code == 409:
                        st.session_state["email_duplicate_active"] = app_id
                        detail = email_response.json().get("detail", t["email_duplicate_active"])
                        if "already used for an active application" in detail:
                            show_duplicate_email_notice(
                                t["email_duplicate_active"],
                                edited_email,
                                t["cancel_email_changes"],
                                t["email_copied"],
                                t["click_email_to_copy"]
                            )
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
                st.session_state["email_updated_message"] = True
                st.session_state["editor_version"] = (
                    st.session_state.get("editor_version", 0) + 1
                )
                st.rerun()            

            # Показываем отложенное сообщение об успехе
            if st.session_state.pop("email_updated_message", False):
                st.success(t["email_updated"])

                  

            # Look here
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

                # New selection → clear old slot, AUTO-EXPAND calendar
                if st.session_state.get("active_application_id") != selected_application_id:
                    st.session_state["active_application_id"] = selected_application_id
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)
                    st.session_state["calendar_expanded"] = True

                edited_email = edited_data[selected_index][t["email"]]
                email_is_valid = bool(
                    edited_email
                    and re.fullmatch(
                        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                        str(edited_email).strip()
                    )
                )

                can_process = selected_application["status"] == "New"
                email_duplicate_for_selected = (
                    st.session_state.get("email_duplicate_active")
                    == selected_application_id
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

                    same_email_hired = (
                        selected_application["status"] == "New"
                        and any(
                            application["id"] != selected_application_id
                            and application["status"] == "Hired"
                            and str(application["email"]).strip().casefold()
                            == str(edited_email).strip().casefold()
                            for application in all_applications
                        )
                    )

                    if same_email_hired:
                        st.warning(t["candidate_already_hired"])

                with col3:
                    reject_clicked = st.button(
                        t["reject"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                        )
                    )

            # =========================================
            # Calendar toggle + guard
            # =========================================
            if "calendar_version" not in st.session_state:
                st.session_state["calendar_version"] = 0

            def _toggle_cal():
                new_state = not st.session_state.get("calendar_expanded", False)
                st.session_state["calendar_expanded"] = new_state
                if not new_state:
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)
                # Убиваем кэш календаря, чтобы он не вернул старый dateClick
                st.session_state["calendar_version"] += 1

            toggle_label = (
                f"▲ {t.get('collapse_calendar', 'Collapse calendar')}"
                if st.session_state.get("calendar_expanded", False)
                else f"▼ {t.get('expand_calendar', 'Expand calendar')}"
            )

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

            # ГАРД (оставляем)
            if not st.session_state.get("calendar_expanded", False):
                st.session_state.pop("booking_start", None)
                st.session_state.pop("booking_end", None)
            
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
                    "validRange": {
                        "start": date.today().isoformat()
                    },
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
                    booked_resp = requests.get(
                        f"{API_URL}/api/interviews/booked-slots",
                        timeout=5,
                    )
                    booked_resp.raise_for_status()
                    booked_slots = booked_resp.json()
                except requests.RequestException as e:
                    st.warning(f"Could not load booked slots: {e}")
                    booked_slots = []

                # Use no chunks split

                # 1 ver - use no 30 min chunks-------------
                # Build events
                calendar_events = []
                color_palette = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6"]
                app_color_map = {}

                booked_title = t.get("booked", "Booked")
                selected_booking_uid = st.session_state.get("selected_booking_uid")

                for slot in booked_slots:
                    app_id = slot.get("application_id", "")
                    if app_id not in app_color_map:
                        app_color_map[app_id] = color_palette[len(app_color_map) % len(color_palette)]
                    slot_color = app_color_map[app_id]

                    is_selected = (selected_booking_uid == slot["booking_uid"])
                    
                    # Ищем имя кандидата по ID заявки
                    app = next((a for a in all_applications if a["id"] == app_id), None)
                    candidate_name = app["full_name"] if app else booked_title

                    # Pass the slot natively as ONE block (no more 30-min chunks)
                    event = {
                        "id": slot["booking_uid"],
                        "title": candidate_name,  # <-- ТЕПЕРЬ ЗДЕСЬ ИМЯ
                        "start": slot["start"],
                        "end": slot["end"],
                        "backgroundColor": slot_color,
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
                # ver 1 end ----------------------

                # Split bookings into 30-min chunks for nicer display

                # # 3 ver -----------------------
                # # Build events
                # calendar_events = []
                # color_palette = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6"]
                # app_color_map = {}

                # booked_title = t.get("booked", "Booked")
                # selected_booking_uid = st.session_state.get("selected_booking_uid")

                # for slot in booked_slots:
                #     app_id = slot.get("application_id", "")
                #     if app_id not in app_color_map:
                #         app_color_map[app_id] = color_palette[len(app_color_map) % len(color_palette)]
                #     slot_color = app_color_map[app_id]

                #     is_selected = (selected_booking_uid == slot["booking_uid"])

                #     # Pass the slot natively. FullCalendar handles multi-hour blocks perfectly.
                #     event = {
                #         "id": slot["booking_uid"],
                #         "title": booked_title,
                #         "start": slot["start"],
                #         "end": slot["end"],
                #         "backgroundColor": slot_color,  # This replaces "color" for background
                #     }

                #     if is_selected:
                #         # Apply the dark blue frame INLINE - guaranteed to work on any version
                #         event["borderColor"] = "#0B1F5E"
                #         event["borderWidth"] = "3px"
                #         event["textColor"] = "#ffffff" # Keeps text readable on the background

                #     calendar_events.append(event)

                #     # 3 ver end -----------------

                # -----------------------------    
                # 2 ver
                # calendar_events = []
                # color_palette = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6"]
                # app_color_map = {}
                
                # # Берем перевод из словаря с фоллбэком на "Booked"
                # booked_title = t.get("booked", "Booked")                

                # for slot in booked_slots:
                #     app_id = slot.get("application_id", "")
                #     if app_id not in app_color_map:
                #         app_color_map[app_id] = color_palette[len(app_color_map) % len(color_palette)]
                #     slot_color = app_color_map[app_id]

                #     s_str = slot["start"].replace("Z", "+00:00")
                #     e_str = slot["end"].replace("Z", "+00:00")
                #     s_dt = datetime.fromisoformat(s_str)
                #     e_dt = datetime.fromisoformat(e_str)

                #     current = s_dt
                #     is_first = True
                #     while current < e_dt:
                #         next_chunk = current + timedelta(minutes=30)
                #         if next_chunk > e_dt:
                #             next_chunk = e_dt
                #         calendar_events.append({
                #             "id": slot["booking_uid"],    
                #             "title": booked_title if is_first else "",  # <-- ИСПОЛЬЗУЕМ ПЕРЕМЕННУЮ
                #             "start": current.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                #             "end": next_chunk.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                #             "color": slot_color,
                #         })
                #         current = next_chunk
                #         is_first = False

                # # 1. Define your CSS in a variable
                # selected_slot_css = """
                #     .fc-event.selected-booking-side {
                #         border-left: 3px solid #0B1F5E !important;
                #         border-right: 3px solid #0B1F5E !important;
                #     }
                #     .fc-event.selected-booking-top {
                #         border-top: 3px solid #0B1F5E !important;
                #     }
                #     .fc-event.selected-booking-bottom {
                #         border-bottom: 3px solid #0B1F5E !important;
                #     }
                # """

                # # 2. Call the calendar function, passing custom_css correctly
                
                # calendar_result = calendar(
                #     events=calendar_events,
                #     options=calendar_options,
                #     # custom_css=selected_slot_css, # use with # 1.Define your CSS in a variable above
                #     key=f"booking_calendar_v{st.session_state['calendar_version']}",  # <--- ВАЖНО
                # )
                # # 2 ver end -------------------------

                # ----- Handle drag-select -----
                if calendar_result and calendar_result.get("callback") == "select":
                    sel = calendar_result["select"]
                    sel_start = datetime.fromisoformat(sel["start"].replace("Z", "+00:00"))
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
                            try:
                                detail = cancel_response.json().get(
                                    "detail",
                                    cancel_response.text
                                )
                            except Exception:
                                detail = cancel_response.text[:300]

                            st.error(f"Cancellation failed: {detail}")

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
                        st.error(f"{t['request_failed']}: {e}")
                        st.stop()

                    if resp.status_code not in (200, 201):
                        try:
                            detail = resp.json().get("detail", resp.text)
                        except Exception:
                            detail = resp.text[:300]

                        detail_lower = str(detail).lower()
                        if resp.status_code == 409:
                            st.error(t["slot_unavailable"])
                        elif resp.status_code == 400 and "past" in detail_lower:
                            st.error(t["slot_in_past"])
                        else:
                            st.error(detail)

                        st.stop()

                    result = resp.json()
                    st.session_state["interview_booking_uid"] = result.get("booking_uid", "")
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)
                    st.session_state["interview_ready_message"] = True
                    st.session_state["calendar_version"] += 1  # <--- ВАЖНО
                    st.rerun()

            if st.session_state.pop("interview_ready_message", False):
                st.success(t["interview_ready"])
            
            if st.session_state.pop("booking_cancelled_message", False):
                st.success(
                    t.get("booking_cancelled", "Interview booking cancelled successfully.")
                )

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
                    st.session_state["application_rejected_message"] = True
                    st.rerun()
                else:
                    st.error(
                        f'{t["reject_error"]} '
                        f'Error code: {response.status_code}.'
                    )

            # ----- Hire -----
            if hire_clicked:
                response = requests.patch(
                    f"{API_URL}/api/applications/{selected_application_id}/status",
                    json={
                        "status": "Hired",
                        "email": edited_email,
                        "support_email": support_email
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    st.session_state["application_hired_message"] = True
                    
                    # Ищем бронь этого кандидата
                    candidate_booking = next(
                        (s for s in booked_slots if s.get("application_id") == selected_application_id), 
                        None
                    )
                    
                    if candidate_booking:
                        # Сохраняем данные брони, чтобы показать предупреждение после перезагрузки
                        st.session_state["hired_booking_to_cancel"] = {
                            "name": selected_application["full_name"],
                            "booking_uid": candidate_booking["booking_uid"],
                            "start": candidate_booking["start"],
                            "end": candidate_booking["end"]
                        }
                        
                    st.rerun()
                else:
                    st.error(
                        f'{t["hire_error"]} '
                        f'Error code: {response.status_code}.'
                    )

        # Display Hire notification after rerun
        if st.session_state.pop("application_hired_message", False):
            st.success(t["application_hired"])

        # Display the Cancel Booking prompt for the hired candidate
        if "hired_booking_to_cancel" in st.session_state:
            booking_info = st.session_state["hired_booking_to_cancel"]
            
            # Форматируем время для уведомления
            try:
                bs_dt = datetime.fromisoformat(booking_info["start"].replace("Z", "+00:00")).replace(tzinfo=None)
                tz_offset = st.session_state.get("user_tz_offset", 0.0)
                bs_dt_local = bs_dt + timedelta(hours=tz_offset)
                time_str = bs_dt_local.strftime('%H:%M %d.%m.%Y')
            except Exception:
                time_str = "scheduled time"

            # Само уведомление
            st.warning(f"⚠️ **{booking_info['name']}** has a booking at **{time_str}**. Do you need to cancel it?")
            
            col_btn, col_empty = st.columns([1, 1])
            with col_btn:
                if st.button(t.get("cancel_booking_for_hired", "Cancel booking for Hired candidate"), type="primary"):
                    # Отправляем запрос на отмену
                    cancel_resp = requests.post(
                        f"{API_URL}/api/interviews/{booking_info['booking_uid']}/cancel",
                        timeout=10
                    )
                    
                    if cancel_resp.status_code == 200:
                        st.success("Booking cancelled successfully.")
                        # Удаляем уведомление
                        del st.session_state["hired_booking_to_cancel"]
                        st.session_state["calendar_version"] += 1  # Обновляем календарь
                        st.rerun()
                    else:
                        st.error("Failed to cancel the booking. Please try again.")
                        
            # Добавляем кнопку, чтобы можно было просто закрыть уведомление (если не нужно отменять)
            with col_empty:
                if st.button(t.get("dismiss", "Dismiss")):
                    del st.session_state["hired_booking_to_cancel"]
                    st.rerun()

        # Display Reject notification after rerun
        if st.session_state.pop("application_rejected_message", False):
            st.success(t["application_rejected"])

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
        positions_response = requests.get(
            f"{API_URL}/api/positions",
            timeout=5
        )

        positions_response.raise_for_status()
        positions = positions_response.json()

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
                use_container_width=True,
                hide_index=True
            )

    except requests.RequestException as e:
        st.error(f"Error loading positions: {e}")

    # -----------------------------------------------------
    # Add position
    # -----------------------------------------------------

    new_position = st.text_input(
        t["new_position"]
    )

    if st.button(t["add_position"]):
        if not new_position.strip():
            st.warning(t["position_empty"])
        else:
            try:
                response = requests.post(
                    f"{API_URL}/api/positions",
                    json={
                        "pos_name": new_position.strip(),
                        "is_free": True
                    },
                    timeout=5
                )

                if response.status_code == 201:
                    st.session_state["position_added_message"] = True
                    st.rerun()
                else:
                    st.error(
                        f'{t["position_add_error"]} '
                        f'Error code: {response.status_code}.'
                    )

            except requests.RequestException:
                st.error(t["request_failed"])

    if st.session_state.pop("position_added_message", False):
        st.success(t["position_added"])

    if st.button(t["reset_demo"]):
        
        # Get the browser-detected timezone offset
        tz_offset = st.session_state.get("user_tz_offset", 0.0)
        
        with st.spinner(t["DemoData&BookingGeneration"]):
            response = requests.post(
                f"{API_URL}/api/reset-demo",
                params={"tz_offset": tz_offset},  # <-- Передаем сдвиг
                timeout=90
            )

        if response.status_code == 200:

            st.session_state["demo_loaded_message"] = True
            st.rerun()

        else:
            st.error(
                f'{t["demo_load_error"]} '
                f'Error code: {response.status_code}.'
            ) 
    if st.session_state.pop("demo_loaded_message", False):
        st.success(t["demo_loaded"])