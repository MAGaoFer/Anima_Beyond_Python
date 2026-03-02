from combate.validaciones import entero_opcional, parsear_modificadores


def test_entero_opcional_valores_validos_e_invalidos():
    assert entero_opcional("15") == 15
    assert entero_opcional("  -3 ") == -3
    assert entero_opcional("") is None
    assert entero_opcional("abc") is None


def test_parsear_modificadores_sumatoria_correcta():
    assert parsear_modificadores("+20-10+5") == 15
    assert parsear_modificadores("-30+10") == -20
    assert parsear_modificadores("") == 0


def test_parsear_modificadores_formato_invalido():
    try:
        parsear_modificadores("+10x-2")
    except ValueError:
        pass
    else:
        raise AssertionError("Se esperaba ValueError para formato inválido")
