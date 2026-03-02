# Manual de Usuario
## Ánima: Beyond Fantasy - Gestor de Personajes

Versión del manual: 01/03/2026

---

## 1. ¿Qué es esta aplicación?

Esta aplicación permite crear, editar y gestionar personajes de **Ánima: Beyond Fantasy**, además de ejecutar combates con reglas automatizadas.

Incluye:
- Interfaz gráfica (GUI) para uso diario.
- Modo terminal (CLI) para pruebas y control avanzado.
- Guardado en JSON por personaje.

---

## 2. Requisitos

### Uso normal desde código fuente
- Python 3.7 o superior.

### Generar ejecutable de Windows
- Windows 10/11.
- Python instalado y disponible en consola.

---

## 3. Inicio rápido

### 3.1 Linux (desde código fuente)
1. Abre terminal en la carpeta del proyecto.
2. Ejecuta:

```bash
python3 main.py
```

### 3.2 Windows (desde código fuente)
1. Abre CMD o PowerShell en la carpeta del proyecto.
2. Ejecuta:

```cmd
python main.py
```

### 3.3 Modo terminal (CLI)

Linux/macOS:
```bash
python3 main.py --cli
```

Windows:
```cmd
python main.py --cli
```

---

## 4. Crear versión Windows sin instalación

La aplicación ya está preparada para crear una versión portable para llevar a cualquier ordenador Windows.

### 4.1 Compilar en Windows
1. Abre una consola en la carpeta del proyecto.
2. Ejecuta:

```cmd
build_windows_exe.bat
```

### 4.2 Resultado
Se crea una carpeta lista para copiar:

```text
App_Windows\
```

Contenido esperado:

```text
App_Windows\AnimaBeyondFantasy.exe
App_Windows\AnimaBeyondFantasy_Portable\
App_Windows\INSTRUCCIONES.txt
```

### 4.3 Uso en otro ordenador
1. Copia `App_Windows` al equipo destino (USB, nube, red local, etc.).
2. Abre `AnimaBeyondFantasy.exe`.
3. No requiere instalación.

> Recomendación: evitar `C:\Program Files` para no tener bloqueos de permisos de escritura.

---

## 5. Dónde se guardan los personajes

### En Linux o ejecución desde código fuente
Se guardan en la carpeta de datos del proyecto.

### En ejecutable Windows (.exe)
Se guardan junto al ejecutable, en:

```text
Personajes\personajes\
```

Esto permite mover la app y sus datos de forma portable.

---

## 6. Menú principal (GUI)

Al iniciar la interfaz gráfica encontrarás:
- **Crear personaje**
- **Editar personaje**
- **Combate**
- **Modo Test**
- **Salir de la aplicación**

---

## 7. Gestión de personajes

### 7.1 Crear personaje
1. Pulsa **Crear personaje**.
2. Selecciona tipo (Guerrero, Domine, Mago, Mentalista, Warlock, Hechicero mentalista o Guerrero mentalista).
3. Introduce atributos.
4. Guarda.

Nota sobre Ki:
- **Puntos de Ki** solo aparece para arquetipos con Ki (Domine y mixtos).

### 7.2 Editar personaje
1. Pulsa **Editar personaje**.
2. Selecciona el JSON del personaje.
3. Modifica campos.
4. Guarda.

### 7.3 Eliminar personaje
Disponible en CLI y en flujos de gestión correspondientes.

---

## 8. Combate

El sistema de combate permite:
- Tiradas de iniciativa automáticas y manuales.
- Resolución de ataque/defensa.
- Manejo de pifias y tiradas abiertas.
- Penalizadores por defensas múltiples.
- Consulta de tablas CSV de modificadores.
- En arquetipos mixtos, elección por turno entre combate con arma o con poder.
- Lanzar poderes mágicos o mentales desde el panel de acciones de la derecha sin resolver un ataque completo.
- Mentalismo completo: tirada de **Potencial Psíquico** y después **Proyección Psíquica** (con opción de saltar potencial).

Flujo básico:
1. Añadir participantes.
2. Configurar modo de combate y equipo.
3. Tirar iniciativas.
4. Resolver acciones por turno.

---

## 9. Modo CLI (terminal)

El menú CLI permite:
1. Crear nuevo personaje.
2. Listar personajes.
3. Ver detalles.
4. Editar personaje.
5. Eliminar personaje.
6. Iniciar combate.
7. Modo test.
8. Salir.

---

## 10. Copias de seguridad recomendadas

Para no perder datos:
- Haz copia periódica de la carpeta `Personajes` (si usas `.exe` en Windows).
- Si usas el proyecto en Linux, respalda la carpeta `datos`.
- Guarda también la carpeta `App_Windows` cuando prepares una versión estable.

---

## 11. Resolución de problemas

### 11.1 No abre el ejecutable en Windows
- Ejecutar con clic derecho → "Ejecutar como administrador" (solo para probar).
- Mover la app a una carpeta no protegida (por ejemplo `D:\Juegos\Anima`).
- Revisar si SmartScreen bloquea la ejecución y usar “Más información” → “Ejecutar de todas formas”.

### 11.2 No guarda personajes
- Confirmar que existe permiso de escritura en la carpeta donde está el `.exe`.
- Verificar que se creó `Personajes\personajes\` junto al ejecutable.

### 11.3 Falta una imagen o tabla
- Comprobar que el build se ha hecho con `build_windows_exe.bat`.
- No borrar carpetas incluidas dentro de `App_Windows`.

---

## 12. Preguntas frecuentes

**¿Necesito instalar algo en el equipo destino?**
No, si usas la carpeta `App_Windows` ya compilada.

**¿Puedo usar la misma carpeta en varios PCs?**
Sí. Puedes copiar `App_Windows` completa entre equipos.

**¿Se puede tener varios perfiles de personajes?**
Sí, duplicando carpetas o cambiando de ubicación de `App_Windows`.

---

## 13. Mantenimiento rápido

Cuando hagas cambios de código y quieras nueva versión Windows:
1. Actualiza el proyecto.
2. Ejecuta `build_windows_exe.bat` en Windows.
3. Reemplaza la carpeta `App_Windows` antigua por la nueva.

---

Fin del manual.