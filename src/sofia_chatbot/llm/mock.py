from sofia_chatbot.llm.base import LLMClient, LLMMessage


class MockLLMClient(LLMClient):
    def complete(self, messages: list[LLMMessage]) -> str:
        last_message = messages[-1].content.lower() if messages else ""

        if any(term in last_message for term in ["preco", "preço", "valor", "frete", "pagamento", "orcamento", "orçamento"]):
            return "pedido_comercial_sensivel"
        if any(term in last_message for term in ["suporte", "garantia", "defeito", "manutencao", "manutenção"]):
            return "suporte_pos_venda"
        if any(term in last_message for term in ["fritadeira", "freezer", "refrigeracao", "refrigeração", "forno", "fogao", "fogão", "chapa", "equipamento"]):
            return "equipamento_especifico"
        if any(term in last_message for term in ["cozinha", "montar", "reformar", "ampliar"]):
            return "projeto_cozinha"
        if any(term in last_message for term in ["fornecedor", "representante", "parceria"]):
            return "fornecedor_representante"
        if any(term in last_message for term in ["consultor", "atendente", "humano"]):
            return "consultor_direto"
        return "nao_classificado"
