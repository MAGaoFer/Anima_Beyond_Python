"""Estructuras de resultado del motor de combate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CriticoResultado:
    daño_inicial: int
    tirada_atacante: int
    tirada_defensor: int
    resistencia_fisica: int
    resultado: int
    tiene_consecuencias: bool


@dataclass
class ChoqueArmasResultado:
    tirada_atacante: int
    tirada_defensor: int
    rotura_atacante: int
    rotura_defensor: int
    total_atacante: int
    total_defensor: int
    entereza_atacante: int
    entereza_defensor: int
    rompe_arma_atacante: bool
    rompe_arma_defensor: bool


@dataclass
class RoturaArmaduraResultado:
    tirada: int
    rotura_arma: int
    total_rotura: int
    entereza_armadura: int
    ta_ataque: str
    ta_objetivo: int
    rompe_armadura: bool


@dataclass
class ResultadoAtaque:
    ataque: dict[str, Any]
    defensa: dict[str, Any] | None
    impacto: bool
    contraataque: bool
    bono_contraataque: int
    diferencia: int
    danio_aplicado: int
    a_la_defensiva: bool
    tipo_defensa: str
    choque_armas: ChoqueArmasResultado | None
    rotura_armadura: RoturaArmaduraResultado | None
    ta_ataque: str
    ta_objetivo: int
    etiqueta_ataque: str
    etiqueta_defensa: str
    reduccion_armadura: int = 0
    diferencia_final: int = 0
    critico: CriticoResultado | None = None

    def a_diccionario(self) -> dict[str, Any]:
        return asdict(self)
