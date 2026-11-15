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
        "invalid_email":         "Please enter a valid email address. To restore the previous value, click Refresh.",
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
                "⏳ Demo data is being loaded and booking via Cal.com is being set up. Please wait...",
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
            "A candidate with this email {email} is already hired for «{hired_position}». Do you want to hire them again for «{current_position}»?",
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
        # "education":             "Education", # есть в кандидате выше
        # "experience":            "Experience", # есть в кандидате выше
        "application_date":      "Application Date",
        "status":                "Status",
        "select":                "Select",

        "submit_error":          "Data not submitted. Please try again later. Error code: {code}.",
        "fill_field":            "Fill {field_name}",

        "status_new":            "New",
        "status_hired":          "Hired",
        "status_canceled":       "Canceled",
        "status_all":            "All",   

        "email_conflict_message": "Email has already been changed by another user. The data has been updated from the database. Click Refresh to close this message.",
        "position_occupied_conflict": "⚠️ The position is already occupied by another user. If you still want to hire this candidate, click «Hire anyway».",
        "application_not_found": "Application not found. The database may have been updated.",
        "position_exists": "A position with this name already exists.",                 
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
        "invalid_email":         "Пожалуйста, введите корректный адрес электронной почты. Чтобы восстановить прежнее значение, нажмите «Обновить».",
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
                "⏳ Идёт генерация демо-данных и записей в Cal.com. Пожалуйста, подождите...",        
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
            "Кандидат с этим email {email} уже принят на должность «{hired_position}». Хотите ли принять его повторно на должность «{current_position}»?",
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
        # "education":             "Образование", # есть в кандидате выше
        # "experience":            "Опыт работы", # есть в кандидате выше
        "application_date":      "Дата заявки",
        "status":                "Статус",
        "select":                "Выбрать",

        "submit_error":          "Не удалось отправить данные. Попробуйте позже. Код ошибки: {code}.",
        "fill_field":            "Заполните поле «{field_name}»",

        "status_new":            "Новая",
        "status_hired":          "Принят",
        "status_canceled":       "Отклонена",
        "status_all":            "Все",

        "email_conflict_message":       
"Email уже был изменён другим пользователем. Данные обновлены из базы. Нажмите обновить, чтоб закрыть это сообщение.",
        "position_occupied_conflict":   
"⚠️ С позицией работает другой HR. Если вы всё равно хотите нанять кандидата, нажмите «Принять всё равно».",
        "application_not_found":        "Заявка не найдена. Возможно, база данных была обновлена.",
        "position_exists":              "Должность с таким названием уже существует.",                
    }

}