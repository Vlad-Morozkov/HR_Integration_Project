# План тестирования, проверок и доставки

Статус: **план; перечисленные новые тесты и CI ещё не добавлены**. База — `df20603afe7b9dcfc59a2d56d6442d0c575c8921`, 27 ноября 2026 года. Цель — доказать сохранение поведения после каждого небольшого извлечения и отдельно подтвердить исправления известных дефектов.

## 1. Что действительно проверено при подготовке плана

- Прочитаны текущие `main.py`, `frontend.py`, `api_client.py`, `models.py`, `validators.py`, `test_validators.py`, `requirements.txt` и эксплуатационные инструкции.
- В [`test_validators.py`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/test_validators.py#L19-L131) есть **11** самостоятельных тестовых функций. В изолированной копии они выполнены адаптером `unittest.FunctionTestCase`: **11/11 успешно**. Backend не импортировался, HTTP и SMTP не использовались.
- `python -m pytest test_validators.py -q` в среде анализа не выполнился: `No module named pytest`. Результат адаптера не является подтверждением работоспособности будущей pytest-конфигурации или окружения Windows.
- Интеграционные, браузерные и конкурентные тесты приложения сейчас не выполнялись; live reset, реальные письма и реальные бронирования не запускались.

Команда выполненного изолированного smoke-теста существующих функций:

```python
import runpy
import unittest

namespace = runpy.run_path("test_validators.py")
suite = unittest.TestSuite(
    unittest.FunctionTestCase(function)
    for name, function in namespace.items()
    if name.startswith("test_") and callable(function)
)
result = unittest.TextTestRunner().run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
```

Для дальнейшей разработки использовать pytest с нормальным сбором тестов, fixtures и отчётами. Адаптер выше — зафиксированная ограниченная проверка текущего набора.

## 2. Подготовительный этап: воспроизводимая и безопасная база

| Место | Наблюдение | Действие отдельным подготовительным коммитом |
|---|---|---|
| [`.gitattributes:1–70`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/.gitattributes#L1-L70) | Вместо атрибутов Git находится Python-код страницы About; Git выдаёт ошибки разбора | Сверить с `ui_about.py`, сохранить полезные отличия при наличии, заменить корректными правилами атрибутов; не запускать массовую renormalize в том же PR |
| [`requirements.txt:1–11`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/requirements.txt#L1-L11) | Почти все версии не закреплены, два PostgreSQL-драйвера; pytest/httpx не объявлены | Записать версии реально рабочего `.venv` и хостинга; подготовить runtime lock и отдельные dev/test зависимости; драйвер выбрать по текущему URL/окружению |
| [`validators.py:27`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/validators.py#L27) | Union-аннотации в этом модуле требуют Python 3.10+ | Зафиксировать поддерживаемую minor-версию после проверки `.venv` и deployment; установленный системный Python не считать версией приложения |
| [`main.py:23–24,374–400`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L374-L400) | `.env` загружается и таблицы создаются при импорте | До импорта тестируемого модуля принудительно назначить временную БД и выключить загрузку реального dotenv; затем выделить app factory и явную инициализацию |
| [`REstart_hr.bat:3–4`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/REstart_hr.bat#L3-L4), [`commands.md:1–4`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/commands.md#L1-L4) | Команда завершает все `python.exe` | В будущем останавливать только проверенные PID проекта/дерево его процессов. Другие Python-приложения не должны завершаться |
| [`REstart_hr.bat:6–14`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/REstart_hr.bat#L6-L14) | Готовность сервера заменена фиксированным ожиданием 3 секунды | Добавить явную проверку readiness с ограниченным ожиданием и сообщением об ошибке; `--reload` оставить только для разработки |

Не обновлять одновременно все зависимости и архитектуру. Сначала воспроизвести существующий рабочий набор, затем обновлять отдельными проверяемыми изменениями. Не включать пароли из `.env` в результаты `pip freeze`, журналы окружения или тестовые fixtures.

## 3. Characterization и спецификация — разные наборы ожиданий

**Characterization** фиксирует то, что приложение действительно делает сегодня: HTTP path/method, статус, JSON, side effects, число удалённых/созданных записей. Он защищает механические переносы. Желаемые исправления документируются отдельно и не объявляются уже работающими.

Подтверждённые расхождения, для которых нужен отдельный defect test:

- `frontend.py:340` сравнивает внутренний mode с переводом и ломает RU Candidate — первоочередной UI-01.
- `TechRev.md` описывает запрет сегодняшней/будущей даты рождения, но `ApplicationCreate` не содержит такого validator. Проверка есть в UI/`validators.py`; серверный запрет — отдельное согласованное изменение API.
- `PositionCreate`/`create_position` не запрещают пустое имя после `strip()` на сервере; не считать UI-проверку серверной гарантией.
- Предварительные duplicate/hire/expected_email проверки не доказывают защиту от конкурентных запросов. Тесты гонок могут выявить текущие дефекты; исправления — отдельная работа с транзакциями и ограничениями БД.
- UI reset и массовая отмена способны показать успех без подтверждённого результата; см. UI-02–04 в плане интерфейса.

Для ещё не исправленного подтверждённого дефекта допустим временный `xfail(strict=True)` с номером задачи и ожидаемым исправлением. Не помечать весь интеграционный набор xfail. Перед завершением соответствующего этапа убрать маркер и получить обычный проходящий тест.

## 4. Как запускать legacy API без доступа к рабочей БД

Одного `app.dependency_overrides[get_db]` недостаточно: создание таблиц происходит раньше, при `import main`. На первом этапе fixture обязана задать окружение **до импорта**, запретить загрузку рабочего dotenv и сетевые побочные действия. Для SQLite использовать файл в `tmp_path_factory`; так не возникает скрытого расхождения между отдельными соединениями `:memory:`.

Пример предлагаемой переходной session fixture (`tests/conftest.py`; требует pytest, FastAPI и httpx в тестовом окружении):

```python
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(scope="session")
def legacy_api(tmp_path_factory):
    if "main" in sys.modules:
        raise RuntimeError("main must not be imported before test isolation")

    db_file = tmp_path_factory.mktemp("hr-test-db") / "isolated.sqlite"
    environment = {
        "DATABASE_URL": f"sqlite:///{db_file.as_posix()}",
        "INTERNAL_API_KEY": "test-only-token",
        "GMAIL_ADDRESS": "",
        "GMAIL_APP_PASSWORD": "",
        "CALCOM_API_KEY": "",
        "CALCOM_EVENT_TYPE": "0",
        "CALCOM_WEBHOOK_SECRET": "test-webhook-only",
    }
    with patch.dict(os.environ, environment), \
         patch("dotenv.load_dotenv", return_value=False), \
         patch("requests.sessions.Session.request",
               side_effect=AssertionError("Unexpected external HTTP")), \
         patch("smtplib.SMTP_SSL",
               side_effect=AssertionError("Unexpected SMTP")):
        module = importlib.import_module("main")
        assert Path(module.engine.url.database).resolve() == db_file.resolve()
        try:
            yield module
        finally:
            module.engine.dispose()
```

Дальше function fixture создаёт/очищает таблицы **только этого проверенного engine**, сбрасывает `SYSTEM_LOCKED`, подменяет `send_email`, подключает `get_db` через `dependency_overrides`, создаёт `TestClient` context manager и в `finally` очищает overrides. Каждый запрос получает отдельную Session. Не переиспользовать Session между потоками.

Конкретные тесты Cal.com вместо запрещённого внешнего HTTP внедряют fake, регистрирующий вызовы и возвращающий заранее заданные ответы; никаких настоящих API keys. SMTP-fake должен позволять моделировать как успех, так и отказ. После выделения app factory зависимости можно задавать явно через согласованный интерфейс фабрики или dependency overrides. Окончательное отсутствие DDL при импорте подтверждается отдельным тестом после P9; до удаления этого побочного эффекта сохраняется переходная изоляция окружения и БД до импорта. Одна только новая функция `create_app` не устраняет импортируемые побочные эффекты автоматически.

## 5. Минимальная матрица проверок backend

| Группа / текущее место | Сценарии и ожидаемые наблюдения |
|---|---|
| API key, `main.py:64–76` | Правильный ключ проходит; неверный/отсутствующий даёт 401; после удаления fallback отсутствие конфигурации останавливает запуск, не открывает API |
| Applications, `main.py:720–837` | 201 с UUID; 404 неизвестной позиции; 422 пустых обязательных полей; trim/normalization; 409 active duplicate; после `Canceled` новая заявка разрешена |
| Hire/Reject, `main.py:844–1015` | Только `New→Hired` и `New→Canceled`; прочие target status 400; terminal application 409; неизвестная 404; occupied position 409 без force; force явно передаётся |
| Транзакция найма | Статус и `is_free=False` меняются вместе; при ошибке commit не меняется ни одно; письмо вызывается после commit; SMTP failure сохраняет успешное изменение БД и `candidate_email_sent=false` |
| Email, `main.py:1018–1092` | 404 неизвестной заявки; 409 при несовпадающем `expected_email`; нормализация; 422 без `@`; отдельный тест гонки двух редакторов |
| Positions, `main.py:1774–1825` | GET shape; POST 201; повтор существующего имени 409; пустое имя — defect test до исправления |
| Bookings, `main.py:1097–1231` | 201; сохранение application_id/UID; правильное число chunks; ошибка первого/среднего chunk; отмена известных успешных UID; отказ компенсации; timeout с неопределённым удалённым исходом |
| Bookings: DB failure | Remote create успешен, локальный commit упал; отдельное ожидаемое поведение компенсации/reconciliation, не просто `db.rollback()` |
| Cancel, `main.py:1272–1325` | Локальные 404/409; remote failure 502; remote success + DB failure 500; успешное изменение `confirmed→cancelled` |
| Webhook, `main.py:634–713` | HMAC по исходным байтам; нет подписи/изменённый body → 401; плохой JSON → 400; повтор отмены; reschedule меняет UID; неизвестный UID; порядок и повтор событий |
| Reset, `main.py:1560–1754` | Блокировка новых записей; повторный reset; разблокировка в finally после исключения; взаимодействие с уже выполняющимся запросом; ошибки внешней отмены и reseed |
| Retention, `main.py:184–212` | keep_last=20; какие записи считаются/удаляются; успешная и неудачная внешняя отмена; точные side effects до и после изменения политики |
| Чтение, `main.py:1233–1270,1330–1345,1827–1871` | Стабильный JSON, фильтры, UTC-представление, `position_name`, отсутствие скрытого изменения данных |

Для webhook отдельно проверить, что выделение защищённого `/api` router не навязывает ему `X-API-Key`: его аутентификация — собственная подпись. Ошибки БД/HTTP и malformed Cal.com JSON должны моделироваться явно.

### Конкретный пример поведенческого API-теста

Ниже предлагаемая форма теста после реализации `client` fixture из раздела 4; создание реального SMTP запрещено fixture. UUID позиции берётся из ответа API, не подставляется числом.

```python
def test_canceled_application_does_not_block_reapply(client):
    client.headers["X-API-Key"] = "test-only-token"
    position = client.post("/api/positions", json={"pos_name": "Engineer"})
    assert position.status_code == 201
    payload = {
        "position_id": position.json()["id"],
        "educ": "College",
        "experience": "Two years",
        "full_name": "Test Candidate",
        "email": "candidate@example.com",
        "birth_date": "1995-01-01",
    }
    first = client.post("/api/applications", json=payload)
    assert first.status_code == 201
    duplicate = client.post("/api/applications", json=payload)
    assert duplicate.status_code == 409

    rejected = client.patch(
        f"/api/applications/{first.json()['id']}/status",
        json={"status": "Canceled", "email": payload["email"]},
    )
    assert rejected.status_code == 200
    second = client.post("/api/applications", json=payload)
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]
```

## 6. Контракт API и frontend

Сохранить OpenAPI из изолированного приложения как `tests/contracts/openapi.json` перед извлечением routers/schemas. Сравнивать paths, методы, параметры, security, response statuses и схемы; случайную перестановку ключей JSON игнорировать. Изменившиеся из-за переноса `operationId` и названия schema components требуют review, а не автоматического принятия нового snapshot. Runtime-ошибки, не описанные OpenAPI, покрываются обычными HTTP-тестами.

Транспорт ApiClient тестировать параметризованно: 200/201, 400, 401, 404, 409, 422, 503, 502, timeout, connection error, пустой/HTML/некорректный JSON. Проверять URL, query params, payload, таймаут и передачу ключа без вывода его значения. Клиент не должен запускать Streamlit или читать секреты при импорте.

Через Streamlit AppTest с fake API проверить:

- EN/RU × Candidate/HR/About; дефект RU Candidate должен стать обычным проходящим тестом UI-01.
- Сохранение анкеты при смене языка/режима; clear и fill-demo; `candidate_form_version`; повторный rerun не отправляет заявку второй раз.
- Неверный email/дата; 201/409/422/503 при submit; сообщение об успехе показывается один раз.
- Редактирование email с `expected_email`; сброс редактора при конфликте; фильтры и выбор ровно одной заявки.
- Hire/Reject и два отдельных force-предупреждения; `force=True` возникает только после подтверждения.
- 404/503 после чужого reset; очищаются устаревшие IDs и выбранные интервалы.
- Запуск demo один раз, poll отдельно от POST; успех/ошибка/неизвестный результат; уход из режима останавливает опрос.
- Fake calendar callback: select/dateClick/eventClick, изменение кандидата, версии компонента, повторный callback; очистка перед `st.rerun()`.

AppTest не доказывает работоспособность JavaScript FullCalendar и custom timezone iframe. Нужен небольшой браузерный smoke на тестовом backend: выбор/отмена/перенос интервала, обнаружение timezone, узкий экран, EN/RU. В fake режиме никакие реальные письма и брони не создаются. Редизайн и новые screenshot-baselines не включать в механический перенос.

## 7. SQLite, PostgreSQL и конкурентность

Unit/API suite сначала использует временный SQLite. PostgreSQL job обязателен до применения миграций или обещания защиты от гонок: одинаковые ORM-запросы не гарантируют одинаковые блокировки и поведение индексов на двух СУБД.

Concurrency tests используют независимые Session/соединения и барьеры синхронизации, а не надежду на случайный `sleep`. Проверить две одновременные заявки с одинаковой нормализованной почтой/позицией, два найма без force на свободное место, два изменения email с одним expected value, reset одновременно с уже начатым hire/booking, двойной webhook. Проверять конечное состояние БД и число side effects, а не только HTTP-коды.

Для миграций: пустая БД → head; копия baseline schema с тестовыми данными → head; дубликаты/грязные значения до уникального индекса; повторный upgrade; соответствие ожидаемому schema diff. SQLite foreign keys включить явно в тестовом engine, чтобы тесты не скрывали ошибки ссылочной целостности. Деструктивный downgrade не считать универсальным откатом данных: проверять восстановление backup отдельно.

## 8. CI и правило завершения каждого этапа

Предлагаемые файлы: `tests/conftest.py`, `tests/unit/`, `tests/api/`, `tests/integration/`, `tests/ui/`, `tests/contracts/openapi.json`, `requirements-dev.txt` или выбранный эквивалент dev-group, `.github/workflows/ci.yml`.

Последовательность CI:

1. Checkout и Python согласованной minor-версии; GitHub Actions закрепить проверенными commit SHA и дать `permissions: contents: read`.
2. Установить воспроизводимые runtime/dev зависимости; секреты deploy в обычный PR job не передавать.
3. Быстрые unit/API/client tests без внешней сети; SQL — только временные БД; отдельный job PostgreSQL с тестовыми credentials.
4. AppTest с fake API и отдельный контрактный diff. Для браузерного smoke использовать локально поднятый тестовый backend.
5. Проверка линтера только на изменённых/новых участках при первом внедрении; массовое форматирование старого файла — самостоятельный коммит. Включить secret scanning/push protection, где доступны для репозитория.
6. Миграционные проверки включаются в gate соответствующего DB-этапа; отчёт содержит выполненные команды, результаты и явные ограничения проверки.

Не нужен произвольный процент покрытия всего монолита: приоритет — бизнес-переходы, транзакции, конфликты, отказ интеграций и API-границы. Поднимать покрытие по извлекаемой области, не писать тесты, которые повторяют строки реализации без проверки поведения.

Перед merge каждого PR: область изменения ограничена, tests зелёные, контракты сопоставлены, secret values отсутствуют, новые ограничения не потеряли существующие данные, описан откат. Для чистого переноса откат — revert; для новой конфигурации и миграций указать совместимость со старой версией и backup/restore. Ротация опубликованного ключа необратима по смыслу безопасности: старый ключ не возвращать при rollback.

## 9. Эксплуатационная проверка после реализации

Развёртывать на отдельном тестовом окружении с тестовыми БД/Cal.com/почтой. Проверить запуск backend/frontend, `/api/system-status` с настроенным ключом, отсутствие секретов в ошибках, успешный ограниченный сценарий Candidate→HR и восстановление после restart. На ПК использовать процессы из конкретного `.venv`, сохранять их PID и перед завершением проверять принадлежность проекту; существующий batch с глобальным `taskkill` не запускать.

Фактический Python/Streamlit/FastAPI runtime, используемый хостинг, количество workers и существующая PostgreSQL schema пока не установлены этим анализом. Это входы подготовительного этапа; они определят окончательный lockfile, миграционную стратегию и механизм координации reset. Планы не дают основания объявить текущую систему защищённой от гонок или считать все перечисленные тесты уже пройденными.

## Источники

- [FastAPI: переопределение зависимостей в тестах](https://fastapi.tiangolo.com/advanced/testing-dependencies/).
- [Streamlit: AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
- [GitHub: безопасность GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use).
- Детали backend — [03-backend-and-integrations.md](03-backend-and-integrations.md); интерфейс — [04-frontend-and-api-client.md](04-frontend-and-api-client.md).
