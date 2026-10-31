import streamlit as st
import requests
import re
import pandas as pd

# added streamlit_calendar
from streamlit_calendar import calendar

from datetime import date, datetime, timedelta


import html
import json
import streamlit.components.v1 as components



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

    components.html(
        f"""
        <div style="
            background-color: #FFF4E5;
            border: 1px solid #F0AD4E;
            border-radius: 8px;
            padding: 12px;
            color: #663C00;
            font-family: sans-serif;
            font-size: 14px;
            line-height: 1.6;
        ">
            {safe_before}<button
                id="copy-email"
                type="button"
                title="{safe_copy_hint}"
                style="
                    border: none;
                    background: transparent;
                    color: #B45309;
                    text-decoration: underline;
                    cursor: pointer;
                    font: inherit;
                    padding: 0 2px;
                "
            >{safe_email}</button>{safe_after}

            <div
                id="copy-status"
                style="font-size: 12px; margin-top: 4px;"
            >{safe_cancel_hint}</div>
        </div>

        <script>
            const emailToCopy = {js_email};
            const copiedMessage = {js_copied};

            document.getElementById("copy-email")
                .addEventListener("click", async () => {{
                    const status =
                        document.getElementById("copy-status");

                    try {{
                        await navigator.clipboard.writeText(emailToCopy);
                        status.textContent = copiedMessage;
                    }} catch (error) {{
                        status.textContent =
                            "Copy unavailable. Please copy the email manually.";
                    }}
                }});
        </script>
        """,
        height=90,
    )




# Local
# API_URL = "http://127.0.0.1:8000" 

# Prod
API_URL = "https://hr-integration-project-swart.vercel.app"


st.set_page_config(
    page_title="HR Hiring System",
    layout="wide"
)


# =========================================================
# LANGUAGE
# =========================================================

LANGUAGES = ["English", "Русский"]

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
        "fill_test_data":        "Заполнить Demo данными",
        "clear_fields":          "Очистить поля",
        "position":              "Должность",
        "full_name":             "ФИО",
        "email":                 "Email",
        "education":             "Образование",
        "experience":            "Опыт работы",
        "birth_date":            "Дата рождения",
        "submit_application":    "Отправить заявку",

        "empty_db":              "База данных пуста. Хотите заполнить demo данными?",
        "success":               "Данные успешно отправлены.",
        "birth_date_error":      "Дата рождения не может быть сегодня или в будущем.",
        "empty_bdate_field":     "Заполните дату рождения.",
        "no_positions":          "Нет доступных вакансий.",
        "connection_error":      "Не удалось подключиться к системе найма.",
        "duplicate_application": "Вы уже подавали заявку на эту должность.",
        "invalid_email":         "Пожалуйста, введите корректный адрес электронной почты.",

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

        "position_empty":        "Название должности не может быть пустым.",
        "position_added":        "Должность успешно добавлена.",
        "position_add_error":    "Не удалось добавить должность.",

        "reset_demo":            "Сбросить и загрузить Demo-данные",

        "demo_loaded":           "Demo-данные успешно загружены.",
        "demo_load_error":       "Не удалось загрузить Demo-данные.",
        "demo_load_error_check_connection":
               "Пожалуйста проверьте соединение и повторите запрос снова.",
        "no_applications":       "Заявки не найдены.",
        "select_one":            "Выберите одну заявку.",
        "select_only_one":       "Пожалуйста, выберите только одну заявку.",
        "candidate_already_hired":"Этот кандидат уже принят на работу",

        "email_help":            "Email кандидата",

        "email_duplicate_active":
            "Этот email {email} уже используется в активной заявке на эту должность.",
        "cancel_email_changes":  "Нажмите Обновить, чтобы отменить изменение email",
        "click_email_to_copy":   "Нажмите, чтобы скопировать",
        "email_copied":          "Email скопирован!",
        "email_updated":         "Email успешно обновлён.",
        "email_update_error":    "Не удалось обновить email.",
        
        #----------
        # HR Mode
        #----------

        # Кнопки
        
        "review":                "Рассмотреть",
        "Interview":             "Собеседовать",
        "hire":                  "Принять на работу",
        "reject":                "Отклонить",

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

            # # -------------------------------------------------
            # # Detect and save changed emails
            # # -------------------------------------------------

            # for index, row in enumerate(edited_data):

            #     original_email = applications[index]["email"]
            #     edited_email = row[t["email"]]

            #     if edited_email != original_email:

            #         edited_email_normalized = str(
            #             edited_email
            #         ).strip().casefold()

            #         duplicate_exists = any(
            #             application["id"] != applications[index]["id"]
            #             and application["position_id"]
            #                 == applications[index]["position_id"]
            #             and application["status"] in ("New", "Hired")
            #             and str(application["email"]).strip().casefold()
            #                 == edited_email_normalized
            #             for application in all_applications
            #         )

            #         if duplicate_exists:
            #             st.session_state["email_duplicate_active"] = (
            #                 applications[index]["id"]
            #             )
                       
            #             # added html clickable form to copy email in notifications
            #             show_duplicate_email_notice(
            #                 t["email_duplicate_active"],
            #                 edited_email,
            #                 t["cancel_email_changes"],
            #                 t["email_copied"],
            #                 t["click_email_to_copy"]
            #             )

            #             break

            #         st.session_state.pop("email_duplicate_active", None)

            #         email_response = requests.patch(

            #             f"{API_URL}/api/applications/"
            #             f"{applications[index]['id']}/email",

            #             json={
            #                 "email": edited_email
            #             },

            #             timeout=5
            #         )

            #         if email_response.status_code == 200:

            #             st.session_state["email_updated_message"] = True
            #             st.rerun()
                    
         
            #         elif email_response.status_code == 409:

            #             st.session_state["email_duplicate_active"] = applications[index]["id"]

            #             detail = email_response.json().get(
            #                 "detail",
            #                 t["email_duplicate_active"]
            #             )

            #             if "already used for an active application" in detail:
            #                 show_duplicate_email_notice(
            #                     t["email_duplicate_active"],
            #                     edited_email,
            #                     t["cancel_email_changes"],
            #                     t["email_copied"],
            #                     t["click_email_to_copy"]
            #                 )
            #             else:
            #                 st.error(detail)


            #         else:
            #             detail = email_response.json().get(
            #                 "detail",
            #                 ""
            #             )

            #             st.error(
            #                 f'{t["email_update_error"]} '
            #                 f'{detail} '
            #                 f'(Error code: {email_response.status_code})'
            #             )

            #         break

            # if st.session_state.pop("email_updated_message", False):
            #     st.success(t["email_updated"])        

            # ---------------------------------------------
            # Find selected rows
            # ---------------------------------------------

            selected_rows = [

                index

                for index, row
                in enumerate(edited_data)

                if row[t["select"]]
            ]


            # ---------------------------------------------
            # Nothing selected
            # ---------------------------------------------

            if len(selected_rows) == 0:

                st.info(t["select_one"])


            # ---------------------------------------------
            # More than one selected
            # ---------------------------------------------

            elif len(selected_rows) > 1:

                st.warning(t["select_only_one"])


            # ---------------------------------------------
            # Exactly one selected
            # ---------------------------------------------

            else:

                selected_index = (
                    selected_rows[0]
                )


                selected_application = (
                    applications[
                        selected_index
                    ]
                )


                selected_application_id = (
                    selected_application[
                        "id"
                    ]
                )

                # Clear any pending selection when the user switches rows
                if st.session_state.get("active_application_id") != selected_application_id:
                    st.session_state["active_application_id"] = selected_application_id
                    st.session_state.pop("booking_start", None)
                    st.session_state.pop("booking_end", None)

                edited_email = (
                    edited_data[
                        selected_index
                    ][t["email"]]
                )


                email_is_valid = bool(
                    edited_email
                    and re.fullmatch(
                        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                        str(edited_email).strip()
                    )
                )

                # -----------------------------------------
                # Candidate status
                # -----------------------------------------

                can_process = (
                    selected_application[
                        "status"
                    ] == "New"
                )


                email_duplicate_for_selected = (
                    st.session_state.get("email_duplicate_active")
                    == selected_application_id
                )


                # -----------------------------------------
                # Actions
                # -----------------------------------------

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # TODO: logic to be added later
                    review_clicked = st.button(
                        t["review"]
                    )

                with col2:
                    interview_clicked = st.button(
                        t["Interview"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                        )
                    )

                with col3:
                    hire_clicked = st.button(
                        t["hire"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                        )
                    )

                    # -----------------------------------------
                    # Check whether candidate is already hired
                    # -----------------------------------------

                    
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


                with col4:
                    reject_clicked = st.button(
                        t["reject"],
                        disabled=(
                            not can_process
                            or not email_is_valid
                            or email_duplicate_for_selected
                        )
                    )


                # -------------------------------------------------
                # Booking calendar (below Hire / Reject)
                # -------------------------------------------------

                calendar_options = {
                    "initialView": "timeGridWeek",
                    "selectable": True,
                    "selectOverlap": False,      # can't select over a booked slot
                    "slotMinTime": "09:00:00",
                    "slotMaxTime": "18:00:00",
                    "slotDuration": "00:30:00",
                    "snapDuration": "00:30:00",
                    "firstDay": 1 if lang == "ru" else 0,   # <-- ADD
                    "validRange": {
                        "start": date.today().isoformat()
                    },                                               # <<< ADD
                    "headerToolbar": {
                        "left": "prev,next today",
                        "center": "title",
                        "right": "timeGridWeek,timeGridDay",
                    },
                    "height": 500,
                    "firstDay": 1 if lang == "ru" else 0,
                }

                # Fetch booked slots from backend (DB is the source of truth)
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

                calendar_events = [
                    {
                        "title": "Booked",
                        "start": slot["start"],
                        "end":   slot["end"],
                        "color": "#e74c3c",
                    }
                    for slot in booked_slots
                ]

                calendar_result = calendar(
                    events=calendar_events,
                    options=calendar_options,
                    key="booking_calendar", # <-- ФИКСИРОВАННЫЙ КЛЮЧ
                )

                # -------------------------------------------------
                # Handle drag-select (multi-slot) → free slots only
                # -------------------------------------------------

                if calendar_result and calendar_result.get("callback") == "select":
                    sel = calendar_result["select"]

                    sel_start = datetime.fromisoformat(
                        sel["start"].replace("Z", "+00:00")
                    )

                    if sel_start.replace(tzinfo=None) < datetime.utcnow():
                        st.warning(
                           t["slot_in_past"]
                            )
                    else:
                        st.session_state["booking_start"] = sel["start"]
                        st.session_state["booking_end"]   = sel["end"]

                # -------------------------------------------------
                # Handle single-click → treat as one 30-min slot
                # -------------------------------------------------

                if calendar_result and calendar_result.get("callback") == "dateClick":
                    date_str = calendar_result["dateClick"]["date"]

                    try:
                        start_dt = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )

                        # Guard: reject past slots
                        if start_dt.replace(tzinfo=None) < datetime.utcnow():
                            st.warning(
                                t["slot_in_past"]
                            )
                            st.stop()

                        end_dt = start_dt + timedelta(minutes=30)

                        # Normalize to FullCalendar's format so string comparisons
                        # with booked_slots are reliable
                        start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                        end_iso   = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

                        # Overlap check against booked (red) slots
                        overlaps_booked = any(
                            start_iso < slot["end"] and end_iso > slot["start"]
                            for slot in booked_slots
                        )

                        if overlaps_booked:
                            st.info(
                                t["slot_already_booked"]
                            )
                        else:
                            st.session_state["booking_start"] = start_iso
                            st.session_state["booking_end"]   = end_iso

                    except Exception as e:
                        st.error(f"Could not parse slot: {e}")

                # -------------------------------------------------
                # Handle clicks on booked events → info only
                # -------------------------------------------------

                if calendar_result and calendar_result.get("callback") == "eventClick":
                    st.info(
                        t["slot_already_booked"]
                    )

                # -------------------------------------------------
                # Show current selection
                # -------------------------------------------------

                if (
                    st.session_state.get("booking_start")
                    and st.session_state.get("booking_end")
                ):
                    st.success(
                        t["selected_slot"] + ": "
                        f"{st.session_state['booking_start']} → "
                        f"{st.session_state['booking_end']}"
                    )
                else:
                    st.info(t["select_slot_first"])
                    # Please select a time slot on the calendar

                # DEBUG — remove this line once you confirm the dict shape
                st.write("DEBUG calendar_result:", calendar_result)

                # -----------------------------------------
                # Interview — book the slot & prepare payload
                # -----------------------------------------

                if interview_clicked:

                    booking_start = st.session_state.get("booking_start")
                    booking_end   = st.session_state.get("booking_end")

                    if not booking_start or not booking_end:
                        st.error(
                            t["select_slot_first"]
                        )
                    else:
                        # 1. Send the payload to YOUR backend
                        interview_payload = {
                            "application_id": selected_application_id,
                            "email":          edited_email,
                            "full_name":      selected_application["full_name"],
                            "booking_start":  booking_start,
                            "booking_end":    booking_end,
                            "support_email":  support_email,
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
                                # Slot is either outside working hours
                                # or already booked in Cal.com
                                st.error(t["slot_unavailable"])
                            elif (
                                resp.status_code == 400
                                and "past" in detail_lower
                            ):
                                st.error(t["slot_in_past"])
                            else:
                                # Unknown error — show raw detail
                                st.error(detail)

                            st.stop()

                        result = resp.json()

                        st.session_state["interview_booking_uid"] = (
                            result.get("booking_uid", "")
                        )

                        # 3. Clear selection & remount calendar
                        st.session_state.pop("booking_start", None)
                        st.session_state.pop("booking_end", None)
                        # st.session_state["calendar_version"] += 1
                        st.session_state["interview_ready_message"] = True
                        st.rerun()

                if st.session_state.pop("interview_ready_message", False):
                    st.success(
                        t["interview_ready"]
                    )

                # -----------------------------------------
                # Reject
                # -----------------------------------------

                if reject_clicked:

                    response = requests.patch(

                        f"{API_URL}/api/applications/"
                        f"{selected_application_id}/status",

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


                # -----------------------------------------
                # Hire
                # -----------------------------------------

                if hire_clicked:

                    response = requests.patch(
                        f"{API_URL}/api/applications/"
                        f"{selected_application_id}/status",
                        json={
                            "status": "Hired",
                            "email": edited_email,
                            "support_email": support_email
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        st.session_state["application_hired_message"] = True
                        st.rerun()

                    else:
                        st.error(
                            f'{t["hire_error"]} '
                            f'Error code: {response.status_code}.'
                        )

        # Display Hire notification after rerun
        if st.session_state.pop("application_hired_message", False):
            st.success(t["application_hired"])

        # Display Reject notification after rerun
        if st.session_state.pop("application_rejected_message", False):
            st.success(t["application_rejected"])

    except requests.RequestException as e:

        st.error(
            f'{t["request_failed"]}: {e}'
        )

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

    # -----------------------------------------------------
    # Reset & Load Demo Data
    # -----------------------------------------------------

    if st.button(t["reset_demo"]):

        response = requests.post(
            f"{API_URL}/api/reset-demo",
            timeout=10
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