# 06. Источники, решения и границы проверки

Дата проверки источников: **27 ноября 2026**. Основные рекомендации сформированы по текущему коду и первичной документации. Источники объясняют механизмы; конкретные границы модулей и приоритеты ниже — инженерные решения для этого проекта.

## 1. Источники самого проекта

- [Базовый коммит `df20603`](https://github.com/Vlad-Morozkov/HR_Integration_Project/commit/df20603afe7b9dcfc59a2d56d6442d0c575c8921): точка привязки всех номеров строк.
- [`main.py`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py), [`frontend.py`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py), [`api_client.py`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/api_client.py): первичные факты о текущем поведении.
- [`models.py`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/models.py), [`test_validators.py`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/test_validators.py), [`requirements.txt`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/requirements.txt).
- [`TechRev.md`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/TechRev.md), [`ProjectContextRus.md`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/ProjectContextRus.md): описания намерений; расхождения с кодом отмечены в плане.
- Вложенное пользователем исследование **DeepWiki Q&A / End-to-End Flows**: исходная методология и карта сценариев. Полный текст не копируется в Git, поскольку он воспроизводит опубликованный секрет; в план перенесены выводы без значения ключа.
- Локальный Windows `Plan.md`: независимое предложение sidebar, обнаружено как untracked. Не является выполненной реализацией и не добавляется автоматически в эту ветку.

## 2. Первичные открытые источники

| Тема | Источник | Как применяется |
| --- | --- | --- |
| Постепенная модернизация | [Martin Fowler — Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html) | Маленькие переходы за сохранёнными интерфейсами; без полного переписывания |
| Зависимости рефакторинга | [The Mikado Method, chapter 3](https://livebook.manning.com/book/the-mikado-method/chapter-3) | Цель, эксперимент, локальный откат, предварительные задачи |
| Проверки при изменении кода | [Fowler — Self Testing Code](https://martinfowler.com/bliki/SelfTestingCode.html) | Короткая обратная связь при переносе поведения |
| Разбиение FastAPI | [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) | APIRouter, явные зависимости и совместимая сборка приложения |
| Конфигурация FastAPI | [Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/) | Настройки вне исходников и возможность подмены в тестах |
| Ресурсы приложения | [Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) | Инициализация/закрытие ресурсов; не механизм миграций |
| Синхронные интеграции | [Concurrency and async / await](https://fastapi.tiangolo.com/async/) | Не вызывать requests/SMTP/sync DB напрямую в event loop |
| Изоляция тестов | [Testing Dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/) и [Testing](https://fastapi.tiangolo.com/tutorial/testing/) | Dependency overrides, TestClient, изолированные внешние эффекты |
| Несколько процессов | [Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/) | Процессная память не является общей блокировкой всех workers |
| SQLAlchemy Session | [Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) | Владелец commit/rollback, autobegin, отдельная Session для каждого concurrent unit of work |
| Миграции | [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) | Кандидат миграции проверяется человеком и на копии БД |
| Условная уникальность | [PostgreSQL Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html) и [SQLAlchemy SQLite Partial Indexes](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#partial-indexes) | Ограничение для активных New/Hired без запрета повторной заявки после Canceled |
| Серверный Streamlit | [Client-server Architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture) | Ключ находится в Python-процессе, не в браузере |
| Streamlit secrets | [Secrets Management](https://docs.streamlit.io/develop/concepts/connections/secrets-management) | env/secrets.toml вне Git, настройки хостинга |
| Кэш ресурсов | [st.cache_resource](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource) | Общий кэш требует thread safety; mutable client нельзя бездумно делить между пользователями |
| UI-тесты | [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest) | Режимы, язык, формы и ошибки без настоящего HTTP |
| Жизненный цикл секретов | [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) | Раздельное хранение, минимальные права, ротация и исключение из логов |
| API security | [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html) | HTTPS, различие ключа приложения и пользовательских разрешений |
| Случайные ключи | [Python secrets](https://docs.python.org/3/library/secrets.html) | `token_urlsafe(32)`, `compare_digest`; не random/base64 как «защита» |
| Утечка в Git | [GitHub — Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) | Ротация прежде истории; оценка последствий переписывания |
| CI secrets | [GitHub Actions — Using secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) | Workflow secrets не равны автоматически runtime settings приложения |
| Сканирование секретов | [GitHub Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning) | Дополнительный контроль, без обещания распознать произвольный самодельный токен |
| Создание бронирования | [Cal.com — Create a booking](https://cal.com/docs/api-reference/v2/bookings/create-a-booking) | Payload, API version, UTC start; поддержка idempotency header не подтверждена этой страницей |
| Отмена бронирования | [Cal.com — Cancel a booking](https://cal.com/docs/api-reference/v2/bookings/cancel-a-booking) | Контракт adapter; текущие 404/410 политики приложения проверять отдельно |
| Подпись webhook | [Официальный GitHub Cal.com — webhooks.mdx](https://github.com/calcom/help/blob/main/webhooks.mdx) | Проверка подписи исходного тела события |
| Компенсации | [Microsoft — Compensating Transaction](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) | Внешняя отмена может упасть; нужен учёт незавершённых действий |
| Дата и время | [Python datetime](https://docs.python.org/3/library/datetime.html) | Различать aware/naive и преобразование момента времени/замену tzinfo |

Ссылки `/latest/`, `/current/` и документация библиотек могут описывать более новую версию, чем установлена у владельца. Перед внедрением сверить APIs с закреплённым окружением. Этот план не требует автоматически обновлять всё до текущих версий документации.

## 3. Короткий журнал решений

| Решение | Основание | Когда пересмотреть |
| --- | --- | --- |
| Модульный монолит | Один небольшой проект, общая БД, связанные сценарии | Появится подтверждённая потребность в независимом масштабировании/владении |
| Сначала тестируемые границы, затем перенос | Основные риски находятся в бизнес-переходах и внешних эффектах | Подход сохраняется при любом дальнейшем росте |
| Config/security — ранний PR | Секрет опубликован в fallback трёх модулей | Ротация остаётся обязательной; способ хранения зависит от хостинга |
| Почту оставить видимой | Прямое решение владельца проекта | Если изменится назначение контактного адреса |
| Без generic repository framework | Несколько конкретных запросов и одна ORM | Если появится реальная потребность в нескольких реализациях persistence |
| Синхронный backend сохранять при extraction | requests/SMTP/SQLAlchemy уже синхронные | После отдельного измерения нагрузки и плана полной async-границы |
| Миграции отдельным этапом | Import-time create_all и существующие БД требуют baseline | До первого изменения schema; production DDL не должен выполняться при импорте |
| Ни одного blind retry create booking | Timeout не доказывает отсутствие бронирования; provider idempotency не подтверждена | После проверки документированного provider contract либо собственной reconciliation-схемы |
| Общий ключ не считать HR-login | UI mode доступен посетителю; ключ различает процессы | При превращении demo в сервис с настоящими ролями |
| Не внедрять очередь только ради структуры | Для extraction достаточно явных синхронных сценариев | Если подтверждённые platform timeouts/crash recovery требуют durable jobs |
| Sidebar — независимая задача | Уже есть локальный Plan.md; UI extraction и дизайн имеют разные причины | После стабильной навигации и UI-тестов |

## 4. Что ещё проверить перед реализацией

| Непроверенный факт | Как проверить без чтения секретов | Что меняет |
| --- | --- | --- |
| Версии Python/библиотек в рабочей `.venv` | `python --version`, список установленных distributions; не выводить environment variables | Совместимость синтаксиса, FastAPI/Pydantic/Streamlit AppTest, driver choices |
| Реальный backend hosting и start command | Настройки deployment/документация владельца | Entry point, lifespan, timeout и запуск миграций |
| Количество процессов/реплик | Deployment configuration, worker count | Возможность временно оставить single-process maintenance coordinator |
| Какая БД используется и есть ли ручные индексы | Схема на тестовой копии/инспекция metadata без публикации DSN | Baseline migration, deduplication/backfill, PostgreSQL concurrency |
| Реальные активные секреты и где они установлены | Проверить наличие/источник через защищённые настройки, без вывода значений | План ротации и согласованный перезапуск |
| Cal.com event type duration/availability/API version | Проверенная sandbox-конфигурация провайдера | Правила chunking, допустимые окна, contract fixtures |
| Retry/delivery policy webhook | Настройки и документация текущей интеграции | Можно ли временно возвращать 503 во время maintenance или нужен durable inbox |
| Допустим ли общий публичный HR demo | Уже заданный характер pet-проекта; уточнение перед настоящими данными | Нужна ли отдельная пользовательская auth/authorization |
| Допустимая длительность reset и цена потери job | Измерение в sandbox и ограничения hosting | Достаточен ли синхронный reset или нужен durable job API |

Наличие этих вопросов не блокирует документацию, удаление fallback и механические extraction при изолированных тестах. Оно определяет границы, которые нельзя выдумать по комментариям в коде.

## 5. Что сделано при подготовке плана

Прочитан переданный DeepWiki текст; проверены tracked исходники GitHub на закреплённом SHA и состояние локальной Windows-копии; изучены первичные источники; выполнена безопасная проверка существующих чистых validators (точный способ и результат — [05](05-testing-and-delivery.md)). Не запускались рабочий backend, реальные API-записи, SMTP, Cal.com, demo reset и миграции; действующие секреты не менялись. Документация представляет план следующих изменений, а не результат уже прошедших интеграционных тестов.
