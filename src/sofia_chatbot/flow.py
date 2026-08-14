import re

from sofia_chatbot.domain import BotReply, ConversationState, ConversationStatus
from sofia_chatbot.guardrails import (
    commercial_limit_message,
    contains_sensitive_commercial_request,
    normalize_for_matching,
    support_limit_message,
)
from sofia_chatbot.llm.base import LLMClient, LLMMessage


# Casado sobre texto normalizado (minusculo, sem acento). \b evita que "pos"
# dispare dentro de palavras comuns como "posso" ou "apos".
_POS_VENDA_REGEX = re.compile(r"\bpos[\s\-]?venda\b|\bpos\b|\bsuporte\b")
_GREETING_REGEX = re.compile(
    r"^(oi|ola|bom\s+dia|boa\s+tarde|boa\s+noite|comecar|inicio|menu)[!.?\s]*$"
)


MENU_OPTIONS = [
    "Procuro um equipamento específico",
    "Vou montar ou reformar uma cozinha",
    "Suporte / Pós-venda",
    "Fornecedor / Representante",
    "Falar com consultor",
]


MENU_NUMBER_ALIASES = {
    "1": "Procuro um equipamento específico",
    "2": "Vou montar ou reformar uma cozinha",
    "3": "Suporte / Pós-venda",
    "4": "Fornecedor / Representante",
    "5": "Falar com consultor",
}


EQUIPMENT_BLOCKS = {
    "Fritadeira": ("BLOCO_EQ_FRITADEIRA_Q1", "equipamento_fritadeira"),
    "Freezer / Refrigeração": ("BLOCO_EQ_FREEZER_Q1", "equipamento_freezer_refrigeracao"),
    "Forno": ("BLOCO_EQ_FORNO_Q1", "equipamento_forno"),
    "Fogão Industrial": ("BLOCO_EQ_FOGAO_Q1", "equipamento_fogao_industrial"),
    "Chapa": ("BLOCO_EQ_CHAPA_Q1", "equipamento_chapa"),
    "Outro equipamento": ("BLOCO_EQ_OUTRO_Q1", "equipamento_outro"),
}


EQUIPMENT_NUMBER_ALIASES = {
    "1": "Fritadeira",
    "2": "Freezer / Refrigeração",
    "3": "Forno",
    "4": "Fogão Industrial",
    "5": "Chapa",
    "6": "Outro equipamento",
}


EQUIPMENT_ALIASES = {
    "fritadeira": "Fritadeira",
    "freezer": "Freezer / Refrigeração",
    "refrigeracao": "Freezer / Refrigeração",
    "refrigeração": "Freezer / Refrigeração",
    "geladeira": "Freezer / Refrigeração",
    "forno": "Forno",
    "fogao": "Fogão Industrial",
    "fogão": "Fogão Industrial",
    "chapa": "Chapa",
}


SUPPORT_ALIASES = {
    "defeito",
    "garantia",
    "manutencao",
    "manutenção",
    "nao funciona",
    "não funciona",
    "nao gela",
    "não gela",
    "quebrado",
    "assistencia",
    "assistência",
    "suporte",
}


EQUIPMENT_QUESTIONS = {
    "BLOCO_EQ_FRITADEIRA_Q1": ("O que você quer preparar?", ["Batata", "Salgados", "Frango", "Porções", "Ainda não sei"], "BLOCO_EQ_FRITADEIRA_Q2", "pergunta_1"),
    "BLOCO_EQ_FRITADEIRA_Q2": ("O uso será como?", ["Pouco uso", "Uso médio", "Uso alto", "Ainda não sei"], "BLOCO_EQ_FRITADEIRA_Q3", "pergunta_2"),
    "BLOCO_EQ_FRITADEIRA_Q3": ("Prefere qual modelo?", ["A gás", "Elétrica", "Quero ajuda"], "BLOCO_COLETA_NOME", "pergunta_3"),
    "BLOCO_EQ_FREEZER_Q1": ("Qual é a necessidade?", ["Refrigerar", "Congelar", "Expor produtos", "Armazenar", "Ainda não sei"], "BLOCO_EQ_FREEZER_Q2", "pergunta_1"),
    "BLOCO_EQ_FREEZER_Q2": ("O que vai guardar?", ["Bebidas", "Carnes", "Laticínios", "Congelados", "Outros"], "BLOCO_EQ_FREEZER_Q3", "pergunta_2"),
    "BLOCO_EQ_FREEZER_Q3": ("Já sabe o tamanho?", ["Pequeno", "Médio", "Grande", "Tenho medidas", "Não sei"], "BLOCO_COLETA_NOME", "pergunta_3"),
    "BLOCO_EQ_FORNO_Q1": ("O que você vai assar?", ["Pães", "Pizzas", "Bolos", "Salgados", "Assados", "Variados"], "BLOCO_EQ_FORNO_Q2", "pergunta_1"),
    "BLOCO_EQ_FORNO_Q2": ("Prefere algum tipo?", ["A gás", "Elétrico", "Pizza", "Combinado", "Quero ajuda"], "BLOCO_EQ_FORNO_Q3", "pergunta_2"),
    "BLOCO_EQ_FORNO_Q3": ("O uso será como?", ["Pouco uso", "Uso médio", "Uso alto", "Ainda não sei"], "BLOCO_COLETA_NOME", "pergunta_3"),
    "BLOCO_EQ_FOGAO_Q1": ("Quantas bocas precisa?", ["2", "4", "6", "8 ou mais", "Ainda não sei"], "BLOCO_EQ_FOGAO_Q2", "pergunta_1"),
    "BLOCO_EQ_FOGAO_Q2": ("Onde será usado?", ["Restaurante", "Lanchonete", "Cozinha industrial", "Buffet", "Outro"], "BLOCO_EQ_FOGAO_Q3", "pergunta_2"),
    "BLOCO_EQ_FOGAO_Q3": ("Já tem ponto de gás?", ["Sim", "Não", "Em preparação", "Não sei"], "BLOCO_COLETA_NOME", "pergunta_3"),
    "BLOCO_EQ_CHAPA_Q1": ("O que você vai preparar?", ["Hambúrguer", "Lanches", "Carnes", "Porções", "Variados"], "BLOCO_EQ_CHAPA_Q2", "pergunta_1"),
    "BLOCO_EQ_CHAPA_Q2": ("Já sabe o tamanho?", ["Pequena", "Média", "Grande", "Tenho medidas", "Não sei"], "BLOCO_EQ_CHAPA_Q3", "pergunta_2"),
    "BLOCO_EQ_CHAPA_Q3": ("Prefere qual modelo?", ["A gás", "Elétrica", "Quero ajuda"], "BLOCO_COLETA_NOME", "pergunta_3"),
    "BLOCO_EQ_OUTRO_Q1": ("Qual equipamento você procura?", ["Vou digitar", "Não sei o nome", "Tenho foto", "Quero ajuda"], "BLOCO_EQ_OUTRO_Q2", "pergunta_1"),
    "BLOCO_EQ_OUTRO_Q2": ("Para que ele será usado?", ["Preparar", "Refrigerar", "Expor", "Lavar", "Organizar", "Outro"], "BLOCO_EQ_OUTRO_Q3", "pergunta_2"),
    "BLOCO_EQ_OUTRO_Q3": ("Qual é o seu tipo de negócio?", ["Restaurante", "Lanchonete", "Padaria", "Mercado", "Cozinha industrial", "Outro"], "BLOCO_COLETA_NOME", "pergunta_3"),
}


ANSWER_LABELS = {
    "pergunta_1": "Resposta 1",
    "pergunta_2": "Resposta 2",
    "pergunta_3": "Resposta 3",
    "pedido_sensivel": "Pedido sensível",
    "projeto_status": "Status do projeto",
    "ja_comprou_ssvale": "Já comprou com a SS Vale",
    "assunto_pos_venda": "Assunto de pós-venda",
    "empresa_fornecedor": "Empresa",
    "tipo_contato_fornecedor": "Tipo de contato",
}


EQUIPMENT_ANSWER_LABELS = {
    "Fritadeira": {
        "pergunta_1": "Preparo desejado",
        "pergunta_2": "Volume de uso",
        "pergunta_3": "Modelo preferido",
    },
    "Freezer / Refrigeração": {
        "pergunta_1": "Necessidade",
        "pergunta_2": "Produto armazenado",
        "pergunta_3": "Tamanho desejado",
    },
    "Forno": {
        "pergunta_1": "Preparo desejado",
        "pergunta_2": "Tipo de forno",
        "pergunta_3": "Volume de uso",
    },
    "Fogão Industrial": {
        "pergunta_1": "Quantidade de bocas",
        "pergunta_2": "Local de uso",
        "pergunta_3": "Ponto de gás",
    },
    "Chapa": {
        "pergunta_1": "Preparo desejado",
        "pergunta_2": "Tamanho desejado",
        "pergunta_3": "Modelo preferido",
    },
    "Outro equipamento": {
        "pergunta_1": "Identificação do equipamento",
        "pergunta_2": "Uso desejado",
        "pergunta_3": "Tipo de negócio",
    },
}


class SofiaFlow:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def start(self, state: ConversationState) -> BotReply:
        state.tags.add("mvp_chatbot")
        state.current_block = "BLOCO_01_MENU_INICIAL"
        return BotReply(
            message=(
                "Olá! Eu sou a Sofia, assistente virtual da SS Vale. Vou te ajudar a encontrar o melhor caminho para o seu atendimento.\n\n"
                "Como posso te ajudar hoje?"
            ),
            options=MENU_OPTIONS,
            next_block=state.current_block,
            tags=sorted(state.tags),
        )

    def handle(self, state: ConversationState, user_message: str) -> BotReply:
        text = user_message.strip()

        if state.status == ConversationStatus.HANDOFF:
            return BotReply(
                message="Seu atendimento já foi encaminhado. A equipe da SS Vale continua com você por aqui.",
                next_block=state.current_block,
                status=ConversationStatus.HANDOFF,
                summary=self._summary(state),
                tags=sorted(state.tags),
            )

        if state.current_block == "BLOCO_00_BOAS_VINDAS":
            greeting = self.start(state)
            if not text or _GREETING_REGEX.match(normalize_for_matching(text)):
                return greeting
            routed = self.handle(state, text)
            return BotReply(
                message=f"{greeting.message}\n\n{routed.message}",
                options=routed.options,
                next_block=routed.next_block,
                status=routed.status,
                summary=routed.summary,
                tags=routed.tags,
            )

        contextual_delivery = (
            state.current_block in EQUIPMENT_QUESTIONS
            or state.current_block == "BLOCO_03_PROJETO_COZINHA"
        )
        if contains_sensitive_commercial_request(text, contextual_delivery=contextual_delivery):
            state.tags.add("bloqueio_comercial")
            state.lead.respostas["pedido_sensivel"] = text
            prompt = self._next_collection_prompt(state)
            return BotReply(
                message=commercial_limit_message() + f"\n\n{prompt}",
                next_block=state.current_block,
                tags=sorted(state.tags),
            )

        if state.current_block == "BLOCO_01_MENU_INICIAL":
            return self._handle_main_menu(state, text)
        if state.current_block == "BLOCO_02_EQUIPAMENTO_ESPECIFICO":
            return self._handle_equipment_menu(state, text)
        if state.current_block in EQUIPMENT_QUESTIONS:
            return self._handle_equipment_question(state, text)
        if state.current_block == "BLOCO_03_PROJETO_COZINHA":
            return self._project_kitchen(state, text)
        if state.current_block == "BLOCO_04_SUPORTE_POS_VENDA":
            return self._support(state, text)
        if state.current_block == "BLOCO_05_FORNECEDOR_REPRESENTANTE":
            return self._supplier(state, text)
        if state.current_block == "BLOCO_06_CONSULTOR_DIRETO":
            state.lead.motivo_contato = text
            state.current_block = "BLOCO_COLETA_NOME"
            return BotReply(message="Qual é o seu nome?", next_block=state.current_block, tags=sorted(state.tags))
        if state.current_block.startswith("BLOCO_COLETA_"):
            return self._collect_lead_data(state, text)

        state.current_block = "BLOCO_01_MENU_INICIAL"
        return self._not_understood(state)

    def resolve_numbered_input(self, state: ConversationState, text: str) -> str:
        """Converte uma escolha numerada na opcao exibida no estado atual.

        O Maxbot envia apenas texto. Esta conversao fica explicita no canal e
        nao interfere em campos livres como nome, telefone e cidade.
        """
        stripped = text.strip()
        if not stripped.isdigit():
            return text

        options = self._options_for_state(state)
        index = int(stripped) - 1
        if 0 <= index < len(options):
            return options[index]
        return text

    @staticmethod
    def _options_for_state(state: ConversationState) -> list[str]:
        if state.current_block == "BLOCO_01_MENU_INICIAL":
            return MENU_OPTIONS
        if state.current_block == "BLOCO_02_EQUIPAMENTO_ESPECIFICO":
            return list(EQUIPMENT_BLOCKS)
        if state.current_block in EQUIPMENT_QUESTIONS:
            return EQUIPMENT_QUESTIONS[state.current_block][1]
        if state.current_block == "BLOCO_03_PROJETO_COZINHA":
            if "projeto_status" not in state.lead.respostas:
                return ["Montando", "Reformando", "Ampliando", "Ainda estou planejando"]
            if not state.lead.tipo_negocio:
                return ["Restaurante", "Lanchonete", "Padaria", "Mercado", "Cozinha industrial", "Outro"]
            return ["Agora", "Em até 30 dias", "Em 1 a 3 meses", "Ainda estou pesquisando"]
        if state.current_block == "BLOCO_04_SUPORTE_POS_VENDA":
            if "ja_comprou_ssvale" not in state.lead.respostas:
                return ["Sim", "Não", "Não sei informar"]
            if "compras_online" in state.tags and "assunto_pos_venda" not in state.lead.respostas:
                return ["Pedido já feito", "Entrega", "Troca", "Outro"]
            return ["Garantia", "Instalação", "Manutenção", "Troca", "Pedido já feito", "Outro"]
        if (
            state.current_block == "BLOCO_05_FORNECEDOR_REPRESENTANTE"
            and "empresa_fornecedor" in state.lead.respostas
        ):
            return ["Fornecedor", "Representante", "Parceria", "Outro"]
        return []

    def _handle_main_menu(self, state: ConversationState, text: str) -> BotReply:
        normalized = text.lower()
        state.tags.add("menu_inicial_mvp")

        if normalized in {"comecar", "começar", "inicio", "início", "menu"}:
            state.current_block = "BLOCO_01_MENU_INICIAL"
            return BotReply("Como posso te ajudar hoje?", MENU_OPTIONS, state.current_block, tags=sorted(state.tags))

        if normalized in MENU_NUMBER_ALIASES:
            normalized = MENU_NUMBER_ALIASES[normalized].lower()

        normalized_matching = normalize_for_matching(normalized)
        if "site" in normalized_matching and re.search(
            r"\b(comprei|compra|pedido)\b", normalized_matching
        ):
            state.lead.motivo_contato = "Compra pelo site"
            state.tags.add("pos_venda")
            state.tags.add("compras_online")
            state.lead.respostas["ja_comprou_ssvale"] = "Sim - pelo site"
            state.current_block = "BLOCO_04_SUPORTE_POS_VENDA"
            return BotReply(
                support_limit_message()
                + "\n\nSobre qual assunto você precisa de ajuda?",
                ["Pedido já feito", "Entrega", "Troca", "Outro"],
                state.current_block,
                tags=sorted(state.tags),
            )

        if self._contains_support_alias(normalized):
            state.lead.motivo_contato = "Suporte / Pós-venda"
            state.tags.add("pos_venda")
            state.current_block = "BLOCO_04_SUPORTE_POS_VENDA"
            return BotReply(support_limit_message() + "\n\nVocê já comprou com a SS Vale?", ["Sim", "Não", "Não sei informar"], state.current_block, tags=sorted(state.tags))

        direct_equipment = self._match_equipment_alias(normalized)
        if direct_equipment:
            return self._route_to_equipment(state, direct_equipment)

        if "equipamento" in normalized:
            state.lead.motivo_contato = "Equipamento específico"
            state.tags.add("equipamento_especifico")
            state.current_block = "BLOCO_02_EQUIPAMENTO_ESPECIFICO"
            return BotReply("Qual equipamento você procura?", list(EQUIPMENT_BLOCKS), state.current_block, tags=sorted(state.tags))
        if "cozinha" in normalized or "reformar" in normalized or "montar" in normalized:
            state.lead.motivo_contato = "Projeto de cozinha"
            state.tags.add("projeto_cozinha")
            state.current_block = "BLOCO_03_PROJETO_COZINHA"
            return BotReply("Você está montando, reformando ou ampliando uma cozinha?", ["Montando", "Reformando", "Ampliando", "Ainda estou planejando"], state.current_block, tags=sorted(state.tags))
        if _POS_VENDA_REGEX.search(normalize_for_matching(normalized)):
            state.lead.motivo_contato = "Suporte / Pós-venda"
            state.tags.add("pos_venda")
            state.current_block = "BLOCO_04_SUPORTE_POS_VENDA"
            return BotReply(support_limit_message() + "\n\nVocê já comprou com a SS Vale?", ["Sim", "Não", "Não sei informar"], state.current_block, tags=sorted(state.tags))
        if "fornecedor" in normalized or "representante" in normalized:
            state.lead.motivo_contato = "Fornecedor / Representante"
            state.tags.add("fornecedor_representante")
            state.current_block = "BLOCO_05_FORNECEDOR_REPRESENTANTE"
            return BotReply("Você fala em nome de qual empresa?", next_block=state.current_block, tags=sorted(state.tags))
        if "consultor" in normalized:
            state.tags.add("consultor_direto")
            state.current_block = "BLOCO_06_CONSULTOR_DIRETO"
            return BotReply("Claro. Para chamar um consultor, me diga rapidamente o que você precisa.", next_block=state.current_block, tags=sorted(state.tags))

        intent = self._classify(text)
        if intent == "equipamento_especifico":
            state.lead.motivo_contato = "Equipamento específico"
            state.tags.add("equipamento_especifico")
            state.current_block = "BLOCO_02_EQUIPAMENTO_ESPECIFICO"
            return BotReply("Qual equipamento você procura?", list(EQUIPMENT_BLOCKS), state.current_block, tags=sorted(state.tags))
        if intent == "projeto_cozinha":
            state.lead.motivo_contato = "Projeto de cozinha"
            state.tags.add("projeto_cozinha")
            state.current_block = "BLOCO_03_PROJETO_COZINHA"
            return BotReply("Você está montando, reformando ou ampliando uma cozinha?", ["Montando", "Reformando", "Ampliando", "Ainda estou planejando"], state.current_block, tags=sorted(state.tags))
        if intent == "fornecedor_representante":
            state.lead.motivo_contato = "Fornecedor / Representante"
            state.tags.add("fornecedor_representante")
            state.current_block = "BLOCO_05_FORNECEDOR_REPRESENTANTE"
            return BotReply("Você fala em nome de qual empresa?", next_block=state.current_block, tags=sorted(state.tags))
        if intent == "suporte_pos_venda":
            state.lead.motivo_contato = "Suporte / Pós-venda"
            state.tags.add("pos_venda")
            state.current_block = "BLOCO_04_SUPORTE_POS_VENDA"
            return BotReply(support_limit_message() + "\n\nVocê já comprou com a SS Vale?", ["Sim", "Não", "Não sei informar"], state.current_block, tags=sorted(state.tags))
        if intent == "consultor_direto":
            state.tags.add("consultor_direto")
            state.current_block = "BLOCO_06_CONSULTOR_DIRETO"
            return BotReply("Claro. Para chamar um consultor, me diga rapidamente o que você precisa.", next_block=state.current_block, tags=sorted(state.tags))

        return self._not_understood(state)

    def _handle_equipment_menu(self, state: ConversationState, text: str) -> BotReply:
        text = EQUIPMENT_NUMBER_ALIASES.get(text.strip(), text)
        chosen = self._match_option(text, list(EQUIPMENT_BLOCKS))
        if not chosen:
            return self._not_understood(state)

        return self._route_to_equipment(state, chosen)

    def _route_to_equipment(self, state: ConversationState, equipment: str) -> BotReply:
        next_block, tag = EQUIPMENT_BLOCKS[equipment]
        state.lead.motivo_contato = "Equipamento específico"
        state.lead.equipamento_interesse = equipment
        state.tags.add("equipamento_especifico")
        state.tags.add(tag)
        state.current_block = next_block
        question, options, _, _ = EQUIPMENT_QUESTIONS[next_block]
        return BotReply(question, options, next_block, tags=sorted(state.tags))

    def _handle_equipment_question(self, state: ConversationState, text: str) -> BotReply:
        question, options, next_block, answer_key = EQUIPMENT_QUESTIONS[state.current_block]
        state.lead.respostas[answer_key] = text
        state.current_block = next_block

        if next_block == "BLOCO_COLETA_NOME":
            return BotReply("Qual é o seu nome?", next_block=next_block, tags=sorted(state.tags))

        next_question, next_options, _, _ = EQUIPMENT_QUESTIONS[next_block]
        return BotReply(next_question, next_options, next_block, tags=sorted(state.tags))

    def _project_kitchen(self, state: ConversationState, text: str) -> BotReply:
        answers = state.lead.respostas
        if "projeto_status" not in answers:
            answers["projeto_status"] = text
            return BotReply("Qual é o tipo de negócio?", ["Restaurante", "Lanchonete", "Padaria", "Mercado", "Cozinha industrial", "Outro"], state.current_block, tags=sorted(state.tags))
        if not state.lead.tipo_negocio:
            state.lead.tipo_negocio = text
            return BotReply("Quando pretende comprar os equipamentos?", ["Agora", "Em até 30 dias", "Em 1 a 3 meses", "Ainda estou pesquisando"], state.current_block, tags=sorted(state.tags))

        state.lead.previsao_compra = text
        state.current_block = "BLOCO_COLETA_NOME"
        return BotReply("Qual é o seu nome?", next_block=state.current_block, tags=sorted(state.tags))

    def _support(self, state: ConversationState, text: str) -> BotReply:
        answers = state.lead.respostas
        if "ja_comprou_ssvale" not in answers:
            answers["ja_comprou_ssvale"] = text
            return BotReply("Sobre qual assunto você precisa de ajuda?", ["Garantia", "Instalação", "Manutenção", "Troca", "Pedido já feito", "Outro"], state.current_block, tags=sorted(state.tags))

        answers["assunto_pos_venda"] = text
        state.current_block = "BLOCO_COLETA_NOME"
        return BotReply("Qual é o seu nome?", next_block=state.current_block, tags=sorted(state.tags))

    def _supplier(self, state: ConversationState, text: str) -> BotReply:
        answers = state.lead.respostas
        if "empresa_fornecedor" not in answers:
            answers["empresa_fornecedor"] = text
            return BotReply("Qual é o tipo de contato?", ["Fornecedor", "Representante", "Parceria", "Outro"], state.current_block, tags=sorted(state.tags))

        answers["tipo_contato_fornecedor"] = text
        state.current_block = "BLOCO_COLETA_NOME"
        return BotReply("Qual é o seu nome?", next_block=state.current_block, tags=sorted(state.tags))

    def _collect_lead_data(self, state: ConversationState, text: str) -> BotReply:
        if state.current_block == "BLOCO_COLETA_NOME":
            state.lead.nome_cliente = text
            if state.lead.telefone_whatsapp:
                state.current_block = "BLOCO_COLETA_CIDADE"
                return BotReply(
                    "Você fala de qual cidade e estado?",
                    next_block=state.current_block,
                    tags=sorted(state.tags),
                )
            state.current_block = "BLOCO_COLETA_TELEFONE"
            return BotReply("Qual é o melhor telefone ou WhatsApp para contato?", next_block=state.current_block, tags=sorted(state.tags))
        if state.current_block == "BLOCO_COLETA_TELEFONE":
            state.lead.telefone_whatsapp = text
            state.current_block = "BLOCO_COLETA_CIDADE"
            return BotReply("Você fala de qual cidade e estado?", next_block=state.current_block, tags=sorted(state.tags))

        state.lead.cidade_estado = text
        state.tags.add("lead_mvp_qualificado")
        state.tags.add("encaminhar_humano")
        destination_tag, destination_block = self._handoff_destination(state)
        state.tags.add(destination_tag)
        state.current_block = destination_block
        state.status = ConversationStatus.HANDOFF
        summary = self._summary(state)
        return BotReply(
            message="Pronto, já registrei suas informações. A equipe da SS Vale vai continuar o atendimento com você.",
            next_block=state.current_block,
            status=ConversationStatus.HANDOFF,
            summary=summary,
            tags=sorted(state.tags),
        )

    @staticmethod
    def _handoff_destination(state: ConversationState) -> tuple[str, str]:
        if "compras_online" in state.tags:
            return "encaminhar_compras_online", "BLOCO_ENCAMINHAMENTO_COMPRAS_ONLINE"
        if "pos_venda" in state.tags:
            return "encaminhar_pos_venda", "BLOCO_ENCAMINHAMENTO_POS_VENDA"
        if "fornecedor_representante" in state.tags:
            return "encaminhar_compras", "BLOCO_ENCAMINHAMENTO_COMPRAS"
        return "encaminhar_comercial", "BLOCO_ENCAMINHAMENTO_COMERCIAL"

    def _not_understood(self, state: ConversationState) -> BotReply:
        state.tags.add("resposta_nao_entendida")
        state.current_block = "BLOCO_01_MENU_INICIAL"
        return BotReply(
            "Não consegui entender. Pode escolher uma das opções do menu?",
            MENU_OPTIONS,
            state.current_block,
            tags=sorted(state.tags),
        )

    _ALLOWED_INTENTS = (
        "equipamento_especifico",
        "projeto_cozinha",
        "suporte_pos_venda",
        "fornecedor_representante",
        "consultor_direto",
        "nao_classificado",
    )

    def _classify(self, text: str) -> str:
        try:
            result = self.llm.complete(
                [
                    LLMMessage(
                        "system",
                        (
                            "Classifique a intencao do cliente. Responda apenas com uma destas categorias: "
                            "equipamento_especifico, projeto_cozinha, suporte_pos_venda, "
                            "fornecedor_representante, consultor_direto, nao_classificado."
                        ),
                    ),
                    LLMMessage("user", text),
                ]
            ).lower().strip()
        except Exception:
            # Falha do provedor (timeout, rede, contrato) nao pode derrubar o
            # fluxo: cai no caminho de "nao entendi" e o menu e reapresentado.
            return "nao_classificado"

        if result in self._ALLOWED_INTENTS:
            return result
        # Saida fora do contrato (ex.: frase inteira): busca em ordem fixa para
        # o comportamento ser deterministico.
        for intent in self._ALLOWED_INTENTS:
            if intent in result:
                return intent
        return "nao_classificado"

    @staticmethod
    def _match_option(text: str, options: list[str]) -> str | None:
        normalized = normalize_for_matching(text)
        for option in options:
            normalized_option = normalize_for_matching(option)
            if normalized == normalized_option or normalized in normalized_option:
                return option
        return None

    @staticmethod
    def _match_equipment_alias(normalized_text: str) -> str | None:
        normalized_text = normalize_for_matching(normalized_text)
        for alias, equipment in EQUIPMENT_ALIASES.items():
            if normalize_for_matching(alias) in normalized_text:
                return equipment
        return None

    @staticmethod
    def _contains_support_alias(normalized_text: str) -> bool:
        normalized_text = normalize_for_matching(normalized_text)
        return any(
            normalize_for_matching(alias) in normalized_text
            for alias in SUPPORT_ALIASES
        )

    @staticmethod
    def _next_collection_prompt(state: ConversationState) -> str:
        if not state.lead.nome_cliente:
            state.current_block = "BLOCO_COLETA_NOME"
            return "Qual é o seu nome?"
        if not state.lead.telefone_whatsapp:
            state.current_block = "BLOCO_COLETA_TELEFONE"
            return "Qual é o melhor telefone ou WhatsApp para contato?"
        if not state.lead.cidade_estado:
            state.current_block = "BLOCO_COLETA_CIDADE"
            return "Você fala de qual cidade e estado?"
        return "A equipe da SS Vale vai continuar o atendimento com você."

    @staticmethod
    def _summary(state: ConversationState) -> str:
        lead = state.lead
        destination = SofiaFlow._summary_destination(state)
        parts = [
            "Resumo do atendimento - Sofia",
            f"Destino: {destination}",
            f"Cliente: {lead.nome_cliente or '-'}",
            f"Telefone/WhatsApp: {lead.telefone_whatsapp or '-'}",
            f"Cidade/Estado: {lead.cidade_estado or '-'}",
            f"Motivo: {lead.motivo_contato or '-'}",
        ]
        if lead.equipamento_interesse:
            parts.append(f"Equipamento de interesse: {lead.equipamento_interesse}")
        if lead.tipo_negocio:
            parts.append(f"Tipo de negócio: {lead.tipo_negocio}")
        if lead.previsao_compra:
            parts.append(f"Previsão de compra: {lead.previsao_compra}")

        formatted_answers = SofiaFlow._formatted_answers(lead.equipamento_interesse, lead.respostas)
        if formatted_answers:
            parts.append("Detalhes coletados:")
            parts.extend(f"- {label}: {value}" for label, value in formatted_answers)

        parts.append(f"Tags: {', '.join(sorted(state.tags))}")
        return "\n".join(parts)

    @staticmethod
    def _summary_destination(state: ConversationState) -> str:
        if "encaminhar_compras_online" in state.tags or "compras_online" in state.tags:
            return "Compras Online"
        if "encaminhar_pos_venda" in state.tags or "pos_venda" in state.tags:
            return "Pós-venda"
        if "encaminhar_compras" in state.tags or "fornecedor_representante" in state.tags:
            return "Compras"
        return "Comercial"

    @staticmethod
    def _formatted_answers(equipment: str | None, answers: dict) -> list[tuple[str, object]]:
        labels = EQUIPMENT_ANSWER_LABELS.get(equipment or "", {})
        formatted: list[tuple[str, object]] = []
        for key, value in answers.items():
            label = labels.get(key) or ANSWER_LABELS.get(key) or key
            formatted.append((label, value))
        return formatted
