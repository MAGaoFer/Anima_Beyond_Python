"""
Clases para modelar personajes del juego Ánima: Beyond Fantasy
"""


TA_CODIGOS = ('FIL', 'CON', 'PEN', 'CAL', 'ELE', 'FRI', 'ENE')


def normalizar_ta(codigo_ta):
    """Normaliza y valida un código TA."""
    if codigo_ta is None:
        return None
    codigo = str(codigo_ta).strip().upper()
    if len(codigo) > 3:
        codigo = codigo[:3]
    if codigo not in TA_CODIGOS:
        raise ValueError(f"TA inválida: {codigo_ta}")
    return codigo


def normalizar_arma(arma):
    """Normaliza estructura de arma para almacenamiento/uso en combate."""
    return {
        'nombre': arma.get('nombre', 'Arma'),
        'turno': int(arma.get('turno', 0)),
        'daño': int(arma.get('daño', 0)),
        'rotura': int(arma.get('rotura', 0)),
        'entereza': int(arma.get('entereza', 0)),
        'tipo_danio': normalizar_ta(arma.get('tipo_danio', arma.get('ta', 'FIL'))),
        'habilidad_ataque': int(arma.get('habilidad_ataque', 0)),
        'habilidad_parada': int(arma.get('habilidad_parada', 0)),
        'es_escudo': bool(arma.get('es_escudo', False))
    }


def normalizar_habilidades_secundarias(habilidades):
    """Normaliza la estructura {categoria: {habilidad: valor}}."""
    if not isinstance(habilidades, dict):
        return {}

    resultado = {}
    for categoria, valores in habilidades.items():
        if not isinstance(valores, dict):
            continue
        categoria_txt = str(categoria).strip()
        if not categoria_txt:
            continue

        categoria_limpia = {}
        for habilidad, valor in valores.items():
            habilidad_txt = str(habilidad).strip()
            if not habilidad_txt:
                continue

            if valor is None:
                valor_limpio = '-'
            elif isinstance(valor, bool):
                valor_limpio = int(valor)
            elif isinstance(valor, (int, float)):
                valor_limpio = int(valor)
            else:
                texto = str(valor).strip()
                valor_limpio = texto if texto else '-'
            categoria_limpia[habilidad_txt] = valor_limpio

        if categoria_limpia:
            resultado[categoria_txt] = categoria_limpia

    return resultado


def personaje_tiene_ki(personaje):
    """Indica si el personaje usa Ki como recurso propio."""
    return bool(getattr(personaje, 'usa_ki', False))


def personaje_puede_usar_armas(personaje):
    """Indica si el personaje puede combatir con habilidades marciales."""
    return bool(getattr(personaje, 'usa_combate_marcial', False))


def personaje_puede_usar_magia(personaje):
    """Indica si el personaje puede lanzar poderes mágicos."""
    return bool(getattr(personaje, 'usa_magia', False))


def personaje_puede_usar_mentalismo(personaje):
    """Indica si el personaje puede lanzar poderes mentales."""
    return bool(getattr(personaje, 'usa_mentalismo', False))


def personaje_tiene_natura(personaje):
    """Indica si el personaje puede realizar tiradas abiertas automáticas."""
    if bool(getattr(personaje, 'es_pj', False)):
        return True
    return bool(getattr(personaje, 'natura', True))


class Personaje:
    """
    Clase base para representar un personaje en Ánima: Beyond Fantasy.
    
    Atributos:
        nombre (str): Nombre del personaje
        puntos_vida (int): Puntos de vida actuales
        puntos_cansancio (int): Puntos de cansancio acumulados
        puntos_ki (int): Puntos de ki disponibles
        turno (int): Valor de turno/iniciativa
        habilidad_ataque (int): Habilidad de ataque del personaje
        habilidad_defensa (int): Habilidad de defensa del personaje
        daño (int): Daño base del personaje
        armadura (int): Valor de armadura
    """
    
    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki=0,
                 turno=0, habilidad_ataque=0, habilidad_defensa=0, daño=0, armadura=0,
                 resistencia_fisica=0, resistencia_enfermedades=0,
                 resistencia_venenos=0, resistencia_magica=0, resistencia_psiquica=0,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 tipo_defensa_preferida='Parada', bonificador=0, penalizador=0,
                 natura=None):
        """
        Inicializa un personaje con sus atributos básicos.
        
        Args:
            nombre (str): Nombre del personaje
            puntos_vida (int): Puntos de vida
            puntos_cansancio (int): Puntos de cansancio
            puntos_ki (int): Puntos de ki
            turno (int): Valor de turno
            habilidad_ataque (int): Habilidad de ataque
            habilidad_defensa (int): Habilidad de defensa
            daño (int): Daño base
            armadura (int): Valor de armadura
        """
        self.nombre = nombre
        self.puntos_vida = puntos_vida
        self.puntos_cansancio = puntos_cansancio
        self.puntos_ki = puntos_ki
        self.turno = turno
        self.habilidad_ataque = habilidad_ataque
        self.habilidad_defensa = habilidad_defensa
        self.daño = daño
        if armaduras_ta is None:
            valor_base = armadura if armadura is not None else 0
            self.armaduras_ta = {codigo: valor_base for codigo in TA_CODIGOS}
        else:
            self.armaduras_ta = {}
            for codigo in TA_CODIGOS:
                self.armaduras_ta[codigo] = int(armaduras_ta.get(codigo, 0))
        self.armadura = self.armaduras_ta.get('FIL', 0)
        self.entereza_armadura = entereza_armadura
        self.resistencia_fisica = resistencia_fisica
        self.resistencia_enfermedades = resistencia_enfermedades
        self.resistencia_venenos = resistencia_venenos
        self.resistencia_magica = resistencia_magica
        self.resistencia_psiquica = resistencia_psiquica
        self.es_pj = es_pj
        self.natura = True if es_pj else (True if natura is None else bool(natura))
        self.arma_nombre = arma_nombre
        self.arma_turno = arma_turno
        self.arma_danio = arma_danio
        self.arma_rotura = arma_rotura
        self.arma_entereza = arma_entereza
        tipo_danio_origen = arma_tipo_danio if arma_tipo_danio else arma_ta
        self.arma_tipo_danio = normalizar_ta(tipo_danio_origen) if tipo_danio_origen else None
        self.turno_doble_armas = turno_doble_armas
        self.tipo_defensa_preferida = tipo_defensa_preferida if tipo_defensa_preferida in ('Parada', 'Esquiva') else 'Parada'
        self.bonificador = int(bonificador)
        self.penalizador = int(penalizador)
        self.armas = [normalizar_arma(a) for a in (armas or [])]
        if not self.armas and self.arma_nombre:
            self.armas = [normalizar_arma({
                'nombre': self.arma_nombre,
                'turno': self.arma_turno or 0,
                'daño': self.arma_danio or 0,
                'rotura': self.arma_rotura or 0,
                'entereza': self.arma_entereza or 0,
                'tipo_danio': self.arma_tipo_danio or 'FIL',
                'habilidad_ataque': self.habilidad_ataque,
                'habilidad_parada': self.habilidad_defensa,
                'es_escudo': False
            })]
        self.tipo = "Guerrero"
        self.usa_combate_marcial = True
        self.usa_magia = False
        self.usa_mentalismo = False
        self.usa_ki = False
        self.habilidades_secundarias = {}

    @property
    def arma_ta(self):
        """Alias legado de compatibilidad para arma_tipo_danio."""
        return self.arma_tipo_danio

    @arma_ta.setter
    def arma_ta(self, valor):
        self.arma_tipo_danio = normalizar_ta(valor) if valor else None

    def obtener_ta(self, codigo_ta):
        """Obtiene la TA correspondiente al tipo de daño."""
        codigo = normalizar_ta(codigo_ta)
        return self.armaduras_ta.get(codigo, 0)

    def romper_armadura(self):
        """Rompe completamente la armadura (todas las TA a 0)."""
        for codigo in TA_CODIGOS:
            self.armaduras_ta[codigo] = 0
        self.armadura = 0
        self.entereza_armadura = 0
    
    def a_diccionario(self):
        """
        Convierte el personaje a un diccionario para serialización JSON.
        
        Returns:
            dict: Diccionario con todos los atributos del personaje
        """
        return {
            'tipo': self.tipo,
            'nombre': self.nombre,
            'puntos_vida': self.puntos_vida,
            'puntos_cansancio': self.puntos_cansancio,
            'puntos_ki': self.puntos_ki,
            'turno': self.turno,
            'habilidad_ataque': self.habilidad_ataque,
            'habilidad_defensa': self.habilidad_defensa,
            'daño': self.daño,
            'armadura': self.armadura,
            'armaduras_ta': self.armaduras_ta,
            'entereza_armadura': self.entereza_armadura,
            'resistencia_fisica': self.resistencia_fisica,
            'resistencia_enfermedades': self.resistencia_enfermedades,
            'resistencia_venenos': self.resistencia_venenos,
            'resistencia_magica': self.resistencia_magica,
            'resistencia_psiquica': self.resistencia_psiquica,
            'es_pj': self.es_pj,
            'natura': self.natura,
            'arma_nombre': self.arma_nombre,
            'arma_turno': self.arma_turno,
            'arma_danio': self.arma_danio,
            'arma_rotura': self.arma_rotura,
            'arma_entereza': self.arma_entereza,
            'arma_tipo_danio': self.arma_tipo_danio,
            'armas': self.armas,
            'turno_doble_armas': self.turno_doble_armas,
            'tipo_defensa_preferida': self.tipo_defensa_preferida,
            'bonificador': self.bonificador,
            'penalizador': self.penalizador,
            'habilidades_secundarias': normalizar_habilidades_secundarias(getattr(self, 'habilidades_secundarias', {})),
        }
    
    @classmethod
    def desde_diccionario(cls, datos):
        """
        Crea un personaje desde un diccionario.
        
        Args:
            datos (dict): Diccionario con los datos del personaje
            
        Returns:
            Personaje: Nueva instancia del personaje
        """
        personaje = cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos.get('puntos_ki', 0),
            turno=datos['turno'],
            habilidad_ataque=datos['habilidad_ataque'],
            habilidad_defensa=datos['habilidad_defensa'],
            daño=datos.get('daño', 0),
            armadura=datos['armadura'],
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            tipo_defensa_preferida=datos.get('tipo_defensa_preferida', 'Parada'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0)
        )
        personaje.habilidades_secundarias = normalizar_habilidades_secundarias(datos.get('habilidades_secundarias', {}))
        return personaje
    
    def __str__(self):
        """
        Representación en texto del personaje.
        
        Returns:
            str: Descripción formateada del personaje
        """
        lineas = [
            "═══════════════════════════════════════",
            f"  {self.tipo.upper()}: {self.nombre}",
            "═══════════════════════════════════════",
            f"  Puntos de Vida:      {self.puntos_vida}",
            f"  Puntos de Cansancio: {self.puntos_cansancio}",
            f"  Turno:               {self.turno}",
            f"  Control:             {'PJ' if self.es_pj else 'PNJ'}",
            f"  Natura:              {'Sí' if self.natura else 'No'}",
            f"  Arma principal:      {self.arma_nombre if self.arma_nombre else '-'}",
            f"  Arma (T/D/R/E/TD):   {self.arma_turno if self.arma_turno is not None else '-'} / {self.arma_danio if self.arma_danio is not None else '-'} / {self.arma_rotura if self.arma_rotura is not None else '-'} / {self.arma_entereza if self.arma_entereza is not None else '-'} / {self.arma_tipo_danio if self.arma_tipo_danio else '-'}",
            f"  Habilidad de Ataque: {self.habilidad_ataque}",
            f"  Habilidad de Defensa:{self.habilidad_defensa}",
            f"  TA FIL/CON/PEN:      {self.armaduras_ta['FIL']}/{self.armaduras_ta['CON']}/{self.armaduras_ta['PEN']}",
            f"  TA CAL/ELE/FRI/ENE:  {self.armaduras_ta['CAL']}/{self.armaduras_ta['ELE']}/{self.armaduras_ta['FRI']}/{self.armaduras_ta['ENE']}",
            f"  Entereza armadura:   {self.entereza_armadura}",
            f"  RF/RE/RV:            {self.resistencia_fisica}/{self.resistencia_enfermedades}/{self.resistencia_venenos}",
            f"  RM/RP:               {self.resistencia_magica}/{self.resistencia_psiquica}",
            "═══════════════════════════════════════"
        ]
        if self.armas:
            lineas.append("  Armas registradas:")
            for arma in self.armas:
                escudo = " [Escudo]" if arma.get('es_escudo') else ""
                lineas.append(
                    f"    - {arma['nombre']}{escudo}: T{arma['turno']} D{arma['daño']} R{arma['rotura']} E{arma['entereza']} TD:{arma['tipo_danio']} ATQ:{arma['habilidad_ataque']} PAR:{arma['habilidad_parada']}"
                )
            if self.turno_doble_armas is not None:
                lineas.append(f"  Turno con dos armas: {self.turno_doble_armas}")
        return '\n'.join(lineas)


class Domine(Personaje):
    """Arquetipo marcial equivalente al guerrero, pero con Ki y Daño propios."""

    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki,
                 turno, habilidad_ataque, habilidad_defensa, daño, armadura,
                 resistencia_fisica, resistencia_enfermedades,
                 resistencia_venenos, resistencia_magica, resistencia_psiquica,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 tipo_defensa_preferida='Parada', bonificador=0, penalizador=0,
                 natura=None):
        super().__init__(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=daño,
            armadura=armadura,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            arma_ta=arma_ta,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
            tipo_defensa_preferida=tipo_defensa_preferida,
            bonificador=bonificador,
            penalizador=penalizador,
            natura=natura,
        )
        self.tipo = "Domine"
        self.usa_ki = True

    @classmethod
    def desde_diccionario(cls, datos):
        return cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos.get('puntos_ki', 0),
            turno=datos['turno'],
            habilidad_ataque=datos.get('habilidad_ataque', 0),
            habilidad_defensa=datos.get('habilidad_defensa', 0),
            daño=datos.get('daño', 0),
            armadura=datos['armadura'],
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            tipo_defensa_preferida=datos.get('tipo_defensa_preferida', 'Parada'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0),
        )

    def __str__(self):
        base = super().__str__().split('\n')
        insercion = [
            f"  Puntos de Ki:        {self.puntos_ki}",
            f"  Daño:                {self.daño}",
        ]
        base = base[:6] + insercion + base[6:]
        return '\n'.join(base)


class Mago(Personaje):
    """
    Clase para representar un mago en Ánima: Beyond Fantasy.
    
    Los magos tienen zeón y proyección mágica que sustituye a las
    habilidades de ataque y defensa normales.
    
    Atributos adicionales:
        zeon (int): Puntos de zeón (energía mágica)
        proyeccion_magica (int): Proyección mágica (sustituye ataque/defensa)
    """
    
    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki,
                 turno, daño, armadura, zeon, proyeccion_magica,
                 resistencia_fisica, resistencia_enfermedades,
                 resistencia_venenos, resistencia_magica, resistencia_psiquica,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 bonificador=0, penalizador=0, natura=None):
        """
        Inicializa un mago.
        
        Args:
            nombre (str): Nombre del mago
            puntos_vida (int): Puntos de vida
            puntos_cansancio (int): Puntos de cansancio
            puntos_ki (int): Puntos de ki
            turno (int): Valor de turno
            daño (int): Daño base
            armadura (int): Valor de armadura
            zeon (int): Puntos de zeón
            proyeccion_magica (int): Valor de proyección mágica
        """
        # Los magos no usan habilidad_ataque/defensa normales
        super().__init__(nombre, puntos_vida, puntos_cansancio, puntos_ki,
                turno, 0, 0, daño, armadura,
                resistencia_fisica, resistencia_enfermedades,
            resistencia_venenos, resistencia_magica, resistencia_psiquica,
            es_pj=es_pj,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            arma_ta=arma_ta,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
            bonificador=bonificador,
            penalizador=penalizador,
            natura=natura)
        self.zeon = zeon
        self.proyeccion_magica = proyeccion_magica
        self.tipo = "Mago"
        self.usa_combate_marcial = False
        self.usa_magia = True
    
    def a_diccionario(self):
        """
        Convierte el mago a un diccionario para serialización JSON.
        
        Returns:
            dict: Diccionario con todos los atributos del mago
        """
        datos = super().a_diccionario()
        datos['zeon'] = self.zeon
        datos['proyeccion_magica'] = self.proyeccion_magica
        return datos
    
    @classmethod
    def desde_diccionario(cls, datos):
        """
        Crea un mago desde un diccionario.
        
        Args:
            datos (dict): Diccionario con los datos del mago
            
        Returns:
            Mago: Nueva instancia del mago
        """
        return cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos['puntos_ki'],
            turno=datos['turno'],
            daño=datos['daño'],
            armadura=datos['armadura'],
            zeon=datos['zeon'],
            proyeccion_magica=datos['proyeccion_magica'],
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0)
        )
    
    def __str__(self):
        """
        Representación en texto del mago.
        
        Returns:
            str: Descripción formateada del mago
        """
        lineas = [
            "═══════════════════════════════════════",
            f"  {self.tipo.upper()}: {self.nombre}",
            "═══════════════════════════════════════",
            f"  Puntos de Vida:      {self.puntos_vida}",
            f"  Puntos de Cansancio: {self.puntos_cansancio}",
            f"  Zeón:                {self.zeon}",
            f"  Turno:               {self.turno}",
            f"  Control:             {'PJ' if self.es_pj else 'PNJ'}",
            f"  Natura:              {'Sí' if self.natura else 'No'}",
            f"  Arma principal:      {self.arma_nombre if self.arma_nombre else '-'}",
            f"  Arma (T/D/R/E/TD):   {self.arma_turno if self.arma_turno is not None else '-'} / {self.arma_danio if self.arma_danio is not None else '-'} / {self.arma_rotura if self.arma_rotura is not None else '-'} / {self.arma_entereza if self.arma_entereza is not None else '-'} / {self.arma_tipo_danio if self.arma_tipo_danio else '-'}",
            f"  Proyección Mágica:   {self.proyeccion_magica}",
            f"  Daño:                {self.daño}",
            f"  TA FIL/CON/PEN:      {self.armaduras_ta['FIL']}/{self.armaduras_ta['CON']}/{self.armaduras_ta['PEN']}",
            f"  TA CAL/ELE/FRI/ENE:  {self.armaduras_ta['CAL']}/{self.armaduras_ta['ELE']}/{self.armaduras_ta['FRI']}/{self.armaduras_ta['ENE']}",
            f"  Entereza armadura:   {self.entereza_armadura}",
            f"  RF/RE/RV:            {self.resistencia_fisica}/{self.resistencia_enfermedades}/{self.resistencia_venenos}",
            f"  RM/RP:               {self.resistencia_magica}/{self.resistencia_psiquica}",
            "═══════════════════════════════════════"
        ]
        return '\n'.join(lineas)


class Mentalista(Personaje):
    """
    Clase para representar un mentalista en Ánima: Beyond Fantasy.
    
    Los mentalistas tienen potencial psíquico, proyección psíquica y CV libres.
    La proyección psíquica sustituye a las habilidades de ataque y defensa.
    
    Atributos adicionales:
        potencial_psiquico (int): Potencial psíquico del mentalista
        proyeccion_psiquica (int): Proyección psíquica (sustituye ataque/defensa)
        cv_libres (int): Capacidad de control variable libre
    """
    
    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki,
                 turno, daño, armadura, potencial_psiquico, 
                 proyeccion_psiquica, cv_libres,
                 resistencia_fisica, resistencia_enfermedades,
                 resistencia_venenos, resistencia_magica, resistencia_psiquica,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 bonificador=0, penalizador=0, natura=None):
        """
        Inicializa un mentalista.
        
        Args:
            nombre (str): Nombre del mentalista
            puntos_vida (int): Puntos de vida
            puntos_cansancio (int): Puntos de cansancio
            puntos_ki (int): Puntos de ki
            turno (int): Valor de turno
            daño (int): Daño base
            armadura (int): Valor de armadura
            potencial_psiquico (int): Potencial psíquico
            proyeccion_psiquica (int): Proyección psíquica
            cv_libres (int): CV libres
        """
        # Los mentalistas no usan habilidad_ataque/defensa normales
        super().__init__(nombre, puntos_vida, puntos_cansancio, puntos_ki,
                turno, 0, 0, daño, armadura,
                resistencia_fisica, resistencia_enfermedades,
            resistencia_venenos, resistencia_magica, resistencia_psiquica,
            es_pj=es_pj,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            arma_ta=arma_ta,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
            bonificador=bonificador,
            penalizador=penalizador,
            natura=natura)
        self.potencial_psiquico = potencial_psiquico
        self.proyeccion_psiquica = proyeccion_psiquica
        self.cv_libres = cv_libres
        self.tipo = "Mentalista"
        self.usa_combate_marcial = False
        self.usa_mentalismo = True
    
    def a_diccionario(self):
        """
        Convierte el mentalista a un diccionario para serialización JSON.
        
        Returns:
            dict: Diccionario con todos los atributos del mentalista
        """
        datos = super().a_diccionario()
        datos['potencial_psiquico'] = self.potencial_psiquico
        datos['proyeccion_psiquica'] = self.proyeccion_psiquica
        datos['cv_libres'] = self.cv_libres
        return datos
    
    @classmethod
    def desde_diccionario(cls, datos):
        """
        Crea un mentalista desde un diccionario.
        
        Args:
            datos (dict): Diccionario con los datos del mentalista
            
        Returns:
            Mentalista: Nueva instancia del mentalista
        """
        return cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos['puntos_ki'],
            turno=datos['turno'],
            daño=datos['daño'],
            armadura=datos['armadura'],
            potencial_psiquico=datos['potencial_psiquico'],
            proyeccion_psiquica=datos['proyeccion_psiquica'],
            cv_libres=datos['cv_libres'],
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0)
        )
    
    def __str__(self):
        """
        Representación en texto del mentalista.
        
        Returns:
            str: Descripción formateada del mentalista
        """
        lineas = [
            "═══════════════════════════════════════",
            f"  {self.tipo.upper()}: {self.nombre}",
            "═══════════════════════════════════════",
            f"  Puntos de Vida:      {self.puntos_vida}",
            f"  Puntos de Cansancio: {self.puntos_cansancio}",
            f"  Turno:               {self.turno}",
            f"  Control:             {'PJ' if self.es_pj else 'PNJ'}",
            f"  Natura:              {'Sí' if self.natura else 'No'}",
            f"  Arma principal:      {self.arma_nombre if self.arma_nombre else '-'}",
            f"  Arma (T/D/R/E/TD):   {self.arma_turno if self.arma_turno is not None else '-'} / {self.arma_danio if self.arma_danio is not None else '-'} / {self.arma_rotura if self.arma_rotura is not None else '-'} / {self.arma_entereza if self.arma_entereza is not None else '-'} / {self.arma_tipo_danio if self.arma_tipo_danio else '-'}",
            f"  Potencial Psíquico:  {self.potencial_psiquico}",
            f"  Proyección Psíquica: {self.proyeccion_psiquica}",
            f"  CV Libres:           {self.cv_libres}",
            f"  Daño:                {self.daño}",
            f"  TA FIL/CON/PEN:      {self.armaduras_ta['FIL']}/{self.armaduras_ta['CON']}/{self.armaduras_ta['PEN']}",
            f"  TA CAL/ELE/FRI/ENE:  {self.armaduras_ta['CAL']}/{self.armaduras_ta['ELE']}/{self.armaduras_ta['FRI']}/{self.armaduras_ta['ENE']}",
            f"  Entereza armadura:   {self.entereza_armadura}",
            f"  RF/RE/RV:            {self.resistencia_fisica}/{self.resistencia_enfermedades}/{self.resistencia_venenos}",
            f"  RM/RP:               {self.resistencia_magica}/{self.resistencia_psiquica}",
            "═══════════════════════════════════════"
        ]
        return '\n'.join(lineas)


class Warlock(Domine):
    """Arquetipo mixto: Guerrero + Mago (incluye Ki)."""

    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki,
                 turno, habilidad_ataque, habilidad_defensa, daño, armadura,
                 zeon, proyeccion_magica,
                 resistencia_fisica, resistencia_enfermedades,
                 resistencia_venenos, resistencia_magica, resistencia_psiquica,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 tipo_defensa_preferida='Parada', bonificador=0, penalizador=0,
                 natura=None):
        super().__init__(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=daño,
            armadura=armadura,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            arma_ta=arma_ta,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
            tipo_defensa_preferida=tipo_defensa_preferida,
            bonificador=bonificador,
            penalizador=penalizador,
            natura=natura,
        )
        self.zeon = zeon
        self.proyeccion_magica = proyeccion_magica
        self.tipo = "Warlock"
        self.usa_magia = True

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos['zeon'] = self.zeon
        datos['proyeccion_magica'] = self.proyeccion_magica
        return datos

    @classmethod
    def desde_diccionario(cls, datos):
        return cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos.get('puntos_ki', 0),
            turno=datos['turno'],
            habilidad_ataque=datos.get('habilidad_ataque', 0),
            habilidad_defensa=datos.get('habilidad_defensa', 0),
            daño=datos.get('daño', 0),
            armadura=datos['armadura'],
            zeon=datos.get('zeon', 0),
            proyeccion_magica=datos.get('proyeccion_magica', 0),
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            tipo_defensa_preferida=datos.get('tipo_defensa_preferida', 'Parada'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0),
        )

    def __str__(self):
        base = super().__str__().split('\n')
        insercion = [
            f"  Zeón:                {self.zeon}",
            f"  Proyección Mágica:   {self.proyeccion_magica}",
        ]
        base = base[:8] + insercion + base[8:]
        return '\n'.join(base)


class HechiceroMentalista(Mago):
    """Arquetipo mixto: Mago + Mentalista (incluye Ki)."""

    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki,
                 turno, daño, armadura, zeon, proyeccion_magica,
                 potencial_psiquico, proyeccion_psiquica, cv_libres,
                 resistencia_fisica, resistencia_enfermedades,
                 resistencia_venenos, resistencia_magica, resistencia_psiquica,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 bonificador=0, penalizador=0, natura=None):
        super().__init__(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            daño=daño,
            armadura=armadura,
            zeon=zeon,
            proyeccion_magica=proyeccion_magica,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            arma_ta=arma_ta,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
            bonificador=bonificador,
            penalizador=penalizador,
            natura=natura,
        )
        self.potencial_psiquico = potencial_psiquico
        self.proyeccion_psiquica = proyeccion_psiquica
        self.cv_libres = cv_libres
        self.tipo = "Hechicero mentalista"
        self.usa_mentalismo = True
        self.usa_ki = True

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos['potencial_psiquico'] = self.potencial_psiquico
        datos['proyeccion_psiquica'] = self.proyeccion_psiquica
        datos['cv_libres'] = self.cv_libres
        return datos

    @classmethod
    def desde_diccionario(cls, datos):
        return cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos.get('puntos_ki', 0),
            turno=datos['turno'],
            daño=datos.get('daño', 0),
            armadura=datos['armadura'],
            zeon=datos.get('zeon', 0),
            proyeccion_magica=datos.get('proyeccion_magica', 0),
            potencial_psiquico=datos.get('potencial_psiquico', 0),
            proyeccion_psiquica=datos.get('proyeccion_psiquica', 0),
            cv_libres=datos.get('cv_libres', 0),
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0),
        )

    def __str__(self):
        base = super().__str__().split('\n')
        insercion = [
            f"  Puntos de Ki:        {self.puntos_ki}",
            f"  Potencial Psíquico:  {self.potencial_psiquico}",
            f"  Proyección Psíquica: {self.proyeccion_psiquica}",
            f"  CV Libres:           {self.cv_libres}",
        ]
        base = base[:7] + insercion + base[7:]
        return '\n'.join(base)


class GuerreroMentalista(Domine):
    """Arquetipo mixto: Guerrero + Mentalista (incluye Ki)."""

    def __init__(self, nombre, puntos_vida, puntos_cansancio, puntos_ki,
                 turno, habilidad_ataque, habilidad_defensa, daño, armadura,
                 potencial_psiquico, proyeccion_psiquica, cv_libres,
                 resistencia_fisica, resistencia_enfermedades,
                 resistencia_venenos, resistencia_magica, resistencia_psiquica,
                 es_pj=False, arma_nombre=None, arma_turno=None,
                 arma_danio=None, arma_rotura=None, arma_entereza=None,
                 arma_tipo_danio=None, arma_ta=None, armaduras_ta=None,
                 entereza_armadura=0, armas=None, turno_doble_armas=None,
                 tipo_defensa_preferida='Parada', bonificador=0, penalizador=0,
                 natura=None):
        super().__init__(
            nombre=nombre,
            puntos_vida=puntos_vida,
            puntos_cansancio=puntos_cansancio,
            puntos_ki=puntos_ki,
            turno=turno,
            habilidad_ataque=habilidad_ataque,
            habilidad_defensa=habilidad_defensa,
            daño=daño,
            armadura=armadura,
            resistencia_fisica=resistencia_fisica,
            resistencia_enfermedades=resistencia_enfermedades,
            resistencia_venenos=resistencia_venenos,
            resistencia_magica=resistencia_magica,
            resistencia_psiquica=resistencia_psiquica,
            es_pj=es_pj,
            arma_nombre=arma_nombre,
            arma_turno=arma_turno,
            arma_danio=arma_danio,
            arma_rotura=arma_rotura,
            arma_entereza=arma_entereza,
            arma_tipo_danio=arma_tipo_danio,
            arma_ta=arma_ta,
            armaduras_ta=armaduras_ta,
            entereza_armadura=entereza_armadura,
            armas=armas,
            turno_doble_armas=turno_doble_armas,
            tipo_defensa_preferida=tipo_defensa_preferida,
            bonificador=bonificador,
            penalizador=penalizador,
            natura=natura,
        )
        self.potencial_psiquico = potencial_psiquico
        self.proyeccion_psiquica = proyeccion_psiquica
        self.cv_libres = cv_libres
        self.tipo = "Guerrero mentalista"
        self.usa_mentalismo = True

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos['potencial_psiquico'] = self.potencial_psiquico
        datos['proyeccion_psiquica'] = self.proyeccion_psiquica
        datos['cv_libres'] = self.cv_libres
        return datos

    @classmethod
    def desde_diccionario(cls, datos):
        return cls(
            nombre=datos['nombre'],
            puntos_vida=datos['puntos_vida'],
            puntos_cansancio=datos['puntos_cansancio'],
            puntos_ki=datos.get('puntos_ki', 0),
            turno=datos['turno'],
            habilidad_ataque=datos.get('habilidad_ataque', 0),
            habilidad_defensa=datos.get('habilidad_defensa', 0),
            daño=datos.get('daño', 0),
            armadura=datos['armadura'],
            potencial_psiquico=datos.get('potencial_psiquico', 0),
            proyeccion_psiquica=datos.get('proyeccion_psiquica', 0),
            cv_libres=datos.get('cv_libres', 0),
            resistencia_fisica=datos.get('resistencia_fisica', 0),
            resistencia_enfermedades=datos.get('resistencia_enfermedades', 0),
            resistencia_venenos=datos.get('resistencia_venenos', 0),
            resistencia_magica=datos.get('resistencia_magica', 0),
            resistencia_psiquica=datos.get('resistencia_psiquica', 0),
            es_pj=datos.get('es_pj', False),
            natura=datos.get('natura'),
            arma_nombre=datos.get('arma_nombre'),
            arma_turno=datos.get('arma_turno'),
            arma_danio=datos.get('arma_danio'),
            arma_rotura=datos.get('arma_rotura'),
            arma_entereza=datos.get('arma_entereza'),
            arma_tipo_danio=datos.get('arma_tipo_danio'),
            arma_ta=datos.get('arma_ta'),
            armaduras_ta=datos.get('armaduras_ta'),
            entereza_armadura=datos.get('entereza_armadura', 0),
            armas=datos.get('armas'),
            turno_doble_armas=datos.get('turno_doble_armas'),
            tipo_defensa_preferida=datos.get('tipo_defensa_preferida', 'Parada'),
            bonificador=datos.get('bonificador', 0),
            penalizador=datos.get('penalizador', 0),
        )

    def __str__(self):
        base = super().__str__().split('\n')
        insercion = [
            f"  Potencial Psíquico:  {self.potencial_psiquico}",
            f"  Proyección Psíquica: {self.proyeccion_psiquica}",
            f"  CV Libres:           {self.cv_libres}",
        ]
        base = base[:8] + insercion + base[8:]
        return '\n'.join(base)
