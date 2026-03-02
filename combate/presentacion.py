"""Utilidades de presentación y narrativa para el combate."""

from __future__ import annotations

import random
from typing import Callable, Iterable

from combate.tipos import DefensaTipo, normalizar_tipo_defensa


def tabla_iniciativas_texto(orden: Iterable, resolver_nombre: Callable) -> str:
    """Genera una tabla ASCII de iniciativas para la ventana de combate."""
    filas = []
    for indice, pc in enumerate(orden, start=1):
        filas.append((indice, resolver_nombre(pc), pc.turno_base, pc.iniciativa, pc.desglose_iniciativa))

    ancho_nombre = max(8, min(72, max((len(f[1]) for f in filas), default=8)))
    linea = f"+----+{'-' * (ancho_nombre + 2)}+--------+-------+"
    cabecera = f"| #  | {'Nombre'.ljust(ancho_nombre)} | Turno  | Ini   |"
    salida = [linea, cabecera, linea]
    for indice, nombre, turno, ini, _desglose in filas:
        salida.append(f"| {str(indice).rjust(2)} | {nombre.ljust(ancho_nombre)} | {str(turno).rjust(6)} | {str(ini).rjust(5)} |")
    salida.append(linea)
    return "\n".join(salida)


def frase_ataque(nombre_atacante: str, nombre_defensor: str) -> str:
    return random.choice(
        [
            f"{nombre_atacante} ataca con furia a {nombre_defensor}.",
            f"{nombre_atacante} lanza un golpe decidido contra {nombre_defensor}.",
            f"{nombre_atacante} toma la iniciativa y carga sobre {nombre_defensor}.",
        ]
    )


def frase_defensa(nombre_defensor: str, tipo_defensa: str) -> str:
    if normalizar_tipo_defensa(tipo_defensa) == DefensaTipo.PARADA:
        opciones = [
            f"{nombre_defensor} intenta frenar el impacto con su arma.",
            f"{nombre_defensor} cruza su guardia para parar el ataque.",
        ]
    else:
        opciones = [
            f"{nombre_defensor} busca espacio para esquivar.",
            f"{nombre_defensor} reacciona con una evasión rápida.",
        ]
    return random.choice(opciones)


def frase_impacto(nombre_defensor: str, danio: int) -> str:
    return random.choice(
        [
            f"¡Impacto limpio! {nombre_defensor} sufre {danio} puntos de daño.",
            f"El ataque conecta de lleno: {nombre_defensor} pierde {danio} PV.",
            f"Golpe certero sobre {nombre_defensor}: daño {danio}.",
        ]
    )


def frase_critico(nombre_defensor: str) -> str:
    return random.choice(
        [
            f"¡{nombre_defensor} ha sufrido un crítico devastador!",
            f"El crítico castiga a {nombre_defensor} con violencia.",
            f"El golpe crítico deja a {nombre_defensor} en muy mala situación.",
        ]
    )


def frase_contraataque(nombre_defensor: str, bono: int) -> str:
    return f"{nombre_defensor} encuentra apertura para contraatacar: +{bono}."


def frase_sin_danio() -> str:
    return "Nadie logra daño en este intercambio."
