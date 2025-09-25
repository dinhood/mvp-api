@echo off
REM Ativa o virtualenv
call venv\Scripts\activate

REM Roda o app com Waitress
python -m waitress --host=0.0.0.0 --port=5000 app:app

REM Pausa para ver erros
pause
