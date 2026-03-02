"""
Sistema de combate para Ánima: Beyond Fantasy
"""
from .dados import tirar_dado, tirar_iniciativa, tirar_ataque, tirar_defensa
from .iniciativa import calcular_iniciativa
from .acciones import resolver_ataque
from .gestor_combate import GestorCombate

__all__ = [
	'tirar_dado',
	'tirar_iniciativa',
	'tirar_ataque',
	'tirar_defensa',
	'calcular_iniciativa',
	'resolver_ataque',
	'GestorCombate'
]
