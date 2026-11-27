# 03. Backend, база данных и внешние интеграции

База анализа: [main @ df20603](https://github.com/Vlad-Morozkov/HR_Integration_Project/tree/df20603afe7b9dcfc59a2d56d6442d0c575c8921), проверено 27.11.2026. Номера строк относятся к этому коммиту, а не к будущим файлам. Это план; приведённые фрагменты ещё не реализованы.

## 1. Порядок и границы изменений

Сначала выделить существующие зависимости и сохранить HTTP-контракт. Затем отдельными изменениями исправлять подтверждённые ошибки. Обозначения ниже:

- **E — extraction:** перемещение кода с сохранением URL, JSON-полей, HTTP-статусов, действующих правил и побочных эффектов.
- **B — behavior:** изменение поведения, для которого сначала нужен воспроизводящий тест и явно описанный новый результат.
- **S — scale:** дополнительный механизм при переходе от одного процесса к нескольким или при необходимости гарантированного восстановления.

Тест существующего поведения не означает, что ошибка становится обязательным контрактом навсегда: после отдельного исправления меняется и ожидаемый результат теста. Обновление SQLAlchemy, переход на async ORM и смену схемы API не объединять с переносом модулей.

## 2. Точная карта переноса

| Текущее место | Целевое место | Содержание и граница |
|---|---|---|
| [main.py:374–400](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L374-L400), engine / SessionLocal / create_all | `app/database.py`, `alembic/` | Сначала вынести engine и factory; автоматическое DDL заменить отдельным шагом миграции. |
| [main.py:453–459](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L453-L459), get_db | `app/database.py` | Одна Session на запрос; закрытие в finally; транзакцию завершает сервис. |
| [main.py:84–86, 215–238, 466–552, 620–628](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L466-L552) | `app/schemas.py` | Pydantic DTO и существующая валидация; новые ограничения отдельно. |
| [models.py:6–46](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/models.py#L6-L46) | `app/models.py` | Перенос без переименования таблиц, колонок и UUID. Корневой models.py временно реэкспортирует типы. |
| [main.py:720–1091](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L720-L1091), create_application / update_application_status / update_application_email | `routers/applications.py`, `services/applications.py`, `services/hiring.py`, `repositories/applications.py` внутри app | HTTP-преобразование → бизнес-операция → конкретные запросы SQLAlchemy. |
| [main.py:1774–1872](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L1774-L1872), positions / applications reads | `app/routers/positions.py`, `app/routers/applications.py`, repositories | Сохранить фильтры ilike и вычисляемое position_name. |
| [main.py:555–598](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L555-L598), send_email / normalize_email | `app/integrations/email.py`, `app/normalization.py` | SMTP отдельно от решений о найме; нормализация одна для create/update/backfill. |
| [main.py:103–209](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L103-L209), parse / cancel / prune | `app/time_utils.py`, `app/integrations/calcom.py`, `app/services/retention.py` | Парсинг, HTTP-транспорт и удаление данных — разные обязанности. |
| [main.py:1097–1342](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L1097-L1342), interviews | `app/routers/interviews.py`, `app/services/interviews.py` | Координация local/remote операций и компенсации; клиент Cal.com не коммитит БД. |
| [main.py:634–714](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L634-L714), calcom_webhook | `app/routers/webhooks.py`, `app/services/webhooks.py` | Отдельная HMAC-аутентификация, исходные байты тела, обновление UID. |
| [main.py:245–364, 1348–1754](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L1348-L1754), demo | `app/demo_data.py`, `app/services/demo.py`, `app/routers/demo.py` | Данные примеров, расписание, destructive reset; HTTP и SQL отделяются от планирования. |
| [main.py:79, 420–447, 1569–1580, 1752–1754](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L420-L447), SYSTEM_LOCKED / get_system_status | `app/services/maintenance.py`, `app/routers/system.py` | E: инкапсуляция флага и сохранение /api/system-status; B: атомарный общий допуск к изменениям; S: координация процессов. |

Названия внутри app относительные к корню проекта. Не создавать универсальный `BaseRepository[T]`: достаточно функций `find_active_duplicate`, `list_applications`, `claim_position`. Простые чтения могут остаться прямо в небольшом router до появления реальной потребности выделять их.

## 3. Что сохранять и где спецификация расходится с кодом

1. `New → Hired` и `New → Canceled`; повторная обработка заявки в конечном статусе — 409. Строка статуса именно `Canceled`.
2. Без `force` занятая позиция запрещает найм с `POSITION_OCCUPIED`. При `force=True` текущий API разрешает его; правило «у позиции может быть только один Hired» сейчас не действует.
3. `Application.status` и `Position.is_free` при найме меняются одной локальной транзакцией. Отказ не освобождает позицию.
4. Активный дубль — нормализованные email + position_id при статусах New/Hired; история Canceled не мешает повторной подаче.
5. Email после решения направляется на `request.email`, а не автоматически на сохранённый адрес заявки. Замена источника адреса — B с изменением контракта.
6. Ошибка SMTP не отменяет уже сохранённый статус; поля `candidate_email_sent` и, для Hired, `support_email_sent` должны отражать результат.
7. `expected_email` необязателен. Когда задан, несовпадение даёт `EMAIL_CONFLICT`; в E не делать его обязательным.
8. Сохранить существующие API response_model и сообщения конфликтов, пока frontend зависит от них. Изменения error envelope выполнять согласованно с API-клиентом.
9. В моделях время хранится как naive UTC. Сначала сохранить эту договорённость; переход к timezone-aware колонкам потребует отдельной миграции.
10. `initialize-demo` прекращает работу, если есть хотя бы одна Position; `reset-demo` удаляет Interviews, Applications, Positions и создаёт новые.
11. В текущем `APPLICATION_DEMO_COLLECTION` **10 заявок: 5 EN + 5 RU**. Старый TechRev.md описывает шесть. Документацию и тесты строить по проверенному коду.
12. В текущем models.py нет уникального индекса для активного дубля и нет unique для pos_name. Обработчик IntegrityError сам по себе этих гарантий не создаёт.
13. TechRev.md требует прошлую дату рождения и непустую должность, но backend не выполняет эти проверки полностью. Это B, а не неожиданное ужесточение при перемещении Pydantic-моделей.
14. Backend проверяет существование позиции при подаче, но не её свободность; проверяет существование заявки при бронировании, но не её статус. Добавлять ограничения только как отдельное принятое правило.

## 4. E: выделение приложения и роутеров

Сохранить совместимость с командой запуска `uvicorn main:app`: корневой main.py временно содержит импорт фабрики и `app = create_app()`. Фабрика собирает зависимости, middleware и роутеры; импорт моделей не создаёт таблицы и не обращается к внешним сервисам.

**Предлагаемый каркас `app/factory.py`, согласованный с [02](02-configuration-and-secrets.md):** в нём показана auth-проверка при запуске и подключение всех групп маршрутов. Реализация текущих middleware и освобождения инфраструктурных ресурсов опущена для краткости; этот фрагмент нельзя использовать как полную замену main.py без их переноса.

~~~python
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from app.config import get_auth_settings
from app.security import verify_api_key
from app.routers import applications, demo, interviews, positions, system, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_auth_settings()  # fail fast, до обслуживания запросов
    yield
    # При подключении инфраструктуры здесь освобождаются её ресурсы.

def create_app() -> FastAPI:
    app = FastAPI(
        title="HR Hiring System API",
        version="1.1.0",
        lifespan=lifespan,
    )
    # Обязательный шаг реализации: перенести существующие CORS и maintenance
    # middleware из main.py:411–435; их настройка в этом фрагменте опущена.
    protected = APIRouter(dependencies=[Depends(verify_api_key)])
    for router in (
        applications.router, positions.router, interviews.router,
        demo.router, system.router,
    ):
        protected.include_router(router)
    app.include_router(protected, prefix="/api")
    app.include_router(webhooks.router, prefix="/api/webhooks")
    return app
~~~

В роутерах пути уже относительные: `/applications`, `/positions`, в system.router — `/system-status`, в demo.router — `/initialize-demo`, `/reset-demo`, `/demo-application`, а у webhook — `/calcom`; иначе получится двойной /api. Не ставить API-key dependency глобально на FastAPI: Cal.com отправляет HMAC, а не внутренний ключ. Проверить сохранение всех 15 маршрутов и отсутствие дублирующей регистрации.

На P3 существующий schema-init лишь изолировать и сохранить безопасный сценарий запуска. Удалить DDL при импорте/startup окончательно на P9, когда подготовлен `alembic upgrade head`; не оставлять промежуточный коммит, который больше не умеет подготовить новую БД. TestClient использовать как context manager, чтобы проверка lifespan действительно выполнялась.

[FastAPI APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/) описывает подключение routers и dependencies. [Lifespan](https://fastapi.tiangolo.com/advanced/events/) подходит для открытия/закрытия инфраструктуры. Миграции выполнять отдельной deployment-командой, а не каждым worker при startup.

## 5. Session и транзакции

**E:** `get_db` в `app/database.py` создаёт новую Session, передаёт её сервису, закрывает в finally. Repository выполняет SQL и при необходимости flush; **не вызывает commit/rollback**. Сервис владеет транзакцией бизнес-операции. DTO для ответа собирать внутри транзакции, чтобы не обращаться к expired ORM-объектам после закрытия Session.

SQLAlchemy автоматически начинает транзакцию при первом запросе. Поэтому нельзя сначала сделать db.get/query в router, а затем без проверки вызвать `with db.begin()` в service. Выбрать один вариант: новая нетронутая Session передаётся сервису, который первым делом открывает begin; либо сохранить явные commit/rollback во время E. Не маскировать ошибку `begin_nested()`: SAVEPOINT не исправляет неясное владение внешней транзакцией. [SQLAlchemy Session](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)

**B: эскиз атомарной обработки статуса; исключения ниже — предлагаемые доменные типы, отображаемые router в прежние 404/409/400.** `db` — свежая Session без предыдущих SELECT; `DecisionResult` — неизменяемый DTO. Опущены определения типов и отправка писем.

~~~python
from sqlalchemy import update

def apply_decision(db, app_id, target, force=False):
    if target not in {"Hired", "Canceled"}:
        raise InvalidStatus()
    with db.begin():
        application = db.get(Application, app_id)
        if application is None:
            raise ApplicationNotFound()
        if application.status != "New":
            raise ApplicationAlreadyProcessed()

        result = DecisionResult(app_id, target, application.full_name)
        changed = db.execute(
            update(Application)
            .where(Application.id == app_id, Application.status == "New")
            .values(status=target)
            .execution_options(synchronize_session=False)
        )
        if changed.rowcount != 1:
            raise ApplicationAlreadyProcessed()

        if target == "Hired":
            position = db.get(Position, application.position_id)
            if position is None:
                raise PositionNotFound()
            claim = update(Position).where(Position.id == position.id)
            if not force:
                claim = claim.where(Position.is_free.is_(True))
            claimed = db.execute(
                claim.values(is_free=False)
                .execution_options(synchronize_session=False)
            )
            if claimed.rowcount != 1:
                raise PositionOccupied()
    return result
~~~

Ошибка захвата позиции откатывает и уже выполненный UPDATE заявки. После успешного выхода из begin сервис уведомлений отправляет письма; его отказ не превращается в фиктивную отмену решения. Для обязательной доставки позднее добавить transactional outbox; обычный BackgroundTasks сам по себе не обеспечивает доставку после падения процесса.

Условные UPDATE устраняют read-then-write race; тестировать две конкурирующие Session. PostgreSQL row locks можно использовать как альтернативу с единым порядком блокировок. SQLite не получает эквивалентную защиту от `FOR UPDATE`: нужен действительно проверенный условный UPDATE и отдельная политика обработки database locked. Ограниченный повтор локальной транзакции допустим только **до любых внешних side effects**. Весь use case с SMTP/Cal.com вслепую не повторять.

Для email-edit использовать UPDATE с условием по `expected_email`, если он задан; rowcount=0 различать как отсутствующую заявку/конфликт. Также проверять active duplicate при смене email и полагаться на уникальный индекс как конечную защиту от конкурентной записи.

## 6. B: миграции и ограничения

1. Зафиксировать фактические версии Python, SQLAlchemy, драйверов, SQLite/PostgreSQL; requirements.txt сейчас не задаёт воспроизводимый набор. Не менять их одновременно с E.
2. На копиях обеих БД сравнить реальную схему с models.py, проверить FK, отсутствующие parent rows, пустые названия, активные дубликаты. Список нарушений — отчёт, а не автоматическое удаление заявок.
3. Добавить Alembic с `target_metadata = Base.metadata`. Начальная revision описывает исходную схему, новая БД проходит `upgrade head`.
4. Для существующей БД использовать stamp baseline **только после** проверки соответствия baseline; stamp не создаёт таблиц и не исправляет расхождения.
5. Нормализовать существующие email той же Python-функцией, что применяется в create/update. Разрешить выявленные конфликты до создания уникального индекса.
6. Добавить частичный unique-index для active email + position. Canceled-история должна оставаться вне индекса.
7. Сначала применить миграцию на копии, проверить данные и новый код, затем выполнить контролируемый выпуск с резервной копией и остановкой writers.
8. Убрать `Base.metadata.create_all` при импорте. Проверить запуск после `alembic upgrade head` и понятную ошибку при устаревшей схеме.
9. Обратное снятие индекса не восстанавливает нормализованные/исправленные данные; восстановление — из проверенной копии либо отдельной обратимой data migration.

**Предлагаемое описание индекса в metadata; создать его должна миграция:**

~~~python
from sqlalchemy import Index

active = Application.status.in_(["New", "Hired"])
Index(
    "uq_applications_active_email_position",
    Application.email,
    Application.position_id,
    unique=True,
    sqlite_where=active,
    postgresql_where=active,
)
~~~

Предпосылка этого варианта: все значения email уже канонизированы и каждый путь записи, включая demo/скрипты, использует одну функцию. Если требуется защищать и произвольные внешние SQL-вставки, отдельно проектировать нормализованную колонку/выражение и проверить Unicode/collation: Python lower и lower БД нельзя молча считать одинаковыми. Не вводить unique(position_id WHERE status='Hired'): он изменит смысл force.

Для SQLite включение FK требует настройки соединений; сначала проверить имеющиеся данные и тесты, поскольку прежде допустимые orphan rows начнут отклоняться. Настройки транзакций sqlite3 зависят от версии Python. [SQLite dialect](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)

Alembic autogenerate выдаёт заготовку, которую нужно прочесть: data backfill и все особенности partial index не считать автоматически проверенными. [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

## 7. E → B: Cal.com client и бронирование

**E:** все requests к Cal.com из cancel/create/demo направить в один `CalComClient`. Он получает настройки и HTTP-транспорт извне, задаёт существующий `cal-api-version: 2024-08-13`, явные таймауты и проверяет HTTP/JSON. Версию API в этом переносе не обновлять. `app/services/interviews.py` управляет последовательностью и БД; клиент ничего не знает о Session.

Сначала сохранить нынешнее разбиение на 30 минут, первый UID в ответе и режимы HTTP-ошибок. Затем отдельными B-изменениями закрыть следующие случаи:

| Случай | Сейчас | Целевой проверяемый результат |
|---|---|---|
| end ≤ start | Пустой набор chunks может завершиться 201 с пустым UID | До внешних вызовов отклонить некорректный диапазон согласованным 4xx. |
| Последний кусок короче 30 минут | Локальный end может не совпасть с фактической длиной event type | Проверить длительность выбранного Cal.com event type; требовать целые слоты либо использовать поддержанный provider API. |
| Ответ 2xx, но JSON/uid отсутствует | Возможны некорректная запись и исключение | Ошибка протокола; сохранить неопределённый результат и компенсировать известные UID. |
| Создано несколько chunks, затем отказ | Отмена предыдущих UID best effort | Учитывать результат каждой отмены; запись unresolved operations вместо сообщения «полностью отменено». |
| Read timeout при POST | Провайдер мог создать запись, UID не получен | Состояние unknown; сверка с провайдером/вебхуком перед повтором. |
| Remote success, local commit failed | Сейчас компенсации этого пути нет | Rollback local, компенсация известных UID, сохранение неустранённых расхождений. |
| Повтор пользователя после timeout | Возможны повторные remote side effects | Локальный operation_id и проверка результата до повторного POST. |

[Cal.com create booking](https://cal.com/docs/api-reference/v2/bookings/create-a-booking) не даёт основания обещать поддержку произвольного Idempotency-Key. Не добавлять автоматический retry POST как «исправление надёжности». Собственный operation_id полезен для корреляции, но без подтверждённой поддержки/сверки у провайдера не превращает операцию в exactly-once.

**B: схема координации без длинной SQL-транзакции вокруг HTTP:**

1. В короткой Session прочитать заявку и собрать неизменяемые входные данные, затем завершить эту транзакцию.
2. Создать chunks через CalComClient; записывать подтверждённые UID и неопределённые ответы.
3. В новой короткой транзакции повторно проверить, что заявка существует, и сохранить все Interview.
4. Если local commit не выполнен, попытаться отменить каждый подтверждённый UID; отсутствие UID не означает отсутствия remote booking.
5. До снятия maintenance gate завершить локальную фиксацию результата/ошибки. Не допускать reset между чтением заявки и записью chunks.
6. Для восстановления после рестарта добавить отдельный небольшой журнал integration_operations в той же БД: operation_id, этап, known UID, тип ошибки, timestamps. Это отдельная additive migration, а не изменение существующих Interview.status без API-плана.

Компенсация сама может отказать, а отмена не возвращает уже отправленное провайдером письмо. Нужен процесс сверки незавершённых операций. Для пет-проекта достаточно явного статуса и команды повторной сверки; очередь и отдельный сервис не обязательны. [Compensating transaction](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)

## 8. Webhook и время

**E:** HMAC вычислять по `await request.body()` до декодирования JSON; проверку `X-Cal-Signature-256` оставить с compare_digest. Несовпадение — 401; некорректный JSON — 400. Не пересобирать JSON перед проверкой подписи. Отсутствующий webhook secret не должен разрешать запросы.

Сохранить сопоставление rescheduleUid → текущая запись → новый uid. Не потерять booked-slots start/end и cancel/reschedule URLs после переноса.

**B: отдельные исправления:**

- В main.py:696–697 сейчас timezone просто отбрасывается. Перевести значение в UTC и лишь затем убрать tzinfo для совместимости с текущими колонками.
- Согласовать единый parser для create и webhook; протестировать Z, +05:00, отрицательный offset, дробные секунды, границу суток. Вопрос naive input решить явно.
- Сейчас исключение reschedule логируется, но возвращается 200. Для временного сбоя БД не подтверждать обработку как успешную; сохранить событие либо вернуть выбранный retriable статус, проверив политику доставки Cal.com.
- Повтор cancel/reschedule не должен повторно менять итог или порождать ошибку unique UID. Для переставленных по времени событий предусмотреть проверку актуального состояния/сверку, а не только дедупликацию тела.
- Sync SQLAlchemy внутри async webhook блокирует event loop. После чтения и проверки тела передавать синхронный обработчик в threadpool; Session создавать и закрывать внутри этого обработчика. Не передавать одну Session параллельным задачам.
- Обычные sync routers с requests/smtplib сохранить как `def`; механическая замена на `async def` не делает requests неблокирующим. [FastAPI async](https://fastapi.tiangolo.com/async/)

**Предлагаемый фрагмент исправления времени; принятие naive input здесь намеренно запрещено и требует отдельного B-теста:**

~~~python
from datetime import datetime, timezone

def parse_provider_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Provider timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)
~~~

## 9. Demo reset, блокировка и retention

**Подтверждённые ограничения:** SYSTEM_LOCKED — bool одного процесса; check/set не защищён mutex, проверки middleware уже недостаточно для начавшихся запросов. Второй worker имеет собственный флаг. Reset исключён из общего middleware, поэтому конкурентные reset также требуют атомарного допуска. Webhook POST сейчас блокируется 503 во время reset.

**E:** спрятать флаг за `app/services/maintenance.py` без обещания новой гарантии. Сохранить /api/system-status и сброс флага в finally.

**B, минимальный рабочий вариант для одного процесса:** общий lock/gate, который все изменяющие use cases берут атомарно до чтения/записи и освобождают в finally. Один `threading.Lock` с неблокирующим acquire может сериализовать все writes: это просто и допустимо для небольшого демо, но увеличивает частоту 503 во время долгого Cal.com запроса. Middleware остаётся быстрым индикатором, не единственным механизмом. Статус maintenance держать отдельно от краткой занятости writer; GET system-status не должен ждать lock. Lock должен покрывать также initialize-demo, webhook, создание позиции, email-edit и retention.

Если требуется параллельность обычных записей, реализовать gate «несколько обычных операций / один reset» с проверкой active writer count под одним mutex. Не писать самодельный read/write lock без concurrency-тестов. Сначала достаточно сериализованного варианта.

**S:** перед несколькими workers перейти к общей координации через PostgreSQL/общий backend и проверить потерю владельца, restart и stale lease. Простое перенесение bool в app.state или Redis GET/SET не решает атомарность. До этого deployment явно ограничить одним worker/экземпляром.

**B: сохранность local/remote данных:**

- `prune_old_interviews` удаляет запись независимо от результата cancel. При отказе сохранять UID и pending cleanup; считать это изменением поведения, с тестом.
- Текущая политика оставляет последние 20 **строк chunks**, сортируя по created_at, а не 20 встреч или только прошедшие события. Она может отменять будущие встречи. Отдельно принять retention-policy; не менять её случайно при выделении сервиса.
- Reset сначала отменяет remote bookings, затем удаляет локальные данные. SQL rollback не восстанавливает отменённые встречи; не обещать пользователю «полный откат».
- При неуспешной отмене остановить destructive reset либо сохранить все unresolved UID в журнал до удаления строк. Выбор — явная B-политика; рекомендуемый безопасный первый вариант: остановить reset с частичным результатом и предложить повторную сверку.
- `generate_demo_interviews` сейчас использует другой путь отправки и сохраняет частичные chunks. Подключить тот же coordinator, что у create_interview, с понятным отчётом created/failed/unknown.
- Подмена `example.com → gmail.com` в main.py:1468 может отправлять настоящие приглашения посторонним адресатам. Убрать её отдельным B-исправлением; для demo использовать fake provider, а реальную отправку разрешать только на контролируемые тестовые адреса.
- `int(tz_offset)` в main.py:1522 теряет дробную часть. На первом исправлении поддержать точный offset, затем при необходимости перейти к IANA zone для DST; это изменение расчёта расписания с тестами.
- Timeout=1 на стороне frontend не доказывает, что reset стартовал/завершился. Координировать изменение reset API с документом frontend; future job_id/202 — отдельное контрактное изменение.
- Webhook во время reset нельзя просто подтвердить и потерять. Либо фиксировать durable inbox до 2xx, либо возвращать временный отказ и иметь проверенный механизм повторной доставки/сверки.

## 10. Приёмка по этапам

| Изменение | Обязательная проверка | Что даёт основание перейти дальше |
|---|---|---|
| Schemas / dependencies / routers | Контракт всех URL, методы, ключи JSON, auth/webhook distinction; существующие validator tests | API ведёт себя одинаково при fake SMTP/Cal.com и временной БД. |
| Hiring / repositories | New→Hired/Canceled; force; занятие позиции; rollback при конфликте; SMTP failure после commit | Одновременный non-force hire одной позиции даёт один успех; один и тот же app обрабатывается один раз. |
| Email / duplicate | create + update; casing/trim; Canceled history; concurrent writers | Индекс предотвращает активный дубль на SQLite и PostgreSQL; ошибка отображается прежним 409. |
| Alembic | Пустая БД; копия существующей; конфликтующие данные; предыдущая revision | Обновление не теряет данные, baseline проверен, backup реально восстанавливается. |
| Cal.com | Отказ второго chunk; timeout unknown; invalid JSON/UID; local commit failure; cancel failure | Известные UID не теряются; ложного «успеха полного отката» нет. |
| Webhook / время | HMAC по raw bytes; duplicate; reschedule UID chain; offsets; DB failure | UTC корректен, повторяемость не повреждает записи, неподтверждённая обработка не маскируется. |
| Reset / retention | Два reset; reset против hire/book/webhook; исключение; restart; 21+ chunks | Нет удаления несогласованных данных; lock освобождается; unresolved remote операции доступны для сверки. |

В E достаточно адресных контрактных тестов затронутого участка. Расширять матрицу только для новых рисков B/S. Тесты используют временные БД и fake внешние сервисы; ни reset настоящих данных, ни SMTP/Cal.com production-вызовы в CI не выполняются.

