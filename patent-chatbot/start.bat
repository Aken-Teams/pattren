@echo off
echo ============================================
echo   Global Patent Search Assistant
echo   Starting server...
echo ============================================
echo.

pip install -r requirements.txt --quiet

echo.
echo Server starting at http://localhost:5000
echo Press Ctrl+C to stop.
echo.

python app.py
pause
