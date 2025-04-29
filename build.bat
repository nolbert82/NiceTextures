@echo off
set VENV_DIR=.venv
set PYTHON_EXE=python

echo --- Setting up Virtual Environment ---
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV_DIR%...
    %PYTHON_EXE% -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b %errorlevel%
    )
) else (
    echo Virtual environment already exists.
)

echo --- Activating Virtual Environment and Installing Requirements ---
call "%VENV_DIR%\Scripts\activate.bat"
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    call "%VENV_DIR%\Scripts\deactivate.bat"
    pause
    exit /b %errorlevel%
)

echo --- Building NiceTextures Executable ---

REM Ensure PyInstaller is accessible, prefer using python -m
REM Now runs using the python from the virtual environment
python -m PyInstaller --onefile --windowed --name NiceTextures --add-data="config.ini;." --add-data="icon.png;." --add-data="textures;textures" main.py

if %errorlevel% neq 0 (
    echo.
    echo PyInstaller build failed!
    call "%VENV_DIR%\Scripts\deactivate.bat"
    pause
    exit /b %errorlevel%
)

call "%VENV_DIR%\Scripts\deactivate.bat"
echo.
echo Build successful! Executable is in the 'dist' folder.
pause 