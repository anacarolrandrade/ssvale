"""Garante que os textos enviados ao cliente permanecam acentuados.

Regressao: as mensagens de limite comercial e de suporte foram esquecidas na
revisao de acentuacao e chegaram assim ao numero oficial ("Eu nao consigo
tratar isso por aqui..."). Este teste percorre os caminhos principais do fluxo
e reprova qualquer palavra que deveria ter acento.
"""

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.domain import ConversationState  # noqa: E402
from sofia_chatbot.flow import SofiaFlow  # noqa: E402
from sofia_chatbot.guardrails import (  # noqa: E402
    commercial_limit_message,
    support_limit_message,
)
from sofia_chatbot.llm.mock import MockLLMClient  # noqa: E402

# Palavras que, sem acento, denunciam texto nao revisado.
PALAVRAS_SEM_ACENTO = {
    "nao",
    "voce",
    "voces",
    "informacoes",
    "informacao",
    "solicitacao",
    "responsavel",
    "tecnico",
    "diagnostico",
    "especifico",
    "opcao",
    "opcoes",
    "orcamento",
    "producao",
    "refrigeracao",
    "sera",
    "possivel",
    "disponivel",
    "duvida",
    "duvidas",
    "proxima",
    "endereco",
    "numero",
    "atencao",
    "servico",
}

CONVERSAS = {
    "equipamento": [
        "Comecar",
        "1",
        "1",
        "Batata",
        "Uso alto",
        "Quero ajuda",
        "Maria",
        "Belo Horizonte, MG",
    ],
    "pedido_sensivel": ["Comecar", "Quanto custa?", "Joao", "Sao Paulo, SP"],
    "pos_venda": [
        "Comecar",
        "Suporte / Pos-venda",
        "Sim",
        "Manutencao",
        "Forno modelo X",
        "Nao aquece",
        "Equipamento parado",
        "Ana",
        "Taubate SP",
    ],
    "nao_entendido": ["Comecar", "xyzabc"],
    "projeto_cozinha": [
        "Comecar",
        "Vou montar ou reformar uma cozinha",
        "Reformando",
        "Restaurante",
        "Em ate 30 dias",
        "Leandro",
        "Rio de Janeiro, RJ",
    ],
    "fornecedor": [
        "Comecar",
        "Fornecedor / Representante",
        "Equipamentos Alfa",
        "Fornecedor",
        "Pecas para cozinha industrial",
        "Apresentar catalogo",
        "Beatriz",
        "Belo Horizonte, MG",
    ],
    "compras_online": ["Comprei pelo site", "Pedido ja feito", "Pedido 123", "Acompanhar entrega", "Não se aplica", "Juliana", "Sao Paulo, SP"],
    "suporte_direto": ["Comecar", "meu freezer esta com defeito"],
}


def palavras_sem_acento(texto: str) -> set[str]:
    return {
        palavra.lower()
        for palavra in re.findall(r"[A-Za-zÀ-ÿ]+", texto)
        if palavra.lower() in PALAVRAS_SEM_ACENTO
    }


class TextosDoClienteTest(unittest.TestCase):
    def test_mensagens_de_limite_estao_acentuadas(self) -> None:
        self.assertIn("Vou encaminhar seu pedido", commercial_limit_message())
        self.assertIn("condições", commercial_limit_message())
        self.assertIn("não consigo fazer diagnóstico técnico", support_limit_message())
        self.assertIn("solicitação", support_limit_message())

    def test_nenhum_caminho_do_fluxo_envia_texto_sem_acento(self) -> None:
        for nome, mensagens in CONVERSAS.items():
            with self.subTest(conversa=nome):
                fluxo = SofiaFlow(MockLLMClient())
                estado = ConversationState(session_id=nome)
                encontrados: set[str] = set()
                for entrada in mensagens:
                    resposta = fluxo.handle(estado, entrada)
                    textos = [resposta.message, *(resposta.options or [])]
                    if resposta.summary:
                        textos.append(resposta.summary)
                    for texto in textos:
                        encontrados |= palavras_sem_acento(texto)

                self.assertEqual(
                    encontrados,
                    set(),
                    f"Texto sem acento enviado ao cliente em {nome}: {sorted(encontrados)}",
                )


if __name__ == "__main__":
    unittest.main()
