"""Validaciones reutilizables para entrada de combate."""

from __future__ import annotations

import re


def entero_opcional(texto):
    """Devuelve `int` o `None` si está vacío/no numérico."""
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return int(texto)
    except ValueError:
        return None


def parsear_modificadores(texto):
    """Parsea expresiones tipo `+20-10+5` y devuelve su suma."""
    texto = (texto or "").replace(" ", "")
    if not texto:
        return 0
    if re.fullmatch(r"[+-]?\d+(?:[+-]\d+)*", texto) is None:
        raise ValueError("Formato inválido")
    return sum(int(m.group(0)) for m in re.finditer(r"[+-]?\d+", texto))
