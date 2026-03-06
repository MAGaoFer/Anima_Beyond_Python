"""
Sistema de cálculo de iniciativa para combate en Ánima: Beyond Fantasy.
"""

from .dados import tirar_iniciativa
from modelos.personaje import personaje_tiene_natura


class PersonajeCombate:
    """
    Envoltorio para un personaje en combate con información adicional.
    
    Atributos:
        personaje: Instancia del personaje (Personaje, Mago o Mentalista)
        turno_base (int): Turno base a usar (puede ser distinto al del personaje)
        iniciativa (int): Iniciativa calculada para la ronda actual
        desglose_iniciativa (str): Desglose de cómo se calculó la iniciativa
        ha_actuado (bool): Indica si ya actuó en la ronda actual
        es_turno_arma (bool): True si usa turno de arma, False si es desarmado
    """
    
    def __init__(self, personaje, turno_base=None, daño_arma=None, rotura_arma=None, entereza_arma=None, ta_ataque=None):
        """
        Inicializa un personaje para combate.
        
        Args:
            personaje: Instancia del personaje
            turno_base (int, opcional): Turno base específico. Si es None, usa el del personaje
        """
        self.personaje = personaje
        self.turno_base = turno_base if turno_base is not None else personaje.turno
        self.es_turno_arma = turno_base is not None and turno_base != personaje.turno
        self.daño_arma = daño_arma
        self.rotura_arma = rotura_arma
        self.entereza_arma = entereza_arma
        self.ta_ataque = ta_ataque
        self.arma_rota = False
        self.armas_rotas = set()
        self.es_escudo = False
        self.armas_activas = []
        self.arma_ataque_actual = None
        self.arma_parada_actual = None
        self.habilidad_ataque_override = None
        self.habilidad_defensa_override = None
        self.inconsciente = False
        
        # Atributos de combate
        self.iniciativa = 0
        self.desglose_iniciativa = ""
        self.ha_actuado = False
        self.puede_atacar = True
        self.esta_a_la_defensiva = False
        self.defensas_realizadas = 0
        self.penalizador_dolor = 0
        self.penalizador_deterioro = 0

    def _clave_arma(self, arma):
        if arma is None:
            return None
        nombre = arma.get('nombre')
        if not nombre:
            return None
        return str(nombre).strip().lower()

    def esta_arma_rota(self, arma):
        clave = self._clave_arma(arma)
        return bool(clave and clave in self.armas_rotas)

    def registrar_arma_rota(self, arma):
        clave = self._clave_arma(arma)
        if clave:
            self.armas_rotas.add(clave)
    
    def calcular_iniciativa(self):
        """
        Calcula la iniciativa para este personaje en la ronda actual.
        
        Returns:
            int: Iniciativa calculada
        """
        iniciativa_base, desglose = tirar_iniciativa(
            self.turno_base,
            permitir_abierta=personaje_tiene_natura(self.personaje),
        )
        penalizador = self.obtener_penalizador_automatico(cansancio_gastado=0)
        self.iniciativa = iniciativa_base + penalizador
        if penalizador:
            self.desglose_iniciativa = f"{desglose} + ({penalizador}) = {self.iniciativa}"
        else:
            self.desglose_iniciativa = desglose
        self.ha_actuado = False
        self.puede_atacar = not self.inconsciente
        self.esta_a_la_defensiva = False
        self.defensas_realizadas = 0
        return self.iniciativa

    def asignar_iniciativa_manual(self, iniciativa, desglose):
        """Asigna iniciativa manual (usada para personajes PJ)."""
        self.iniciativa = iniciativa
        self.desglose_iniciativa = desglose
        self.ha_actuado = False
        self.puede_atacar = not self.inconsciente
        self.esta_a_la_defensiva = False
        self.defensas_realizadas = 0
        return self.iniciativa
    
    def marcar_turno_completado(self):
        """Marca que este personaje ya actuó en su turno."""
        self.ha_actuado = True
    
    def reiniciar_turno(self):
        """Reinicia el estado del turno para una nueva ronda."""
        self.ha_actuado = False
        self.puede_atacar = not self.inconsciente
        self.esta_a_la_defensiva = False
        self.defensas_realizadas = 0

    def obtener_penalizador_cansancio(self):
        """Devuelve penalizador por cansancio actual."""
        cansancio = self.personaje.puntos_cansancio
        if cansancio <= 0:
            return -120
        if cansancio == 1:
            return -80
        if cansancio == 2:
            return -40
        if cansancio == 3:
            return -20
        if cansancio == 4:
            return -10
        return 0

    def obtener_penalizador_dolor_total(self):
        """Penalizador total por dolor y deterioro físico."""
        return -(self.penalizador_dolor + self.penalizador_deterioro)

    def obtener_penalizador_automatico(self, cansancio_gastado=0):
        """Penalizador automático para acciones (iniciativa/ataque/defensa)."""
        penalizador = self.obtener_penalizador_dolor_total()
        if cansancio_gastado <= 0:
            penalizador += self.obtener_penalizador_cansancio()
        return penalizador

    def aplicar_critico(self, exceso_critico):
        """Aplica penalizadores persistentes por crítico no resistido."""
        if exceso_critico <= 0:
            return
        if exceso_critico > 50:
            dolor = exceso_critico // 2
            deterioro = exceso_critico - dolor
            self.penalizador_dolor += dolor
            self.penalizador_deterioro += deterioro
            return
        self.penalizador_dolor += exceso_critico

    def recuperar_dolor_fin_ronda(self):
        """Recupera dolor a ritmo de 5 por asalto."""
        self.penalizador_dolor = max(0, self.penalizador_dolor - 5)

    def marcar_inconsciente(self):
        """Marca personaje inconsciente (fuera de combate)."""
        self.inconsciente = True
        self.puede_atacar = False
        self.ha_actuado = True

    def marcar_defensiva(self):
        """Marca al personaje como 'a la defensiva' para el resto de la ronda."""
        self.puede_atacar = False
        self.esta_a_la_defensiva = True

    def obtener_penalizador_defensas_multiples(self):
        """Devuelve el penalizador automático por número de defensa en la ronda."""
        siguiente_defensa = self.defensas_realizadas + 1
        if siguiente_defensa <= 1:
            return 0
        if siguiente_defensa == 2:
            return -30
        if siguiente_defensa == 3:
            return -50
        if siguiente_defensa == 4:
            return -70
        return -90

    def registrar_defensa(self):
        """Incrementa el contador de defensas realizadas en la ronda."""
        self.defensas_realizadas += 1

    def configurar_arma_ataque(self, arma):
        """Configura el arma activa para ataque."""
        if arma is None:
            self.arma_ataque_actual = None
            self.habilidad_ataque_override = None
            self.daño_arma = None
            self.rotura_arma = None
            self.entereza_arma = None
            self.ta_ataque = None
            self.es_escudo = False
            self.arma_rota = False
            return
        self.arma_ataque_actual = arma
        self.habilidad_ataque_override = arma.get('habilidad_ataque')
        self.daño_arma = arma.get('daño')
        self.rotura_arma = arma.get('rotura')
        self.entereza_arma = arma.get('entereza')
        self.ta_ataque = arma.get('tipo_danio')
        self.es_escudo = bool(arma.get('es_escudo', False))
        self.arma_rota = self.esta_arma_rota(arma)

    def configurar_arma_parada(self, arma):
        """Configura el arma/escudo activa para parada."""
        if arma is None:
            self.arma_parada_actual = None
            self.habilidad_defensa_override = None
            self.rotura_arma = None
            self.entereza_arma = None
            self.arma_rota = False
            return
        self.arma_parada_actual = arma
        self.habilidad_defensa_override = arma.get('habilidad_parada')
        self.rotura_arma = arma.get('rotura')
        self.entereza_arma = arma.get('entereza')
        self.arma_rota = self.esta_arma_rota(arma)
    
    def obtener_info_turno(self):
        """
        Obtiene información del turno base usado.
        
        Returns:
            str: Descripción del turno base
        """
        if self.es_turno_arma:
            return f"{self.turno_base} (Armado)"
        return f"{self.turno_base} (Desarmado)"
    
    def __str__(self):
        """
        Representación en texto del personaje en combate.
        
        Returns:
            str: Descripción del estado en combate
        """
        if self.ha_actuado:
            estado = "✓ Actuó"
        elif self.inconsciente:
            estado = "✖ Inconsciente"
        elif self.esta_a_la_defensiva:
            estado = "◈ Defensiva"
        else:
            estado = "→ Esperando"
        return (f"{self.personaje.nombre} | "
                f"Ini: {self.iniciativa} | "
                f"PV: {self.personaje.puntos_vida} | "
                f"{estado}")


def calcular_iniciativa(personaje, turno_base=None):
    """
    Calcula la iniciativa para un personaje.
    
    Esta es una función de conveniencia que crea un PersonajeCombate
    y calcula su iniciativa.
    
    Args:
        personaje: Instancia del personaje
        turno_base (int, opcional): Turno base a usar
        
    Returns:
        tuple: (iniciativa, desglose_texto)
    """
    pc = PersonajeCombate(personaje, turno_base)
    iniciativa = pc.calcular_iniciativa()
    return iniciativa, pc.desglose_iniciativa


def ordenar_por_iniciativa(personajes_combate):
    """
    Ordena una lista de PersonajeCombate por iniciativa (de mayor a menor).
    
    En caso de empate, mantiene el orden original.
    
    Args:
        personajes_combate (list): Lista de PersonajeCombate
        
    Returns:
        list: Lista ordenada por iniciativa descendente
    """
    return sorted(personajes_combate, key=lambda pc: pc.iniciativa, reverse=True)
