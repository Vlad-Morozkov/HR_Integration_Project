"""
Единые правила валидации.
Меняешь здесь — меняется во всём приложении.
"""

import re
from datetime import date

# Единый шаблон для email
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_email(email: str) -> str:
    """Приводит email к единому виду для сравнения."""
    if not email:
        return ""
    return str(email).strip().casefold()


def is_valid_email(email: str) -> bool:
    """Проверяет, похож ли текст на валидный email."""
    if not email:
        return False
    return bool(EMAIL_REGEX.fullmatch(str(email).strip()))


def is_valid_birth_date(birth_date: date | None) -> bool:
    """Проверяет, что дата рождения корректна (не в будущем и не сегодня)."""
    if birth_date is None:
        return False
    return birth_date < date.today()


def has_email_duplicate(
    email: str,
    current_app_id: int,
    applications: list,
    same_position_only: bool = False,
    target_position_id: int | None = None,
) -> bool:
    """
    Проверяет, есть ли уже заявка с таким email.
    :param same_position_only: проверять только в рамках одной должности
    :param target_position_id: ID должности для проверки
    """
    if not email:
        return False
    
    norm_email = normalize_email(email)
    
    for app in applications:
        if app["id"] == current_app_id:
            continue
        if app["status"] not in ("New", "Hired"):
            continue
        if same_position_only and target_position_id is not None:
            if app["position_id"] != target_position_id:
                continue
        if normalize_email(app["email"]) == norm_email:
            return True
    return False