@echo off
SETLOCAL

REM Check if python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Downloading and installing Python 3.12...
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe -OutFile python_installer.exe"
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python_installer.exe
)

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

echo.
echo Setup complete! To activate later, run:
echo   venv\Scripts\activate.bat
echo To run the app:
echo   python main.py
pause
