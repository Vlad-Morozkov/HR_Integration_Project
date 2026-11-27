# План рефакторинга Streamlit и API-клиента

Статус: **предложено; изменения приложения ещё не выполнены**. База анализа — `df20603afe7b9dcfc59a2d56d6442d0c575c8921`, 27 ноября 2026 года. Номера строк относятся только к этой версии. Примеры ниже показывают будущий код и требуют включения в соответствующий небольшой PR.

## 1. Цель и порядок

Сохранить рабочие сценарии Candidate, HR и About, отделить HTTP от отображения, затем извлекать небольшие части интерфейса. Сначала зафиксировать текущее поведение тестами и исправить подтверждённые дефекты отдельными коммитами. Изменение расположения навигации и переработку календаря не совмещать с переносом HTTP-вызовов.

В `frontend.py` найдено **12 прямых HTTP-вызовов**, в `ApiClient` — ещё **3**. Сейчас UI и клиент независимо читают конфигурацию ключа. Все запросы должны проходить через один транспорт, а конфигурация поступать в его конструктор из bootstrap. Клиент не должен импортировать `streamlit`, читать `.env` или обращаться к `st.secrets` при импорте.

## 2. Карта текущего кода

| Текущий участок | Назначение | Предлагаемое место |
|---|---|---|
| [`frontend.py:25–49`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L25-L49) | Настройки подключения и создание клиента | `ui/config.py` из плана 02; `ui/bootstrap.py` создаёт `ApiClient(base_url, api_key)` из проверенной конфигурации |
| [`frontend.py:52–69`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L52-L69) | Три кэшируемые загрузки | `ui/data.py`: только чтение и инвалидирование кэша |
| [`frontend.py:71–127`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L71-L127) | Часовой пояс и язык браузера | `ui/context.py`; существующий `timezone_component` оставить самостоятельным компонентом |
| [`frontend.py:220–304`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L220-L304) | Язык и навигация | `ui/navigation.py` |
| [`frontend.py:313–333`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L313-L333) | Постоянное состояние анкеты | `ui/state.py` |
| [`frontend.py:340–857`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L340-L857) | Анкета, демоданные, список броней кандидата | `ui/views/candidate.py`; затем `ui/components/candidate_bookings.py` |
| [`frontend.py:859–861`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L859-L861) | About уже выделен | Сохранить `ui_about.show_about_page`; перенос необязателен |
| [`frontend.py:872–1000`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L872-L1000) | Отмена броней, сброс устаревшего состояния, ожидание reset | `ui/actions.py`, `ui/components/demo_status.py` |
| [`frontend.py:1037–1458`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L1037-L1458) | Фильтры, редактирование email, выбор заявки | `ui/components/application_table.py` |
| [`frontend.py:1465–1953`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L1465-L1953) | Кнопки действий, предупреждения, отмена связанных броней | `ui/components/hiring_actions.py`, `ui/actions.py` |
| [`frontend.py:1957–2447`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L1957-L2447) | FullCalendar, выбор интервала, создание/отмена брони | `ui/components/interview_calendar.py`; обработчики — в `ui/actions.py` |
| [`frontend.py:2450–2562`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L2450-L2562) | Hire/Reject и force-подтверждение | `ui/actions.py` |
| [`frontend.py:2703–2751`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L2703-L2751) | Добавление должности, сообщения о reset | `ui/components/positions.py`, оболочка `ui/views/hr.py` |
| [`api_client.py:19–89`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/api_client.py#L19-L89) | Три метода и ошибки клиента | Расширить существующий `api_client.py`; новый HTTP-фреймворк пока не нужен |

Не создавать все перечисленные модули пустыми заранее. Извлекать модуль, когда в него переносится законченная ответственность. `frontend.py` постепенно становится точкой сборки; серверные ORM-модели и сервисы в UI не импортировать.

## 3. Первоочередной подтверждённый дефект RU-навигации

В [`frontend.py:304`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L304) `mode` получает внутреннее значение `"Candidate"`, но в строке 340 оно сравнивается с переводом `t["candidate"]`. В [русском словаре](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/translations.py#L227) значение — `"Кандидат"`. Условие ложно, и выполнение попадает в HR-ветку `else`.

**UI-01, отдельный bugfix до крупного переноса:** зафиксировать исходное наблюдение, добавить тест ожидаемого RU Candidate и заменить сравнение на `mode == "Candidate"`. Не переименовывать сохранённые значения `"Candidate"`, `"HR"`, `"About"` и не заменять статус `"Canceled"` на `"Rejected"`.

После выделения views диспетчер может выглядеть так (иллюстрация целевого кода):

```python
def render_selected_view(mode, context, api):
    if mode == "Candidate":
        render_candidate(context, api)
    elif mode == "HR":
        render_hr(context, api)
    elif mode == "About":
        show_about_page(context.translations)
    else:
        raise ValueError("Unknown UI mode")
```

`render_candidate`, `render_hr` и `context` — предлагаемые интерфейсы, которых сейчас нет. Для первого исправления они не требуются: достаточно одного сравнения и регрессионного теста.

## 4. Полная матрица HTTP-вызовов

Сохранить начальные таймауты и реакцию UI при механическом переносе. Их оптимизацию выполнить отдельно после измерения длительности операций. `timeout` в Requests не является гарантированным общим пределом времени всей бизнес-операции.

| Источник | Запрос | Сейчас, секунд | Будущий метод |
|---|---|---:|---|
| `frontend.py:54` | `GET /api/applications` | 10 | `list_applications()` |
| `frontend.py:60` | `GET /api/positions` | 10 | `list_positions()` |
| `frontend.py:66` | `GET /api/interviews/booked-slots` | 10 | `list_booked_slots()` |
| `frontend.py:388` | `GET /api/demo-application?lang=...` | 5 | `get_demo_application(lang)` |
| `frontend.py:435` | `POST /api/initialize-demo` | 15 | `initialize_demo()` |
| `frontend.py:636` | `POST /api/applications` | 5 | `create_application(payload)` |
| `frontend.py:817,967` | `GET /api/system-status` | 2 | `get_system_status()` |
| `frontend.py:948` | `POST /api/reset-demo?tz_offset=...` | 1 | `reset_demo(tz_offset)`; затем отдельное изменение протокола |
| `frontend.py:1918,2326` | `POST /api/interviews/{uid}/cancel` | 10 / 15 | `cancel_interview(uid, timeout=...)` |
| `frontend.py:2405` | `POST /api/interviews` | 15 | `create_interview(payload)` |
| `api_client.py:34` | `PATCH /api/applications/{id}/email` | 10 | Существующий `update_email()` |
| `api_client.py:58` | `PATCH /api/applications/{id}/status` | 10 | Существующий `update_status()` |
| `api_client.py:76` | `POST /api/positions` | 10 | Существующий `create_position()` |

Для каждого метода записать успешный статус и JSON, ошибки, параметры запроса и очистку кэша. `create_application` ожидает 201; `create_position` — 201; `update_email` и `update_status` — 200; интерфейс бронирования сейчас принимает 200 или 201. Не сводить всё к условию `status_code == 200`.

Промежуточный транспорт без глобальной изменяемой HTTP-сессии:

```python
import requests


class ApiClient:
    def __init__(self, base_url: str, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("INTERNAL_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}

    def _request_raw(self, method: str, path: str, *, timeout: float, **kwargs):
        return requests.request(
            method,
            f"{self.base_url}{path}",
            headers=dict(self.headers),
            timeout=timeout,
            **kwargs,
        )

    def list_positions(self) -> list[dict]:
        response = self._request_raw("GET", "/api/positions", timeout=10)
        response.raise_for_status()
        return response.json()
```

Это **частичный пример будущей реализации**: существующие методы и их обработчики остаются до последовательного переноса. Поле `self.headers` сохраняет совместимость с ними; конструктор согласован с планом 02. Не изменять общий словарь заголовков при обработке запроса, в транспорт передаётся его копия. В тестах подменяется `requests.request` или транспорт; реальные запросы не выполняются. `base_url` берётся только из доверенной конфигурации.

Правила дальнейшей унификации ошибок:

- Сначала сохранить `ApiConflictError.detail`, `.code`, `ApiLockedError` и совместимость обработчиков. У `update_email` сейчас все 409 имеют код `EMAIL_CONFLICT`; изменение этого различения — отдельное улучшение.
- Затем ввести `ApiError(status_code, detail, code)` и специализации network/auth/validation. `detail` может быть строкой, словарём или списком ошибок Pydantic; HTML/пустой ответ не должен порождать вторичную ошибку JSON.
- Для бронирования сохранить различие 400 с причиной `past`, 404, 409, 503 и 502. Для найма сохранить `POSITION_OCCUPIED`, а также `force` и `expected_email` без изменения полезной нагрузки.
- UUID заявок и должностей — строки: исправить аннотации `app_id: int` в клиенте/хелперах отдельной маленькой правкой, не преобразовывать UUID в числа.
- Не повторять автоматически POST/PATCH после сетевого таймаута. Пользователь должен увидеть неопределённость результата; последующее чтение состояния и серверный протокол определяют безопасное продолжение.
- Не показывать заголовки, ключ или полный диагностический дамп запроса в UI. Публичный контактный email оставить публичным по требованию владельца.

## 5. Состояние и кэш

Вынести инициализацию и сбросы в функции над `st.session_state`. Сохранить `store_*`, `candidate_form_version`, `editor_version`, `calendar_version`, `selected_row_app_id`, `active_application_id`, выбор брони и одноразовые сообщения. Перенос функции не должен создавать повторную отправку формы при каждом rerun.

Сейчас анкета — набор виджетов и обработчиков; автоматическое превращение в `st.form` меняет момент передачи значений и callbacks. Это отдельная задача, не часть механического извлечения view.

| Событие | Кэш / состояние, которые надо проверить |
|---|---|
| Создана заявка | Очистить applications; очистить поля только после подтверждённого 201 |
| Изменён email | Applications; версия редактора; уведомление один раз |
| Hire | Applications и positions; предложение отменить будущие брони; выбранный кандидат |
| Reject (`Canceled`) | Applications; предложение отмены броней; повторный submit недоступен |
| Создана/отменена бронь | Booked slots и applications; выбранный интервал/UID; версия календаря |
| Reset завершён | Все три кэша; редактор/выбранные заявки/слоты; query parameter ожидания |
| 404/503 после чужого reset | Снять устаревший выбор, убрать недействующие действия, перечитать данные |

На первом шаге сохранить TTL: applications 15 секунд, positions 30, slots 15. Данные кэшировать отдельно от клиента. Дешёвый stateless `ApiClient` допустимо создавать на каждом rerun. Глобальный `st.cache_resource` для изменяемого `requests.Session` вводить только после обоснования thread safety; по умолчанию ресурс доступен разным сессиям. Не использовать новые параметры Streamlit без проверки закреплённой версии.

`st.cache_data` для списков сейчас общий и ключуется URL. Это допустимо только при принятой модели общих демоданных. Если появятся роли или разные наборы данных, авторизационный контекст должен участвовать в разделении кэша; исходный секрет не использовать как отображаемый cache key. Смена настроек/ротация ключа требует очистки кэша и пересоздания клиента.

## 6. Календарь, часовой пояс и demo reset

Выделять календарь после API-клиента и таблицы заявок: у него больше всего связанных ключей состояния. Сначала вынести чистые преобразования событий и интервалов, затем отображение, последними — обработчики. Сохранить ключ компонента `booking_calendar_v{calendar_version}`, блокировку повторного callback, очистку выбора при смене кандидата и `st.rerun()` только после завершённого изменения состояния.

Для timezone проверить UTC, положительный/отрицательный и дробный offset, границу дня, offset в ISO-строке и переход DST. Нынешний offset браузера не описывает все будущие даты; перевод на IANA timezone/`zoneinfo` согласовать с backend отдельным изменением контракта времени. Не «исправлять» только одну сторону преобразования.

Известные дефекты для отдельных задач с failing tests:

1. **UI-02:** `frontend.py:948–990` считает таймаут reset нормальным и трактует `locked=false` как успех. Это не доказывает, что запрос был принят или успешно завершился. После согласования backend ввести `202 + job_id`, состояния pending/running/succeeded/failed и опрос конкретного задания; более простой первоначальный вариант — дождаться результата синхронного reset и явно показать его ошибку. Не смешивать два протокола.
2. **UI-03:** `frontend.py:1915–1932` игнорирует исключения и HTTP-ошибки массовой отмены, затем сообщает об успехе. Новый обработчик собирает успешные/неудачные UID, обновляет календарь и предлагает продолжение только для подтверждённых неудач; uncertain outcome проверяется чтением состояния.
3. **UI-04:** `frontend.py:2363–2373` содержит очистку устаревшего выбора после `st.rerun()`. Перенести нужную очистку до rerun и проверить 404/409 отдельно от 503.

При извлечении `@st.fragment` сохранить stop/полный rerun после завершения и обеспечить остановку опроса при уходе со страницы. Не выполнять повторный reset из poller. Поддержку fallback без fragment сохранить до явного изменения минимальной версии Streamlit.

## 7. Совместимость с прежним планом сайдбара

На Windows найден незакоммиченный `Plan.md` с предложением перенести язык и навигацию в sidebar. Этот план не является выполненным изменением исходников. Сохранить файл и учесть его отдельным UI-коммитом после UI-01 и тестов навигации.

При реализации sidebar использовать внутренние стабильные mode keys и `format_func` для перевода; не менять сохранённое `mode` на локализованный текст. Сохранить единственный language selector с ключом `language_selector`; проверить переключение EN/RU во всех трёх режимах и сохранность введённой анкеты. Строки `frontend.py:344–345` с закомментированным debug-выводом удалить при очистке; не включать их.

## 8. Порядок маленьких PR и приёмка

1. Тест навигации + UI-01. Результат: RU Candidate действительно показывает анкету.
2. Конфигурация клиента через конструктор; существующие три метода остаются совместимыми.
3. Три GET-загрузки → ApiClient; затем по одному перенести create application, demo, booking/cancel. Проверить все 15 мест из матрицы.
4. Выделить `state`, `navigation`, Candidate и оболочку HR. About уже выделен.
5. Выделить HR table/actions, затем calendar и pure time helpers.
6. UI-02–04 отдельными изменениями поведения; sidebar — отдельный визуальный коммит.

Приёмка каждого извлечения: тот же HTTP payload/status mapping, те же widget keys и числа вызовов на клик, те же EN/RU подписи, ввод не теряется на rerun, `force` требует явного клика, сброс/ошибка не создают «успешное» сообщение. Все тесты используют fake API. HTML/FullCalendar/timezone компоненты дополнительно проверить в браузере на тестовом backend: одного AppTest недостаточно.

Откат — revert конкретного UI-коммита; серверные маршруты на этапах извлечения остаются совместимыми. Для нового reset-протокола откат выполняется согласованно с серверным изменением.

## Источники

- [Streamlit: архитектура клиента и сервера](https://docs.streamlit.io/develop/concepts/architecture/architecture).
- [Streamlit: `st.cache_resource`, разделение ресурсов и thread safety](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource).
- [Streamlit: AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
- Проверки и этапы доставки — [05-testing-and-delivery.md](05-testing-and-delivery.md); backend-контракты — [03-backend-and-integrations.md](03-backend-and-integrations.md).
