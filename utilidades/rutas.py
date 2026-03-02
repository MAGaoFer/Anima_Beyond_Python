"""Helpers de rutas para desarrollo y ejecutables empaquetados."""

import os
import sys
from pathlib import Path


NOMBRE_APP_DATOS = "Anima_Beyond_Python"


def en_modo_ejecutable():
    """Indica si la app se está ejecutando como binario empaquetado."""
    return bool(getattr(sys, "frozen", False))


def ruta_base_recursos():
    """Devuelve la ruta base para acceder a recursos empaquetados."""
    if en_modo_ejecutable() and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent.parent


def ruta_recurso(*partes):
    """Construye una ruta a un recurso del proyecto."""
    return ruta_base_recursos().joinpath(*partes)


def ruta_datos_persistentes(nombre_app=NOMBRE_APP_DATOS):
    """Devuelve el directorio de datos persistentes del usuario."""
    if en_modo_ejecutable() and os.name == "nt":
        return Path(sys.executable).resolve().parent / "Personajes"

    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    return base / nombre_app / "datos"
