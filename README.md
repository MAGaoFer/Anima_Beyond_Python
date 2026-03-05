# Gestor de Personajes - Ánima: Beyond Fantasy

Aplicación para crear, editar e importar personajes de **Ánima: Beyond Fantasy**, con dos modos de uso:

- **GUI (recomendado)** con Tkinter
- **CLI** para uso en terminal

También incluye un sistema de combate con iniciativas, rondas, ataque/defensa y soporte para poderes.
También incluye un **Modo Secundarias** para gestionar tiradas de habilidades secundarias y resistencias.

## Changelog

El historial de cambios está en `CHANGELOG.md`.

## Qué hace la aplicación

- Crear personajes de distintos arquetipos (Guerrero, Domine, Mago, Mentalista, Warlock y mixtos)
- Guardar y cargar personajes en JSON
- Importar personajes desde fichas Excel (`.xlsm` / `.xlsx`)
- Extraer e importar habilidades secundarias desde Excel
- Gestionar combate con:
  - iniciativa (automática o manual)
  - ataque/defensa
  - pifias, tiradas abiertas y críticos
  - poderes mágicos y mentales
  - acciones de recurso (incluyendo acumulación de Zeón/Ki)
- Gestionar modo secundarias con:
  - tiradas de habilidades secundarias con pifia/abierta
  - gasto de cansancio y modificadores
  - cálculo de dificultad alcanzada
  - tiradas de resistencias (RF/RE/RV/RM/RP) sin pifia ni abierta

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

### Modo terminal (CLI)

**Linux / macOS**

```bash
python3 main.py --cli
```

## Uso rápido

1. Inicia la app en GUI (`main.py`).
2. Crea personaje o impórtalo desde Excel.
3. Guarda los cambios.
4. Abre **Combate** para añadir PJ/PNJ y empezar rondas.
5. Abre **Modo Secundarias** para tirar habilidades secundarias y resistencias.

## Windows para usuarios

Pasos para usuario final:

1. Ir a **Releases** del repositorio.
2. Descargar `AnimaBeyondFantasy_Windows_Portable.zip`.
3. Descomprimir el ZIP en una carpeta con permisos de escritura (por ejemplo, Escritorio o Documentos).
4. Ejecutar `AnimaBeyondFantasy.exe`.

Los personajes se guardarán en `Personajes/personajes/` junto a la aplicación.

## Notas

- Los personajes se guardan en `datos/personajes/`.
- Los nombres de archivo de personaje reemplazan espacios por `_`.
- El manual editable está en `docs/Manual_Usuario.md`.
- Plantilla para texto de release: `docs/PLANTILLA_RELEASE_WINDOWS.md`.

## Licencia

Este proyecto está licenciado bajo **GNU Affero General Public License v3.0 (AGPLv3)**.

Consulta el texto completo en [LICENSE](LICENSE).
