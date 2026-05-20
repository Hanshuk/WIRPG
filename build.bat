@echo off
echo ============================================
echo  CostPlus SolarDocs - Build System
echo  Cost Plus Inc.
echo ============================================
echo.

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)

echo [2/3] Building portable EXE...
pyinstaller build.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo [3/3] Build complete!
echo Portable EXE: dist\CostPlusSolarDocs.exe
echo.
pause
