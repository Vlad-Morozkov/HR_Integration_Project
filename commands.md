
# остановка всех проццессов на python:

taskkill /F /IM python.exe


# запуск сервера и фронта

uvicorn main:app --reload

streamlit run frontend.py

# автоматический перезапуск

.\REstart_hr.bat
