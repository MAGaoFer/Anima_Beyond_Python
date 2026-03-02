# Gestor de Personajes - Ánima: Beyond Fantasy

Aplicación para crear, editar e importar personajes de **Ánima: Beyond Fantasy**, con dos modos de uso:

- **GUI (recomendado)** con Tkinter
- **CLI** para uso en terminal

También incluye un sistema de combate con iniciativas, rondas, ataque/defensa y soporte para poderes.

## Qué hace la aplicación

- Crear personajes de distintos arquetipos (Guerrero, Domine, Mago, Mentalista, Warlock y mixtos)
- Guardar y cargar personajes en JSON
- Importar personajes desde fichas Excel (`.xlsm` / `.xlsx`)
- Gestionar combate con:
  - iniciativa (automática o manual)
  - ataque/defensa
  - pifias, tiradas abiertas y críticos
  - poderes mágicos y mentales
  - acciones de recurso (incluyendo acumulación de Zeón/Ki)

## Requisitos

- Python 3.10 o superior (recomendado 3.12)
- Dependencias Python de `requirements.txt`
- En Linux, si falta Tkinter, instalar `python3-tk`

## Instalación

### Linux (entorno virtual recomendado)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si falla Tkinter:

```bash
sudo apt-get update
sudo apt-get install -y python3-tk
```

### Linux (opcional con conda)

```bash
conda create -n anima python=3.12 -y
conda activate anima
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Cómo ejecutar

### Interfaz gráfica (recomendado)

**Linux / macOS**

```bash
python3 main.py
```

**Windows**

```cmd
python main.py
```

### Modo terminal (CLI)

**Linux / macOS**

```bash
python3 main.py --cli
```

**Windows**

```cmd
python main.py --cli
```

## Uso rápido

1. Inicia la app en GUI (`main.py`).
2. Crea personaje o impórtalo desde Excel.
3. Guarda los cambios.
4. Abre **Combate** para añadir PJ/PNJ y empezar rondas.

## Ejecutable de Windows

Si quieres generar `.exe` en Windows:

```cmd
build_windows_exe.bat
```

El resultado se prepara en la carpeta `App_Windows/`.

## Tests

Para ejecutar la suite:

```bash
python -m pytest
```

## Estructura (resumen)

- `main.py`: entrada principal (GUI/CLI)
- `interfaz/`: ventanas y flujo de GUI
- `combate/`: motor de combate
- `modelos/`: modelos de personaje
- `almacenamiento/`: persistencia JSON e importador Excel
- `tests/`: tests automáticos

## Notas

- Los personajes se guardan en `datos/personajes/`.
- Los nombres de archivo de personaje reemplazan espacios por `_`.
- El manual editable está en `docs/Manual_Usuario.md`.

## Licencia

Este proyecto está licenciado bajo **GNU Affero General Public License v3.0 (AGPLv3)**.

Consulta el texto completo en [LICENSE](LICENSE).
