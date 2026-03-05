@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=AnimaBeyondFantasy"
set "APP_PORTABLE=AnimaBeyondFantasy_Portable"
set "PACKAGE_DIR=App_Windows"
set "DATA_DIR=Personajes\personajes"
set "ZIP_NAME=%APP_NAME%_Windows_Portable.zip"

echo [1/5] Instalando dependencias de build...
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 (
  echo Error instalando dependencias.
  exit /b 1
)

echo [2/5] Generando ejecutable unico (.exe) con PyInstaller...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name %APP_NAME% ^
  --add-data "assets;assets" ^
  --add-data "tablas;tablas" ^
  main.py
if errorlevel 1 (
  echo Error durante el build de PyInstaller.
  exit /b 1
)

echo [3/5] Generando version portable (carpeta) con PyInstaller...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --name %APP_PORTABLE% ^
  --add-data "assets;assets" ^
  --add-data "tablas;tablas" ^
  main.py
if errorlevel 1 (
  echo Error durante el build portable de PyInstaller.
  exit /b 1
)

echo [4/6] Preparando carpeta %PACKAGE_DIR%...
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"
copy /y "dist\%APP_NAME%.exe" "%PACKAGE_DIR%\%APP_NAME%.exe" >nul
xcopy "dist\%APP_PORTABLE%" "%PACKAGE_DIR%\%APP_PORTABLE%\" /E /I /Y >nul
mkdir "%PACKAGE_DIR%\%DATA_DIR%"

(
  echo ANIMA BEYOND FANTASY - APP WINDOWS
  echo.
  echo 1^) Ejecuta directamente %APP_NAME%.exe ^(sin instalacion^)
  echo 2^) Tambien tienes la version portable completa en la carpeta %APP_PORTABLE%
  echo 3^) Los personajes se guardan junto al .exe en la carpeta %DATA_DIR%\
  echo.
  echo Recomendacion: no ejecutar desde C:\Program Files para evitar problemas de permisos.
) > "%PACKAGE_DIR%\INSTRUCCIONES.txt"

echo [5/6] Generando ZIP portable para distribuir...
if exist "%ZIP_NAME%" del /f /q "%ZIP_NAME%"
powershell -NoProfile -Command "Compress-Archive -Path '%PACKAGE_DIR%\\*' -DestinationPath '%ZIP_NAME%' -Force"
if errorlevel 1 (
  echo Error creando el ZIP portable.
  exit /b 1
)

echo [6/6] Build completado.
echo Carpeta lista para copiar: %PACKAGE_DIR%\
echo - %PACKAGE_DIR%\%APP_NAME%.exe
echo - %PACKAGE_DIR%\%APP_PORTABLE%\
echo - %PACKAGE_DIR%\%DATA_DIR%\
echo - %PACKAGE_DIR%\INSTRUCCIONES.txt
echo ZIP listo para distribuir: %ZIP_NAME%
echo.
echo Nota: al ejecutar en Windows, los datos se guardan junto al .exe en %DATA_DIR%\

endlocal
