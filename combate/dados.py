"""
Sistema de dados para Ánima: Beyond Fantasy.
Implementa tiradas de d100 con reglas especiales de pifia y tiradas abiertas.
"""

import random


def configurar_semilla(semilla):
    """
    Configura la semilla del generador aleatorio.
    
    Args:
        semilla (int|None): Valor de semilla o None
    """
    random.seed(semilla)


def tirar_dado():
    """
    Tira un dado de 100 caras (1d100).
    
    Returns:
        int: Resultado de la tirada (1-100)
    """
    return random.randint(1, 100)


def tirar_d10():
    """
    Tira un dado de 10 caras (1d10).

    Returns:
        int: Resultado de la tirada (1-10)
    """
    return random.randint(1, 10)


def tirar_abierta_desde_primera(primera_tirada, umbral_inicial=90):
    """
    Continúa una tirada abierta partiendo de una primera tirada ya realizada.
    
    En Ánima, cuando se obtiene un resultado igual o superior al umbral inicial,
    se vuelve a tirar el dado. Cada nueva tirada incrementa el umbral en 1.
    Las tiradas abiertas NO tienen pifia (si sale 1-3, se suma normalmente).
    
    Args:
        primera_tirada (int): Resultado de la primera tirada
        umbral_inicial (int): Umbral a partir del cual se abre la tirada
        
    Returns:
        tuple: (resultado_total, tiradas)
    """
    tiradas = [primera_tirada]
    resultado_total = primera_tirada
    umbral_actual = umbral_inicial + 1
    
    while True:
        tirada = tirar_dado()
        tiradas.append(tirada)
        resultado_total += tirada
        
        if tirada < umbral_actual:
            break
        
        umbral_actual += 1
    
    return resultado_total, tiradas


def tirar_iniciativa(turno_base, permitir_abierta=True):
    """
    Calcula la iniciativa para un personaje según las reglas de Ánima.
    
    Reglas:
    - Se tira 1d100 y se suma al turno base
    - Pifia (1-3): -125, -100, -75 respectivamente
    - Tirada abierta (≥90): se vuelve a tirar con umbral creciente
    - Las tiradas abiertas no tienen pifia
    
    Args:
        turno_base (int): Turno base del personaje
        permitir_abierta (bool): Si se permiten tiradas abiertas (>= 90)
        
    Returns:
        tuple: (iniciativa_final, desglose_texto)
            - iniciativa_final (int): Iniciativa calculada
            - desglose_texto (str): Descripción de la tirada
    """
    primera_tirada = tirar_dado()
    
    # Verificar pifia (solo en la primera tirada)
    if primera_tirada == 1:
        penalizacion = -125
        iniciativa = turno_base + penalizacion
        desglose_texto = f"¡PIFIA! (1): {turno_base} - 125 = {iniciativa}"
        return iniciativa, desglose_texto
    
    elif primera_tirada == 2:
        penalizacion = -100
        iniciativa = turno_base + penalizacion
        desglose_texto = f"¡PIFIA! (2): {turno_base} - 100 = {iniciativa}"
        return iniciativa, desglose_texto
    
    elif primera_tirada == 3:
        penalizacion = -75
        iniciativa = turno_base + penalizacion
        desglose_texto = f"¡PIFIA! (3): {turno_base} - 75 = {iniciativa}"
        return iniciativa, desglose_texto
    
    # Verificar tirada abierta
    if permitir_abierta and primera_tirada >= 90:
        resultado_total, tiradas = tirar_abierta_desde_primera(primera_tirada, umbral_inicial=90)
        iniciativa = turno_base + resultado_total
        tiradas_str = " + ".join(str(t) for t in tiradas)
        desglose_texto = f"¡ABIERTA! ({tiradas_str}): {turno_base} + {resultado_total} = {iniciativa}"
        return iniciativa, desglose_texto
    
    # Tirada normal (4-89)
    iniciativa = turno_base + primera_tirada
    desglose_texto = f"{turno_base} + {primera_tirada} = {iniciativa}"
    return iniciativa, desglose_texto


def simular_tiradas_iniciativa(turno_base, num_simulaciones=10):
    """
    Simula múltiples tiradas de iniciativa para pruebas o estadísticas.
    
    Args:
        turno_base (int): Turno base del personaje
        num_simulaciones (int): Número de simulaciones a realizar
        
    Returns:
        list: Lista de tuplas (iniciativa, desglose) de cada simulación
    """
    resultados = []
    for _ in range(num_simulaciones):
        iniciativa, desglose = tirar_iniciativa(turno_base)
        resultados.append((iniciativa, desglose))
    return resultados


def resolver_pifia(primer_resultado):
    """
    Resuelve la tirada de pifia para ataques o defensas.
    
    Regla: se vuelve a tirar 1d100 y se modifica el resultado:
    - Pifia 1: +15
    - Pifia 2: +0
    - Pifia 3: -15
    
    Args:
        primer_resultado (int): Valor de la tirada inicial (1, 2 o 3)
        
    Returns:
        dict: Información de la pifia
    """
    segunda_tirada = tirar_dado()
    modificador = 0
    
    if primer_resultado == 1:
        modificador = 15
    elif primer_resultado == 3:
        modificador = -15
    
    resultado_modificado = segunda_tirada + modificador
    
    return {
        'tirada_original': primer_resultado,
        'tirada_pifia': segunda_tirada,
        'modificador': modificador,
        'resultado_final': resultado_modificado,
        'pifia_grave': resultado_modificado >= 80
    }


def tirar_ataque(valor_base, modificador=0, cansancio_gastado=0, permitir_abierta=True):
    """
    Realiza una tirada de ataque con reglas de pifia y abierta.
    
    Args:
        valor_base (int): Habilidad base de ataque
        modificador (int): Modificadores externos
        cansancio_gastado (int): Puntos de cansancio gastados (0-5)
        permitir_abierta (bool): Si se permiten tiradas abiertas (>= 90)
        
    Returns:
        dict: Detalles de la tirada de ataque
    """
    primera_tirada = tirar_dado()
    bono_cansancio = cansancio_gastado * 15
    
    if primera_tirada in (1, 2, 3):
        pifia_info = resolver_pifia(primera_tirada)
        return {
            'tipo': 'pifia',
            'valor_base': valor_base,
            'modificador': modificador,
            'cansancio': cansancio_gastado,
            'bono_cansancio': bono_cansancio,
            'primera_tirada': primera_tirada,
            'pifia': pifia_info
        }
    
    if permitir_abierta and primera_tirada >= 90:
        resultado_total, tiradas = tirar_abierta_desde_primera(primera_tirada, umbral_inicial=90)
        return {
            'tipo': 'abierta',
            'valor_base': valor_base,
            'modificador': modificador,
            'cansancio': cansancio_gastado,
            'bono_cansancio': bono_cansancio,
            'tiradas': tiradas,
            'resultado_dados': resultado_total,
            'resultado_total': valor_base + modificador + bono_cansancio + resultado_total
        }
    
    return {
        'tipo': 'normal',
        'valor_base': valor_base,
        'modificador': modificador,
        'cansancio': cansancio_gastado,
        'bono_cansancio': bono_cansancio,
        'tiradas': [primera_tirada],
        'resultado_dados': primera_tirada,
        'resultado_total': valor_base + modificador + bono_cansancio + primera_tirada
    }


def tirar_defensa(valor_base, modificador=0, cansancio_gastado=0, permitir_abierta=True):
    """
    Realiza una tirada de defensa con reglas de pifia y abierta.
    
    Args:
        valor_base (int): Habilidad base de defensa
        modificador (int): Modificadores externos
        cansancio_gastado (int): Puntos de cansancio gastados (0-5)
        permitir_abierta (bool): Si se permiten tiradas abiertas (>= 90)
        
    Returns:
        dict: Detalles de la tirada de defensa
    """
    primera_tirada = tirar_dado()
    bono_cansancio = cansancio_gastado * 15
    
    if primera_tirada in (1, 2, 3):
        pifia_info = resolver_pifia(primera_tirada)
        resultado_total = valor_base + modificador + bono_cansancio - pifia_info['resultado_final']
        return {
            'tipo': 'pifia',
            'valor_base': valor_base,
            'modificador': modificador,
            'cansancio': cansancio_gastado,
            'bono_cansancio': bono_cansancio,
            'primera_tirada': primera_tirada,
            'pifia': pifia_info,
            'resultado_total': resultado_total
        }
    
    if permitir_abierta and primera_tirada >= 90:
        resultado_total, tiradas = tirar_abierta_desde_primera(primera_tirada, umbral_inicial=90)
        return {
            'tipo': 'abierta',
            'valor_base': valor_base,
            'modificador': modificador,
            'cansancio': cansancio_gastado,
            'bono_cansancio': bono_cansancio,
            'tiradas': tiradas,
            'resultado_dados': resultado_total,
            'resultado_total': valor_base + modificador + bono_cansancio + resultado_total
        }
    
    return {
        'tipo': 'normal',
        'valor_base': valor_base,
        'modificador': modificador,
        'cansancio': cansancio_gastado,
        'bono_cansancio': bono_cansancio,
        'tiradas': [primera_tirada],
        'resultado_dados': primera_tirada,
        'resultado_total': valor_base + modificador + bono_cansancio + primera_tirada
    }
