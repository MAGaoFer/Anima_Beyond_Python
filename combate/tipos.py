"""Tipos y enums de dominio para combate."""

from __future__ import annotations

from enum import Enum


class DefensaTipo(str, Enum):
    ESQUIVA = "Esquiva"
    PARADA = "Parada"


def normalizar_tipo_defensa(valor) -> DefensaTipo:
    """Convierte texto/enum en `DefensaTipo` válido."""
    if isinstance(valor, DefensaTipo):
        return valor
    texto = str(valor or "").strip().lower()
    if texto == "parada":
        return DefensaTipo.PARADA
    return DefensaTipo.ESQUIVA
