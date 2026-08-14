import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.api import SofiaApplication
from sofia_chatbot.config import Settings, load_settings
from sofia_chatbot.domain import ConversationStatus, ConversationState
from sofia_chatbot.flow import MENU_OPTIONS, SofiaFlow
from sofia_chatbot.llm.mock import MockLLMClient
from sofia_chatbot.session_store import SQLiteSessionStore


class SofiaFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = SofiaFlow(MockLLMClient())
        self.state = ConversationState(session_id="test")

    def send(self, text: str):
        return self.flow.handle(self.state, text)

    def complete_lead(self, name: str = "Maria"):
        self.send(name)
        self.send("31999990000")
        return self.send("Belo Horizonte, MG")

    def test_all_equipment_paths_handoff_to_commercial(self) -> None:
        scenarios = [
            ("Fritadeira", ["Batata", "Uso alto", "Quero ajuda"], "equipamento_fritadeira"),
            ("Freezer / Refrigeração", ["Congelar", "Carnes", "Grande"], "equipamento_freezer_refrigeracao"),
            ("Forno", ["Pizzas", "Pizza", "Uso medio"], "equipamento_forno"),
            ("Fogão Industrial", ["6", "Restaurante", "Nao sei"], "equipamento_fogao_industrial"),
            ("Chapa", ["Hamburguer", "Grande", "A gas"], "equipamento_chapa"),
            ("Outro equipamento", ["Nao sei o nome", "Preparar", "Padaria"], "equipamento_outro"),
        ]

        for equipment, answers, expected_tag in scenarios:
            with self.subTest(equipment=equipment):
                self.state = ConversationState(session_id=equipment)
                self.send("Comecar")
                self.send("Procuro um equipamento especifico")
                self.send(equipment)
                for answer in answers:
                    self.send(answer)
                reply = self.complete_lead()

                self.assertEqual(reply.status, ConversationStatus.HANDOFF)
                self.assertIn(expected_tag, reply.tags)
                self.assertIn("encaminhar_comercial", reply.tags)
                self.assertIn("lead_mvp_qualificado", reply.tags)
                self.assertIn(equipment, reply.summary or "")
                self.assertIn("Resumo do atendimento - Sofia", reply.summary or "")
                self.assertIn("Destino: Comercial", reply.summary or "")
                self.assertEqual(reply.next_block, "BLOCO_ENCAMINHAMENTO_COMERCIAL")

    def test_first_turn_shows_main_menu(self) -> None:
        reply = self.send("Comecar")

        self.assertIn("Como posso te ajudar hoje?", reply.message)
        self.assertIn("Procuro um equipamento específico", reply.options)
        self.assertEqual(reply.next_block, "BLOCO_01_MENU_INICIAL")

    def test_comecar_from_menu_keeps_menu_visible(self) -> None:
        self.send("Comecar")
        reply = self.send("Comecar")

        self.assertIn("Como posso te ajudar hoje?", reply.message)
        self.assertIn("Falar com consultor", reply.options)
        self.assertNotIn("resposta_nao_entendida", reply.tags)

    def test_main_menu_accepts_numeric_options(self) -> None:
        self.send("Comecar")
        reply = self.send("1")

        self.assertEqual(reply.next_block, "BLOCO_02_EQUIPAMENTO_ESPECIFICO")
        self.assertIn("Fritadeira", reply.options)

    def test_equipment_menu_accepts_numeric_options(self) -> None:
        self.send("Comecar")
        self.send("1")
        reply = self.send("1")

        self.assertEqual(reply.next_block, "BLOCO_EQ_FRITADEIRA_Q1")
        self.assertIn("equipamento_fritadeira", reply.tags)

    def test_direct_equipment_name_from_main_menu(self) -> None:
        self.send("Comecar")
        reply = self.send("quero comprar uma fritadeira")

        self.assertEqual(reply.next_block, "BLOCO_EQ_FRITADEIRA_Q1")
        self.assertIn("equipamento_fritadeira", reply.tags)
        self.assertIn("O que você quer preparar?", reply.message)

    def test_project_kitchen_handoff_to_commercial(self) -> None:
        self.send("Comecar")
        self.send("Vou montar ou reformar uma cozinha")
        self.send("Reformando")
        self.send("Restaurante")
        self.send("Em ate 30 dias")
        reply = self.complete_lead("Fernanda")

        self.assertEqual(reply.status, ConversationStatus.HANDOFF)
        self.assertIn("projeto_cozinha", reply.tags)
        self.assertIn("encaminhar_comercial", reply.tags)
        self.assertIn("Restaurante", reply.summary or "")
        self.assertIn("Em ate 30 dias", reply.summary or "")

    def test_support_handoff_to_pos_venda(self) -> None:
        self.send("Comecar")
        self.send("Suporte / Pos-venda")
        self.send("Sim")
        self.send("Manutencao")
        reply = self.complete_lead("Roberto")

        self.assertEqual(reply.status, ConversationStatus.HANDOFF)
        self.assertIn("pos_venda", reply.tags)
        self.assertIn("encaminhar_pos_venda", reply.tags)
        self.assertNotIn("encaminhar_comercial", reply.tags)

    def test_direct_support_message_shows_limit(self) -> None:
        self.send("Comecar")
        reply = self.send("meu freezer esta com defeito")

        self.assertIn("não consigo fazer diagnóstico técnico", reply.message)
        self.assertIn("pos_venda", reply.tags)
        self.assertEqual(reply.next_block, "BLOCO_04_SUPORTE_POS_VENDA")

    def test_supplier_handoff_to_fornecedor(self) -> None:
        self.send("Comecar")
        self.send("Fornecedor / Representante")
        self.send("Equipamentos Alfa")
        self.send("Fornecedor")
        reply = self.complete_lead("Rafael")

        self.assertEqual(reply.status, ConversationStatus.HANDOFF)
        self.assertIn("fornecedor_representante", reply.tags)
        self.assertIn("encaminhar_compras", reply.tags)
        self.assertIn("Destino: Compras", reply.summary or "")

    def test_site_purchase_handoff_to_compras_online(self) -> None:
        first = self.send("Comprei pelo site")
        self.assertEqual(first.next_block, "BLOCO_04_SUPORTE_POS_VENDA")
        self.assertIn("compras_online", first.tags)

        self.send("Pedido ja feito")
        handoff = self.complete_lead("Marina")

        self.assertEqual(
            handoff.next_block, "BLOCO_ENCAMINHAMENTO_COMPRAS_ONLINE"
        )
        self.assertIn("encaminhar_compras_online", handoff.tags)
        self.assertIn("Destino: Compras Online", handoff.summary or "")
        self.assertNotIn("encaminhar_comercial", handoff.tags)

    def test_consultor_direto_handoff_to_commercial(self) -> None:
        self.send("Comecar")
        self.send("Falar com consultor")
        self.send("Quero ajuda para comprar equipamentos")
        reply = self.complete_lead("Juliana")

        self.assertEqual(reply.status, ConversationStatus.HANDOFF)
        self.assertIn("consultor_direto", reply.tags)
        self.assertIn("encaminhar_comercial", reply.tags)

    def test_sensitive_request_goes_to_human_collection(self) -> None:
        self.send("Comecar")
        reply = self.send("Qual o preco e o frete?")

        self.assertIn("não consigo tratar isso", reply.message)
        self.assertEqual(reply.next_block, "BLOCO_COLETA_NOME")
        self.assertIn("bloqueio_comercial", reply.tags)
        self.assertEqual(self.state.lead.respostas["pedido_sensivel"], "Qual o preco e o frete?")

        self.send("Marcos")
        self.send("31999990000")
        handoff = self.send("Belo Horizonte, MG")
        self.assertIn("Pedido sensível: Qual o preco e o frete?", handoff.summary or "")

    def test_sensitive_terms_from_whatsapp_are_blocked(self) -> None:
        phrases = [
            "quanto custa a chapa?",
            "quanto sai o forno?",
            "tem pronta entrega?",
            "aceita pix?",
            "parcela no cartao?",
            "qual o prazo?",
        ]

        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.state = ConversationState(session_id=phrase)
                self.send("Comecar")
                reply = self.send(phrase)

                self.assertIn("não consigo tratar isso", reply.message)
                self.assertIn("bloqueio_comercial", reply.tags)

    def test_sensitive_request_during_collection_does_not_restart_name(self) -> None:
        self.send("Comecar")
        self.send("Falar com consultor")
        self.send("Quero comprar uma chapa")
        self.send("Patricia")
        reply = self.send("quanto custa?")

        self.assertEqual(reply.next_block, "BLOCO_COLETA_TELEFONE")
        self.assertIn("Qual é o melhor telefone ou WhatsApp", reply.message)
        self.assertEqual(self.state.lead.nome_cliente, "Patricia")

    def test_unknown_answer_returns_to_menu(self) -> None:
        self.send("Comecar")
        reply = self.send("Quero ver tudo")

        self.assertIn("Não consegui entender", reply.message)
        self.assertEqual(reply.next_block, "BLOCO_01_MENU_INICIAL")
        self.assertIn("resposta_nao_entendida", reply.tags)

    def test_after_handoff_bot_does_not_restart_menu(self) -> None:
        self.send("Comecar")
        self.send("Falar com consultor")
        self.send("Quero comprar equipamentos")
        self.complete_lead("Juliana")

        reply = self.send("ainda estou aqui")

        self.assertEqual(reply.status, ConversationStatus.HANDOFF)
        self.assertEqual(reply.next_block, "BLOCO_ENCAMINHAMENTO_COMERCIAL")
        self.assertNotIn("resposta_nao_entendida", reply.tags)
        self.assertIn("já foi encaminhado", reply.message)


    def test_expanded_price_phrases_are_blocked(self) -> None:
        phrases = [
            "quanto que custa a fritadeira?",
            "quanto é o forno?",
            "quanto tá a chapa?",
            "quanto está o freezer?",
            "qual o custo?",
            "custa quanto?",
            "quanto vai ficar?",
            "tem promoção?",
            "qual a cotação?",
            "tem mais barato?",
            "qto custa",
        ]

        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.state = ConversationState(session_id=phrase)
                self.send("Comecar")
                reply = self.send(phrase)

                self.assertIn("não consigo tratar isso", reply.message)
                self.assertIn("bloqueio_comercial", reply.tags)

    def test_guardrail_avoids_substring_false_positives(self) -> None:
        from sofia_chatbot.guardrails import contains_sensitive_commercial_request

        phrases = [
            "vou propagar a marca nas redes",
            "quanto pesa a chapa?",
            "quero um pixel art no cardapio",
            "quanto tempo demora a analise?",
            "o ar condicionador nao liga",
        ]

        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertFalse(contains_sensitive_commercial_request(phrase))

    def test_posso_is_not_routed_to_support(self) -> None:
        self.send("Comecar")
        reply = self.send("posso falar com um atendente?")

        self.assertNotIn("pos_venda", reply.tags)
        self.assertEqual(reply.next_block, "BLOCO_06_CONSULTOR_DIRETO")
        self.assertIn("consultor_direto", reply.tags)

    def test_apos_a_compra_still_routes_to_support(self) -> None:
        self.send("Comecar")
        reply = self.send("preciso de suporte pos venda")

        self.assertIn("pos_venda", reply.tags)
        self.assertEqual(reply.next_block, "BLOCO_04_SUPORTE_POS_VENDA")

    def test_classifier_failure_falls_back_to_menu(self) -> None:
        class FailingLLM(MockLLMClient):
            def complete(self, messages):
                raise RuntimeError("provedor fora do ar")

        flow = SofiaFlow(FailingLLM())
        state = ConversationState(session_id="llm-falha")
        flow.handle(state, "Comecar")
        reply = flow.handle(state, "texto que exige o classificador")

        self.assertIn("Não consegui entender", reply.message)
        self.assertEqual(reply.next_block, "BLOCO_01_MENU_INICIAL")

    def test_first_message_routes_without_forcing_customer_to_repeat(self) -> None:
        reply = self.flow.handle(self.state, "quero uma fritadeira")

        self.assertEqual(reply.next_block, "BLOCO_EQ_FRITADEIRA_Q1")
        self.assertIn("Eu sou a Sofia", reply.message)
        self.assertIn("O que você quer preparar?", reply.message)
        self.assertEqual(self.state.lead.equipamento_interesse, "Fritadeira")

    def test_plain_greeting_still_shows_initial_menu(self) -> None:
        reply = self.flow.handle(self.state, "Bom dia!")

        self.assertEqual(reply.next_block, "BLOCO_01_MENU_INICIAL")
        self.assertEqual(reply.options, MENU_OPTIONS)

    def test_contextual_delivery_answer_is_not_commercially_blocked(self) -> None:
        self.send("Comecar")
        self.send("Procuro um equipamento especifico")
        self.send("Chapa")
        reply = self.send("faco lanches para entrega")

        self.assertNotIn("bloqueio_comercial", reply.tags)
        self.assertEqual(reply.next_block, "BLOCO_EQ_CHAPA_Q2")
        self.assertEqual(self.state.lead.respostas["pergunta_1"], "faco lanches para entrega")

    def test_delivery_question_remains_blocked_during_qualification(self) -> None:
        self.send("Comecar")
        self.send("Procuro um equipamento especifico")
        self.send("Chapa")
        reply = self.send("voces fazem entrega em Santos?")

        self.assertIn("bloqueio_comercial", reply.tags)
        self.assertEqual(reply.next_block, "BLOCO_COLETA_NOME")
        self.assertIn("Qual é o seu nome?", reply.message)


class SQLiteSessionStoreTest(unittest.TestCase):
    def test_persists_conversation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "sessions.db")
            store = SQLiteSessionStore(db_path)
            state = store.get("abc")
            state.current_block = "BLOCO_COLETA_NOME"
            state.tags.add("equipamento_fritadeira")
            state.lead.equipamento_interesse = "Fritadeira"
            store.save(state)

            reloaded = SQLiteSessionStore(db_path).get("abc")

            self.assertEqual(reloaded.current_block, "BLOCO_COLETA_NOME")
            self.assertIn("equipamento_fritadeira", reloaded.tags)
            self.assertEqual(reloaded.lead.equipamento_interesse, "Fritadeira")


class SettingsTest(unittest.TestCase):
    def test_load_settings_reads_env_file_and_environment_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "LOCAL_API_ENABLED=false\n"
                "WHATSAPP_SEND_MESSAGES=false\n"
                "MAXBOT_WEBHOOK_SECRET=segredo-teste\n"
                "MAXBOT_PILOT_SEGMENT=SEGMENTO_TESTE\n"
                "MAXBOT_PILOT_PHONES=5531999990001, 5531999990002\n"
                "MAXBOT_SEND_MESSAGES=true\n"
                "SOFIA_PORT=8123\n",
                encoding="utf-8",
            )

            with patch.dict("os.environ", {"SOFIA_PORT": "9001"}, clear=True):
                settings = load_settings(env_path)

            self.assertFalse(settings.local_api_enabled)
            self.assertFalse(settings.whatsapp_send_messages)
            self.assertTrue(settings.maxbot_send_messages)
            self.assertEqual(settings.maxbot_webhook_secret, "segredo-teste")
            self.assertEqual(settings.maxbot_pilot_segment, "SEGMENTO_TESTE")
            self.assertEqual(
                settings.maxbot_pilot_phones,
                ("5531999990001", "5531999990002"),
            )
            self.assertEqual(settings.port, 9001)


class SofiaApplicationPersistenceTest(unittest.TestCase):
    def test_application_uses_persistent_store_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "sessions.db")
            settings = Settings(
                session_store="sqlite",
                sqlite_path=db_path,
                event_log_enabled=True,
                event_log_path=str(Path(tmpdir) / "events.db"),
            )

            app_one = SofiaApplication(settings)
            app_one.chat("sessao-1", "Comecar")
            app_one.chat("sessao-1", "Procuro um equipamento especifico")

            app_two = SofiaApplication(settings)
            response = app_two.chat("sessao-1", "Fritadeira")

            self.assertEqual(response["next_block"], "BLOCO_EQ_FRITADEIRA_Q1")
            self.assertIn("equipamento_fritadeira", response["tags"])


class IsolamentoDeDadosTest(unittest.TestCase):
    """A suite nunca pode gravar nos bancos reais, que contem PII do piloto.

    Regressao: um teste sem `event_log_path` explicito usava o caminho padrao
    `data/sofia_events.db` e poluia o log real com eventos `chat` de teste,
    contaminando a contagem usada nas janelas de teste do Maxbot.
    """

    def test_aplicacao_configurada_nao_grava_nos_caminhos_padrao(self) -> None:
        padrao = Settings()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cwd_original = Path.cwd()
            os.chdir(tmp)
            try:
                app = SofiaApplication(
                    Settings(
                        session_store="sqlite",
                        sqlite_path=str(tmp / "sessions.db"),
                        event_log_enabled=True,
                        event_log_path=str(tmp / "events.db"),
                    )
                )
                app.chat("sessao-isolada", "Comecar")
            finally:
                os.chdir(cwd_original)

            self.assertTrue((tmp / "events.db").is_file())
            self.assertFalse((tmp / padrao.event_log_path).exists())
            self.assertFalse((tmp / padrao.sqlite_path).exists())


if __name__ == "__main__":
    unittest.main()
