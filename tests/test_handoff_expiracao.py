"""B6 - liberacao automatica de sessoes presas em handoff.

Sem isso, quem conclui o fluxo fica em silencio permanente ate alguem rodar
`scripts/resetar_sessao.py --confirmar` a mao. Confirmado no banco real: a
sessao do telefone piloto ficou presa de 04/08 a 14/08.

A invariante mais importante testada aqui: a expiracao libera o handoff da
Sofia, mas NUNCA fala por cima de um atendente humano.
"""

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.api import SofiaApplication
from sofia_chatbot.config import Settings
from sofia_chatbot.domain import ConversationState, ConversationStatus
from sofia_chatbot.flow import agora_utc, handoff_expirado
from sofia_chatbot.session_store import _state_from_dict, _state_to_dict


def maxbot_payload(
    text: str,
    message_id: str,
    from_number: str = "5531911112222",
    in_attendance: str = "0",
    current_attendant: str = "",
) -> dict:
    return {
        "origin": "2",
        "contact": {
            "id": "1",
            "name": "Fulano",
            "surname": "Teste",
            "whatsapp": from_number,
            "in_attendance": in_attendance,
            "current_protocol": "2398" if in_attendance == "1" else "",
            "current_attendant": current_attendant,
        },
        "msg_id": message_id,
        "msg": text,
        "type": "T",
    }


def estado_em_handoff(horas_atras: float | None) -> ConversationState:
    inicio = (
        None
        if horas_atras is None
        else (agora_utc() - timedelta(hours=horas_atras)).isoformat(timespec="seconds")
    )
    return ConversationState(
        session_id="5531911112222",
        current_block="BLOCO_ENCAMINHAMENTO_COMERCIAL",
        status=ConversationStatus.HANDOFF,
        handoff_since=inicio,
    )


class RegraDeExpiracaoTest(unittest.TestCase):
    def test_dentro_do_prazo_continua_em_silencio(self) -> None:
        self.assertFalse(handoff_expirado(estado_em_handoff(2), 24.0))

    def test_prazo_excedido_libera(self) -> None:
        self.assertTrue(handoff_expirado(estado_em_handoff(25), 24.0))

    def test_exatamente_no_limite_libera(self) -> None:
        self.assertTrue(handoff_expirado(estado_em_handoff(24), 24.0))

    def test_sessao_ativa_nunca_expira(self) -> None:
        ativa = ConversationState(session_id="x", status=ConversationStatus.ACTIVE)
        self.assertFalse(handoff_expirado(ativa, 24.0))

    def test_zero_desliga_a_liberacao_automatica(self) -> None:
        self.assertFalse(handoff_expirado(estado_em_handoff(999), 0))

    def test_sessao_antiga_sem_registro_de_inicio_e_liberada(self) -> None:
        """Sessoes gravadas antes desta funcionalidade nao tem `handoff_since`.

        Mante-las presas para sempre seria preservar exatamente o defeito que
        esta correcao existe para resolver.
        """
        self.assertTrue(handoff_expirado(estado_em_handoff(None), 24.0))

    def test_timestamp_corrompido_libera_em_vez_de_prender(self) -> None:
        estado = estado_em_handoff(1)
        estado.handoff_since = "nao-e-uma-data"
        self.assertTrue(handoff_expirado(estado, 24.0))

    def test_timestamp_sem_fuso_e_tratado_como_utc(self) -> None:
        estado = estado_em_handoff(1)
        estado.handoff_since = (
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=30)
        ).isoformat(timespec="seconds")
        self.assertTrue(handoff_expirado(estado, 24.0))


class PersistenciaDoMarcoTest(unittest.TestCase):
    def test_handoff_since_sobrevive_a_serializacao(self) -> None:
        original = estado_em_handoff(3)
        recuperado = _state_from_dict(_state_to_dict(original))
        self.assertEqual(recuperado.handoff_since, original.handoff_since)

    def test_sessao_sem_o_campo_carrega_como_none(self) -> None:
        antigo = {
            "session_id": "5531911112222",
            "current_block": "BLOCO_ENCAMINHAMENTO_COMERCIAL",
            "tags": [],
            "status": "handoff",
            "lead": {},
        }
        self.assertIsNone(_state_from_dict(antigo).handoff_since)

    def test_fluxo_registra_o_marco_ao_entrar_em_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="sqlite",
                    sqlite_path=str(Path(tmpdir) / "s.db"),
                    event_log_enabled=False,
                )
            )
            # Caminho completo pelo canal direto: menu, equipamento, as tres
            # perguntas especificas, nome, telefone e cidade.
            conversa = (
                "Comecar",
                "1",
                "Fritadeira",
                "Salgados",
                "Uso alto",
                "Eletrica",
                "Ana",
                "31999990000",
                "Belo Horizonte MG",
            )
            for mensagem in conversa:
                resposta = app.chat("sessao-handoff", mensagem)
                if resposta["status"] == ConversationStatus.HANDOFF.value:
                    break

            gravado = app.store.get("sessao-handoff")
            self.assertEqual(gravado.status, ConversationStatus.HANDOFF)
            self.assertIsNotNone(gravado.handoff_since)
            idade = agora_utc() - datetime.fromisoformat(gravado.handoff_since)
            self.assertLess(idade.total_seconds(), 60)


class ExpiracaoNoWebhookTest(unittest.TestCase):
    def _app(self, tmpdir: str, horas: float = 24.0) -> SofiaApplication:
        return SofiaApplication(
            Settings(
                session_store="sqlite",
                sqlite_path=str(Path(tmpdir) / "s.db"),
                event_log_enabled=True,
                event_log_path=str(Path(tmpdir) / "e.db"),
                maxbot_send_messages=False,
                maxbot_pilot_phones=("5531911112222",),
            )
        )

    def _prender(self, app: SofiaApplication, horas_atras: float | None) -> None:
        app.store.save(estado_em_handoff(horas_atras))

    def test_dentro_do_prazo_a_sofia_continua_muda(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            self._prender(app, 2)

            resultado = app.maxbot_webhook(maxbot_payload("Oi", "m1"))

            self.assertEqual(len(resultado["processed"]), 0)
            self.assertEqual(
                resultado["ignored"][0]["ignored_reason"], "handoff_pending"
            )

    def test_depois_do_prazo_a_conversa_recomeca(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            self._prender(app, 30)

            resultado = app.maxbot_webhook(maxbot_payload("Oi", "m2"))

            self.assertEqual(len(resultado["processed"]), 1)
            self.assertEqual(len(resultado["ignored"]), 0)
            self.assertEqual(
                app.store.get("5531911112222").status, ConversationStatus.ACTIVE
            )

    def test_expiracao_nao_atropela_atendimento_humano(self) -> None:
        """A invariante que nao pode quebrar.

        Mesmo com o handoff vencido ha dias, se ha atendente no protocolo a
        Sofia precisa continuar calada. Quem decide isso e o `in_attendance`
        que o Maxbot manda a cada mensagem, verificado antes da expiracao.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            self._prender(app, 240)

            resultado = app.maxbot_webhook(
                maxbot_payload(
                    "Oi",
                    "m3",
                    in_attendance="1",
                    current_attendant="Kaique Carletti",
                )
            )

            self.assertEqual(len(resultado["processed"]), 0)
            self.assertEqual(
                resultado["ignored"][0]["ignored_reason"], "human_attendance"
            )
            self.assertEqual(
                app.store.get("5531911112222").status, ConversationStatus.HANDOFF
            )

    def test_liberacao_fica_registrada_no_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            self._prender(app, 30)

            app.maxbot_webhook(maxbot_payload("Oi", "m4"))

            tipos = [
                evento["event_type"]
                for evento in app.event_logger.list_events(limit=50)
            ]
            self.assertIn("maxbot_handoff_expirado", tipos)

    def test_sessao_legada_sem_marco_e_registrada_com_motivo_proprio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            self._prender(app, None)

            app.maxbot_webhook(maxbot_payload("Oi", "m5"))

            evento = next(
                e
                for e in app.event_logger.list_events(limit=50)
                if e["event_type"] == "maxbot_handoff_expirado"
            )
            self.assertEqual(evento["payload"]["motivo"], "sem_registro_de_inicio")

    def test_desligada_mantem_o_comportamento_de_reset_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir, horas=0)
            app.settings = Settings(
                session_store="sqlite",
                sqlite_path=str(Path(tmpdir) / "s.db"),
                event_log_enabled=False,
                maxbot_send_messages=False,
                maxbot_pilot_phones=("5531911112222",),
                handoff_expira_horas=0,
            )
            self._prender(app, 9999)

            resultado = app.maxbot_webhook(maxbot_payload("Oi", "m6"))

            self.assertEqual(len(resultado["processed"]), 0)
            self.assertEqual(
                resultado["ignored"][0]["ignored_reason"], "handoff_pending"
            )


if __name__ == "__main__":
    unittest.main()
