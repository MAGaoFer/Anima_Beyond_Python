"""Reglas puras de combate reutilizables y testeables."""

from __future__ import annotations


def modificador_sorpresa(iniciativa_atacante: int, iniciativa_defensor: int) -> int:
    """Devuelve penalizador de defensa por sorpresa según diferencia de iniciativa."""
    return -90 if (iniciativa_atacante - iniciativa_defensor) > 150 else 0
