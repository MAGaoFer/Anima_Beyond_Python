#!/usr/bin/env python3
"""
Sistema de Gestión de Personajes para Ánima: Beyond Fantasy
Aplicación CLI para crear, gestionar y guardar personajes.
"""

import sys
import csv
import shutil
import textwrap
from modelos.personaje import (
    Domine,
    GuerreroMentalista,
    HechiceroMentalista,
    Mago,
    Mentalista,
    Personaje,
    TA_CODIGOS,
    Warlock,
    normalizar_ta,
    personaje_tiene_ki,
    personaje_tiene_natura,
)
from almacenamiento.almacenamiento_json import AlmacenamientoPersonajes
from combate.gestor_combate import GestorCombate
from combate.acciones import (
    resolver_ataque,
    obtener_valor_ataque,
    obtener_valor_defensa,
    obtener_valor_ataque_combate,
    obtener_valor_defensa_combate,
)
from combate.tipos import DefensaTipo
from combate.iniciativa import PersonajeCombate
from combate.servicio_ataque import preparar_y_resolver_ataque
from combate.dados import configurar_semilla, tirar_ataque
from utilidades.rutas import ruta_recurso


def limpiar_pantalla():
    """Limpia la pantalla de la consola (multiplataforma)."""
    print("\n" * 50)


def mostrar_encabezado():
    """Muestra el encabezado de la aplicación."""
    print("╔═══════════════════════════════════════════════════╗")
    print("║   ÁNIMA: BEYOND FANTASY - GESTOR DE PERSONAJES   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()


def mostrar_menu():
    """Muestra el menú principal de opciones."""
    print("\n┌───────────────── MENÚ PRINCIPAL ─────────────────┐")
    print("│  1. Crear nuevo personaje                        │")
    print("│  2. Listar todos los personajes                  │")
    print("│  3. Ver detalles de un personaje                 │")
    print("│  4. Editar personaje                             │")
    print("│  5. Eliminar personaje                           │")
    print("│  6. Iniciar combate                              │")
    print("│  7. Modo test                                    │")
    print("│  8. Salir                                        │")
    print("└──────────────────────────────────────────────────┘")


def solicitar_numero(mensaje, minimo=0, maximo=None):
    """
    Solicita un número al usuario con validación.
    
    Args:
        mensaje (str): Mensaje a mostrar
        minimo (int): Valor mínimo permitido
        maximo (int, opcional): Valor máximo permitido
        
    Returns:
        int: Número válido ingresado por el usuario
    """
    while True:
        try:
            valor = int(input(mensaje))
            if valor < minimo:
                print(f"⚠ El valor debe ser al menos {minimo}")
                continue
            if maximo is not None and valor > maximo:
                print(f"⚠ El valor no puede ser mayor que {maximo}")
                continue
            return valor
        except ValueError:
            print("⚠ Por favor, introduce un número válido")


def solicitar_entero(mensaje, minimo=None, maximo=None):
    """
    Solicita un número entero al usuario, permitiendo valores negativos.
    
    Args:
        mensaje (str): Mensaje a mostrar
        minimo (int, opcional): Valor mínimo permitido
        maximo (int, opcional): Valor máximo permitido
        
    Returns:
        int: Número válido ingresado por el usuario
    """
    while True:
        try:
            valor = int(input(mensaje))
            if minimo is not None and valor < minimo:
                print(f"⚠ El valor debe ser al menos {minimo}")
                continue
            if maximo is not None and valor > maximo:
                print(f"⚠ El valor no puede ser mayor que {maximo}")
                continue
            return valor
        except ValueError:
            print("⚠ Por favor, introduce un número válido")


def solicitar_texto(mensaje, permitir_vacio=False):
    """
    Solicita texto al usuario con validación.
    
    Args:
        mensaje (str): Mensaje a mostrar
        permitir_vacio (bool): Si se permite texto vacío
        
    Returns:
        str: Texto ingresado por el usuario
    """
    while True:
        texto = input(mensaje).strip()
        if not texto and not permitir_vacio:
            print("⚠ Este campo no puede estar vacío")
            continue
        return texto


def es_respuesta_si(respuesta):
    """Devuelve True si la respuesta textual representa un sí."""
    return respuesta.strip().lower() in ['s', 'si', 'sí']


def solicitar_control_personaje():
    """Solicita si el personaje se controla como PJ o PNJ."""
    print("\nControl del personaje:")
    print("  1. PJ (tiradas manuales)")
    print("  2. PNJ (tiradas automáticas)")
    opcion = solicitar_numero("Selecciona control (1-2): ", minimo=1, maximo=2)
    return opcion == 1


def solicitar_natura_personaje(es_pj, valor_actual=True):
    """Solicita si un PNJ tiene Natura. Los PJ siempre la tienen."""
    if es_pj:
        return True

    print("\nNatura del PNJ:")
    print("  1. Con Natura (puede abrir tiradas)")
    print("  2. Sin Natura (no abre tiradas)")
    recomendada = 1 if valor_actual else 2
    opcion = solicitar_numero(
        f"Selecciona Natura (1-2, recomendado {recomendada}): ",
        minimo=1,
        maximo=2,
    )
    return opcion == 1


def solicitar_ta(mensaje="TA (FIL/CON/PEN/CAL/ELE/FRI/ENE): "):
    """Solicita y valida una TA."""
    while True:
        valor = solicitar_texto(mensaje).upper()
        try:
            return normalizar_ta(valor)
        except ValueError:
            print("⚠ TA inválida. Usa: FIL, CON, PEN, CAL, ELE, FRI o ENE")


def solicitar_armaduras_ta():
    """Solicita las TA de armadura por tipo y su entereza."""
    print("\n--- Tipos de Armadura (TA) ---")
    armaduras_ta = {}
    for codigo in TA_CODIGOS:
        armaduras_ta[codigo] = solicitar_numero(f"TA {codigo}: ", minimo=0)
    entereza_armadura = solicitar_numero("Entereza de la armadura: ", minimo=0)
    return armaduras_ta, entereza_armadura


def solicitar_datos_arma(opcional=True):
    """Solicita datos de arma principal para guardarlos en el personaje."""
    if opcional:
        definir_arma = solicitar_texto("¿Definir arma principal del personaje? (s/n): ")
        if not es_respuesta_si(definir_arma):
            return None, None, None, None, None, None

    print("\n--- Arma principal ---")
    arma_nombre = solicitar_texto("Nombre del arma: ")
    arma_turno = solicitar_numero("Turno del arma: ", minimo=0)
    arma_danio = solicitar_numero("Daño del arma: ", minimo=0)
    arma_rotura = solicitar_numero("Rotura del arma: ", minimo=0)
    arma_entereza = solicitar_numero("Entereza del arma: ", minimo=0)
    arma_tipo_danio = solicitar_ta("Tipo de daño del arma (FIL/CON/PEN/CAL/ELE/FRI/ENE): ")
    return arma_nombre, arma_turno, arma_danio, arma_rotura, arma_entereza, arma_tipo_danio


def solicitar_datos_arma_completa(opcional=True, ataque_base=0):
    """Solicita datos completos de arma (incluye habilidades y escudo)."""
    if opcional:
        definir_arma = solicitar_texto("¿Definir arma? (s/n): ")
        if not es_respuesta_si(definir_arma):
            return None

    arma_nombre, arma_turno, arma_danio, arma_rotura, arma_entereza, arma_tipo_danio = solicitar_datos_arma(opcional=False)
    habilidad_ataque = solicitar_numero(f"Habilidad de ataque con {arma_nombre}: ", minimo=0)
    habilidad_parada = solicitar_numero(f"Habilidad de parada con {arma_nombre}: ", minimo=0)
    es_escudo = es_respuesta_si(solicitar_texto("¿Es un escudo? (s/n): "))
    if es_escudo:
        habilidad_ataque = min(habilidad_ataque, ataque_base)
        arma_danio = min(arma_danio or 0, 20)

    return {
        'nombre': arma_nombre,
        'turno': arma_turno,
        'daño': arma_danio,
        'rotura': arma_rotura,
        'entereza': arma_entereza,
        'tipo_danio': arma_tipo_danio,
        'habilidad_ataque': habilidad_ataque,
        'habilidad_parada': habilidad_parada,
        'es_escudo': es_escudo
    }


def seleccionar_arma_lista(armas, titulo, permitir_cancelar=True):
    """Selecciona una arma de una lista de armas."""
    if not armas:
        return None
    print(f"\n{titulo}")
    for i, arma in enumerate(armas, 1):
        escudo = " [Escudo]" if arma.get('es_escudo') else ""
        print(f"  {i}. {arma['nombre']}{escudo} (ATQ {arma['habilidad_ataque']} / PAR {arma['habilidad_parada']} / T {arma['turno']})")
    tope = len(armas)
    if permitir_cancelar:
        print(f"  {tope + 1}. Cancelar")
        tope += 1
    opcion = solicitar_numero(f"Selecciona (1-{tope}): ", minimo=1, maximo=tope)
    if permitir_cancelar and opcion == tope:
        return None
    return armas[opcion - 1]


def sincronizar_arma_principal_desde_lista(personaje):
    """Sincroniza campos de arma principal usando la primera arma del arsenal."""
    if getattr(personaje, 'armas', None):
        principal = personaje.armas[0]
        personaje.arma_nombre = principal.get('nombre')
        personaje.arma_turno = principal.get('turno')
        personaje.arma_danio = principal.get('daño')
        personaje.arma_rotura = principal.get('rotura')
        personaje.arma_entereza = principal.get('entereza')
        personaje.arma_tipo_danio = principal.get('tipo_danio')
        return
    personaje.arma_nombre = None
    personaje.arma_turno = None
    personaje.arma_danio = None
    personaje.arma_rotura = None
    personaje.arma_entereza = None
    personaje.arma_tipo_danio = None


def obtener_resumen_arma(personaje):
    """Devuelve resumen breve de arma guardada en personaje."""
    if getattr(personaje, 'armas', None):
        return f"{len(personaje.armas)} arma(s) registradas"
    if not getattr(personaje, 'arma_nombre', None):
        return "Sin arma guardada"
    return (
        f"{personaje.arma_nombre} "
        f"(T:{personaje.arma_turno}, D:{personaje.arma_danio}, "
        f"R:{personaje.arma_rotura}, E:{personaje.arma_entereza}, TD:{personaje.arma_tipo_danio})"
    )


def seleccionar_participante_combate(gestor, permitir_cancelar=True):
    """Permite seleccionar cualquier participante del combate."""
    candidatos = [pc for pc in gestor.orden_iniciativa]
    if not candidatos:
        return None

    print("\nParticipantes:")
    for i, pc in enumerate(candidatos, 1):
        estado = "Inconsciente" if pc.inconsciente else f"PV: {pc.personaje.puntos_vida}"
        print(f"  {i}. {pc.personaje.nombre} ({estado})")

    tope = len(candidatos)
    if permitir_cancelar:
        print(f"  {tope + 1}. Cancelar")
        tope += 1

    opcion = solicitar_numero(f"\nSelecciona participante (1-{tope}): ", minimo=1, maximo=tope)
    if permitir_cancelar and opcion == tope:
        return None
    return candidatos[opcion - 1]


def describir_penalizador_automatico(pc, cansancio_gastado):
    """Describe el penalizador automático para una acción."""
    penalizador = pc.obtener_penalizador_automatico(cansancio_gastado)
    if penalizador == 0:
        return "Sin penalizador automático", 0
    return f"Penalizador automático aplicado: {penalizador}", penalizador


def obtener_tablas_disponibles():
    """Obtiene los CSV disponibles en la carpeta tablas/."""
    ruta_tablas = ruta_recurso('tablas')
    if not ruta_tablas.exists() or not ruta_tablas.is_dir():
        return []
    return sorted(ruta_tablas.glob('*.csv'))


def detectar_delimitador_csv(texto):
    """Detecta delimitador CSV (si falla, usa coma)."""
    candidatos = [',', ';', '\t', '|']
    try:
        dialecto = csv.Sniffer().sniff(texto[:2048], delimiters=''.join(candidatos))
        return dialecto.delimiter
    except csv.Error:
        return ','


def leer_filas_csv(ruta_csv):
    """Lee filas de un CSV conservando cabecera y columnas."""
    with open(ruta_csv, 'r', encoding='utf-8', newline='') as archivo:
        texto = archivo.read()

    if not texto.strip():
        return []

    delimitador = detectar_delimitador_csv(texto)
    lector = csv.reader(texto.splitlines(), delimiter=delimitador)
    filas = [fila for fila in lector if any(col.strip() for col in fila)]

    if not filas:
        return []

    max_cols = max(len(fila) for fila in filas)
    filas_normalizadas = []
    for fila in filas:
        normalizada = [col.strip() for col in fila]
        if len(normalizada) < max_cols:
            normalizada.extend([''] * (max_cols - len(normalizada)))
        filas_normalizadas.append(normalizada)
    return filas_normalizadas


def ajustar_anchos_columnas(filas):
    """Calcula anchos de columna adaptados al ancho de terminal."""
    cabecera = filas[0]
    columnas = len(cabecera)
    alto_max_contenido = 40
    anchos = []

    for indice in range(columnas):
        max_len = max(len(str(fila[indice])) for fila in filas)
        nombre_col = cabecera[indice].lower()
        tope = 52 if 'nota' in nombre_col else 28
        anchos.append(min(max(max_len, len(cabecera[indice]), 8), tope))

    ancho_terminal = shutil.get_terminal_size((120, 20)).columns
    ancho_disponible = max(60, ancho_terminal - (columnas * 3 + 1))

    while sum(anchos) > ancho_disponible:
        idx_mayor = max(range(columnas), key=lambda i: anchos[i])
        if anchos[idx_mayor] <= 8:
            break
        anchos[idx_mayor] -= 1

    anchos = [min(alto_max_contenido, ancho) for ancho in anchos]
    return anchos


def renderizar_tabla_csv(filas):
    """Renderiza filas CSV como tabla visual con ajuste de texto."""
    if not filas:
        return "(Tabla vacía)"

    anchos = ajustar_anchos_columnas(filas)
    columnas = len(anchos)

    def borde(izq, centro, der, fill='─'):
        return izq + centro.join(fill * (ancho + 2) for ancho in anchos) + der

    def envolver_celda(texto, ancho):
        texto = str(texto).strip()
        if not texto:
            return ['']
        return textwrap.wrap(texto, width=ancho, break_long_words=True, break_on_hyphens=False) or ['']

    def renderizar_fila(celdas):
        celdas_envueltas = [envolver_celda(celdas[i], anchos[i]) for i in range(columnas)]
        altura = max(len(bloque) for bloque in celdas_envueltas)
        lineas = []
        for linea_idx in range(altura):
            segmentos = []
            for col_idx in range(columnas):
                contenido = celdas_envueltas[col_idx][linea_idx] if linea_idx < len(celdas_envueltas[col_idx]) else ''
                segmentos.append(f" {contenido.ljust(anchos[col_idx])} ")
            lineas.append("│" + "│".join(segmentos) + "│")
        return lineas

    salida = [borde('┌', '┬', '┐')]
    salida.extend(renderizar_fila(filas[0]))
    salida.append(borde('├', '┼', '┤'))

    for i, fila in enumerate(filas[1:], start=1):
        salida.extend(renderizar_fila(fila))
        if i < len(filas) - 1:
            salida.append(borde('├', '┼', '┤'))

    salida.append(borde('└', '┴', '┘'))
    return "\n".join(salida)


def mostrar_tablas_modificadores():
    """Permite visualizar tablas CSV de modificadores durante el combate."""
    tablas = obtener_tablas_disponibles()

    if not tablas:
        print("\n⚠ No se encontraron tablas CSV en la carpeta 'tablas/'.")
        input("\nPresiona Enter para continuar...")
        return

    while True:
        print("\n┌─── TABLAS DE CONSULTA ───┐")
        for i, ruta in enumerate(tablas, 1):
            print(f"│ {i:2}. {ruta.name.ljust(22)} │")
        print(f"│ {len(tablas) + 1:2}. Volver{' ' * 19}│")
        print("└───────────────────────────┘")

        opcion = solicitar_numero(
            f"\nSelecciona tabla (1-{len(tablas) + 1}): ",
            minimo=1,
            maximo=len(tablas) + 1
        )

        if opcion == len(tablas) + 1:
            return

        ruta = tablas[opcion - 1]
        print("\n" + "=" * 70)
        print(f"TABLA: {ruta.name}")
        print("=" * 70)
        try:
            filas = leer_filas_csv(ruta)
            print(renderizar_tabla_csv(filas))
        except OSError as exc:
            print(f"⚠ No se pudo leer la tabla: {exc}")

        input("\nPresiona Enter para volver al listado de tablas...")


def consultar_tablas_si_se_necesita():
    """Ofrece abrir el visor de tablas antes de introducir modificadores."""
    ver_tablas = solicitar_texto("¿Quieres consultar tablas de modificadores? (s/n): ")
    if es_respuesta_si(ver_tablas):
        mostrar_tablas_modificadores()


def solicitar_tirada_iniciativa_manual(personaje_combate):
    """Solicita iniciativa manual para personajes PJ."""
    nombre = personaje_combate.personaje.nombre
    turno_base = personaje_combate.turno_base

    print(f"\nIniciativa manual para {nombre} (turno base {turno_base}):")
    print("  1. Tirada normal/abierta")
    print("  2. Pifia (1-3)")
    tipo = solicitar_numero("Selecciona tipo (1-2): ", minimo=1, maximo=2)

    if tipo == 2:
        primer_resultado = solicitar_numero("Resultado inicial de pifia (1-3): ", minimo=1, maximo=3)
        penalizaciones = {1: 125, 2: 100, 3: 75}
        penalizacion = penalizaciones[primer_resultado]
        iniciativa = turno_base - penalizacion
        desglose = f"MANUAL PIFIA ({primer_resultado}): {turno_base} - {penalizacion} = {iniciativa}"
        return iniciativa, desglose

    resultado_dados = solicitar_entero("Suma total de dados obtenida en mesa: ")
    iniciativa = turno_base + resultado_dados
    desglose = f"MANUAL: {turno_base} + {resultado_dados} = {iniciativa}"
    return iniciativa, desglose


def proveedor_iniciativa_combate(personaje_combate):
    """Proveedor de iniciativa para el gestor de combate (manual en PJ, auto en PNJ)."""
    if getattr(personaje_combate.personaje, 'es_pj', False):
        iniciativa, desglose = solicitar_tirada_iniciativa_manual(personaje_combate)
        penalizador = personaje_combate.obtener_penalizador_automatico(cansancio_gastado=0)
        if penalizador:
            iniciativa_final = iniciativa + penalizador
            return iniciativa_final, f"{desglose} + ({penalizador}) = {iniciativa_final}"
        return iniciativa, desglose
    return None, None


def construir_resultado_tirada_manual(valor_base, modificador, cansancio_gastado, es_defensa=False):
    """Construye una tirada manual con el formato esperado por el motor."""
    print("\nTipo de tirada manual:")
    print("  1. Normal")
    print("  2. Abierta")
    print("  3. Pifia")
    tipo = solicitar_numero("Selecciona tipo (1-3): ", minimo=1, maximo=3)
    bono_cansancio = cansancio_gastado * 15

    if tipo == 3:
        primer_resultado = solicitar_numero("Resultado inicial de pifia (1-3): ", minimo=1, maximo=3)
        tirada_pifia = solicitar_numero("Tirada de pifia (1-100): ", minimo=1, maximo=100)
        modificador_pifia = 0
        if primer_resultado == 1:
            modificador_pifia = 15
        elif primer_resultado == 3:
            modificador_pifia = -15
        resultado_pifia = tirada_pifia + modificador_pifia
        pifia = {
            'tirada_original': primer_resultado,
            'tirada_pifia': tirada_pifia,
            'modificador': modificador_pifia,
            'resultado_final': resultado_pifia,
            'pifia_grave': resultado_pifia >= 80
        }
        resultado = {
            'tipo': 'pifia',
            'valor_base': valor_base,
            'modificador': modificador,
            'cansancio': cansancio_gastado,
            'bono_cansancio': bono_cansancio,
            'primera_tirada': primer_resultado,
            'pifia': pifia
        }
        if es_defensa:
            resultado['resultado_total'] = valor_base + modificador + bono_cansancio - resultado_pifia
        return resultado

    resultado_dados = solicitar_entero("Suma total de dados obtenida en mesa: ")
    tipo_tirada = 'abierta' if tipo == 2 else 'normal'
    return {
        'tipo': tipo_tirada,
        'valor_base': valor_base,
        'modificador': modificador,
        'cansancio': cansancio_gastado,
        'bono_cansancio': bono_cansancio,
        'tiradas': [resultado_dados],
        'resultado_dados': resultado_dados,
        'resultado_total': valor_base + modificador + bono_cansancio + resultado_dados
    }


def solicitar_tipo_defensa():
    """Solicita el tipo de defensa del defensor."""
    print("\nTipo de defensa del objetivo:")
    print(f"  1. {DefensaTipo.ESQUIVA.value}")
    print(f"  2. {DefensaTipo.PARADA.value}")
    opcion = solicitar_numero("Selecciona defensa (1-2): ", minimo=1, maximo=2)
    return DefensaTipo.PARADA.value if opcion == 2 else DefensaTipo.ESQUIVA.value


def proveedor_tirada_critica(tipo, personaje_combate):
    """Obtiene la tirada d100 para crítico/resistencia (manual PJ, automática PNJ)."""
    if getattr(personaje_combate.personaje, 'es_pj', False):
        etiqueta = "atacante" if tipo == 'ataque' else "defensor"
        return solicitar_numero(
            f"Tirada manual d100 de crítico ({etiqueta} - {personaje_combate.personaje.nombre}): ",
            minimo=1,
            maximo=100
        )
    return None


def asistente_crear_personaje(almacenamiento):
    """
    Asistente interactivo para crear un nuevo personaje.
    
    Args:
        almacenamiento (AlmacenamientoPersonajes): Sistema de almacenamiento
    """
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           CREAR NUEVO PERSONAJE                  ║")
    print("╚═══════════════════════════════════════════════════╝\n")
    
    # Solicitar nombre y verificar que no exista
    while True:
        nombre = solicitar_texto("Nombre del personaje: ")
        if almacenamiento.existe_personaje(nombre):
            print(f"⚠ Ya existe un personaje llamado '{nombre}'. Elige otro nombre.")
        else:
            break
    
    # Solicitar tipo de personaje
    print("\nTipo de personaje:")
    print("  1. Personaje normal")
    print("  2. Domine")
    print("  3. Mago")
    print("  4. Mentalista")
    print("  5. Warlock (Guerrero + Mago)")
    print("  6. Hechicero mentalista (Mago + Mentalista)")
    print("  7. Guerrero mentalista (Guerrero + Mentalista)")
    
    tipo = solicitar_numero("Selecciona el tipo (1-7): ", minimo=1, maximo=7)
    es_pj = solicitar_control_personaje()
    natura = solicitar_natura_personaje(es_pj)
    
    # Atributos comunes a todos los personajes
    print("\n--- Atributos básicos ---")
    puntos_vida = solicitar_numero("Puntos de Vida: ", minimo=1)
    puntos_cansancio = solicitar_numero("Puntos de Cansancio: ", minimo=0)
    tipos_con_ki = {2, 5, 6, 7}
    puntos_ki = solicitar_numero("Puntos de Ki: ", minimo=0) if tipo in tipos_con_ki else 0
    turno = solicitar_numero("Turno: ", minimo=0)
    daño = solicitar_numero("Daño (Domine/Mago/Mentalista/Mixtos): ", minimo=0)
    armaduras_ta, entereza_armadura = solicitar_armaduras_ta()
    
    print("\n--- Resistencias ---")
    resistencia_fisica = solicitar_numero("Resistencia Física (RF): ", minimo=0)
    resistencia_enfermedades = solicitar_numero("Resistencia Enfermedades (RE): ", minimo=0)
    resistencia_venenos = solicitar_numero("Resistencia Venenos (RV): ", minimo=0)
    resistencia_magica = solicitar_numero("Resistencia Mágica (RM): ", minimo=0)
    resistencia_psiquica = solicitar_numero("Resistencia Psíquica (RP): ", minimo=0)
    arma_nombre, arma_turno, arma_danio, arma_rotura, arma_entereza, arma_tipo_danio = (None, None, None, None, None, None)
    armas = []
    turno_doble_armas = None
    
    # Crear personaje según el tipo
    if tipo == 1:
        # Personaje normal
        print("\n--- Habilidades de combate ---")
        habilidad_ataque = solicitar_numero("Habilidad de Ataque: ", minimo=0)
        habilidad_defensa = solicitar_numero("Habilidad de Defensa: ", minimo=0)

        definir_armas = solicitar_texto("¿Registrar arsenal de armas del guerrero? (s/n): ")
        if es_respuesta_si(definir_armas):
            cantidad_armas = solicitar_numero("¿Cuántas armas/escudos quieres registrar? ", minimo=1, maximo=4)
            for indice in range(cantidad_armas):
                print(f"\nArma {indice + 1} de {cantidad_armas}")
                arma = solicitar_datos_arma_completa(opcional=False, ataque_base=habilidad_ataque)
                armas.append(arma)

            if len(armas) >= 2:
                turno_doble_armas = solicitar_numero("Turno usando dos armas simultáneamente: ", minimo=0)

            principal = armas[0]
            arma_nombre = principal['nombre']
            arma_turno = principal['turno']
            arma_danio = principal['daño']
            arma_rotura = principal['rotura']
            arma_entereza = principal['entereza']
            arma_tipo_danio = principal['tipo_danio']
        
        personaje = Personaje(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=0,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=0,
            armadura=armaduras_ta['FIL'],
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas
        )
    
    elif tipo == 2:
        # Domine
        print("\n--- Habilidades de combate (Domine) ---")
        habilidad_ataque = solicitar_numero("Habilidad de Ataque: ", minimo=0)
        habilidad_defensa = solicitar_numero("Habilidad de Defensa: ", minimo=0)

        definir_armas = solicitar_texto("¿Registrar arsenal de armas del Domine? (s/n): ")
        if es_respuesta_si(definir_armas):
            cantidad_armas = solicitar_numero("¿Cuántas armas/escudos quieres registrar? ", minimo=1, maximo=4)
            for indice in range(cantidad_armas):
                print(f"\nArma {indice + 1} de {cantidad_armas}")
                arma = solicitar_datos_arma_completa(opcional=False, ataque_base=habilidad_ataque)
                armas.append(arma)

            if len(armas) >= 2:
                turno_doble_armas = solicitar_numero("Turno usando dos armas simultáneamente: ", minimo=0)

            principal = armas[0]
            arma_nombre = principal['nombre']
            arma_turno = principal['turno']
            arma_danio = principal['daño']
            arma_rotura = principal['rotura']
            arma_entereza = principal['entereza']
            arma_tipo_danio = principal['tipo_danio']

        personaje = Domine(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=daño,
            armadura=armaduras_ta['FIL'],
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
        )

    elif tipo == 3:
        # Mago
        print("\n--- Atributos mágicos ---")
        zeon = solicitar_numero("Zeón: ", minimo=0)
        proyeccion_magica = solicitar_numero("Proyección Mágica: ", minimo=0)
        
        personaje = Mago(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=0,
            turno=turno,
            daño=daño,
            armadura=armaduras_ta['FIL'],
            zeon=zeon,
            proyeccion_magica=proyeccion_magica,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura
        )
    
    elif tipo == 4:
        # Mentalista
        print("\n--- Atributos psíquicos ---")
        potencial_psiquico = solicitar_numero("Potencial Psíquico: ", minimo=0)
        proyeccion_psiquica = solicitar_numero("Proyección Psíquica: ", minimo=0)
        cv_libres = solicitar_numero("CV Libres: ", minimo=0)
        
        personaje = Mentalista(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=0,
            turno=turno,
            daño=daño,
            armadura=armaduras_ta['FIL'],
            potencial_psiquico=potencial_psiquico,
            proyeccion_psiquica=proyeccion_psiquica,
            cv_libres=cv_libres,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura
        )

    elif tipo == 5:
        print("\n--- Habilidades de combate (Warlock) ---")
        habilidad_ataque = solicitar_numero("Habilidad de Ataque: ", minimo=0)
        habilidad_defensa = solicitar_numero("Habilidad de Defensa: ", minimo=0)
        print("\n--- Atributos mágicos (Warlock) ---")
        zeon = solicitar_numero("Zeón: ", minimo=0)
        proyeccion_magica = solicitar_numero("Proyección Mágica: ", minimo=0)

        definir_armas = solicitar_texto("¿Registrar arsenal de armas del Warlock? (s/n): ")
        if es_respuesta_si(definir_armas):
            cantidad_armas = solicitar_numero("¿Cuántas armas/escudos quieres registrar? ", minimo=1, maximo=4)
            for indice in range(cantidad_armas):
                print(f"\nArma {indice + 1} de {cantidad_armas}")
                arma = solicitar_datos_arma_completa(opcional=False, ataque_base=habilidad_ataque)
                armas.append(arma)
            if len(armas) >= 2:
                turno_doble_armas = solicitar_numero("Turno usando dos armas simultáneamente: ", minimo=0)
            principal = armas[0]
            arma_nombre = principal['nombre']
            arma_turno = principal['turno']
            arma_danio = principal['daño']
            arma_rotura = principal['rotura']
            arma_entereza = principal['entereza']
            arma_tipo_danio = principal['tipo_danio']

        personaje = Warlock(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=daño,
            armadura=armaduras_ta['FIL'],
            zeon=zeon,
            proyeccion_magica=proyeccion_magica,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
        )

    elif tipo == 6:
        print("\n--- Atributos mágicos (Hechicero mentalista) ---")
        zeon = solicitar_numero("Zeón: ", minimo=0)
        proyeccion_magica = solicitar_numero("Proyección Mágica: ", minimo=0)
        print("\n--- Atributos psíquicos (Hechicero mentalista) ---")
        potencial_psiquico = solicitar_numero("Potencial Psíquico: ", minimo=0)
        proyeccion_psiquica = solicitar_numero("Proyección Psíquica: ", minimo=0)
        cv_libres = solicitar_numero("CV Libres: ", minimo=0)

        personaje = HechiceroMentalista(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            daño=daño,
            armadura=armaduras_ta['FIL'],
            zeon=zeon,
            proyeccion_magica=proyeccion_magica,
            potencial_psiquico=potencial_psiquico,
            proyeccion_psiquica=proyeccion_psiquica,
            cv_libres=cv_libres,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
        )

    else:  # tipo == 7
        print("\n--- Habilidades de combate (Guerrero mentalista) ---")
        habilidad_ataque = solicitar_numero("Habilidad de Ataque: ", minimo=0)
        habilidad_defensa = solicitar_numero("Habilidad de Defensa: ", minimo=0)
        print("\n--- Atributos psíquicos (Guerrero mentalista) ---")
        potencial_psiquico = solicitar_numero("Potencial Psíquico: ", minimo=0)
        proyeccion_psiquica = solicitar_numero("Proyección Psíquica: ", minimo=0)
        cv_libres = solicitar_numero("CV Libres: ", minimo=0)

        definir_armas = solicitar_texto("¿Registrar arsenal de armas del Guerrero mentalista? (s/n): ")
        if es_respuesta_si(definir_armas):
            cantidad_armas = solicitar_numero("¿Cuántas armas/escudos quieres registrar? ", minimo=1, maximo=4)
            for indice in range(cantidad_armas):
                print(f"\nArma {indice + 1} de {cantidad_armas}")
                arma = solicitar_datos_arma_completa(opcional=False, ataque_base=habilidad_ataque)
                armas.append(arma)
            if len(armas) >= 2:
                turno_doble_armas = solicitar_numero("Turno usando dos armas simultáneamente: ", minimo=0)
            principal = armas[0]
            arma_nombre = principal['nombre']
            arma_turno = principal['turno']
            arma_danio = principal['daño']
            arma_rotura = principal['rotura']
            arma_entereza = principal['entereza']
            arma_tipo_danio = principal['tipo_danio']

        personaje = GuerreroMentalista(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=daño,
            armadura=armaduras_ta['FIL'],
            potencial_psiquico=potencial_psiquico,
            proyeccion_psiquica=proyeccion_psiquica,
            cv_libres=cv_libres,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            natura=natura,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
        )
    
    # Guardar personaje
    if almacenamiento.guardar_personaje(personaje):
        print(f"\n✓ Personaje '{nombre}' creado y guardado exitosamente!")
    else:
        print(f"\n✗ Error al guardar el personaje '{nombre}'")
    
    input("\nPresiona Enter para continuar...")


def listar_personajes(almacenamiento):
    """
    Lista todos los personajes guardados.
    
    Args:
        almacenamiento (AlmacenamientoPersonajes): Sistema de almacenamiento
    """
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           LISTADO DE PERSONAJES                  ║")
    print("╚═══════════════════════════════════════════════════╝\n")
    
    personajes = almacenamiento.cargar_todos_personajes()
    
    if not personajes:
        print("  No hay personajes guardados todavía.")
    else:
        print(f"  Total de personajes: {len(personajes)}\n")
        for i, personaje in enumerate(personajes, 1):
            control = 'PJ' if getattr(personaje, 'es_pj', False) else 'PNJ'
            texto_natura = " | Natura" if personaje_tiene_natura(personaje) else " | Sin Natura"
            arma = obtener_resumen_arma(personaje)
            print(f"  {i}. {personaje.nombre} ({personaje.tipo}, {control}{texto_natura}) | {arma}")
    
    input("\nPresiona Enter para continuar...")


def ver_personaje(almacenamiento):
    """
    Muestra los detalles completos de un personaje.
    
    Args:
        almacenamiento (AlmacenamientoPersonajes): Sistema de almacenamiento
    """
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           VER DETALLES DE PERSONAJE              ║")
    print("╚═══════════════════════════════════════════════════╝\n")
    
    nombres = almacenamiento.obtener_nombres_personajes()
    
    if not nombres:
        print("  No hay personajes guardados.")
        input("\nPresiona Enter para continuar...")
        return
    
    print("Personajes disponibles:")
    for i, nombre in enumerate(nombres, 1):
        print(f"  {i}. {nombre}")
    
    print(f"  {len(nombres) + 1}. Volver")
    
    opcion = solicitar_numero(f"\nSelecciona un personaje (1-{len(nombres) + 1}): ", 
                              minimo=1, maximo=len(nombres) + 1)
    
    if opcion == len(nombres) + 1:
        return
    
    nombre_seleccionado = nombres[opcion - 1]
    personaje = almacenamiento.cargar_personaje(nombre_seleccionado)
    
    if personaje:
        print(f"\n{personaje}")
    else:
        print(f"\n✗ No se pudo cargar el personaje '{nombre_seleccionado}'")
    
    input("\nPresiona Enter para continuar...")


def editar_personaje(almacenamiento):
    """
    Permite editar los atributos de un personaje existente.
    
    Args:
        almacenamiento (AlmacenamientoPersonajes): Sistema de almacenamiento
    """
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           EDITAR PERSONAJE                       ║")
    print("╚═══════════════════════════════════════════════════╝\n")
    
    nombres = almacenamiento.obtener_nombres_personajes()
    
    if not nombres:
        print("  No hay personajes guardados.")
        input("\nPresiona Enter para continuar...")
        return
    
    print("Personajes disponibles:")
    for i, nombre in enumerate(nombres, 1):
        print(f"  {i}. {nombre}")
    
    print(f"  {len(nombres) + 1}. Volver")
    
    opcion = solicitar_numero(f"\nSelecciona un personaje (1-{len(nombres) + 1}): ", 
                              minimo=1, maximo=len(nombres) + 1)
    
    if opcion == len(nombres) + 1:
        return
    
    nombre_seleccionado = nombres[opcion - 1]
    personaje = almacenamiento.cargar_personaje(nombre_seleccionado)
    
    if not personaje:
        print(f"\n✗ No se pudo cargar el personaje '{nombre_seleccionado}'")
        input("\nPresiona Enter para continuar...")
        return
    
    # Mostrar personaje actual
    print(f"\n{personaje}")
    
    # Menú de edición según tipo de personaje
    print("\n¿Qué atributo deseas editar?")
    
    opciones = [
        ('puntos_vida', 'Puntos de Vida'),
        ('puntos_cansancio', 'Puntos de Cansancio'),
        ('turno', 'Turno'),
        ('es_pj', 'Control (PJ/PNJ)'),
        ('natura', 'Natura (solo PNJ)'),
        ('arma_principal', 'Arma principal'),
        ('daño', 'Daño'),
        ('ta_fil', 'TA FIL'),
        ('ta_con', 'TA CON'),
        ('ta_pen', 'TA PEN'),
        ('ta_cal', 'TA CAL'),
        ('ta_ele', 'TA ELE'),
        ('ta_fri', 'TA FRI'),
        ('ta_ene', 'TA ENE'),
        ('entereza_armadura', 'Entereza armadura'),
        ('resistencia_fisica', 'Resistencia Física (RF)'),
        ('resistencia_enfermedades', 'Resistencia Enfermedades (RE)'),
        ('resistencia_venenos', 'Resistencia Venenos (RV)'),
        ('resistencia_magica', 'Resistencia Mágica (RM)'),
        ('resistencia_psiquica', 'Resistencia Psíquica (RP)')
    ]

    if personaje_tiene_ki(personaje):
        opciones.insert(2, ('puntos_ki', 'Puntos de Ki'))
    
    if isinstance(personaje, Personaje) and not isinstance(personaje, (Mago, Mentalista)):
        opciones.extend([
            ('habilidad_ataque', 'Habilidad de Ataque'),
            ('habilidad_defensa', 'Habilidad de Defensa')
        ])
    elif isinstance(personaje, Mago):
        opciones.extend([
            ('zeon', 'Zeón'),
            ('proyeccion_magica', 'Proyección Mágica')
        ])
    elif isinstance(personaje, Mentalista):
        opciones.extend([
            ('potencial_psiquico', 'Potencial Psíquico'),
            ('proyeccion_psiquica', 'Proyección Psíquica'),
            ('cv_libres', 'CV Libres')
        ])
    
    for i, (_, etiqueta) in enumerate(opciones, 1):
        print(f"  {i}. {etiqueta}")
    
    print(f"  {len(opciones) + 1}. Cancelar")
    
    atributo = solicitar_numero(
        f"\nSelecciona atributo (1-{len(opciones) + 1}): ",
        minimo=1,
        maximo=len(opciones) + 1
    )
    
    if atributo == len(opciones) + 1:
        print("\nEdición cancelada.")
        input("\nPresiona Enter para continuar...")
        return
    
    nombre_attr, descripcion = opciones[atributo - 1]
    if nombre_attr == 'arma_principal':
        if isinstance(personaje, Personaje) and not isinstance(personaje, (Mago, Mentalista)):
            while True:
                print("\n--- Arsenal del guerrero ---")
                if personaje.armas:
                    for i, arma in enumerate(personaje.armas, 1):
                        escudo = " [Escudo]" if arma.get('es_escudo') else ""
                        print(f"  {i}. {arma['nombre']}{escudo} (ATQ {arma['habilidad_ataque']} / PAR {arma['habilidad_parada']} / T {arma['turno']})")
                else:
                    print("  (Sin armas registradas)")
                print("\n  1. Añadir arma")
                print("  2. Eliminar arma")
                print("  3. Configurar turno con dos armas")
                print("  4. Finalizar")
                opcion_arsenal = solicitar_numero("Selecciona opción (1-4): ", minimo=1, maximo=4)

                if opcion_arsenal == 1:
                    arma = solicitar_datos_arma_completa(opcional=False, ataque_base=personaje.habilidad_ataque)
                    if arma is not None:
                        personaje.armas.append(arma)
                elif opcion_arsenal == 2:
                    if not personaje.armas:
                        print("No hay armas para eliminar.")
                        continue
                    idx = solicitar_numero("Índice de arma a eliminar: ", minimo=1, maximo=len(personaje.armas))
                    personaje.armas.pop(idx - 1)
                elif opcion_arsenal == 3:
                    if len(personaje.armas) < 2:
                        print("Se necesitan al menos 2 armas registradas.")
                        continue
                    personaje.turno_doble_armas = solicitar_numero("Turno al usar dos armas simultáneamente: ", minimo=0)
                else:
                    break

            sincronizar_arma_principal_desde_lista(personaje)
        else:
            print(f"\nArma actual: {obtener_resumen_arma(personaje)}")
            redefinir = solicitar_texto("¿Configurar/reemplazar arma principal? (s/n): ")
            if es_respuesta_si(redefinir):
                arma_nombre, arma_turno, arma_danio, arma_rotura, arma_entereza, arma_tipo_danio = solicitar_datos_arma(opcional=False)
                personaje.arma_nombre = arma_nombre
                personaje.arma_turno = arma_turno
                personaje.arma_danio = arma_danio
                personaje.arma_rotura = arma_rotura
                personaje.arma_entereza = arma_entereza
                personaje.arma_tipo_danio = arma_tipo_danio
            else:
                limpiar = solicitar_texto("¿Eliminar arma principal guardada? (s/n): ")
                if es_respuesta_si(limpiar):
                    personaje.arma_nombre = None
                    personaje.arma_turno = None
                    personaje.arma_danio = None
                    personaje.arma_rotura = None
                    personaje.arma_entereza = None
                    personaje.arma_tipo_danio = None
    elif nombre_attr.startswith('ta_'):
        codigo = nombre_attr.split('_', 1)[1].upper()
        valor_actual = personaje.armaduras_ta.get(codigo, 0)
        print(f"\nValor actual de TA {codigo}: {valor_actual}")
        personaje.armaduras_ta[codigo] = solicitar_numero("Nuevo valor: ", minimo=0)
        personaje.armadura = personaje.armaduras_ta.get('FIL', 0)
    else:
        valor_actual = getattr(personaje, nombre_attr)
        print(f"\nValor actual de {descripcion}: {valor_actual}")
        if nombre_attr == 'es_pj':
            personaje.es_pj = solicitar_control_personaje()
            personaje.natura = solicitar_natura_personaje(personaje.es_pj, valor_actual=getattr(personaje, 'natura', True))
        elif nombre_attr == 'natura':
            if getattr(personaje, 'es_pj', False):
                personaje.natura = True
                print("\nLos PJ siempre tienen Natura.")
            else:
                personaje.natura = solicitar_natura_personaje(False, valor_actual=getattr(personaje, 'natura', True))
        else:
            nuevo_valor = solicitar_numero("Nuevo valor: ", minimo=0)
            setattr(personaje, nombre_attr, nuevo_valor)

    # Guardar cambios
    if almacenamiento.guardar_personaje(personaje):
        print(f"\n✓ Personaje '{personaje.nombre}' actualizado exitosamente!")
    else:
        print("\n✗ Error al guardar los cambios")

    input("\nPresiona Enter para continuar...")


def eliminar_personaje(almacenamiento):
    """
    Elimina un personaje del almacenamiento.

    Args:
        almacenamiento (AlmacenamientoPersonajes): Sistema de almacenamiento
    """
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           ELIMINAR PERSONAJE                     ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    nombres = almacenamiento.obtener_nombres_personajes()

    if not nombres:
        print("  No hay personajes guardados.")
        input("\nPresiona Enter para continuar...")
        return

    print("Personajes disponibles:")
    for i, nombre in enumerate(nombres, 1):
        print(f"  {i}. {nombre}")

    print(f"  {len(nombres) + 1}. Cancelar")

    opcion = solicitar_numero(f"\nSelecciona un personaje (1-{len(nombres) + 1}): ",
                              minimo=1, maximo=len(nombres) + 1)

    if opcion == len(nombres) + 1:
        print("\nOperación cancelada.")
        input("\nPresiona Enter para continuar...")
        return

    nombre_seleccionado = nombres[opcion - 1]

    # Confirmar eliminación
    confirmacion = solicitar_texto(
        f"\n¿Estás seguro de que quieres eliminar a '{nombre_seleccionado}'? (s/n): "
    ).lower()

    if confirmacion == 's' or confirmacion == 'si' or confirmacion == 'sí':
        if almacenamiento.eliminar_personaje(nombre_seleccionado):
            print(f"\n✓ Personaje '{nombre_seleccionado}' eliminado exitosamente!")
        else:
            print("\n✗ Error al eliminar el personaje")
    else:
        print("\nEliminación cancelada.")

    input("\nPresiona Enter para continuar...")


def gestionar_combate(almacenamiento):
    """
    Gestiona el sistema de combate completo.
    
    Args:
        almacenamiento (AlmacenamientoPersonajes): Sistema de almacenamiento
    """
    gestor = GestorCombate()
    
    # Fase 1: Configuración del combate
    if not configurar_combate(almacenamiento, gestor):
        return
    
    # Fase 2: Iniciar combate y calcular iniciativas
    print("\n" + "=" * 60)
    print("CALCULANDO INICIATIVAS...")
    print("=" * 60)
    
    gestor.iniciar_combate(proveedor_iniciativa=proveedor_iniciativa_combate)
    
    # Mostrar desglose de iniciativas
    print(gestor.obtener_desglose_iniciativas())
    input("\nPresiona Enter para comenzar el combate...")
    
    # Fase 3: Loop de combate
    while gestor.esta_combate_activo():
        limpiar_pantalla()
        mostrar_encabezado()
        
        # Mostrar tabla de combate
        print(gestor.obtener_tabla_combate())
        
        # Verificar si la ronda terminó
        personaje_actual = gestor.obtener_personaje_actual()
        
        if personaje_actual is None:
            # Ronda completada
            print("\n" + "=" * 60)
            print(f"¡RONDA {gestor.ronda_actual} COMPLETADA!")
            print("=" * 60)
            
            if not gestionar_nueva_ronda(gestor):
                break
            continue
        
        # Turno del personaje actual
        print(f"\n┌─── TURNO DE: {personaje_actual.personaje.nombre} ───┐")
        print(f"│ Iniciativa: {personaje_actual.iniciativa}")
        print(f"│ PV: {personaje_actual.personaje.puntos_vida}")
        print(f"│ Turno base: {personaje_actual.obtener_info_turno()}")
        if personaje_actual.esta_a_la_defensiva:
            print("│ Estado: A LA DEFENSIVA")
        print("└" + "─" * 40 + "┘")
        
        # Menú de acciones
        if not menu_turno_personaje(personaje_actual, gestor):
            break
    
    # Fin del combate
    print("\n" + "=" * 60)
    print("COMBATE FINALIZADO")
    print("=" * 60)
    gestor.finalizar_combate()
    input("\nPresiona Enter para volver al menú principal...")


def configurar_combate(almacenamiento, gestor):
    """
    Configura los personajes que participarán en el combate.
    
    Args:
        almacenamiento: Sistema de almacenamiento
        gestor: GestorCombate
        
    Returns:
        bool: True si se configuró correctamente, False si se canceló
    """
    limpiar_pantalla()
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           CONFIGURAR COMBATE                     ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    # Configurar modo test
    activar_modo_test = solicitar_texto("¿Activar modo test de tiradas? (s/n): ").lower()
    gestor.modo_test = activar_modo_test in ['s', 'si', 'sí']
    gestor.semilla_test = None

    if gestor.modo_test:
        semilla_texto = solicitar_texto("Semilla aleatoria (Enter para aleatoria): ", permitir_vacio=True)
        if semilla_texto:
            try:
                gestor.semilla_test = int(semilla_texto)
                configurar_semilla(gestor.semilla_test)
            except ValueError:
                print("⚠ Semilla inválida, se usará aleatoria")
    
    personajes_disponibles = almacenamiento.cargar_todos_personajes()
    
    if not personajes_disponibles:
        print("No hay personajes guardados. Crea personajes primero.")
        input("\nPresiona Enter para continuar...")
        return False
    
    print("Personajes disponibles:")
    for i, p in enumerate(personajes_disponibles, 1):
        control = 'PJ' if getattr(p, 'es_pj', False) else 'PNJ'
        print(f"  {i}. {p.nombre} ({p.tipo}, {control}) - PV: {p.puntos_vida}, Turno: {p.turno}")
    
    print("\nAñade personajes al combate (escribe 0 para terminar)")
    
    while True:
        opcion = solicitar_numero(f"\nSelecciona personaje (0-{len(personajes_disponibles)}): ", 
                                  minimo=0, maximo=len(personajes_disponibles))
        
        if opcion == 0:
            break
        
        personaje = personajes_disponibles[opcion - 1]
        es_guerrero = isinstance(personaje, Personaje) and not isinstance(personaje, (Mago, Mentalista))
        
        print(f"\n{personaje.nombre} - Turno base: {personaje.turno} (Desarmado)")
        usa_arma_guardada = False

        if es_guerrero and getattr(personaje, 'armas', None):
            print("\nModo de combate del guerrero:")
            print("  1. Desarmado")
            print("  2. Una arma")
            print("  3. Dos armas simultáneas")
            modo_guerrero = solicitar_numero("Selecciona modo (1-3): ", minimo=1, maximo=3)

            if modo_guerrero == 2:
                arma = seleccionar_arma_lista(personaje.armas, "Elige arma activa", permitir_cancelar=False)
                if arma is None:
                    continue
                pc = gestor.añadir_personaje(
                    personaje,
                    arma.get('turno', personaje.turno),
                    arma.get('daño'),
                    arma.get('rotura'),
                    arma.get('entereza'),
                    arma.get('tipo_danio')
                )
                pc.armas_activas = [arma]
                pc.configurar_arma_ataque(arma)
                pc.configurar_arma_parada(arma)
                print(f"✓ {personaje.nombre} añadido con arma {arma['nombre']}")
                continue

            if modo_guerrero == 3 and len(personaje.armas) >= 2:
                arma1 = seleccionar_arma_lista(personaje.armas, "Selecciona primera arma", permitir_cancelar=False)
                if arma1 is None:
                    continue
                restantes = [a for a in personaje.armas if a is not arma1]
                arma2 = seleccionar_arma_lista(restantes, "Selecciona segunda arma", permitir_cancelar=False)
                if arma2 is None:
                    continue
                turno_doble = personaje.turno_doble_armas
                if turno_doble is None:
                    turno_doble = solicitar_numero("Turno usando dos armas: ", minimo=0)
                pc = gestor.añadir_personaje(
                    personaje,
                    turno_doble,
                    arma1.get('daño'),
                    arma1.get('rotura'),
                    arma1.get('entereza'),
                    arma1.get('tipo_danio')
                )
                pc.armas_activas = [arma1, arma2]
                pc.configurar_arma_ataque(arma1)
                pc.configurar_arma_parada(arma2)
                print(f"✓ {personaje.nombre} añadido con dos armas: {arma1['nombre']} + {arma2['nombre']}")
                continue
            elif modo_guerrero == 3 and len(personaje.armas) < 2:
                print("⚠ No hay suficientes armas registradas; se añadirá desarmado.")
                gestor.añadir_personaje(personaje, None, None, None, None, None)
                continue

        if getattr(personaje, 'arma_nombre', None):
            print(f"Arma guardada: {obtener_resumen_arma(personaje)}")
            usar_guardada = solicitar_texto("¿Usar arma guardada? (s/n): ")
            usa_arma_guardada = es_respuesta_si(usar_guardada)

        if usa_arma_guardada:
            turno_arma = personaje.arma_turno if personaje.arma_turno is not None else personaje.turno
            daño_arma = personaje.arma_danio if personaje.arma_danio is not None else personaje.daño
            rotura_arma = personaje.arma_rotura
            entereza_arma = personaje.arma_entereza
            tipo_danio_ataque = personaje.arma_tipo_danio
            if tipo_danio_ataque is None:
                tipo_danio_ataque = solicitar_ta("El arma guardada no tiene tipo de daño. Indica uno para este combate: ")
            pc = gestor.añadir_personaje(personaje, turno_arma, daño_arma, rotura_arma, entereza_arma, tipo_danio_ataque)
            if es_guerrero and personaje.armas:
                pc.armas_activas = [personaje.armas[0]]
                pc.configurar_arma_ataque(personaje.armas[0])
                pc.configurar_arma_parada(personaje.armas[0])
            print(f"✓ {personaje.nombre} añadido con su arma guardada ({personaje.arma_nombre})")
        else:
            usar_arma = solicitar_texto("¿Usa arma? (s/n): ")

            if es_respuesta_si(usar_arma):
                turno_arma = solicitar_numero("Turno del arma: ", minimo=0)
                daño_arma = solicitar_numero("Daño del arma: ", minimo=0)
                rotura_arma = solicitar_numero("Rotura del arma: ", minimo=0)
                entereza_arma = solicitar_numero("Entereza del arma: ", minimo=0)
                tipo_danio_ataque = solicitar_ta("Tipo de daño del arma para este combate: ")
                pc = gestor.añadir_personaje(personaje, turno_arma, daño_arma, rotura_arma, entereza_arma, tipo_danio_ataque)
                if es_guerrero:
                    arma_temp = {
                        'nombre': 'Arma temporal',
                        'turno': turno_arma,
                        'daño': daño_arma,
                        'rotura': rotura_arma,
                        'entereza': entereza_arma,
                        'tipo_danio': tipo_danio_ataque,
                        'habilidad_ataque': personaje.habilidad_ataque,
                        'habilidad_parada': personaje.habilidad_defensa,
                        'es_escudo': False
                    }
                    pc.armas_activas = [arma_temp]
                    pc.configurar_arma_ataque(arma_temp)
                    pc.configurar_arma_parada(arma_temp)
                print(f"✓ {personaje.nombre} añadido con turno de arma: {turno_arma}")
            else:
                definir_daño = solicitar_texto("¿Definir daño ahora? (s/n): ")
                if es_respuesta_si(definir_daño):
                    daño_arma = solicitar_numero("Daño para este combate: ", minimo=0)
                else:
                    daño_arma = None
                gestor.añadir_personaje(personaje, None, daño_arma, None, None, None)
                print(f"✓ {personaje.nombre} añadido con turno desarmado: {personaje.turno}")
    
    if len(gestor.personajes_combate) < 1:
        print("\nDebe haber al menos 1 personaje en combate.")
        input("\nPresiona Enter para continuar...")
        return False
    
    print(f"\n✓ {len(gestor.personajes_combate)} personajes listos para combatir")
    input("\nPresiona Enter para calcular iniciativas...")
    return True


def seleccionar_objetivo(gestor, nombre_atacante):
    """
    Permite seleccionar un objetivo para un ataque.
    
    Args:
        gestor: GestorCombate
        nombre_atacante (str): Nombre del atacante
        
    Returns:
        PersonajeCombate|None: Objetivo seleccionado o None si se cancela
    """
    candidatos = [
        pc for pc in gestor.orden_iniciativa
        if pc.personaje.nombre != nombre_atacante and not pc.inconsciente
    ]
    
    if not candidatos:
        print("\nNo hay objetivos disponibles.")
        input("\nPresiona Enter para continuar...")
        return None
    
    print("\nObjetivos disponibles:")
    for i, pc in enumerate(candidatos, 1):
        print(f"  {i}. {pc.personaje.nombre} (PV: {pc.personaje.puntos_vida})")
    
    print(f"  {len(candidatos) + 1}. Cancelar")
    
    opcion = solicitar_numero(
        f"\nSelecciona objetivo (1-{len(candidatos) + 1}): ",
        minimo=1,
        maximo=len(candidatos) + 1
    )
    
    if opcion == len(candidatos) + 1:
        return None
    
    return candidatos[opcion - 1]


def solicitar_cansancio_gastado(personaje):
    """
    Solicita cuántos puntos de cansancio gastar en un ataque.
    
    Args:
        personaje: Instancia del personaje
        
    Returns:
        int: Puntos de cansancio a gastar
    """
    max_disponible = min(5, personaje.puntos_cansancio)
    
    if max_disponible <= 0:
        return 0
    
    print(f"\nPuntos de cansancio disponibles: {personaje.puntos_cansancio}")
    print("Cada punto de cansancio da +15 a la tirada de ataque (máx. 5)")
    return solicitar_numero("¿Cuántos puntos gastar? ", minimo=0, maximo=max_disponible)


def mostrar_detalle_tirada_ataque(resultado):
    """
    Muestra el detalle de la tirada de ataque.
    """
    if resultado['tipo'] == 'pifia':
        pifia = resultado['pifia']
        mod = pifia['modificador']
        mod_texto = f"{mod:+d}" if mod != 0 else "0"
        print("\n⚠ ¡PIFIA EN EL ATAQUE!")
        print(f"Tirada inicial: {resultado['primera_tirada']}")
        print(f"Tirada de pifia: {pifia['tirada_pifia']} ({mod_texto}) = {pifia['resultado_final']}")
        if pifia['pifia_grave']:
            print("‼ PIFIA GRAVE (80 o más) ‼")
        return
    
    tiradas = " + ".join(str(t) for t in resultado['tiradas'])
    base = resultado['valor_base']
    mod = resultado['modificador']
    bono_cansancio = resultado['bono_cansancio']
    total = resultado['resultado_total']
    
    tipo = "ABIERTA" if resultado['tipo'] == 'abierta' else "NORMAL"
    print(f"\nTirada de ataque ({tipo}): {tiradas}")
    print(f"Base {base} + Mod {mod:+d} + Cansancio {bono_cansancio:+d} + Dados {resultado['resultado_dados']} = {total}")


def mostrar_detalle_tirada_defensa(resultado):
    """
    Muestra el detalle de la tirada de defensa.
    """
    if resultado['tipo'] == 'pifia':
        pifia = resultado['pifia']
        mod = pifia['modificador']
        mod_texto = f"{mod:+d}" if mod != 0 else "0"
        print("\n⚠ ¡PIFIA EN LA DEFENSA!")
        print(f"Tirada inicial: {resultado['primera_tirada']}")
        print(f"Tirada de pifia: {pifia['tirada_pifia']} ({mod_texto}) = {pifia['resultado_final']}")
        if pifia['pifia_grave']:
            print("‼ PIFIA GRAVE (80 o más) ‼")
        print(f"Defensa final: {resultado['resultado_total']}")
        return
    
    tiradas = " + ".join(str(t) for t in resultado['tiradas'])
    base = resultado['valor_base']
    mod = resultado['modificador']
    bono_cansancio = resultado.get('bono_cansancio', 0)
    total = resultado['resultado_total']
    
    tipo = "ABIERTA" if resultado['tipo'] == 'abierta' else "NORMAL"
    print(f"\nTirada de defensa ({tipo}): {tiradas}")
    print(f"Base {base} + Mod {mod:+d} + Cansancio {bono_cansancio:+d} + Dados {resultado['resultado_dados']} = {total}")


def realizar_ataque(personaje_combate, gestor, objetivo_forzado=None, bono_ataque_extra=0, permitir_contraataque=True):
    """
    Ejecuta una acción de ataque.
    
    Args:
        personaje_combate: PersonajeCombate atacante
        gestor: GestorCombate
        objetivo_forzado (PersonajeCombate, opcional): Objetivo preseleccionado
        bono_ataque_extra (int): Bono adicional al ataque (contraataque)
        permitir_contraataque (bool): Si se permite contraataque recursivo
    """
    atacante = personaje_combate.personaje
    
    if not personaje_combate.puede_atacar:
        print("\n⚠ Este personaje está a la defensiva y no puede atacar esta ronda.")
        input("\nPresiona Enter para continuar...")
        return
    
    objetivo = objetivo_forzado or seleccionar_objetivo(gestor, atacante.nombre)
    if objetivo is None:
        return

    if personaje_combate.armas_activas:
        if len(personaje_combate.armas_activas) == 1:
            personaje_combate.configurar_arma_ataque(personaje_combate.armas_activas[0])
        else:
            arma_ataque = seleccionar_arma_lista(personaje_combate.armas_activas, "Elige arma para este ataque", permitir_cancelar=False)
            personaje_combate.configurar_arma_ataque(arma_ataque)
    
    consultar_tablas_si_se_necesita()
    print("\n--- Modificadores de ataque ---")
    modificador_ataque = solicitar_entero("Modificador total al ataque (puede ser negativo): ")
    if bono_ataque_extra:
        print(f"Bono adicional al ataque: +{bono_ataque_extra}")
    
    cansancio_gastado = solicitar_cansancio_gastado(atacante)
    atacante.puntos_cansancio = max(0, atacante.puntos_cansancio - cansancio_gastado)
    texto_penalizador_ataque, penalizador_auto_ataque = describir_penalizador_automatico(personaje_combate, cansancio_gastado)
    if penalizador_auto_ataque:
        print(texto_penalizador_ataque)
    
    consultar_tablas_si_se_necesita()
    print("\n--- Modificadores de defensa ---")
    modificador_defensa_manual = solicitar_entero("Modificador total a la defensa (puede ser negativo): ")

    tipo_defensa = solicitar_tipo_defensa()
    penalizador_auto_defensa = objetivo.obtener_penalizador_defensas_multiples()
    if penalizador_auto_defensa != 0:
        print(f"Penalizador automático por defensa múltiple: {penalizador_auto_defensa}")
    
    valor_base_ataque, _ = obtener_valor_ataque_combate(personaje_combate)
    if getattr(atacante, 'es_pj', False):
        print(f"\n{atacante.nombre} es PJ: introduce tirada manual de ataque")
        resultado_ataque = construir_resultado_tirada_manual(
            valor_base=valor_base_ataque,
            modificador=modificador_ataque + bono_ataque_extra + penalizador_auto_ataque,
            cansancio_gastado=cansancio_gastado,
            es_defensa=False
        )
    else:
        resultado_ataque = tirar_ataque(
            valor_base=valor_base_ataque,
            modificador=modificador_ataque + bono_ataque_extra,
            cansancio_gastado=cansancio_gastado,
            permitir_abierta=personaje_tiene_natura(atacante),
        )
    
    print("\n" + "=" * 60)
    print(f"ATAQUE: {atacante.nombre} → {objetivo.personaje.nombre}")
    print("=" * 60)
    
    mostrar_detalle_tirada_ataque(resultado_ataque)
    
    if resultado_ataque['tipo'] == 'pifia':
        print("\nEl ataque falla automáticamente. No hay defensa.")
        input("\nPresiona Enter para continuar...")
        return
    
    # Solicitar daño de arma si no está definido
    daño_arma = personaje_combate.daño_arma
    ta_ataque = personaje_combate.ta_ataque
    if isinstance(atacante, (Mago, Mentalista)):
        daño_arma = solicitar_numero("Daño base del ataque sobrenatural: ", minimo=0)
        ta_ataque = solicitar_ta("Tipo de daño del ataque sobrenatural: ")
    else:
        if daño_arma is None:
            daño_arma = solicitar_numero("Daño del arma para este ataque: ", minimo=0)
            personaje_combate.daño_arma = daño_arma
        if ta_ataque is None:
            ta_ataque = solicitar_ta("Tipo de daño del ataque para este asalto: ")
            personaje_combate.ta_ataque = ta_ataque
    
    # Defensa: permitir gasto de cansancio
    defensor = objetivo.personaje
    defensa_cansancio = solicitar_cansancio_gastado(defensor)
    defensor.puntos_cansancio = max(0, defensor.puntos_cansancio - defensa_cansancio)
    texto_penalizador_defensa, penalizador_auto_defensor = describir_penalizador_automatico(objetivo, defensa_cansancio)
    if penalizador_auto_defensor:
        print(texto_penalizador_defensa)

    if tipo_defensa == DefensaTipo.PARADA.value:
        if objetivo.armas_activas:
            if len(objetivo.armas_activas) == 1:
                objetivo.configurar_arma_parada(objetivo.armas_activas[0])
            else:
                arma_parada = seleccionar_arma_lista(objetivo.armas_activas, f"Arma/escudo de parada de {defensor.nombre}", permitir_cancelar=False)
                objetivo.configurar_arma_parada(arma_parada)
    else:
        objetivo.configurar_arma_parada(None)

    valor_base_defensa, _ = obtener_valor_defensa_combate(objetivo)
    if getattr(defensor, 'es_pj', False):
        print(f"\n{defensor.nombre} es PJ: introduce tirada manual de defensa")
        resultado_defensa = construir_resultado_tirada_manual(
            valor_base=valor_base_defensa,
            modificador=modificador_defensa_manual + penalizador_auto_defensa + penalizador_auto_defensor,
            cansancio_gastado=defensa_cansancio,
            es_defensa=True
        )
    else:
        resultado_defensa = None
    
    contexto = preparar_y_resolver_ataque(
        personaje_combate,
        objetivo,
        {
            'daño': daño_arma,
            'ta': ta_ataque,
            'mod_ataque': modificador_ataque + bono_ataque_extra,
            'mod_defensa': modificador_defensa_manual,
            'cansancio_ataque': cansancio_gastado,
            'cansancio_defensa': defensa_cansancio,
            'tipo_defensa': tipo_defensa,
            'resultado_ataque_precalculado': resultado_ataque,
            'resultado_defensa_precalculado': resultado_defensa,
            'usar_estado_arma_actual': True,
        },
        proveedor_tirada_critica=proveedor_tirada_critica,
    )
    resultado = contexto.resultado
    
    if resultado['defensa'] is not None:
        mostrar_detalle_tirada_defensa(resultado['defensa'])
    
    ataque_total = resultado['ataque']['resultado_total']
    defensa_total = resultado['defensa']['resultado_total']
    print(f"\nResultado: Ataque {ataque_total} vs Defensa {defensa_total}")
    
    if resultado['impacto']:
        print("\n✅ El ataque impacta.")
        print(f"Diferencia: {resultado['diferencia']}")
        print(f"Tipo de daño aplicado ({resultado['ta_ataque']}): TA objetivo {resultado['ta_objetivo']}")
        print(f"Reducción por armadura: {resultado['reduccion_armadura']}")
        print(f"Diferencia final: {resultado['diferencia_final']}")
        
        if resultado['a_la_defensiva']:
            objetivo.marcar_defensiva()
            print("Impacto leve: el defensor queda A LA DEFENSIVA (sin daño).")
        elif resultado['danio_aplicado'] > 0:
            print(f"Daño aplicado: {resultado['danio_aplicado']}")
            print(f"PV restantes de {objetivo.personaje.nombre}: {objetivo.personaje.puntos_vida}")
            
            if resultado.get('critico'):
                critico = resultado['critico']
                print("\n‼ CRÍTICO ‼")
                print(f"Tirada atacante: {critico['tirada_atacante']}")
                print(f"Tirada defensor: {critico['tirada_defensor']} + RF {critico['resistencia_fisica']}")
                print(f"Resultado crítico: {critico['resultado']}")
                if critico['tiene_consecuencias']:
                    dolor = objetivo.penalizador_dolor
                    deterioro = objetivo.penalizador_deterioro
                    print(f"→ Penalizador activo: -{dolor + deterioro} (dolor: -{dolor}, deterioro: -{deterioro})")
                else:
                    print("→ Sin consecuencias")

            if objetivo.inconsciente:
                print(f"→ {objetivo.personaje.nombre} cae inconsciente y queda fuera del combate")

        else:
            print("El impacto no causa daño.")

        if resultado.get('choque_armas'):
            choque = resultado['choque_armas']
            print("\n⚒ CHOQUE DE ARMAS (Parada)")
            print(f"{atacante.nombre}: d10 {choque['tirada_atacante']} + Rotura {choque['rotura_atacante']} = {choque['total_atacante']}")
            print(f"{objetivo.personaje.nombre}: d10 {choque['tirada_defensor']} + Rotura {choque['rotura_defensor']} = {choque['total_defensor']}")
            if choque['rompe_arma_atacante']:
                print(f"→ El arma de {atacante.nombre} se rompe")
            if choque['rompe_arma_defensor']:
                print(f"→ El arma de {objetivo.personaje.nombre} se rompe")
            if not choque['rompe_arma_atacante'] and not choque['rompe_arma_defensor']:
                print("→ No se rompe ninguna arma")

        if resultado.get('rotura_armadura'):
            rotura_armadura = resultado['rotura_armadura']
            print("\n🛡 PRUEBA DE ROTURA DE ARMADURA")
            print(f"d10 {rotura_armadura['tirada']} + Rotura {rotura_armadura['rotura_arma']} = {rotura_armadura['total_rotura']}")
            print(f"Contra entereza de armadura: {rotura_armadura['entereza_armadura']}")
            if rotura_armadura['rompe_armadura']:
                print("→ La armadura se rompe (TA a 0)")
            else:
                print("→ La armadura resiste")
    
    elif resultado['contraataque']:
        print("\n❌ La defensa supera al ataque.")
        print(f"Diferencia: {resultado['diferencia']}")
        print(f"Contraataque disponible con bono +{resultado['bono_contraataque']}")
        
        if permitir_contraataque:
            respuesta = solicitar_texto("¿Realizar contraataque ahora? (s/n): ").lower()
            if respuesta in ['s', 'si', 'sí']:
                realizar_ataque(
                    objetivo,
                    gestor,
                    objetivo_forzado=personaje_combate,
                    bono_ataque_extra=resultado['bono_contraataque'],
                    permitir_contraataque=False
                )
    else:
        print("\n⚖ Ataque y defensa se igualan: sin daño ni contraataque.")
    
    input("\nPresiona Enter para continuar...")


def aplicar_ajuste_recurso(personaje, atributo, etiqueta):
    """
    Aplica un ajuste a un atributo numérico del personaje.
    """
    actual = getattr(personaje, atributo)
    print(f"\n{etiqueta} actual: {actual}")
    ajuste = solicitar_entero("Ajuste (puede ser negativo): ")
    nuevo_valor = max(0, actual + ajuste)
    setattr(personaje, atributo, nuevo_valor)
    print(f"{etiqueta} actualizado: {nuevo_valor}")


def realizar_ajustes(gestor):
    """
    Permite ajustar recursos durante el combate para cualquier participante.
    """
    objetivo_pc = seleccionar_participante_combate(gestor)
    if objetivo_pc is None:
        return

    personaje = objetivo_pc.personaje
    
    print("\n┌─── AJUSTES DE RECURSOS ───┐")
    print("│ 1. Puntos de Vida         │")
    print("│ 2. Puntos de Cansancio    │")
    print("│ 3. Puntos de Ki           │")
    
    opciones = {
        1: ('puntos_vida', 'Puntos de Vida'),
        2: ('puntos_cansancio', 'Puntos de Cansancio'),
        3: ('puntos_ki', 'Puntos de Ki')
    }
    
    siguiente = 4
    if isinstance(personaje, Mago):
        print(f"│ {siguiente}. Zeón                   │")
        opciones[siguiente] = ('zeon', 'Zeón')
        siguiente += 1
    if isinstance(personaje, Mentalista):
        print(f"│ {siguiente}. CV Libres             │")
        opciones[siguiente] = ('cv_libres', 'CV Libres')
        siguiente += 1
    
    print(f"│ {siguiente}. Cancelar              │")
    print("└───────────────────────────┘")
    
    opcion = solicitar_numero(f"\nSelecciona ajuste (1-{siguiente}): ", minimo=1, maximo=siguiente)
    
    if opcion == siguiente:
        return
    
    atributo, etiqueta = opciones[opcion]
    aplicar_ajuste_recurso(personaje, atributo, etiqueta)
    if personaje.puntos_vida <= 0:
        objetivo_pc.marcar_inconsciente()
    elif objetivo_pc.inconsciente and personaje.puntos_vida > 0:
        objetivo_pc.inconsciente = False
        objetivo_pc.ha_actuado = False
        objetivo_pc.puede_atacar = True

    input("\nPresiona Enter para continuar...")


def cambiar_equipo_participante(gestor):
    """Permite cambiar arma o armadura de cualquier participante en combate."""
    objetivo_pc = seleccionar_participante_combate(gestor)
    if objetivo_pc is None:
        return

    personaje = objetivo_pc.personaje
    print("\n¿Qué quieres cambiar?")
    print("  1. Arma")
    print("  2. Armadura")
    print("  3. Cancelar")

    opcion = solicitar_numero("Selecciona opción (1-3): ", minimo=1, maximo=3)
    if opcion == 3:
        return

    if opcion == 1:
        usa_arma = solicitar_texto("¿Equipar arma? (s/n): ")
        if es_respuesta_si(usa_arma):
            arma_nombre, arma_turno, arma_danio, arma_rotura, arma_entereza, arma_tipo_danio = solicitar_datos_arma(opcional=False)
            personaje.arma_nombre = arma_nombre
            personaje.arma_turno = arma_turno
            personaje.arma_danio = arma_danio
            personaje.arma_rotura = arma_rotura
            personaje.arma_entereza = arma_entereza
            personaje.arma_tipo_danio = arma_tipo_danio

            objetivo_pc.turno_base = arma_turno
            objetivo_pc.es_turno_arma = True
            objetivo_pc.daño_arma = arma_danio
            objetivo_pc.rotura_arma = arma_rotura
            objetivo_pc.entereza_arma = arma_entereza
            objetivo_pc.ta_ataque = arma_tipo_danio
            objetivo_pc.arma_rota = False
        else:
            personaje.arma_nombre = None
            personaje.arma_turno = None
            personaje.arma_danio = None
            personaje.arma_rotura = None
            personaje.arma_entereza = None
            personaje.arma_tipo_danio = None

            objetivo_pc.turno_base = personaje.turno
            objetivo_pc.es_turno_arma = False
            objetivo_pc.daño_arma = None
            objetivo_pc.rotura_arma = None
            objetivo_pc.entereza_arma = None
            objetivo_pc.ta_ataque = None
            objetivo_pc.arma_rota = False

    elif opcion == 2:
        print("\nActualizar armadura del participante")
        armaduras_ta, entereza_armadura = solicitar_armaduras_ta()
        personaje.armaduras_ta = dict(armaduras_ta)
        personaje.armadura = personaje.armaduras_ta.get('FIL', 0)
        personaje.entereza_armadura = entereza_armadura

    input("\nPresiona Enter para continuar...")


def menu_turno_personaje(personaje_combate, gestor):
    """
    Muestra el menú de acciones para el turno de un personaje.
    
    Args:
        personaje_combate: PersonajeCombate que está actuando
        gestor: GestorCombate
        
    Returns:
        bool: False si se debe salir del combate, True para continuar
    """
    print("\n┌─── ACCIONES ───┐")
    print("│ 1. Atacar      │")
    print("│ 2. Ajustes     │")
    print("│ 3. Equipo      │")
    print("│ 4. Pasar turno │")
    print("│ 5. Ver estado  │")
    print("│ 6. Salir       │")
    print("└────────────────┘")
    
    opcion = solicitar_numero("\nSelecciona acción (1-6): ", minimo=1, maximo=6)
    
    if opcion == 1:
        realizar_ataque(personaje_combate, gestor)
        finalizar = solicitar_texto("\n¿Finalizar turno? (s/n): ").lower()
        if finalizar in ['s', 'si', 'sí']:
            gestor.pasar_turno()
        return True
    
    elif opcion == 2:
        realizar_ajustes(gestor)
        finalizar = solicitar_texto("\n¿Finalizar turno? (s/n): ").lower()
        if finalizar in ['s', 'si', 'sí']:
            gestor.pasar_turno()
        return True
    
    elif opcion == 3:
        cambiar_equipo_participante(gestor)
        finalizar = solicitar_texto("\n¿Finalizar turno? (s/n): ").lower()
        if finalizar in ['s', 'si', 'sí']:
            gestor.pasar_turno()
        return True

    elif opcion == 4:
        gestor.pasar_turno()
        return True
    
    elif opcion == 5:
        print(f"\n{personaje_combate.personaje}")
        input("\nPresiona Enter para continuar...")
        return True
    
    elif opcion == 6:
        confirmacion = solicitar_texto("\n¿Seguro que quieres salir del combate? (s/n): ").lower()
        if confirmacion in ['s', 'si', 'sí']:
            return False
        return True
    
    return True


def gestionar_nueva_ronda(gestor):
    """
    Gestiona el inicio de una nueva ronda.
    
    Args:
        gestor: GestorCombate
        
    Returns:
        bool: True si continúa el combate, False si termina
    """
    print("\n¿Qué deseas hacer?")
    print("  1. Nueva ronda (recalcular iniciativas)")
    print("  2. Repetir orden actual (mismas iniciativas)")
    print("  3. Finalizar combate")
    
    opcion = solicitar_numero("\nSelecciona opción (1-3): ", minimo=1, maximo=3)
    
    if opcion == 1:
        # Nueva ronda con nuevas iniciativas
        print("\nCalculando nuevas iniciativas...")
        gestor.nueva_ronda(proveedor_iniciativa=proveedor_iniciativa_combate)
        print(gestor.obtener_desglose_iniciativas())
        input("\nPresiona Enter para continuar...")
        return True
    
    elif opcion == 2:
        # Reiniciar con mismo orden
        gestor.reiniciar_ronda_rapido()
        print("\n✓ Nueva ronda con el mismo orden de iniciativa")
        input("\nPresiona Enter para continuar...")
        return True
    
    else:
        # Finalizar combate
        return False


def crear_personaje_test(nombre, ataque=180, defensa=140, daño=100, pv=120, rf=30):
    """Crea un personaje base para escenarios de test."""
    armaduras_ta = {codigo: 3 for codigo in TA_CODIGOS}
    return Personaje(
        nombre=nombre,
        puntos_vida=pv,
        puntos_cansancio=8,
        puntos_ki=20,
        turno=100,
        habilidad_ataque=ataque,
        habilidad_defensa=defensa,
        daño=daño,
        armadura=armaduras_ta['FIL'],
        resistencia_fisica=rf,
        resistencia_enfermedades=0,
        resistencia_venenos=0,
        resistencia_magica=0,
        resistencia_psiquica=0,
        armaduras_ta=armaduras_ta,
        entereza_armadura=20
    )


def resultado_test_normal(valor_base, modificador, total_final, tipo='normal', cansancio=0):
    """Construye una tirada de test con total final controlado."""
    bono_cansancio = cansancio * 15
    dados = total_final - (valor_base + modificador + bono_cansancio)
    return {
        'tipo': tipo,
        'valor_base': valor_base,
        'modificador': modificador,
        'cansancio': cansancio,
        'bono_cansancio': bono_cansancio,
        'tiradas': [dados],
        'resultado_dados': dados,
        'resultado_total': total_final
    }


def resultado_test_pifia(valor_base, modificador, primera=2, tirada_pifia=70, cansancio=0, es_defensa=False):
    """Construye una pifia de test."""
    bono_cansancio = cansancio * 15
    modificador_pifia = 0
    if primera == 1:
        modificador_pifia = 15
    elif primera == 3:
        modificador_pifia = -15
    resultado_pifia = tirada_pifia + modificador_pifia
    datos = {
        'tipo': 'pifia',
        'valor_base': valor_base,
        'modificador': modificador,
        'cansancio': cansancio,
        'bono_cansancio': bono_cansancio,
        'primera_tirada': primera,
        'pifia': {
            'tirada_original': primera,
            'tirada_pifia': tirada_pifia,
            'modificador': modificador_pifia,
            'resultado_final': resultado_pifia,
            'pifia_grave': resultado_pifia >= 80
        }
    }
    if es_defensa:
        datos['resultado_total'] = valor_base + modificador + bono_cansancio - resultado_pifia
    return datos


def obtener_escenarios_test():
    """Devuelve escenarios predefinidos para validar casuísticas de combate."""
    return [
        {
            'nombre': 'Impacto limpio',
            'descripcion': 'Ataque exitoso con daño normal.',
            'ataque_total': 250,
            'defensa_total': 120,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'FIL'
        },
        {
            'nombre': 'Fallo con contraataque',
            'descripcion': 'La defensa supera al ataque y genera bono de contraataque.',
            'ataque_total': 140,
            'defensa_total': 210,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'FIL'
        },
        {
            'nombre': 'Pifia de ataque',
            'descripcion': 'Pifia automática sin defensa.',
            'pifia_ataque': True,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'FIL'
        },
        {
            'nombre': 'Crítico resistido',
            'descripcion': 'Hay crítico, pero el defensor lo resiste sin consecuencias.',
            'ataque_total': 280,
            'defensa_total': 120,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'FIL',
            'critico_tiradas': (45, 95)
        },
        {
            'nombre': 'Crítico severo (dolor+deterioro)',
            'descripcion': 'Crítico > 50 tras resistencia; se divide entre dolor y deterioro.',
            'ataque_total': 320,
            'defensa_total': 90,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'FIL',
            'critico_tiradas': (100, 1)
        },
        {
            'nombre': 'Golpe apuntado (cabeza)',
            'descripcion': 'Simula localización con penalizador de ataque importante.',
            'ataque_total': 230,
            'defensa_total': 150,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'CON',
            'nota': 'Modificador de localización aplicado en el escenario: -60'
        },
        {
            'nombre': 'Choque de armas (parada)',
            'descripcion': 'Impacto con parada y chequeo de rotura entre armas.',
            'ataque_total': 240,
            'defensa_total': 160,
            'tipo_defensa': 'Parada',
            'tipo_danio': 'FIL',
            'rotura_arma': True
        },
        {
            'nombre': 'Rotura de armadura',
            'descripcion': 'Impacto que además chequea y rompe armadura del defensor.',
            'ataque_total': 260,
            'defensa_total': 140,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'PEN',
            'rotura_armadura': True
        },
        {
            'nombre': 'KO por daño (PV ≤ 0)',
            'descripcion': 'El defensor cae inconsciente y se retira del combate.',
            'ataque_total': 350,
            'defensa_total': 100,
            'tipo_defensa': 'Esquiva',
            'tipo_danio': 'FIL',
            'pv_defensor': 60
        }
    ]


def ejecutar_escenario_test(escenario, semilla=1234):
    """Ejecuta un escenario individual de test y muestra resultado detallado."""
    configurar_semilla(semilla)
    atacante = crear_personaje_test('Atacante', ataque=200, defensa=140, daño=120, pv=160, rf=20)
    defensor_pv = escenario.get('pv_defensor', 140)
    defensor = crear_personaje_test('Defensor', ataque=150, defensa=150, daño=90, pv=defensor_pv, rf=25)

    atacante_pc = PersonajeCombate(atacante, turno_base=120, daño_arma=120, rotura_arma=8, entereza_arma=12, ta_ataque=escenario.get('tipo_danio', 'FIL'))
    defensor_pc = PersonajeCombate(defensor, turno_base=100, daño_arma=70, rotura_arma=6, entereza_arma=10, ta_ataque='FIL')

    if escenario.get('rotura_arma'):
        atacante_pc.rotura_arma = 25
        atacante_pc.entereza_arma = 6
        defensor_pc.rotura_arma = 20
        defensor_pc.entereza_arma = 4

    if escenario.get('rotura_armadura'):
        atacante_pc.rotura_arma = 30
        defensor.entereza_armadura = 5

    valor_ataque, _ = obtener_valor_ataque(atacante)
    valor_defensa, _ = obtener_valor_defensa(defensor)

    if escenario.get('pifia_ataque'):
        resultado_ataque = resultado_test_pifia(valor_ataque, 0, primera=2, tirada_pifia=80)
        resultado_defensa = None
    else:
        resultado_ataque = resultado_test_normal(valor_ataque, 0, escenario['ataque_total'])
        resultado_defensa = resultado_test_normal(valor_defensa, 0, escenario['defensa_total'])

    critico_tiradas = escenario.get('critico_tiradas')
    def proveedor_critico(tipo, _pc):
        if not critico_tiradas:
            return None
        return critico_tiradas[0] if tipo == 'ataque' else critico_tiradas[1]

    resultado = resolver_ataque(
        atacante_pc,
        defensor_pc,
        modificador_ataque=0,
        cansancio_gastado=0,
        modificador_defensa=0,
        cansancio_defensa=0,
        daño_arma=atacante_pc.daño_arma,
        resultado_ataque=resultado_ataque,
        resultado_defensa=resultado_defensa,
        tipo_defensa=escenario.get('tipo_defensa', 'Esquiva'),
        proveedor_tirada_critica=proveedor_critico,
        ta_ataque=escenario.get('tipo_danio', 'FIL')
    )

    print("\n" + "=" * 70)
    print(f"ESCENARIO: {escenario['nombre']}")
    print(f"Descripción: {escenario['descripcion']}")
    if escenario.get('nota'):
        print(f"Nota: {escenario['nota']}")
    print("=" * 70)
    mostrar_detalle_tirada_ataque(resultado['ataque'])
    if resultado['defensa'] is not None:
        mostrar_detalle_tirada_defensa(resultado['defensa'])

    if resultado['defensa'] is None:
        print("\nResultado: pifia de ataque, sin defensa.")
    else:
        print(f"\nResultado numérico: Ataque {resultado['ataque']['resultado_total']} vs Defensa {resultado['defensa']['resultado_total']}")

    if resultado['impacto']:
        print("✅ Impacto")
        print(f"Daño aplicado: {resultado['danio_aplicado']}")
        print(f"PV defensor: {defensor.puntos_vida}")
    elif resultado['contraataque']:
        print(f"❌ Fallo con contraataque +{resultado['bono_contraataque']}")
    else:
        print("⚖ Empate sin daño")

    if resultado.get('critico'):
        critico = resultado['critico']
        print(f"Crítico: {critico['resultado']} (consecuencias: {'sí' if critico['tiene_consecuencias'] else 'no'})")
        print(f"Penalizador actual defensor: -{defensor_pc.penalizador_dolor + defensor_pc.penalizador_deterioro}")

    if resultado.get('choque_armas'):
        choque = resultado['choque_armas']
        print(f"Choque de armas: A={choque['total_atacante']} vs D={choque['total_defensor']}")
        print(f"Arma atacante rota: {'sí' if choque['rompe_arma_atacante'] else 'no'}")
        print(f"Arma defensor rota: {'sí' if choque['rompe_arma_defensor'] else 'no'}")

    if resultado.get('rotura_armadura'):
        rot = resultado['rotura_armadura']
        print(f"Rotura armadura: {rot['total_rotura']} vs entereza {rot['entereza_armadura']} -> {'rota' if rot['rompe_armadura'] else 'resiste'}")

    if defensor_pc.inconsciente:
        print("✖ Defensor inconsciente (fuera de combate)")


def ejecutar_bateria_tests(semilla):
    """Ejecuta todos los escenarios de test en serie."""
    escenarios = obtener_escenarios_test()
    for i, escenario in enumerate(escenarios, 1):
        ejecutar_escenario_test(escenario, semilla=semilla + i)
        print("\n" + "-" * 70)


def modo_test(_almacenamiento):
    """Modo test orientado a escenarios predefinidos de combate."""
    semilla_test = 1234
    escenarios = obtener_escenarios_test()

    while True:
        limpiar_pantalla()
        print("\n╔═══════════════════════════════════════════════════╗")
        print("║              MODO TEST ESCENARIOS                ║")
        print("╚═══════════════════════════════════════════════════╝\n")

        print(f"Semilla actual: {semilla_test}")
        print("1. Ejecutar batería completa")
        print("2. Ejecutar escenario individual")
        print("3. Cambiar semilla")
        print("4. Ver listado de escenarios")
        print("5. Volver")

        opcion = solicitar_numero("\nSelecciona opción (1-5): ", minimo=1, maximo=5)

        if opcion == 1:
            ejecutar_bateria_tests(semilla_test)
            input("\nPresiona Enter para continuar...")

        elif opcion == 2:
            print("\nEscenarios disponibles:")
            for i, escenario in enumerate(escenarios, 1):
                print(f"  {i}. {escenario['nombre']}")
            print(f"  {len(escenarios) + 1}. Cancelar")

            elegido = solicitar_numero(
                f"\nSelecciona escenario (1-{len(escenarios) + 1}): ",
                minimo=1,
                maximo=len(escenarios) + 1
            )
            if elegido <= len(escenarios):
                ejecutar_escenario_test(escenarios[elegido - 1], semilla=semilla_test)
                input("\nPresiona Enter para continuar...")

        elif opcion == 3:
            nueva = solicitar_texto("Nueva semilla (Enter para 1234): ", permitir_vacio=True)
            if nueva:
                try:
                    semilla_test = int(nueva)
                except ValueError:
                    print("⚠ Semilla inválida")
                    input("\nPresiona Enter para continuar...")
            else:
                semilla_test = 1234

        elif opcion == 4:
            print("\nListado de escenarios:")
            for i, escenario in enumerate(escenarios, 1):
                print(f"\n{i}. {escenario['nombre']}")
                print(f"   - {escenario['descripcion']}")
                if escenario.get('nota'):
                    print(f"   - Nota: {escenario['nota']}")
            input("\nPresiona Enter para continuar...")

        else:
            return


def ejecutar_cli():
    """Ejecuta la aplicación en modo terminal (CLI)."""
    almacenamiento = AlmacenamientoPersonajes()
    
    while True:
        limpiar_pantalla()
        mostrar_encabezado()
        mostrar_menu()
        
        opcion = solicitar_numero("\nSelecciona una opción (1-8): ", minimo=1, maximo=8)
        
        if opcion == 1:
            asistente_crear_personaje(almacenamiento)
        elif opcion == 2:
            listar_personajes(almacenamiento)
        elif opcion == 3:
            ver_personaje(almacenamiento)
        elif opcion == 4:
            editar_personaje(almacenamiento)
        elif opcion == 5:
            eliminar_personaje(almacenamiento)
        elif opcion == 6:
            gestionar_combate(almacenamiento)
        elif opcion == 7:
            modo_test(almacenamiento)
        elif opcion == 8:
            print("\n¡Hasta luego!")
            sys.exit(0)


def main():
    """Punto de entrada principal; GUI por defecto, CLI con --cli."""
    argumentos = {arg.strip().lower() for arg in sys.argv[1:]}
    usar_cli = "--cli" in argumentos or "--terminal" in argumentos

    if usar_cli:
        ejecutar_cli()
        return

    try:
        from interfaz.gui import iniciar_interfaz_grafica
        iniciar_interfaz_grafica()
    except (ImportError, ModuleNotFoundError, OSError, RuntimeError) as error:
        print(f"⚠ No se pudo iniciar la interfaz gráfica ({error}).")
        print("⚠ Se iniciará el modo terminal automáticamente.\n")
        ejecutar_cli()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n¡Hasta luego!")
        sys.exit(0)
