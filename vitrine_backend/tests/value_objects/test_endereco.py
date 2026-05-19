"""Testes do Value Object Endereco (app.domain.value_objects.endereco)."""

import pytest
from app.domain.value_objects.endereco import (
    Endereco,
    validar_cep,
    validar_uf,
    formatar_cep,
)


class TestValidarCep:
    def test_cep_8_digitos_sem_mascara(self):
        assert validar_cep("01001000") == "01001000"

    def test_cep_com_mascara(self):
        assert validar_cep("01001-000") == "01001000"

    def test_cep_7_digitos_rejeitado(self):
        with pytest.raises(ValueError, match="CEP inválido"):
            validar_cep("0100100")

    def test_cep_com_letras_rejeitado(self):
        with pytest.raises(ValueError, match="CEP inválido"):
            validar_cep("abcde-fgh")

    def test_cep_vazio_rejeitado(self):
        with pytest.raises(ValueError, match="CEP inválido"):
            validar_cep("")

    def test_cep_espacos_ignorados(self):
        assert validar_cep("  01001-000  ") == "01001000"


class TestValidarUf:
    def test_uf_valida(self):
        assert validar_uf("SP") == "SP"
        assert validar_uf("rj") == "RJ"
        assert validar_uf("Ba") == "BA"

    def test_uf_invalida(self):
        with pytest.raises(ValueError, match="UF inválida"):
            validar_uf("XX")
        with pytest.raises(ValueError, match="UF inválida"):
            validar_uf("Sao Paulo")
        with pytest.raises(ValueError, match="UF inválida"):
            validar_uf("")

    def test_todas_as_27_ufs(self):
        for uf in ["AC","AL","AP","AM","BA","CE","DF","ES","GO",
                    "MA","MT","MS","MG","PA","PB","PR","PE","PI",
                    "RJ","RN","RS","RO","RR","SC","SP","SE","TO"]:
            assert validar_uf(uf) == uf
            assert validar_uf(uf.lower()) == uf


class TestFormatarCep:
    def test_formata_8_digitos(self):
        assert formatar_cep("01001000") == "01001-000"

    def test_ja_formatado_permanece(self):
        assert formatar_cep("01001-000") == "01001-000"

    def test_string_curta_retorna_original(self):
        assert formatar_cep("123") == "123"


class TestEnderecoValidacao:
    def test_endereco_completo_valido(self):
        end = Endereco(
            rua="Rua Augusta",
            numero="1500",
            complemento="Apto 42",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP",
            cep="01304-001",
        )
        assert end.rua == "Rua Augusta"
        assert end.cep == "01304001"
        assert end.estado == "SP"
        assert end.completo is True

    def test_endereco_sem_complemento(self):
        end = Endereco(
            rua="Av. Paulista",
            numero="1000",
            bairro="Bela Vista",
            cidade="São Paulo",
            estado="SP",
            cep="01310100",
        )
        assert end.complemento == ""
        assert end.completo is True

    def test_endereco_incompleto(self):
        end = Endereco(rua="Rua X", numero="10")
        assert end.completo is False

    def test_cep_invalido_rejeitado(self):
        with pytest.raises(ValueError, match="CEP inválido"):
            Endereco(cep="123")

    def test_uf_invalida_rejeitada(self):
        with pytest.raises(ValueError, match="UF inválida"):
            Endereco(estado="XX")


class TestEnderecoFormatacao:
    def test_formatado_simples(self):
        end = Endereco(
            rua="Rua Augusta",
            numero="1500",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP",
            cep="01304001",
        )
        assert "Rua Augusta, 1500" in end.formatado
        assert "Consolação, São Paulo - SP" in end.formatado
        assert "CEP 01304-001" in end.formatado

    def test_formatado_com_complemento(self):
        end = Endereco(
            rua="Rua Augusta",
            numero="1500",
            complemento="Apto 42",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP",
            cep="01304001",
        )
        assert "Rua Augusta, 1500 — Apto 42" in end.formatado

    def test_formatado_minimo(self):
        end = Endereco(rua="Rua A", numero="1")
        assert end.formatado == "Rua A, 1"

    def test_cep_formatado_propriedade(self):
        end = Endereco(cep="01304001")
        assert end.cep_formatado == "01304-001"

    def test_cep_formatado_vazio(self):
        end = Endereco()
        assert end.cep_formatado == ""


class TestEnderecoParaIa:
    def test_para_prompt_ia_estrutura(self):
        end = Endereco(
            rua="Rua Augusta",
            numero="1500",
            complemento="Apto 42",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP",
            cep="01304001",
        )
        prompt = end.para_prompt_ia()
        assert "LOGRADOURO: Rua Augusta" in prompt
        assert "NUMERO: 1500" in prompt
        assert "COMPLEMENTO: Apto 42" in prompt
        assert "BAIRRO: Consolação" in prompt
        assert "CIDADE: São Paulo" in prompt
        assert "ESTADO: SP" in prompt
        assert "CEP: 01304-001" in prompt
        assert "IBGE: (não informado)" in prompt

    def test_para_prompt_ia_sem_complemento(self):
        end = Endereco(
            rua="Rua Augusta",
            numero="1500",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP",
            cep="01304001",
        )
        prompt = end.para_prompt_ia()
        assert "COMPLEMENTO: (vazio)" in prompt

    def test_para_json_ia(self):
        end = Endereco(
            rua="Rua Augusta",
            numero="1500",
            cidade="São Paulo",
            estado="SP",
            cep="01304001",
            codigo_ibge="3550308",
            ddd="11",
        )
        data = end.para_json_ia()
        assert data["rua"] == "Rua Augusta"
        assert data["codigo_ibge"] == "3550308"
        assert data["ddd"] == "11"


class TestEnderecoEnriquecimento:
    def test_model_copy_atualiza_campos(self):
        """Simula o que enriquecer_por_cep faria."""
        end = Endereco(cep="01304001")
        enriquecido = end.model_copy(update={
            "codigo_ibge": "3550308",
            "ddd": "11",
            "latitude": -23.5505,
            "longitude": -46.6333,
        })
        assert enriquecido.codigo_ibge == "3550308"
        assert enriquecido.ddd == "11"
        assert enriquecido.latitude == -23.5505
        assert enriquecido.longitude == -46.6333
        # Original permanece inalterado
        assert end.codigo_ibge is None


class TestEnderecoEdgeCases:
    def test_campos_vazios_nao_quebram_formatado(self):
        end = Endereco()
        assert end.formatado == ""
        assert end.completo is False
        assert end.cep_formatado == ""

    def test_estado_vazio_nao_e_validado(self):
        """Estado vazio não deve disparar validação de UF."""
        end = Endereco(estado="")
        assert end.estado == ""
