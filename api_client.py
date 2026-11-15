"""
Модуль для работы с API бэкенда.
Инкапсулирует requests, обработку таймаутов и ошибок 409 (конфликты).
"""
import requests

class ApiConflictError(Exception):
    """Ошибка 409: данные устарели или конфликтуют с текущим состоянием."""
    def __init__(self, detail: str, code: str = ""):
        self.detail = detail
        self.code = code  # Например, "EMAIL_CONFLICT" или "POSITION_OCCUPIED"
        super().__init__(detail)

class ApiLockedError(Exception):
    """Ошибка 503: система на тех. обслуживании."""
    pass

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def update_email(self, app_id: int, new_email: str, expected_email: str):
        """
        Обновляет email с проверкой конфликта версий.
        Если expected_email не совпадает с базой — выбросит ApiConflictError.
        """
        response = requests.patch(
            f"{self.base_url}/api/applications/{app_id}/email",
            json={"email": new_email, "expected_email": expected_email},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 409:
            detail = response.json().get("detail", "")
            raise ApiConflictError(detail, code="EMAIL_CONFLICT")
        elif response.status_code == 503:
            raise ApiLockedError("Система обновляется.")
        else:
            raise Exception(f"Ошибка сервера: {response.status_code} - {response.text}")

    def update_status(self, app_id: int, status: str, email: str, support_email: str = "", force: bool = False):
        """
        Меняет статус заявки. 
        Если позиция занята, а force=False — выбросит ApiConflictError с кодом POSITION_OCCUPIED.
        """
        payload = {
            "status": status,
            "email": email,
            "support_email": support_email,
            "force": force
        }
        response = requests.patch(
            f"{self.base_url}/api/applications/{app_id}/status",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 409:
            detail = response.json().get("detail", "")
            raise ApiConflictError(detail, code="POSITION_OCCUPIED" if "POSITION_OCCUPIED" in detail else "OTHER")
        elif response.status_code == 503:
            raise ApiLockedError("Система обновляется.")
        else:
            raise Exception(f"Ошибка сервера: {response.status_code} - {response.text}")

    def create_position(self, pos_name: str):
        """Создает должность. Защищено от дублей уникальным индексом."""
        response = requests.post(
            f"{self.base_url}/api/positions",
            json={"pos_name": pos_name, "is_free": True},
            timeout=10
        )
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 409:
            raise ApiConflictError(response.json().get("detail", ""), code="POSITION_EXISTS")
        elif response.status_code == 503:
            raise ApiLockedError("Система обновляется.")
        else:
            raise Exception(f"Ошибка сервера: {response.status_code} - {response.text}")