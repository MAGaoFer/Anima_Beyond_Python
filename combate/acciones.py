"""
Acciones de combate para Ánima: Beyond Fantasy.
"""

from combate.dados import tirar_ataque, tirar_defensa, tirar_dado, tirar_d10
from combate.resultados import (
    ChoqueArmasResultado,
    CriticoResultado,
    ResultadoAtaque,
    RoturaArmaduraResultado,
)
from combate.tipos import DefensaTipo, normalizar_tipo_defensa
from modelos.personaje import Mago, Mentalista, normalizar_ta, personaje_tiene_natura


def obtener_valor_ataque(personaje):
    """
    Obtiene el valor de ataque según el tipo de personaje.
    
    Args:
        personaje: Instancia del personaje
        
    Returns:
        tuple: (valor_ataque, etiqueta)
    """
    if isinstance(personaje, Mago):
        return personaje.proyeccion_magica, "Proyección Mágica"
    if isinstance(personaje, Mentalista):
        return personaje.proyeccion_psiquica, "Proyección Psíquica"
    return personaje.habilidad_ataque, "Habilidad de Ataque"


def obtener_valor_defensa(personaje):
    """
    Obtiene el valor de defensa según el tipo de personaje.
    
    Args:
        personaje: Instancia del personaje
        
    Returns:
        tuple: (valor_defensa, etiqueta)
    """
    if isinstance(personaje, Mago):
        return personaje.proyeccion_magica, "Proyección Mágica"
    if isinstance(personaje, Mentalista):
        return personaje.proyeccion_psiquica, "Proyección Psíquica"
    return personaje.habilidad_defensa, "Habilidad de Defensa"


def obtener_valor_ataque_combate(personaje_combate):
    """Obtiene valor de ataque considerando arma activa y overrides."""
    if personaje_combate.habilidad_ataque_override is not None:
        etiqueta = "Ataque con arma" if personaje_combate.arma_ataque_actual else "Ataque"
        return personaje_combate.habilidad_ataque_override, etiqueta
    return obtener_valor_ataque(personaje_combate.personaje)


def obtener_valor_defensa_combate(personaje_combate):
    """Obtiene valor de defensa considerando arma/escudo de parada."""
    if personaje_combate.habilidad_defensa_override is not None:
        etiqueta = "Parada con arma" if personaje_combate.arma_parada_actual else "Parada"
        return personaje_combate.habilidad_defensa_override, etiqueta
    return obtener_valor_defensa(personaje_combate.personaje)


def resolver_choque_armas(atacante_pc, defensor_pc):
    """
    Resuelve el choque de armas en caso de defensa con parada.

    Cada arma tira 1d10 y suma su rotura. Si ese valor supera la entereza
    del arma rival, el arma rival se rompe.
    """
    if atacante_pc.rotura_arma is None or atacante_pc.entereza_arma is None:
        return None
    if defensor_pc.rotura_arma is None or defensor_pc.entereza_arma is None:
        return None
    if isinstance(defensor_pc.personaje, (Mago, Mentalista)):
        return None
    if atacante_pc.esta_arma_rota(atacante_pc.arma_ataque_actual):
        return None
    if defensor_pc.esta_arma_rota(defensor_pc.arma_parada_actual):
        return None

    tirada_atacante = tirar_d10()
    tirada_defensor = tirar_d10()
    total_atacante = tirada_atacante + atacante_pc.rotura_arma
    total_defensor = tirada_defensor + defensor_pc.rotura_arma

    atacante_es_escudo = bool(getattr(atacante_pc, 'es_escudo', False))
    defensor_es_escudo = bool(defensor_pc.arma_parada_actual and defensor_pc.arma_parada_actual.get('es_escudo', False))

    rompe_arma_defensor = total_atacante > defensor_pc.entereza_arma
    rompe_arma_atacante = (total_defensor > atacante_pc.entereza_arma) if not defensor_es_escudo else False
    if atacante_es_escudo:
        rompe_arma_defensor = False

    if rompe_arma_defensor:
        defensor_pc.registrar_arma_rota(defensor_pc.arma_parada_actual)
        defensor_pc.arma_rota = True
    if rompe_arma_atacante:
        atacante_pc.registrar_arma_rota(atacante_pc.arma_ataque_actual)
        atacante_pc.arma_rota = True

    return ChoqueArmasResultado(
        tirada_atacante=tirada_atacante,
        tirada_defensor=tirada_defensor,
        rotura_atacante=atacante_pc.rotura_arma,
        rotura_defensor=defensor_pc.rotura_arma,
        total_atacante=total_atacante,
        total_defensor=total_defensor,
        entereza_atacante=atacante_pc.entereza_arma,
        entereza_defensor=defensor_pc.entereza_arma,
        rompe_arma_atacante=rompe_arma_atacante,
        rompe_arma_defensor=rompe_arma_defensor,
    )


def resolver_rotura_armadura(atacante_pc, defensor_pc, ta_ataque):
    """Resuelve posible rotura de armadura por arma con rotura (sin tirada de armadura)."""
    defensor = defensor_pc.personaje

    if isinstance(defensor, (Mago, Mentalista)):
        return None
    if atacante_pc.rotura_arma is None:
        return None
    if getattr(defensor, 'entereza_armadura', 0) <= 0:
        return None
    if getattr(defensor, 'obtener_ta', None) is None:
        return None

    ta_objetivo = defensor.obtener_ta(ta_ataque)
    if ta_objetivo <= 0:
        return None

    tirada = tirar_d10()
    total_rotura = tirada + atacante_pc.rotura_arma
    entereza = defensor.entereza_armadura
    rompe = total_rotura > entereza

    if rompe:
        defensor.romper_armadura()

    return RoturaArmaduraResultado(
        tirada=tirada,
        rotura_arma=atacante_pc.rotura_arma,
        total_rotura=total_rotura,
        entereza_armadura=entereza,
        ta_ataque=ta_ataque,
        ta_objetivo=ta_objetivo,
        rompe_armadura=rompe,
    )


def resolver_ataque(atacante_pc, defensor_pc, modificador_ataque=0, cansancio_gastado=0,
                    modificador_defensa=0, cansancio_defensa=0, daño_arma=None,
                    resultado_ataque=None, resultado_defensa=None,
                    tipo_defensa="Esquiva", proveedor_tirada_critica=None,
                    ta_ataque=None):
    """
    Resuelve una acción de ataque completa.
    
    Args:
        atacante_pc: PersonajeCombate atacante
        defensor_pc: PersonajeCombate defensor
        modificador_ataque (int): Modificadores al ataque
        cansancio_gastado (int): Puntos de cansancio gastados (0-5)
        modificador_defensa (int): Modificadores a la defensa
        cansancio_defensa (int): Puntos de cansancio gastados en defensa (0-5)
        daño_arma (int, opcional): Daño del arma utilizada
        resultado_ataque (dict, opcional): Tirada de ataque ya calculada
        resultado_defensa (dict, opcional): Tirada de defensa ya calculada
        tipo_defensa (str): "Esquiva" o "Parada"
        proveedor_tirada_critica (callable, opcional): Proveedor de tiradas para crítico
        
    Returns:
        dict: Resultado detallado del ataque
    """
    atacante = atacante_pc.personaje
    defensor = defensor_pc.personaje
    tipo_defensa_enum = normalizar_tipo_defensa(tipo_defensa)
    tipo_defensa_txt = tipo_defensa_enum.value

    valor_ataque, etiqueta_ataque = obtener_valor_ataque_combate(atacante_pc)
    valor_defensa, etiqueta_defensa = obtener_valor_defensa_combate(defensor_pc)
    ta_ataque_codigo = normalizar_ta(ta_ataque or atacante_pc.ta_ataque or getattr(atacante, 'arma_tipo_danio', 'FIL') or 'FIL')
    
    # Tirada de ataque
    if resultado_ataque is None:
        penalizador_auto_ataque = atacante_pc.obtener_penalizador_automatico(cansancio_gastado)
        resultado_ataque = tirar_ataque(
            valor_ataque,
            modificador_ataque + penalizador_auto_ataque,
            cansancio_gastado,
            permitir_abierta=personaje_tiene_natura(atacante),
        )
    
    if resultado_ataque['tipo'] == 'pifia':
        return ResultadoAtaque(
            ataque=resultado_ataque,
            defensa=None,
            impacto=False,
            contraataque=False,
            bono_contraataque=0,
            diferencia=0,
            danio_aplicado=0,
            a_la_defensiva=False,
            tipo_defensa=tipo_defensa_txt,
            choque_armas=None,
            rotura_armadura=None,
            ta_ataque=ta_ataque_codigo,
            ta_objetivo=0,
            etiqueta_ataque=etiqueta_ataque,
            etiqueta_defensa=etiqueta_defensa,
        ).a_diccionario()
    
    # Tirada de defensa
    if resultado_defensa is None:
        penalizador_auto_defensa = defensor_pc.obtener_penalizador_automatico(cansancio_defensa)
        resultado_defensa = tirar_defensa(
            valor_defensa,
            modificador_defensa + penalizador_auto_defensa,
            cansancio_defensa,
            permitir_abierta=personaje_tiene_natura(defensor),
        )
    defensor_pc.registrar_defensa()
    ataque_total = resultado_ataque['resultado_total']
    defensa_total = resultado_defensa['resultado_total']
    choque_armas = resolver_choque_armas(atacante_pc, defensor_pc) if tipo_defensa_enum == DefensaTipo.PARADA else None
    
    if ataque_total > defensa_total:
        diferencia = ataque_total - defensa_total
        ta_objetivo = defensor.obtener_ta(ta_ataque_codigo) if hasattr(defensor, 'obtener_ta') else getattr(defensor, 'armadura', 0)
        reduccion_armadura = 20 + (ta_objetivo * 10)
        diferencia_final = diferencia - reduccion_armadura
        a_la_defensiva = diferencia_final <= 5
        
        danio_aplicado = 0
        critico = None
        
        if not a_la_defensiva and diferencia_final > 0:
            daño_arma_valor = daño_arma if daño_arma is not None else atacante.daño
            danio_aplicado = int(daño_arma_valor * (diferencia_final / 100))
            pv_antes = defensor.puntos_vida
            defensor.puntos_vida = max(0, defensor.puntos_vida - danio_aplicado)
            
            if pv_antes > 0 and danio_aplicado >= (pv_antes / 2):
                if proveedor_tirada_critica is not None:
                    tirada_atacante = proveedor_tirada_critica('ataque', atacante_pc)
                    tirada_defensor = proveedor_tirada_critica('defensa', defensor_pc)
                    if tirada_atacante is None:
                        tirada_atacante = tirar_dado()
                    if tirada_defensor is None:
                        tirada_defensor = tirar_dado()
                else:
                    tirada_atacante = tirar_dado()
                    tirada_defensor = tirar_dado()
                resistencia_fisica = getattr(defensor, 'resistencia_fisica', 0)
                resultado_critico = (danio_aplicado + tirada_atacante) - (tirada_defensor + resistencia_fisica)
                critico = CriticoResultado(
                    daño_inicial=danio_aplicado,
                    tirada_atacante=tirada_atacante,
                    tirada_defensor=tirada_defensor,
                    resistencia_fisica=resistencia_fisica,
                    resultado=resultado_critico,
                    tiene_consecuencias=resultado_critico > 0,
                )
                defensor_pc.aplicar_critico(resultado_critico)

            if defensor.puntos_vida <= 0:
                defensor_pc.marcar_inconsciente()

        rotura_armadura = resolver_rotura_armadura(atacante_pc, defensor_pc, ta_ataque_codigo)
        
        return ResultadoAtaque(
            ataque=resultado_ataque,
            defensa=resultado_defensa,
            impacto=True,
            contraataque=False,
            bono_contraataque=0,
            diferencia=diferencia,
            danio_aplicado=danio_aplicado,
            a_la_defensiva=a_la_defensiva,
            tipo_defensa=tipo_defensa_txt,
            choque_armas=choque_armas,
            rotura_armadura=rotura_armadura,
            ta_ataque=ta_ataque_codigo,
            ta_objetivo=ta_objetivo,
            etiqueta_ataque=etiqueta_ataque,
            etiqueta_defensa=etiqueta_defensa,
            reduccion_armadura=reduccion_armadura,
            diferencia_final=diferencia_final,
            critico=critico,
        ).a_diccionario()
    
    if defensa_total > ataque_total:
        diferencia = defensa_total - ataque_total
        bono_contraataque = diferencia // 2
        
        return ResultadoAtaque(
            ataque=resultado_ataque,
            defensa=resultado_defensa,
            impacto=False,
            contraataque=True,
            bono_contraataque=bono_contraataque,
            diferencia=diferencia,
            danio_aplicado=0,
            a_la_defensiva=False,
            tipo_defensa=tipo_defensa_txt,
            choque_armas=choque_armas,
            rotura_armadura=None,
            ta_ataque=ta_ataque_codigo,
            ta_objetivo=0,
            etiqueta_ataque=etiqueta_ataque,
            etiqueta_defensa=etiqueta_defensa,
            critico=None,
        ).a_diccionario()
    
    return ResultadoAtaque(
        ataque=resultado_ataque,
        defensa=resultado_defensa,
        impacto=False,
        contraataque=False,
        bono_contraataque=0,
        diferencia=0,
        danio_aplicado=0,
        a_la_defensiva=False,
        tipo_defensa=tipo_defensa_txt,
        choque_armas=choque_armas,
        rotura_armadura=None,
        ta_ataque=ta_ataque_codigo,
        ta_objetivo=0,
        etiqueta_ataque=etiqueta_ataque,
        etiqueta_defensa=etiqueta_defensa,
        critico=None,
    ).a_diccionario()
