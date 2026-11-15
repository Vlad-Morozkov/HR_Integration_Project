"""
Модуль для работы с API бэкенда.
Инкапсулирует requests, обработку таймаутов и ошибок 409 (конфликты).
"""
import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Умная инициализация ключа
try:
    API_KEY = st.secrets["INTERNAL_API_KEY"]
except (KeyError, FileNotFoundError):
    API_KEY = os.getenv("INTERNAL_API_KEY", "super_secret_hiring_key_04061994")

class ApiConflictError(Exception):
    def __init__(self, detail: str, code: str = ""):
        self.detail = detail
        self.code = code
        super().__init__(detail)

class ApiLockedError(Exception):
    pass

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": API_KEY}

    def update_email(self, app_id: int, new_email: str, expected_email: str):
        response = requests.patch(
            f"{self.base_url}/api/applications/{app_id}/email",
            json={"email": new_email, "expected_email": expected_email},
            headers=self.headers,
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
        payload = {
            "status": status,
            "email": email,
            "support_email": support_email,
            "force": force
        }
        response = requests.patch(
            f"{self.base_url}/api/applications/{app_id}/status",
            json=payload,
            headers=self.headers,
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
        response = requests.post(
            f"{self.base_url}/api/positions",
            json={"pos_name": pos_name, "is_free": True},
            headers=self.headers,
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