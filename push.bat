@echo off
REM push.bat - sube el dashboard Mundial 2026 a GitHub
cd /d "%~dp0"
echo === Inicializando repo y subiendo a GitHub ===
git init
git add .
git commit -m "Dashboard Mundial 2026"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/lopezmaxi22/Mundial.2026.git
git push -u origin main --force
echo.
echo === Listo. Si pidio login, completalo en el navegador o en el Credential Manager. ===
echo === Despues: activar GitHub Pages y cargar el secret FOOTBALL_API_KEY (ver README). ===
pause
