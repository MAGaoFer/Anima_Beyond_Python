from combate.iniciativa import PersonajeCombate
from combate.servicio_ataque import preparar_y_resolver_ataque
from modelos.personaje import Personaje


def _arma(nombre, turno=100, danio=45, rotura=2, entereza=10, ta="FIL", ataque=80, parada=80):
    return {
        "nombre": nombre,
        "turno": turno,
        "daño": danio,
        "rotura": rotura,
        "entereza": entereza,
        "tipo_danio": ta,
        "habilidad_ataque": ataque,
        "habilidad_parada": parada,
        "es_escudo": False,
    }


def _guerrero(nombre, armas):
    ta = {"FIL": 2, "CON": 2, "PEN": 2, "CAL": 2, "ELE": 2, "FRI": 2, "ENE": 2}
    return Personaje(
        nombre=nombre,
        puntos_vida=120,
        puntos_cansancio=5,
        turno=100,
        habilidad_ataque=80,
        habilidad_defensa=80,
        daño=0,
        armadura=2,
        armaduras_ta=ta,
        armas=armas,
    )


def test_preparar_y_resolver_ataque_devuelve_contexto_con_mod_sorpresa():
    atacante = _guerrero("A", [_arma("Espada", ataque=95)])
    defensor = _guerrero("D", [_arma("Hacha", parada=90)])

    pa = PersonajeCombate(atacante)
    pd = PersonajeCombate(defensor)

    datos = {
        "arma_ataque": "Arma 1: Espada",
        "arma_parada": "Arma 1: Hacha",
        "tipo_defensa": "Parada",
        "daño": 45,
        "ta": "FIL",
        "mod_ataque": 0,
        "mod_defensa": 0,
        "cansancio_ataque": 0,
        "cansancio_defensa": 0,
        "tirada_ataque": 60,
        "tirada_defensa": 20,
    }

    contexto = preparar_y_resolver_ataque(
        pa,
        pd,
        datos,
        proveedor_modificador_sorpresa=lambda _a, _d: -90,
    )

    assert contexto.tipo_defensa == "Parada"
    assert contexto.mod_sorpresa_defensa == -90
    assert isinstance(contexto.resultado, dict)
    assert "impacto" in contexto.resultado


def test_preparar_y_resolver_con_tiradas_precalculadas_y_arma_actual():
    atacante = _guerrero("A", [_arma("Espada", ataque=95, danio=60, ta="PEN")])
    defensor = _guerrero("D", [_arma("Hacha", parada=90)])

    pa = PersonajeCombate(atacante)
    pd = PersonajeCombate(defensor)
    pa.configurar_arma_ataque(atacante.armas[0])
    pd.configurar_arma_parada(defensor.armas[0])

    datos = {
        "daño": 10,
        "ta": "FIL",
        "mod_ataque": 0,
        "mod_defensa": 0,
        "cansancio_ataque": 0,
        "cansancio_defensa": 0,
        "tipo_defensa": "Parada",
        "resultado_ataque_precalculado": {
            "tipo": "normal",
            "resultado_total": 170,
            "valor_base": 95,
            "modificador": 0,
            "bono_cansancio": 0,
            "tiradas": [75],
            "resultado_dados": 75,
        },
        "resultado_defensa_precalculado": {
            "tipo": "normal",
            "resultado_total": 80,
            "valor_base": 90,
            "modificador": -10,
            "bono_cansancio": 0,
            "tiradas": [0],
            "resultado_dados": 0,
        },
        "usar_estado_arma_actual": True,
    }

    contexto = preparar_y_resolver_ataque(pa, pd, datos)

    assert contexto.ta_ataque == "PEN"
    assert contexto.resultado["ta_ataque"] == "PEN"
