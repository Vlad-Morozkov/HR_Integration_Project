# 02. Конфигурация и секрет связи frontend/backend

Статус: **план и примеры, ещё не внедрены**. База: `df20603afe7b9dcfc59a2d56d6442d0c575c8921`. Значения секретов в этот документ не копируются.

## 1. Что именно нужно защитить

Здесь «пароль для соединения фронта с сервером» — общий **`INTERNAL_API_KEY`**, который Streamlit передаёт FastAPI в заголовке `X-API-Key`. Это служебный токен, а не пароль пользователя.

Python-код Streamlit исполняется на сервере. Поэтому ключ может оставаться в окружении этого процесса, а запрос с ключом — отправляться из Python напрямую в backend. Браузеру ключ не нужен: [архитектура Streamlit](https://docs.streamlit.io/develop/concepts/architecture/architecture). Если позднее появится SPA/JavaScript-клиент с прямыми запросами, ту же схему со встроенным общим ключом переносить туда нельзя.

| Значение | Секрет? | Где хранить |
| --- | --- | --- |
| Публичная контактная почта, адрес отправителя | Нет, по решению владельца проекта | Обычная конфигурация/переводы/UI; можно оставить видимой |
| `API_URL`, Cal.com event type ID | Обычно нет | Окружение или обычная конфигурация |
| `INTERNAL_API_KEY` | Да | Backend env и Streamlit server env/`st.secrets` |
| `GMAIL_APP_PASSWORD` | Да | Только backend secret storage |
| `CALCOM_API_KEY`, `CALCOM_WEBHOOK_SECRET` | Да, разные значения и назначения | Только backend secret storage |
| `DATABASE_URL` с логином/паролем | Да | Backend secret storage, не выводить в лог целиком |

Публичность контактной почты не означает, что нужно публиковать базы настоящих кандидатов или содержимое писем. Рефакторинг сохраняет видимую почту и демо-примеры, а не расширяет перечень публикуемых данных.

## 2. Точные места изменения

| Текущее место | Что изменить | Цель |
| --- | --- | --- |
| [`main.py:63–76`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L63-L76) | Удалить строковый fallback; вынести загрузку настроек и проверку заголовка | Без ключа приложение не запускается; неверный ключ даёт прежний 401 |
| [`frontend.py:24–49`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L24-L49) | Чтение URL и ключа по отдельности, без секретного default; передача ключа в ApiClient | Один и тот же конфиг для всех вызовов UI |
| [`api_client.py:5–17,28–31`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/api_client.py#L5-L31) | Удалить `streamlit`, `load_dotenv` и глобальное чтение секрета | Чистый тестируемый клиент `ApiClient(base_url, api_key)` |
| [`frontend.py:344–345`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/frontend.py#L344-L345) | Удалить закомментированный вывод DEBUG Key | Чтобы диагностический код не был случайно включён |
| [`main.py:81,565–566,606–617`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/main.py#L565-L617) | Собрать webhook, SMTP и Cal.com настройки в backend config | Явная доступность опциональных интеграций и проверка согласованности |
| [`.gitignore:12–15`](https://github.com/Vlad-Morozkov/HR_Integration_Project/blob/df20603afe7b9dcfc59a2d56d6442d0c575c8921/.gitignore#L12-L15) | Сохранить существующие `.env`-правила; добавить `.streamlit/secrets.toml` | Локальные secrets не попадают в следующие коммиты |
| Новые `.env.example`, `.streamlit/secrets.example.toml` | Только названия и пустые значения | Воспроизводимая настройка без действующих токенов |

В исходниках опубликован резервный ключ. Активный ключ на хостинге может быть переопределён окружением/`st.secrets`; значения runtime в рамках анализа не читались. Тем не менее опубликованное значение следует считать непригодным для использования и убрать из всех fallback.

## 3. Минимальная реализация без новой зависимости

Ниже — **предлагаемые фрагменты**, которые нужно добавить отдельным PR и связать с app factory. Они показывают только обязательную auth-настройку. Остальные настройки переносить с сохранением текущих имён переменных и поведения интеграций.

### `app/config.py`

```python
import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class AuthSettings:
    internal_api_key: str = field(repr=False)


@lru_cache(maxsize=1)
def get_auth_settings() -> AuthSettings:
    value = os.environ.get("INTERNAL_API_KEY")
    if value is None or not value.strip():
        raise RuntimeError("INTERNAL_API_KEY must be configured")
    return AuthSettings(internal_api_key=value)
```

Настройки читаются при явном вызове, не как случайный побочный эффект импорта. `repr=False` не допускает случайного вывода токена через repr этого объекта. Это не защита от сознательного логирования полей. Для расширенного типизированного config допустим `pydantic-settings`, но тогда добавить его явной зависимостью и проверять выбранную версию; уже установленный `pydantic` сам по себе этот пакет не заменяет. См. [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/).

### `app/security.py`

```python
from secrets import compare_digest

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import AuthSettings, get_auth_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key: str | None = Security(api_key_header),
    settings: AuthSettings = Depends(get_auth_settings),
) -> str:
    if not api_key or not compare_digest(
        api_key.encode("utf-8"),
        settings.internal_api_key.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key
```

Сохранены заголовок и контракт ошибки. `compare_digest` используется для сравнения секретных значений; байтовые аргументы также избегают ограничения строкового сравнения на non-ASCII. [Python secrets](https://docs.python.org/3/library/secrets.html).

### Проверка обязательных настроек при запуске

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_auth_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_auth_settings()  # fail fast, до обслуживания запросов
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="HR Hiring System API",
        version="1.1.0",
        lifespan=lifespan,
    )
    # Здесь будут include_router и необходимые middleware.
    # Их нельзя опустить при переносе из существующего main.py.
    return app
```

Это каркас, а не полноценная замена `main.py`: текущие маршруты, CORS, зависимости и lock подключаются в соответствующих этапах. `create_all`/demo seed не помещать сюда как постоянный механизм миграций. Тест с `TestClient` должен входить в context manager, чтобы запускалась lifespan-проверка.

### Настройки UI и один источник ключа

Читать каждую настройку отдельно. В исходном `try` ошибка одного поля заставляет сразу оба поля перейти на env/default; это может незаметно заменить заданный облачный API_URL на localhost.

```python
# Предлагаемый ui/config.py; вызывается из frontend.py после локального dotenv.
import os
import streamlit as st


def read_setting(name: str, default: str | None = None) -> str | None:
    try:
        return str(st.secrets[name])
    except (KeyError, FileNotFoundError):
        return os.environ.get(name, default)


def load_frontend_settings() -> tuple[str, str]:
    api_url = read_setting("API_URL", "http://127.0.0.1:8000")
    api_key = read_setting("INTERNAL_API_KEY")
    if not api_url or not api_key or not api_key.strip():
        st.error("Не настроено соединение с API. Обратитесь к владельцу приложения.")
        st.stop()
    return api_url.rstrip("/"), api_key
```

Исключения для отсутствующего файла сверить с закреплённой версией Streamlit; ошибка синтаксиса TOML должна оставаться видимой оператору, её нельзя глотать широким `except Exception`. Пустой ключ в `st.secrets` трактуется как ошибка конфигурации, а не разрешение включить запасной пароль.

```python
# Предлагаемые изменения конструктора api_client.py
class ApiClient:
    def __init__(self, base_url: str, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("INTERNAL_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}

# В frontend.py:
# api_url, api_key = load_frontend_settings()
# api = ApiClient(base_url=api_url, api_key=api_key)
```

До P7 прямые `requests` в UI должны использовать `HEADERS`, построенные из того же загруженного ключа. В P7 удалить эти обходы полностью. Нельзя убрать ключ из frontend и оставить опубликованный default внутри ApiClient.

## 4. Локальная конфигурация Windows

Для этой папки проще начать с одного **локального `.env`**, из которого оба процесса получают одно значение. `python-dotenv` уже присутствует в requirements. Вызывать `load_dotenv` явно из entrypoint, с путём к проекту и `override=False`, чтобы процессное окружение имело приоритет. Не распределять поиск `.env` по API-клиентам и библиотечным модулям.

Будущий **`.env.example`**, который можно коммитить:

```dotenv
API_URL=http://127.0.0.1:8000
INTERNAL_API_KEY=
DATABASE_URL=sqlite:///./hr_project.db
GMAIL_ADDRESS=public-contact@example.com
GMAIL_APP_PASSWORD=
CALCOM_API_KEY=
CALCOM_EVENT_TYPE=
CALCOM_WEBHOOK_SECRET=
```

Пустое значение специально требует настройки. Значение `public-contact@example.com` — пример, а не требование заменить текущую публичную почту. Существующий `.env` не перезаписывать шаблоном: добавить/заменить только нужную настройку.

Альтернатива для Streamlit — локальный `.streamlit/secrets.toml`:

```toml
API_URL = "http://127.0.0.1:8000"
INTERNAL_API_KEY = ""
```

В реальном **неотслеживаемом** файле заполнить ключ тем же значением, что у FastAPI. Если используются одновременно `.env` и secrets.toml, задокументировать приоритет `st.secrets` → env и обновлять выбранный источник, иначе легко получить 401 после ротации. Для обычного локального запуска одного источника достаточно.

Будущие правила `.gitignore`:

```gitignore
.env
.env.*
!.env.example
.streamlit/secrets.toml
```

`.gitignore` не скрывает уже закоммиченный файл и не удаляет историю. Сначала проверить `git ls-files -- .env .streamlit/secrets.toml`; если файл отслеживается, убрать именно его из index, сохранив локальную копию. В текущем снимке этих файлов среди tracked нет; содержимое локальных секретных файлов не исследовалось.

## 5. Хостинг и ротация

**Сначала заменить скомпрометированный секрет.** Простое удаление литерала из нового коммита не отменяет доступ по старому значению. Это прямо отражено в [рекомендации GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Порядок для небольшой демонстрационной системы с коротким окном обслуживания:

1. Подготовить совместимое чтение настроек без fallback во всех трёх местах и auth-тесты. Не ждать полного архитектурного рефакторинга.
2. Сгенерировать новый случайный ключ локально, например `secrets.token_urlsafe(32)` средствами Python. Не публиковать результат в commit, issue, документации, скриншоте или чате. Не генерировать новый ключ при каждом запуске сервиса.
3. Записать одно новое значение в секретные настройки backend и Streamlit. На backend также хранятся отдельные SMTP/Cal.com/DB secrets. Точные платформы и доступ к ним проверяются перед выполнением; комментарий с Vercel URL в коде не доказывает текущий deployment.
4. Согласованно перезапустить/развернуть оба процесса. При последовательном обновлении возможен короткий период 401 — для pet-проекта проще явно запланировать его. Опубликованный старый ключ не оставлять принимаемым для длительного «переходного периода».
5. Выполнить безопасный `GET /api/positions` с новым ключом; ожидается 200. Старый, пустой и отсутствующий ключ должны возвращать 401. Не использовать reset/hire/create booking для такой проверки.
6. Проверить логи и UI на отсутствие ключа, освежить процессный settings cache перезапуском, проверить каждый экземпляр backend/Streamlit, если их несколько.
7. Проверить CI/будущие коммиты на повторное появление секретов. GitHub secret scanning полезен, но обнаружение произвольного самодельного ключа не гарантируется.

Для Streamlit Community Cloud секреты задаются средствами хостинга по [инструкции Streamlit](https://docs.streamlit.io/develop/concepts/connections/secrets-management). Для backend — через защищённые переменные его платформы. **GitHub Actions Secrets относятся к workflow:** создание такого секрета само по себе не задаёт переменную работающему Streamlit/FastAPI. Нужна явная передача в deployment или настройка самой платформы: [GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

История Git обсуждается отдельно после ротации. Переписывание истории меняет SHA, требует согласования клонов/веток и не гарантирует удаления чужих копий. Для отозванного служебного ключа часто достаточно самой ротации и удаления активных fallback. В эту документационную задачу force push и чистка истории не входят.

## 6. Граница авторизации и webhook

Общий ключ подтверждает доступ серверного клиента к API. Он не различает посетителей Streamlit. Сейчас Candidate/HR/About выбираются в UI; скрытие ключа не сделает HR-действия недоступными обычному посетителю. Для сознательно открытого demo это можно сохранить и явно обозначить; для настоящего HR-сервиса нужны отдельная идентификация пользователей и проверки разрешений на backend. Нельзя доверять присланному UI полю `role="HR"` без проверяемой идентичности. [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html).

`/api/webhooks/calcom` использует другую схему: HMAC-SHA256 raw body с `CALCOM_WEBHOOK_SECRET`. Router webhook нельзя случайно подключить к общей зависимости INTERNAL_API_KEY. Отсутствующий webhook secret должен продолжать запрещать приём подписанных событий, а не отключать проверку. Детали переноса и reset-гонки — в [03](03-backend-and-integrations.md).

`X-API-Key` передавать через HTTPS вне локального loopback. Не помещать его в query string, HTML/JS, browser localStorage или сообщения ошибок. CORS не является авторизацией: серверные запросы Python Streamlit не зависят от браузерного CORS. Текущий wildcard CORS пересмотреть по реальным browser-клиентам отдельным небольшим изменением, а не считать URL Streamlit достаточной защитой.

Base64 и перенос ключа в другой `.py` не защищают от читателя репозитория. Хеширование общего токена на стороне backend может ограничить некоторые последствия утечки его хранилища, но frontend всё равно должен знать исходный токен; для текущей задачи достаточно случайного ключа, хранения вне Git, HTTPS и ротации.

## 7. Критерии приёмки P1

- [ ] В backend/frontend/ApiClient нет секретного литерала по умолчанию; templates пустые.
- [ ] При отсутствии INTERNAL_API_KEY backend не обслуживает запросы; UI показывает понятное сообщение без значений.
- [ ] Один новый ключ установлен обоим сервисам; опубликованный старый отклоняется.
- [ ] Верный ключ → 200 на безопасном GET; неверный/отсутствующий/пустой → 401 с прежним detail.
- [ ] `.env` и `.streamlit/secrets.toml` не отслеживаются; `.env.example` и secrets example доступны для настройки.
- [ ] ApiClient получает ключ через constructor и не импортирует Streamlit.
- [ ] Webhook HMAC продолжает работать независимо от service key.
- [ ] Публичная почта осталась доступна; секреты отсутствуют в UI, логах и новых документах.
- [ ] Описан способ выпуска и безопасного отката; значение ключа в checklist не записывается.
