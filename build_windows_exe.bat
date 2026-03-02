@echo off
setlocal

cd /d "%~dp0"

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
  --name AnimaBeyondFantasy ^
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
  --name AnimaBeyondFantasy_Portable ^
  --add-data "assets;assets" ^
  --add-data "tablas;tablas" ^
  main.py
if errorlevel 1 (
  echo Error durante el build portable de PyInstaller.
  exit /b 1
)

echo [4/5] Preparando carpeta App_Windows...
if exist "App_Windows" rmdir /s /q "App_Windows"
mkdir "App_Windows"
copy /y "dist\AnimaBeyondFantasy.exe" "App_Windows\AnimaBeyondFantasy.exe" >nul
xcopy "dist\AnimaBeyondFantasy_Portable" "App_Windows\AnimaBeyondFantasy_Portable\" /E /I /Y >nul

(
  echo ANIMA BEYOND FANTASY - APP WINDOWS
  echo.
  echo 1^) Ejecuta directamente AnimaBeyondFantasy.exe ^(sin instalacion^)
  echo 2^) Tambien tienes la version portable completa en la carpeta AnimaBeyondFantasy_Portable
  echo 3^) Los personajes se guardan junto al .exe en la carpeta Personajes\personajes\
  echo.
  echo Recomendacion: no ejecutar desde C:\Program Files para evitar problemas de permisos.
) > "App_Windows\INSTRUCCIONES.txt"

echo [5/5] Build completado.
echo Carpeta lista para copiar: App_Windows\
echo - App_Windows\AnimaBeyondFantasy.exe
echo - App_Windows\AnimaBeyondFantasy_Portable\
echo - App_Windows\INSTRUCCIONES.txt
echo.
echo Nota: al ejecutar en Windows, los datos se guardan junto al .exe en Personajes\personajes\

endlocal
