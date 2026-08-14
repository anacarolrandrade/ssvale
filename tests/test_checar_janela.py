"""Testes do go/no-go pre-janela (scripts/checar_janela.py)."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import checar_janela  # noqa: E402


class VereditoTest(unittest.TestCase):
    def test_todas_aprovadas_libera_a_janela(self) -> None:
        liberado, reprovadas = checar_janela.veredito(
            [("Suite", True, "OK"), ("Preflight", True, "APROVADO")]
        )
        self.assertTrue(liberado)
        self.assertEqual(reprovadas, [])

    def test_uma_etapa_reprovada_bloqueia_a_janela(self) -> None:
        liberado, reprovadas = checar_janela.veredito(
            [
                ("Suite", True, "OK"),
                ("Preflight", False, "Preflight: PENDENCIAS ACIMA"),
                ("Ensaio", True, "Ensaio OK"),
            ]
        )
        self.assertFalse(liberado)
        self.assertEqual(reprovadas, ["Preflight"])

    def test_sem_etapas_nao_e_tratado_como_reprovacao_silenciosa(self) -> None:
        # Guarda contra uma lista de etapas vazia passar como "liberado" sem
        # ter verificado nada: o script sempre precisa declarar suas etapas.
        self.assertTrue(checar_janela.ETAPAS)


class LeituraDeSaidaTest(unittest.TestCase):
    def test_resumo_usa_a_ultima_linha_util(self) -> None:
        self.assertEqual(
            checar_janela.ultima_linha_util("linha 1\nEnsaio OK\n\n  \n"),
            "Ensaio OK",
        )

    def test_saida_vazia_nao_quebra(self) -> None:
        self.assertEqual(checar_janela.ultima_linha_util("   \n\n"), "(sem saida)")

    def test_motivo_da_reprovacao_nao_fica_escondido(self) -> None:
        saida = (
            "== Sessoes residuais ==\n"
            "  [NAO] ***9238 em status 'handoff' desde 2026-08-04 23:46:55\n"
            "  [ok ] MAXBOT_API_TOKEN: configurado\n"
            "Preflight: PENDENCIAS ACIMA\n"
        )
        detalhes = checar_janela.pendencias(saida)
        self.assertEqual(len(detalhes), 1)
        self.assertIn("handoff", detalhes[0])


if __name__ == "__main__":
    unittest.main()
