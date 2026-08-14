"""Regressoes das correcoes de prontidao para deploy.

Cada teste aqui existe por causa de um item do `DIAGNOSTICO-DEPLOY.md`. Sao
falhas que nao aparecem na maquina de desenvolvimento e so se manifestam quando
o processo roda em outro diretorio, em outro fuso ou sob um gerenciador de
servico que envia SIGTERM.
"""

import json
import os
import signal
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.api import (
    SofiaApplication,
    configurar_saida_sem_buffer,
    create_server,
    install_shutdown_handlers,
)
from sofia_chatbot.channels.maxbot import MaxbotClient, MaxbotReplyRenderer
from sofia_chatbot.config import (
    PROJECT_ROOT,
    Settings,
    load_settings,
    resolve_data_path,
    resolve_env_path,
)
from sofia_chatbot.domain import BotReply, ConversationStatus


class RespostaFalsa:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"status": 1, "msg": "Success"}'


class CaminhosIndependentesDoDiretorioTest(unittest.TestCase):
    """B2: a aplicacao subia com configuracao vazia fora do diretorio do projeto.

    O efeito no ar era silencioso e caro: sem `MAXBOT_WEBHOOK_SECRET` o webhook
    responde 404 a tudo, o `/health` continua dizendo `ok` e a Sofia nunca
    responde, sem registrar erro nenhum.
    """

    def test_env_e_encontrado_a_partir_de_outro_diretorio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            env_path = tmp / "producao.env"
            env_path.write_text(
                "MAXBOT_WEBHOOK_SECRET=segredo-de-producao\n"
                "SQLITE_PATH=/var/lib/sofia/sessoes.db\n"
                "EVENT_LOG_PATH=/var/lib/sofia/eventos.db\n",
                encoding="utf-8",
            )

            cwd_original = Path.cwd()
            os.chdir(tmp)
            try:
                with patch.dict(
                    "os.environ", {"SOFIA_ENV_FILE": str(env_path)}, clear=True
                ):
                    settings = load_settings()
            finally:
                os.chdir(cwd_original)

            self.assertEqual(settings.maxbot_webhook_secret, "segredo-de-producao")
            self.assertEqual(settings.env_file, str(env_path))

    def test_env_ausente_fica_registrado_em_vez_de_falhar_calado(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ausente = Path(tmpdir) / "nao-existe.env"

            with patch.dict("os.environ", {}, clear=True):
                settings = load_settings(ausente)

            self.assertEqual(settings.env_file, "")
            self.assertEqual(settings.maxbot_webhook_secret, "")

    def test_caminho_relativo_de_banco_e_ancorado_na_raiz_do_projeto(self) -> None:
        resolvido = Path(resolve_data_path("data/sofia_sessions.db"))

        self.assertTrue(resolvido.is_absolute())
        self.assertEqual(resolvido, PROJECT_ROOT / "data" / "sofia_sessions.db")

    def test_caminho_absoluto_de_banco_e_respeitado(self) -> None:
        absoluto = str(Path(tempfile.gettempdir()) / "sofia" / "sessoes.db")

        self.assertEqual(resolve_data_path(absoluto), absoluto)

    def test_precedencia_do_arquivo_env(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(resolve_env_path(), PROJECT_ROOT / ".env")

        with patch.dict("os.environ", {"SOFIA_ENV_FILE": "/etc/sofia.env"}, clear=True):
            self.assertEqual(resolve_env_path(), Path("/etc/sofia.env"))

        with patch.dict("os.environ", {"SOFIA_ENV_FILE": "/etc/sofia.env"}, clear=True):
            self.assertEqual(resolve_env_path("/outro.env"), Path("/outro.env"))


class PortaDePlataformaTest(unittest.TestCase):
    """B4: plataformas gerenciadas injetam `PORT`, o projeto lia `SOFIA_PORT`."""

    def _porta(self, ambiente: dict[str, str]) -> int:
        with tempfile.TemporaryDirectory() as tmpdir:
            ausente = Path(tmpdir) / "sem.env"
            with patch.dict("os.environ", ambiente, clear=True):
                return load_settings(ausente).port

    def test_usa_port_quando_sofia_port_nao_existe(self) -> None:
        self.assertEqual(self._porta({"PORT": "10000"}), 10000)

    def test_sofia_port_tem_precedencia(self) -> None:
        self.assertEqual(
            self._porta({"PORT": "10000", "SOFIA_PORT": "8123"}), 8123
        )

    def test_valor_invalido_cai_no_padrao(self) -> None:
        self.assertEqual(self._porta({"PORT": "nao-e-numero"}), 8000)

    def test_sem_nenhuma_variavel_usa_padrao(self) -> None:
        self.assertEqual(self._porta({}), 8000)


class ParadaLimpaTest(unittest.TestCase):
    """B7: SIGTERM matava requisicoes em voo.

    A mensagem e marcada como processada ANTES do envio. Morrer no meio disso
    consome a mensagem sem responder e sem deixar rastro.
    """

    def _servidor(self):
        settings = Settings(session_store="memory", event_log_enabled=False, port=0)
        return create_server(SofiaApplication(settings), settings)

    def test_servidor_espera_requisicoes_em_voo(self) -> None:
        server = self._servidor()
        try:
            self.assertFalse(server.daemon_threads)
            self.assertTrue(server.block_on_close)
        finally:
            server.server_close()

    def test_shutdown_encerra_o_serve_forever(self) -> None:
        server = self._servidor()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            threading.Thread(target=server.shutdown, daemon=True).start()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        finally:
            server.server_close()

    def test_sigterm_fica_registrado(self) -> None:
        server = self._servidor()
        anterior_term = signal.getsignal(signal.SIGTERM)
        anterior_int = signal.getsignal(signal.SIGINT)
        try:
            self.assertTrue(install_shutdown_handlers(server))
            self.assertNotEqual(signal.getsignal(signal.SIGTERM), signal.SIG_DFL)
            self.assertNotEqual(signal.getsignal(signal.SIGTERM), anterior_term)
        finally:
            signal.signal(signal.SIGTERM, anterior_term)
            signal.signal(signal.SIGINT, anterior_int)
            server.server_close()


class SaidaSemBufferTest(unittest.TestCase):
    """Sob systemd o stdout vira pipe e o log so aparecia quando o processo
    morria. Verificado no ar: o servico ficou 3 segundos sem imprimir nada e a
    saida inteira apareceu de uma vez depois do SIGTERM.
    """

    def test_ativa_buffer_por_linha_no_stdout(self) -> None:
        configurar_saida_sem_buffer()
        self.assertTrue(sys.stdout.line_buffering)

    def test_tolera_stdout_sem_reconfigure(self) -> None:
        import io

        class SemReconfigure(io.StringIO):
            def reconfigure(self, **kwargs):
                raise AttributeError("dublê sem suporte")

        original = sys.stdout
        sys.stdout = SemReconfigure()
        try:
            configurar_saida_sem_buffer()
        finally:
            sys.stdout = original


class TimeoutDeEnvioTest(unittest.TestCase):
    """B9: 30s dentro do handler do webhook seguram o ACK e convidam reenvio."""

    def test_padrao_e_dez_segundos(self) -> None:
        self.assertEqual(Settings().maxbot_timeout_seconds, 10.0)

    def test_timeout_configurado_chega_no_urlopen(self) -> None:
        client = MaxbotClient(
            Settings(
                maxbot_api_token="segredo",
                maxbot_send_messages=True,
                maxbot_timeout_seconds=7.5,
            )
        )

        with patch(
            "sofia_chatbot.channels.maxbot.urllib.request.urlopen",
            return_value=RespostaFalsa(),
        ) as urlopen:
            client.send_text("5531911112222", "Ola")

        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7.5)

    def test_timeout_invalido_no_env_cai_no_padrao(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ausente = Path(tmpdir) / "sem.env"
            with patch.dict(
                "os.environ", {"MAXBOT_TIMEOUT_SECONDS": "zero"}, clear=True
            ):
                self.assertEqual(load_settings(ausente).maxbot_timeout_seconds, 10.0)


class FusoDeBrasiliaTest(unittest.TestCase):
    """B10: `datetime.now()` num servidor em UTC gravava tres horas a mais."""

    def test_msg_date_sql_usa_horario_de_brasilia(self) -> None:
        payload = MaxbotReplyRenderer().render_attendance(
            "2398",
            BotReply(
                message="Ola",
                options=[],
                status=ConversationStatus.ACTIVE,
                summary=None,
                tags=[],
                next_block="BLOCO_00_BOAS_VINDAS",
            ),
        )

        gravado = datetime.strptime(payload["msg_date_sql"], "%Y-%m-%d %H:%M:%S")
        esperado = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

        self.assertLess(abs((gravado - esperado).total_seconds()), 60)

    def test_nao_usa_o_fuso_do_servidor(self) -> None:
        """Com TZ=UTC o resultado ainda precisa ser horario de Brasilia."""
        payload = MaxbotReplyRenderer().render_attendance(
            "2398",
            BotReply(
                message="Ola",
                options=[],
                status=ConversationStatus.ACTIVE,
                summary=None,
                tags=[],
                next_block="BLOCO_00_BOAS_VINDAS",
            ),
        )

        gravado = datetime.strptime(payload["msg_date_sql"], "%Y-%m-%d %H:%M:%S")
        utc = datetime.now(timezone.utc).replace(tzinfo=None)
        diferenca_horas = (utc - gravado).total_seconds() / 3600

        self.assertAlmostEqual(diferenca_horas, 3.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
