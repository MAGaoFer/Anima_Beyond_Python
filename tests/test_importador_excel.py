from almacenamiento.importador_excel import mapear_categoria_excel, normalizar_numero_excel


def test_normalizar_numero_excel_admite_formato_texto():
    assert normalizar_numero_excel("(46)") == 46
    assert normalizar_numero_excel("X", default=0) == 0
    assert normalizar_numero_excel(None, default=7) == 7


def test_mapear_categoria_excel_grupos_principales():
    assert mapear_categoria_excel("Guerrero", {}) == "Guerrero"
    assert mapear_categoria_excel("Tao", {}) == "Guerrero"
    assert mapear_categoria_excel("Warlock", {}) == "Warlock"
    assert mapear_categoria_excel("Hechicero", {}) == "Mago"
    assert mapear_categoria_excel("Mentalista (C)", {}) == "Mentalista"
    assert mapear_categoria_excel("Hechicero mentalista", {}) == "Hechicero mentalista"


def test_mapear_categoria_excel_novel_por_datos():
    assert mapear_categoria_excel("Novel", {"zeon": 100, "proyeccion_psiquica": 80}) == "Hechicero mentalista"
    assert mapear_categoria_excel("Novel", {"zeon": 100, "proyeccion_psiquica": 0}) == "Warlock"
    assert mapear_categoria_excel("Novel", {"zeon": 0, "proyeccion_psiquica": 80}) == "Guerrero mentalista"
    assert mapear_categoria_excel("Novel", {"zeon": 0, "proyeccion_psiquica": 0}) == "Guerrero"
