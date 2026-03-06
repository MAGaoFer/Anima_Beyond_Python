import json

from almacenamiento.almacenamiento_json import AlmacenamientoPersonajes
from modelos.personaje import (
    Domine,
    GuerreroMentalista,
    HechiceroMentalista,
    Mago,
    Mentalista,
    Personaje,
    Warlock,
)


def _base_ta(valor=2):
    return {"FIL": valor, "CON": valor, "PEN": valor, "CAL": valor, "ELE": valor, "FRI": valor, "ENE": valor}


def test_guardar_y_cargar_domine_en_directorio_temporal(tmp_path):
    almacenamiento = AlmacenamientoPersonajes(tmp_path / "personajes.json")

    domine = Domine(
        nombre="Xan",
        puntos_vida=140,
        puntos_cansancio=6,
        puntos_ki=30,
        turno=110,
        habilidad_ataque=120,
        habilidad_defensa=115,
        daño=65,
        armadura=3,
        resistencia_fisica=40,
        resistencia_enfermedades=35,
        resistencia_venenos=30,
        resistencia_magica=25,
        resistencia_psiquica=20,
        armaduras_ta=_base_ta(3),
    )

    assert almacenamiento.guardar_personaje(domine) is True
    cargado = almacenamiento.cargar_personaje("Xan")

    assert isinstance(cargado, Domine)
    assert cargado.puntos_ki == 30
    assert cargado.daño == 65


def test_migracion_desde_legacy_json(tmp_path):
    ruta_legacy = tmp_path / "personajes.json"
    datos_legacy = {
        "Veterano": {
            "tipo": "Guerrero",
            "puntos_vida": 100,
            "puntos_cansancio": 5,
            "turno": 90,
            "habilidad_ataque": 80,
            "habilidad_defensa": 75,
            "armadura": 2,
            "armaduras_ta": _base_ta(2),
            "resistencia_fisica": 30,
            "resistencia_enfermedades": 20,
            "resistencia_venenos": 20,
            "resistencia_magica": 15,
            "resistencia_psiquica": 15,
            "es_pj": False,
        }
    }
    ruta_legacy.write_text(json.dumps(datos_legacy, ensure_ascii=False, indent=2), encoding="utf-8")

    almacenamiento = AlmacenamientoPersonajes(ruta_legacy)
    personaje = almacenamiento.cargar_personaje("Veterano")

    assert isinstance(personaje, Personaje)
    assert personaje.nombre == "Veterano"
    assert personaje.puntos_ki == 0
    assert personaje.daño == 0
    assert personaje.natura is True


def test_cargar_todos_personajes_tipos_mixtos(tmp_path):
    almacenamiento = AlmacenamientoPersonajes(tmp_path / "personajes.json")

    guerrero = Personaje(
        nombre="G1",
        puntos_vida=100,
        puntos_cansancio=5,
        turno=90,
        habilidad_ataque=70,
        habilidad_defensa=65,
        daño=0,
        armadura=2,
        armaduras_ta=_base_ta(2),
    )
    mago = Mago(
        nombre="M1",
        puntos_vida=80,
        puntos_cansancio=4,
        puntos_ki=0,
        turno=70,
        daño=45,
        armadura=1,
        zeon=120,
        proyeccion_magica=95,
        armaduras_ta=_base_ta(1),
        resistencia_fisica=20,
        resistencia_enfermedades=20,
        resistencia_venenos=20,
        resistencia_magica=40,
        resistencia_psiquica=25,
    )
    mentalista = Mentalista(
        nombre="Psi1",
        puntos_vida=85,
        puntos_cansancio=4,
        puntos_ki=0,
        turno=75,
        daño=40,
        armadura=1,
        potencial_psiquico=90,
        proyeccion_psiquica=88,
        cv_libres=12,
        armaduras_ta=_base_ta(1),
        resistencia_fisica=20,
        resistencia_enfermedades=20,
        resistencia_venenos=20,
        resistencia_magica=20,
        resistencia_psiquica=35,
    )

    assert almacenamiento.guardar_personaje(guerrero)
    assert almacenamiento.guardar_personaje(mago)
    assert almacenamiento.guardar_personaje(mentalista)

    tipos = {type(p).__name__ for p in almacenamiento.cargar_todos_personajes()}
    assert "Personaje" in tipos
    assert "Mago" in tipos
    assert "Mentalista" in tipos


def test_guardado_reemplaza_espacios_por_guion_bajo_en_nombre_archivo(tmp_path):
    almacenamiento = AlmacenamientoPersonajes(tmp_path / "personajes.json")
    personaje = Personaje(
        nombre="Alphonse de Lorme",
        puntos_vida=100,
        puntos_cansancio=5,
        turno=90,
        habilidad_ataque=80,
        habilidad_defensa=75,
        daño=0,
        armadura=2,
        armaduras_ta=_base_ta(2),
    )

    assert almacenamiento.guardar_personaje(personaje) is True
    assert (almacenamiento.ruta_personajes / "Alphonse_de_Lorme.json").exists()


def test_guardar_y_cargar_arquetipos_mixtos(tmp_path):
    almacenamiento = AlmacenamientoPersonajes(tmp_path / "personajes.json")

    warlock = Warlock(
        nombre="W",
        puntos_vida=110,
        puntos_cansancio=6,
        puntos_ki=20,
        turno=95,
        habilidad_ataque=90,
        habilidad_defensa=85,
        daño=55,
        armadura=2,
        zeon=120,
        proyeccion_magica=100,
        resistencia_fisica=30,
        resistencia_enfermedades=25,
        resistencia_venenos=25,
        resistencia_magica=35,
        resistencia_psiquica=30,
        armaduras_ta=_base_ta(2),
    )
    hechicero = HechiceroMentalista(
        nombre="HM",
        puntos_vida=90,
        puntos_cansancio=5,
        puntos_ki=15,
        turno=80,
        daño=45,
        armadura=1,
        zeon=140,
        proyeccion_magica=105,
        potencial_psiquico=95,
        proyeccion_psiquica=92,
        cv_libres=14,
        resistencia_fisica=22,
        resistencia_enfermedades=22,
        resistencia_venenos=22,
        resistencia_magica=40,
        resistencia_psiquica=40,
        armaduras_ta=_base_ta(1),
    )
    guerrero_mentalista = GuerreroMentalista(
        nombre="GM",
        puntos_vida=120,
        puntos_cansancio=6,
        puntos_ki=18,
        turno=100,
        habilidad_ataque=95,
        habilidad_defensa=90,
        daño=60,
        armadura=2,
        potencial_psiquico=88,
        proyeccion_psiquica=91,
        cv_libres=10,
        resistencia_fisica=34,
        resistencia_enfermedades=28,
        resistencia_venenos=28,
        resistencia_magica=26,
        resistencia_psiquica=36,
        armaduras_ta=_base_ta(2),
    )

    assert almacenamiento.guardar_personaje(warlock)
    assert almacenamiento.guardar_personaje(hechicero)
    assert almacenamiento.guardar_personaje(guerrero_mentalista)

    assert isinstance(almacenamiento.cargar_personaje("W"), Warlock)
    assert isinstance(almacenamiento.cargar_personaje("HM"), HechiceroMentalista)
    assert isinstance(almacenamiento.cargar_personaje("GM"), GuerreroMentalista)


def test_guardar_y_cargar_natura_pnj(tmp_path):
    almacenamiento = AlmacenamientoPersonajes(tmp_path / "personajes.json")
    personaje = Personaje(
        nombre="SinNatura",
        puntos_vida=90,
        puntos_cansancio=5,
        turno=80,
        habilidad_ataque=60,
        habilidad_defensa=55,
        daño=0,
        armadura=2,
        armaduras_ta=_base_ta(2),
        es_pj=False,
        natura=False,
    )

    assert almacenamiento.guardar_personaje(personaje) is True
    cargado = almacenamiento.cargar_personaje("SinNatura")

    assert isinstance(cargado, Personaje)
    assert cargado.es_pj is False
    assert cargado.natura is False
