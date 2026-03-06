from combate.acciones import resolver_ataque
from combate.iniciativa import PersonajeCombate
from modelos.personaje import Personaje


def _arma(nombre, turno=100, danio=50, rotura=3, entereza=10, ta="FIL", ataque=80, parada=80, escudo=False):
    return {
        "nombre": nombre,
        "turno": turno,
        "daño": danio,
        "rotura": rotura,
        "entereza": entereza,
        "tipo_danio": ta,
        "habilidad_ataque": ataque,
        "habilidad_parada": parada,
        "es_escudo": escudo,
    }


def _guerrero(nombre, pv=120, cansancio=5, ataque=80, defensa=80, armas=None, entereza_armadura=0, ta_fil=2):
    armaduras_ta = {"FIL": ta_fil, "CON": ta_fil, "PEN": ta_fil, "CAL": ta_fil, "ELE": ta_fil, "FRI": ta_fil, "ENE": ta_fil}
    return Personaje(
        nombre=nombre,
        puntos_vida=pv,
        puntos_cansancio=cansancio,
        turno=100,
        habilidad_ataque=ataque,
        habilidad_defensa=defensa,
        daño=0,
        armadura=ta_fil,
        resistencia_fisica=40,
        resistencia_enfermedades=30,
        resistencia_venenos=30,
        resistencia_magica=20,
        resistencia_psiquica=20,
        armaduras_ta=armaduras_ta,
        entereza_armadura=entereza_armadura,
        armas=armas or [],
    )


def test_choque_armas_se_resuelve_aunque_defensa_supere(monkeypatch):
    atacante = _guerrero("A", armas=[_arma("Espada", rotura=2, entereza=10)])
    defensor = _guerrero("D", armas=[_arma("Lanza", rotura=2, entereza=10)])
    pa = PersonajeCombate(atacante)
    pd = PersonajeCombate(defensor)
    pa.configurar_arma_ataque(atacante.armas[0])
    pd.configurar_arma_parada(defensor.armas[0])

    secuencia = iter([3, 4])
    monkeypatch.setattr("combate.acciones.tirar_d10", lambda: next(secuencia))

    resultado = resolver_ataque(
        pa,
        pd,
        resultado_ataque={"tipo": "normal", "resultado_total": 80, "valor_base": 80, "modificador": 0, "bono_cansancio": 0, "tiradas": [0], "resultado_dados": 0},
        resultado_defensa={"tipo": "normal", "resultado_total": 120, "valor_base": 80, "modificador": 0, "bono_cansancio": 0, "tiradas": [40], "resultado_dados": 40},
        tipo_defensa="Parada",
        ta_ataque="FIL",
    )

    assert resultado["contraataque"] is True
    assert resultado["choque_armas"] is not None


def test_rotura_armadura_solo_si_hay_impacto(monkeypatch):
    atacante = _guerrero("A", armas=[_arma("Martillo", rotura=4, entereza=12, ta="PEN")])
    defensor = _guerrero("D", armas=[_arma("Escudo", rotura=1, entereza=15, escudo=True)], entereza_armadura=18, ta_fil=5)
    pa = PersonajeCombate(atacante)
    pd = PersonajeCombate(defensor)
    pa.configurar_arma_ataque(atacante.armas[0])
    pd.configurar_arma_parada(defensor.armas[0])

    secuencia = iter([2, 2])
    monkeypatch.setattr("combate.acciones.tirar_d10", lambda: next(secuencia))

    resultado = resolver_ataque(
        pa,
        pd,
        resultado_ataque={"tipo": "normal", "resultado_total": 70, "valor_base": 80, "modificador": 0, "bono_cansancio": 0, "tiradas": [0], "resultado_dados": 0},
        resultado_defensa={"tipo": "normal", "resultado_total": 130, "valor_base": 80, "modificador": 0, "bono_cansancio": 0, "tiradas": [50], "resultado_dados": 50},
        tipo_defensa="Parada",
        ta_ataque="PEN",
    )

    assert resultado["impacto"] is False
    assert resultado["rotura_armadura"] is None


def test_cambio_arma_reinicia_estado_rotura_local():
    atacante = _guerrero("A", armas=[_arma("Arma1"), _arma("Arma2")])
    pc = PersonajeCombate(atacante)

    pc.registrar_arma_rota(atacante.armas[0])
    pc.configurar_arma_ataque(atacante.armas[0])
    assert pc.arma_rota is True

    pc.configurar_arma_ataque(atacante.armas[1])
    assert pc.arma_rota is False

    pc.configurar_arma_ataque(None)
    assert pc.arma_rota is False
    assert pc.rotura_arma is None


def test_resolver_ataque_devuelve_diccionario_compatible():
    atacante = _guerrero("A", armas=[_arma("Espada", ta="FIL")])
    defensor = _guerrero("D", armas=[_arma("Daga")])
    pa = PersonajeCombate(atacante)
    pd = PersonajeCombate(defensor)
    pa.configurar_arma_ataque(atacante.armas[0])

    resultado = resolver_ataque(
        pa,
        pd,
        resultado_ataque={"tipo": "normal", "resultado_total": 120, "valor_base": 80, "modificador": 0, "bono_cansancio": 0, "tiradas": [40], "resultado_dados": 40},
        resultado_defensa={"tipo": "normal", "resultado_total": 60, "valor_base": 80, "modificador": -20, "bono_cansancio": 0, "tiradas": [0], "resultado_dados": 0},
        tipo_defensa="Esquiva",
        daño_arma=50,
        ta_ataque="FIL",
    )

    assert isinstance(resultado, dict)
    for clave in ("impacto", "contraataque", "ataque", "defensa", "ta_ataque", "tipo_defensa"):
        assert clave in resultado


def test_pnj_sin_natura_no_obtiene_tirada_abierta_automatica(monkeypatch):
    atacante = _guerrero("A", ataque=50, armas=[_arma("Espada", ta="FIL")])
    defensor = _guerrero("D", defensa=0, armas=[])
    atacante.es_pj = False
    atacante.natura = False
    defensor.es_pj = False
    defensor.natura = True

    pa = PersonajeCombate(atacante)
    pd = PersonajeCombate(defensor)
    pa.configurar_arma_ataque(atacante.armas[0])

    secuencia = iter([95, 10])
    monkeypatch.setattr("combate.dados.tirar_dado", lambda: next(secuencia))

    resultado = resolver_ataque(pa, pd, tipo_defensa="Esquiva", daño_arma=50, ta_ataque="FIL")

    assert resultado["ataque"]["tipo"] == "normal"
    assert resultado["ataque"]["tiradas"] == [95]
    assert resultado["ataque"]["resultado_dados"] == 95


def test_iniciativa_pnj_sin_natura_no_abre(monkeypatch):
    personaje = _guerrero("PNJ", armas=[])
    personaje.es_pj = False
    personaje.natura = False
    pc = PersonajeCombate(personaje)

    monkeypatch.setattr("combate.dados.tirar_dado", lambda: 95)
    iniciativa = pc.calcular_iniciativa()

    assert iniciativa == personaje.turno + 95
    assert "ABIERTA" not in pc.desglose_iniciativa
