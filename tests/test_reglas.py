from combate.reglas import modificador_sorpresa


def test_modificador_sorpresa_aplica_con_mas_de_150():
    assert modificador_sorpresa(200, 25) == -90


def test_modificador_sorpresa_no_aplica_en_150_o_menos():
    assert modificador_sorpresa(200, 50) == 0
    assert modificador_sorpresa(120, 10) == 0
