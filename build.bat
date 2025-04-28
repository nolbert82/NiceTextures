@echo off
echo Building NiceTextures executable...

REM Ensure PyInstaller is accessible, prefer using python -m
python -m PyInstaller --onefile --windowed --name NiceTextures --add-data="config.ini;." --add-data="icon.png;." --add-data="textures;textures" main.py

if %errorlevel% neq 0 (
    echo.
    echo PyInstaller build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo Build successful! Executable is in the 'dist' folder.
pause 