
# остановка всех проццессов на python:

taskkill /F /IM python.exe


# запуск сервера и фронта

uvicorn main:app --reload

streamlit run frontend.py

# автоматический перезапуск

.\REstart_hr.bat

# запуск venv
.\.venv\Scripts\Activate.ps1


# установка на новой платформе
pip install streamlit fastapi uvicorn sqlalchemy pandas requests streamlit-calendar pydantic python-dotenv

# установит всё чот используется в проекте
-PIP INSTALL -R REQUIREMENTS.TXT-pip install -r requirements.txt

# Проверка автотестами

pytest test_validators.py -v
