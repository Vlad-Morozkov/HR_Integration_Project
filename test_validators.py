"""
Тесты для validators.py.
Запуск: pytest test_validators.py -v
"""

from datetime import date, timedelta
from validators import (
    normalize_email,
    is_valid_email,
    is_valid_birth_date,
    has_email_duplicate,
)


# =========================================
# 1. Тесты нормализации email
# =========================================

def test_normalize_email_basic():
    assert normalize_email("  Test@Example.COM ") == "test@example.com"

def test_normalize_email_empty():
    assert normalize_email("") == ""
    assert normalize_email(None) == ""


# =========================================
# 2. Тесты валидации email
# =========================================

def test_valid_emails():
    assert is_valid_email("test@example.com") is True
    assert is_valid_email("a.b+c@sub.domain.co.uk") is True

def test_invalid_emails():
    assert is_valid_email("") is False
    assert is_valid_email("test") is False
    assert is_valid_email("test@") is False
    assert is_valid_email("@example.com") is False
    assert is_valid_email("test@example") is False


# =========================================
# 3. Тесты проверки даты рождения
# =========================================

def test_valid_birth_date():
    # Вчера — валидно
    yesterday = date.today() - timedelta(days=1)
    assert is_valid_birth_date(yesterday) is True

    # 2000 год — валидно
    assert is_valid_birth_date(date(2000, 1, 1)) is True

def test_invalid_birth_date():
    # Сегодня — невалидно (должно быть строго меньше)
    assert is_valid_birth_date(date.today()) is False
    # Завтра — невалидно
    assert is_valid_birth_date(date.today() + timedelta(days=1)) is False
    # None — невалидно
    assert is_valid_birth_date(None) is False


# =========================================
# 4. Тесты поиска дубликатов email
# =========================================

# Фиктивные заявки для тестов
MOCK_APPS = [
    {"id": 1, "email": "alice@example.com", "status": "New", "position_id": 10},
    {"id": 2, "email": "bob@example.com", "status": "Hired", "position_id": 10},
    {"id": 3, "email": "alice@example.com", "status": "New", "position_id": 20}, 
    {"id": 4, "email": "charlie@example.com", "status": "Canceled", "position_id": 10},
]

def test_duplicate_same_position():
    # Ищем alice@example.com на позицию 10 (у неё уже есть заявка id=1)
    # Но мы проверяем с точки зрения новой заявки (id=99)
    is_dup = has_email_duplicate(
        email="alice@example.com",
        current_app_id=99,
        applications=MOCK_APPS,
        same_position_only=True,
        target_position_id=10
    )
    assert is_dup is True

def test_duplicate_ignores_canceled():
    # charlie@example.com имеет статус Canceled, не должен блокировать
    is_dup = has_email_duplicate(
        email="charlie@example.com",
        current_app_id=99,
        applications=MOCK_APPS,
        same_position_only=True,
        target_position_id=10
    )
    assert is_dup is False

def test_duplicate_different_position():
    # alice@example.com есть на позиции 10 и 20.
    # Если мы ищем на позицию 30 — дубликата нет.
    is_dup = has_email_duplicate(
        email="alice@example.com",
        current_app_id=99,
        applications=MOCK_APPS,
        same_position_only=True,
        target_position_id=30
    )
    assert is_dup is False

def test_duplicate_ignores_self():
    # Если мы обновляем заявку id=1 и проверяем её же email,
    # она не должна считаться дубликатом сама для себя.
    is_dup = has_email_duplicate(
        email="alice@example.com",
        current_app_id=1,
        applications=MOCK_APPS,
        same_position_only=True,
        target_position_id=10
    )
    assert is_dup is False

def test_duplicate_case_insensitive():
    # Email должен сравниваться без учёта регистра
    is_dup = has_email_duplicate(
        email="ALICE@EXAMPLE.COM",
        current_app_id=99,
        applications=MOCK_APPS,
        same_position_only=True,
        target_position_id=10
    )
    assert is_dup is True