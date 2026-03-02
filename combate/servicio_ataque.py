"""Servicio de dominio para preparar y resolver ataques sin dependencia de GUI."""

from __future__ import annotations

from dataclasses import dataclass

from combate.acciones import (
    obtener_valor_ataque_combate,
    obtener_valor_defensa_combate,
    resolver_ataque,
)
from combate.tipos import DefensaTipo, normalizar_tipo_defensa
from modelos.personaje import Mago, Mentalista, Personaje


@dataclass
class ContextoResolucionAtaque:
    resultado: dict
    tipo_defensa: str
    mod_ataque_base: int
    mod_defensa_base: int
    mod_sorpresa_defensa: int
    penalizador_defensas_adicionales: int
    penalizador_auto_ataque: int
    penalizador_auto_defensa: int
    ta_ataque: str


def _seleccionar_arma_por_etiqueta(armas, seleccion):
    if not seleccion or not seleccion.startswith("Arma "):
        return None
    try:
        indice = int(seleccion.split(":", 1)[0].split()[1]) - 1
        return list(armas)[indice]
    except (ValueError, IndexError):
        return None


def _resultado_tirada_manual(valor_base, tirada, modificador, cansancio):
    bono_cansancio = cansancio * 15
    return {
        "tipo": "normal",
        "valor_base": valor_base,
        "modificador": modificador,
        "cansancio": cansancio,
        "bono_cansancio": bono_cansancio,
        "tiradas": [tirada],
        "resultado_dados": tirada,
        "resultado_total": valor_base + modificador + bono_cansancio + tirada,
    }


def preparar_y_resolver_ataque(
    atacante_pc,
    defensor_pc,
    datos,
    proveedor_tirada_critica=None,
    proveedor_modificador_sorpresa=None,
):
    atacante = atacante_pc.personaje
    defensor = defensor_pc.personaje

    usar_estado_arma_actual = bool(datos.get("usar_estado_arma_actual", False))

    daño_ataque = datos["daño"]
    ta_ataque = datos["ta"]

    if usar_estado_arma_actual:
        if atacante_pc.arma_ataque_actual is not None:
            daño_ataque = atacante_pc.arma_ataque_actual.get("daño", daño_ataque)
            ta_ataque = atacante_pc.arma_ataque_actual.get("tipo_danio", ta_ataque)
    else:
        atacante_pc.configurar_arma_ataque(None)
        if isinstance(atacante, Personaje) and not isinstance(atacante, (Mago, Mentalista)):
            arma = _seleccionar_arma_por_etiqueta(getattr(atacante, "armas", []), datos.get("arma_ataque"))
            if arma is not None:
                atacante_pc.configurar_arma_ataque(arma)
                daño_ataque = arma.get("daño", daño_ataque)
                ta_ataque = arma.get("tipo_danio", ta_ataque)

    tipo_defensa = DefensaTipo.ESQUIVA.value
    if not isinstance(defensor, (Mago, Mentalista)):
        tipo_defensa = normalizar_tipo_defensa(datos.get("tipo_defensa", DefensaTipo.ESQUIVA.value)).value

    if not usar_estado_arma_actual:
        if tipo_defensa == DefensaTipo.PARADA.value:
            arma_parada = _seleccionar_arma_por_etiqueta(getattr(defensor, "armas", []), datos.get("arma_parada"))
            defensor_pc.configurar_arma_parada(arma_parada)
        else:
            defensor_pc.configurar_arma_parada(None)

    valor_ataque, _ = obtener_valor_ataque_combate(atacante_pc)
    valor_defensa, _ = obtener_valor_defensa_combate(defensor_pc)

    mod_ataque_base = datos["mod_ataque"]
    mod_sorpresa_base = 0
    if callable(proveedor_modificador_sorpresa):
        mod_sorpresa_base = proveedor_modificador_sorpresa(atacante_pc, defensor_pc)
    mod_sorpresa_defensa = int(datos.get("mod_sorpresa_defensa", mod_sorpresa_base))
    mod_defensa_base = datos["mod_defensa"] + mod_sorpresa_defensa
    penalizador_defensas_adicionales = defensor_pc.obtener_penalizador_defensas_multiples()

    cansancio_ataque = min(datos["cansancio_ataque"], atacante.puntos_cansancio)
    cansancio_defensa = min(datos["cansancio_defensa"], defensor.puntos_cansancio)
    atacante.puntos_cansancio = max(0, atacante.puntos_cansancio - cansancio_ataque)
    defensor.puntos_cansancio = max(0, defensor.puntos_cansancio - cansancio_defensa)

    penalizador_auto_ataque = atacante_pc.obtener_penalizador_automatico(cansancio_ataque)
    penalizador_auto_defensa = defensor_pc.obtener_penalizador_automatico(cansancio_defensa)

    resultado_ataque = datos.get("resultado_ataque_precalculado")
    resultado_defensa = datos.get("resultado_defensa_precalculado")
    if resultado_ataque is None and datos.get("tirada_ataque") is not None:
        resultado_ataque = _resultado_tirada_manual(
            valor_ataque,
            datos["tirada_ataque"],
            mod_ataque_base + penalizador_auto_ataque,
            cansancio_ataque,
        )
    if resultado_defensa is None and datos.get("tirada_defensa") is not None:
        resultado_defensa = _resultado_tirada_manual(
            valor_defensa,
            datos["tirada_defensa"],
            mod_defensa_base + penalizador_auto_defensa + penalizador_defensas_adicionales,
            cansancio_defensa,
        )

    mod_ataque_resolver = mod_ataque_base
    mod_defensa_resolver = mod_defensa_base + penalizador_defensas_adicionales

    resultado = resolver_ataque(
        atacante_pc,
        defensor_pc,
        modificador_ataque=mod_ataque_resolver,
        cansancio_gastado=cansancio_ataque,
        modificador_defensa=mod_defensa_resolver,
        cansancio_defensa=cansancio_defensa,
        resultado_ataque=resultado_ataque,
        resultado_defensa=resultado_defensa,
        tipo_defensa=tipo_defensa,
        daño_arma=daño_ataque,
        ta_ataque=ta_ataque,
        proveedor_tirada_critica=proveedor_tirada_critica,
    )

    return ContextoResolucionAtaque(
        resultado=resultado,
        tipo_defensa=tipo_defensa,
        mod_ataque_base=mod_ataque_base,
        mod_defensa_base=mod_defensa_base,
        mod_sorpresa_defensa=mod_sorpresa_defensa,
        penalizador_defensas_adicionales=penalizador_defensas_adicionales,
        penalizador_auto_ataque=penalizador_auto_ataque,
        penalizador_auto_defensa=penalizador_auto_defensa,
        ta_ataque=ta_ataque,
    )
