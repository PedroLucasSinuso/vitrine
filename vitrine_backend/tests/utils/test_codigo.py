from app.domain.value_objects.codigo import Codigo
import pytest

# EANs válidos para testes
_EAN13 = "4006381333931"
_EAN12 = "789191000203"
_EAN8 = "78936478"
_PLU = "123456"

# Casos inválidos
@pytest.mark.parametrize("codigo", [
    "abc",
    "123456789010",
    "1234567",
    "12345678901",
    "12345A",
    "",
])
def test_codigos_invalidos(codigo):
    with pytest.raises(ValueError):
        Codigo(codigo)

# Tipos inválidos
@pytest.mark.parametrize("entrada", [
    123456,
    12.34,
    None,
    ["123456"],
    {"codigo": "123456"},
])
def test_codigo_nao_string(entrada):
    with pytest.raises(TypeError):
        Codigo(entrada)

# Códigos válidos
@pytest.mark.parametrize("codigo, tipo", [
    (_PLU, "PLU6"),
    (_EAN13, "EAN13"),
    (_EAN12, "EAN12"),
    (_EAN8, "EAN8"),
])
def test_codigos_validos(codigo, tipo):
    c = Codigo(codigo)
    assert c.valor == codigo
    assert c.tipo == tipo

# Normalização
def test_normalizacao():
    c = Codigo(" 123-456 ")
    assert c.valor == "123456"

def test_codigo_com_espacos_e_hifen():
    codigo = Codigo(" 4006-3813 33931 ")
    assert codigo.valor == "4006381333931"

# Igualdade
def test_igualdade():
    c1 = Codigo(_PLU)
    c2 = Codigo(_PLU)
    assert c1 == c2

def test_diferenca():
    c1 = Codigo(_PLU)
    c2 = Codigo("654321")
    assert c1 != c2

@pytest.mark.parametrize("entrada, esperado", [
    ("42", "000042"),
    ("1", "000001"),
    ("999", "000999"),
    ("123456", "123456"),
])
def test_plu_zero_padding(entrada, esperado):
    c = Codigo(entrada)
    assert c.valor == esperado
    assert c.tipo == "PLU6"