@echo off
REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set inverted class index (model predicts class 1=REAL, class 0=FAKE)
set INVERT_CLASS_INDEX=1

REM Start the app
cd src
python app.py

pause
