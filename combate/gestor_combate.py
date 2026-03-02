"""
Gestor de combate para Ánima: Beyond Fantasy.
Coordina rondas, turnos y el flujo general del combate.
"""

from .iniciativa import PersonajeCombate, ordenar_por_iniciativa


class GestorCombate:
    """
    Gestiona el flujo completo de un combate en Ánima: Beyond Fantasy.
    
    Responsabilidades:
    - Añadir personajes al combate
    - Calcular y ordenar iniciativas
    - Controlar el turno actual
    - Gestionar rondas
    - Mantener el estado del combate
    
    Atributos:
        personajes_combate (list): Lista de PersonajeCombate en el combate
        orden_iniciativa (list): Lista ordenada por iniciativa
        indice_turno_actual (int): Índice del personaje que está actuando
        ronda_actual (int): Número de la ronda actual
        combate_iniciado (bool): Si el combate ha comenzado
    """
    
    def __init__(self):
        """Inicializa un nuevo gestor de combate."""
        self.personajes_combate = []
        self.orden_iniciativa = []
        self.indice_turno_actual = 0
        self.ronda_actual = 0
        self.combate_iniciado = False
        self.modo_test = False
        self.semilla_test = None
    
    def añadir_personaje(self, personaje, turno_base=None, daño_arma=None, rotura_arma=None, entereza_arma=None, ta_ataque=None):
        """
        Añade un personaje al combate.
        
        Args:
            personaje: Instancia del personaje
            turno_base (int, opcional): Turno base a usar (None = usar turno del personaje)
            
        Returns:
            PersonajeCombate: El personaje añadido al combate
        """
        pc = PersonajeCombate(personaje, turno_base, daño_arma, rotura_arma, entereza_arma, ta_ataque)
        self.personajes_combate.append(pc)
        return pc
    
    def eliminar_personaje(self, nombre_personaje):
        """
        Elimina un personaje del combate.
        
        Args:
            nombre_personaje (str): Nombre del personaje a eliminar
            
        Returns:
            bool: True si se eliminó, False si no se encontró
        """
        for i, pc in enumerate(self.personajes_combate):
            if pc.personaje.nombre == nombre_personaje:
                self.personajes_combate.pop(i)
                # Recalcular orden si el combate ya inició
                if self.combate_iniciado:
                    self._recalcular_orden_iniciativa()
                return True
        return False
    
    def obtener_personajes_nombres(self):
        """
        Obtiene los nombres de todos los personajes en combate.
        
        Returns:
            list: Lista de nombres de personajes
        """
        return [pc.personaje.nombre for pc in self.personajes_combate]
    
    def actualizar_turno_base(self, nombre_personaje, nuevo_turno):
        """
        Actualiza el turno base de un personaje.
        
        Args:
            nombre_personaje (str): Nombre del personaje
            nuevo_turno (int): Nuevo valor de turno base
            
        Returns:
            bool: True si se actualizó, False si no se encontró
        """
        for pc in self.personajes_combate:
            if pc.personaje.nombre == nombre_personaje:
                pc.turno_base = nuevo_turno
                pc.es_turno_arma = nuevo_turno != pc.personaje.turno
                return True
        return False
    
    def iniciar_combate(self, proveedor_iniciativa=None):
        """
        Inicia el combate calculando iniciativas y ordenando personajes.
        
        Returns:
            bool: True si se inició correctamente
        """
        if not self.personajes_combate:
            return False
        
        # Calcular iniciativas
        for pc in self.personajes_combate:
            if proveedor_iniciativa is not None:
                iniciativa_manual, desglose = proveedor_iniciativa(pc)
                if iniciativa_manual is not None:
                    pc.asignar_iniciativa_manual(iniciativa_manual, desglose)
                    continue
            pc.calcular_iniciativa()
        
        # Ordenar por iniciativa
        self.orden_iniciativa = ordenar_por_iniciativa(self.personajes_combate)
        
        # Configurar estado inicial
        self.indice_turno_actual = 0
        self.ronda_actual = 1
        self.combate_iniciado = True
        
        return True
    
    def _recalcular_orden_iniciativa(self):
        """Recalcula el orden de iniciativa sin cambiar las iniciativas."""
        self.orden_iniciativa = ordenar_por_iniciativa(self.personajes_combate)
        # Ajustar índice del turno actual
        if self.indice_turno_actual >= len(self.orden_iniciativa):
            self.indice_turno_actual = 0
    
    def obtener_personaje_actual(self):
        """
        Obtiene el personaje que está actuando actualmente.
        
        Returns:
            PersonajeCombate|None: Personaje actual o None si no hay
        """
        if not self.combate_iniciado or not self.orden_iniciativa:
            return None
        
        while self.indice_turno_actual < len(self.orden_iniciativa):
            candidato = self.orden_iniciativa[self.indice_turno_actual]
            if not candidato.inconsciente:
                return candidato
            self.indice_turno_actual += 1
        
        return None
    
    def pasar_turno(self):
        """
        Marca el turno actual como completado y pasa al siguiente personaje.
        
        Returns:
            tuple: (turno_pasado, ronda_completada)
                - turno_pasado (bool): Si se pasó el turno correctamente
                - ronda_completada (bool): Si se completó la ronda
        """
        if not self.combate_iniciado:
            return False, False
        
        personaje_actual = self.obtener_personaje_actual()
        if personaje_actual:
            personaje_actual.marcar_turno_completado()
        
        # Avanzar al siguiente personaje
        self.indice_turno_actual += 1
        
        # Verificar si la ronda se completó
        if self.indice_turno_actual >= len(self.orden_iniciativa):
            return True, True
        
        return True, False
    
    def nueva_ronda(self, proveedor_iniciativa=None):
        """
        Finaliza la ronda actual e inicia una nueva.
        
        Recalcula iniciativas y reinicia el orden de turnos.
        
        Returns:
            bool: True si se inició correctamente la nueva ronda
        """
        if not self.combate_iniciado:
            return False
        
        # Recuperar dolor y calcular nuevas iniciativas
        for pc in self.personajes_combate:
            pc.recuperar_dolor_fin_ronda()
            if proveedor_iniciativa is not None:
                iniciativa_manual, desglose = proveedor_iniciativa(pc)
                if iniciativa_manual is not None:
                    pc.asignar_iniciativa_manual(iniciativa_manual, desglose)
                    continue
            pc.calcular_iniciativa()
        
        # Reordenar por nueva iniciativa
        self.orden_iniciativa = ordenar_por_iniciativa(self.personajes_combate)
        
        # Reiniciar estado de ronda
        self.indice_turno_actual = 0
        self.ronda_actual += 1
        
        return True
    
    def reiniciar_ronda_rapido(self):
        """
        Reinicia la ronda sin recalcular iniciativas.
        
        Útil cuando se quiere repetir el mismo orden de turnos.
        
        Returns:
            bool: True si se reinició correctamente
        """
        if not self.combate_iniciado:
            return False
        
        # Reiniciar estado de turno sin recalcular iniciativa
        for pc in self.personajes_combate:
            pc.recuperar_dolor_fin_ronda()
            pc.reiniciar_turno()
        
        self.indice_turno_actual = 0
        self.ronda_actual += 1
        
        return True
    
    def obtener_tabla_combate(self):
        """
        Genera una tabla visual del estado del combate.
        
        Returns:
            str: Tabla formateada con el estado del combate
        """
        if not self.combate_iniciado or not self.orden_iniciativa:
            return "No hay combate activo"
        
        lineas = []
        lineas.append("╔═══════════════════════════════════════════════════════════════╗")
        lineas.append(f"║  COMBATE - RONDA {self.ronda_actual}                                            ║")
        lineas.append("╠═══════════════════════════════════════════════════════════════╣")
        lineas.append("║ #  │ Nombre          │ Ini  │ PV   │ Estado                 ║")
        lineas.append("╟────┼─────────────────┼──────┼──────┼────────────────────────╢")
        
        for i, pc in enumerate(self.orden_iniciativa, 1):
            # Indicador de turno actual
            indicador = "►" if i == self.indice_turno_actual + 1 else " "
            
            # Estado
            if pc.inconsciente:
                estado = "✖ Inconsciente"
            elif pc.ha_actuado:
                estado = "✓ Actuó"
            elif pc.esta_a_la_defensiva:
                estado = "◈ Defensiva"
            elif i == self.indice_turno_actual + 1:
                estado = "→ Actuando"
            else:
                estado = "○ Esperando"
            
            # Formato de la fila
            nombre = pc.personaje.nombre[:15].ljust(15)
            ini = str(pc.iniciativa).rjust(4)
            pv = str(pc.personaje.puntos_vida).rjust(4)
            
            lineas.append(f"║ {indicador}{i}  │ {nombre} │ {ini} │ {pv} │ {estado.ljust(22)} ║")
        
        lineas.append("╚═══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lineas)
    
    def obtener_desglose_iniciativas(self):
        """
        Obtiene el desglose de cómo se calculó la iniciativa de cada personaje.
        
        Returns:
            str: Desglose formateado de todas las iniciativas
        """
        if not self.combate_iniciado or not self.orden_iniciativa:
            return "No hay iniciativas calculadas"
        
        lineas = []
        lineas.append("\n┌─── DESGLOSE DE INICIATIVAS ───┐")
        
        for pc in self.orden_iniciativa:
            turno_info = pc.obtener_info_turno()
            lineas.append(f"│ {pc.personaje.nombre}:")
            lineas.append(f"│   Turno base: {turno_info}")
            lineas.append(f"│   Tirada: {pc.desglose_iniciativa}")
            lineas.append("│")
        
        lineas.append("└───────────────────────────────┘")
        
        return "\n".join(lineas)
    
    def esta_combate_activo(self):
        """
        Verifica si hay un combate activo.
        
        Returns:
            bool: True si el combate está activo
        """
        return self.combate_iniciado
    
    def finalizar_combate(self):
        """
        Finaliza el combate y limpia el estado.
        """
        self.personajes_combate = []
        self.orden_iniciativa = []
        self.indice_turno_actual = 0
        self.ronda_actual = 0
        self.combate_iniciado = False
    
    def obtener_resumen(self):
        """
        Obtiene un resumen del estado del combate.
        
        Returns:
            dict: Diccionario con información del combate
        """
        return {
            'activo': self.combate_iniciado,
            'ronda': self.ronda_actual,
            'num_personajes': len(self.personajes_combate),
            'turno_actual': self.indice_turno_actual + 1 if self.combate_iniciado else 0
        }
