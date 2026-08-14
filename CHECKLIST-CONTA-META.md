# Checklist para criar a conta Meta da SS Vale

Atualizado em 28/07/2026.

Este roteiro foi escrito para a pessoa responsavel pela empresa. Ele nao exige
conhecimento tecnico. Os nomes das telas podem mudar levemente conforme a Meta
atualiza o Business Suite.

## Antes de comecar

Definir uma pessoa da SS Vale como responsavel principal. A conta deve ficar sob
controle da empresa, e nao de fornecedor, agencia ou desenvolvedor.

Separar:

- razao social e nome fantasia;
- CNPJ;
- endereco completo e telefone comercial;
- site e e-mail com dominio da empresa, se disponiveis;
- documento empresarial oficial, legivel, colorido e sem alteracoes;
- documento do representante legal, caso seja solicitado;
- um segundo responsavel interno para recuperacao de acesso;
- celular dos responsaveis para autenticacao em duas etapas;
- numero que futuramente sera usado no WhatsApp.

Os dados digitados devem coincidir com os documentos oficiais. Divergencias de
nome, endereco ou telefone podem atrasar a verificacao.

## Fase 1 - Responsaveis e seguranca

- [ ] Escolher o administrador principal da SS Vale.
- [ ] Escolher um segundo administrador interno.
- [ ] Confirmar que cada pessoa usa seu proprio perfil autentico.
- [ ] Ativar autenticacao em duas etapas nos dois acessos.
- [ ] Guardar codigos de recuperacao em local corporativo seguro.
- [ ] Nao compartilhar senhas por e-mail, WhatsApp ou com fornecedores.
- [ ] Registrar quem possui controle total e revisar os acessos periodicamente.

Controle total permite alterar acessos e configuracoes importantes. Por isso,
deve ser concedido somente a pessoas de confianca da empresa.

## Fase 2 - Estrutura empresarial

- [ ] Acessar o Meta Business Suite pelo computador.
- [ ] Criar um Portfolio Empresarial em nome da SS Vale.
- [ ] Informar os dados empresariais exatamente como constam no CNPJ.
- [ ] Adicionar a Pagina oficial da empresa, caso ja exista.
- [ ] Adicionar o segundo administrador interno.
- [ ] Conferir se a SS Vale aparece como proprietaria dos ativos.
- [ ] Iniciar a verificacao empresarial quando a opcao estiver disponivel.
- [ ] Enviar somente documentos oficiais, completos, validos e legiveis.
- [ ] Guardar a confirmacao e o identificador do Portfolio Empresarial.

A verificacao empresarial nao deve ser confundida com a assinatura paga Meta
Verified. A necessidade e o caminho exibido podem variar conforme os recursos
que a Meta liberar para a conta.

## Fase 3 - Preparacao do numero

- [ ] Decidir se sera usado um numero novo ou o numero atual.
- [ ] Confirmar que a empresa controla o chip, SMS ou chamada desse numero.
- [ ] Identificar se o numero esta atualmente vinculado ao Maxbot.
- [ ] Solicitar ao Maxbot, por escrito, as regras e o prazo para liberar ou
  migrar o numero.
- [ ] Nao cancelar o Maxbot antes do teste completo na Meta.
- [ ] Nao tentar cadastrar o numero oficial na Cloud API sem um plano de
  migracao e retorno.
- [ ] Preferir inicialmente o numero de teste fornecido no processo da Meta.

O numero oficial pode exigir liberacao ou migracao. Fazer essa etapa sem
coordenacao pode interromper o atendimento atual.

## Fase 4 - WhatsApp Business Platform

Esta fase deve ser feita com apoio tecnico depois que o Portfolio Empresarial
estiver criado.

- [ ] Criar ou vincular a conta do WhatsApp Business (WABA).
- [ ] Criar o aplicativo empresarial no ambiente de desenvolvedores da Meta.
- [ ] Adicionar o produto WhatsApp ao aplicativo.
- [ ] Comecar com o numero de teste.
- [ ] Registrar o ID da WABA e o Phone Number ID.
- [ ] Gerar as credenciais de homologacao.
- [ ] Configurar o webhook da Sofia.
- [ ] Validar a assinatura e o token do webhook.
- [ ] Manter os endpoints locais e de depuracao desativados na internet.
- [ ] Testar recebimento e envio antes de considerar o numero oficial.

Credenciais, tokens e segredos nao devem ser colocados em documentos, capturas
de tela, mensagens ou arquivos versionados.

## Fase 5 - Homologacao

- [ ] Testar saudacao, menus, texto livre, botoes e listas.
- [ ] Testar pedidos de preco, frete, prazo, estoque e pagamento.
- [ ] Testar comercial, suporte, fornecedor e representante.
- [ ] Confirmar o resumo enviado ao atendente humano.
- [ ] Definir quem assume a conversa depois do encaminhamento.
- [ ] Definir quando a Sofia pode voltar a atender o mesmo numero.
- [ ] Validar logs, privacidade e politica de retencao de dados.
- [ ] Manter um responsavel acompanhando o teste.
- [ ] Documentar como pausar imediatamente os envios.
- [ ] Registrar o aceite da area comercial.

## Fase 6 - Migracao do numero oficial

Executar somente depois da homologacao.

- [ ] Escolher data e horario de menor movimento.
- [ ] Avisar atendimento, vendas e suporte.
- [ ] Fazer copia das configuracoes relevantes do Maxbot.
- [ ] Confirmar previamente o procedimento de liberacao do numero.
- [ ] Confirmar um plano de retorno em caso de falha.
- [ ] Migrar o numero com os responsaveis tecnico e comercial presentes.
- [ ] Fazer testes de entrada, resposta e handoff.
- [ ] Monitorar intensamente as primeiras conversas.
- [ ] Desativar o Maxbot somente depois do aceite formal.

## Informacoes que a SS Vale entregara ao time tecnico

Nao incluir valores secretos neste checklist. Entregar por um meio corporativo
seguro:

- identificador do Portfolio Empresarial;
- identificador da WABA;
- Phone Number ID do numero de teste;
- confirmacao de quem administra a conta;
- decisao sobre o numero oficial;
- destino do atendimento humano;
- confirmacao da politica de dados.

## Links oficiais da Meta

- Meta Business Suite: https://business.facebook.com/
- Documentos empresariais aceitos:
  https://www.facebook.com/help/243868559497297/
- Autenticacao em duas etapas:
  https://www.facebook.com/help/148233965247823/
- Niveis de acesso e controle:
  https://www.facebook.com/help/289207354498410/
- Conexao entre Pagina e WhatsApp:
  https://www.facebook.com/help/2783732558314697/

## Ponto de parada atual

Enquanto a SS Vale nao criar o Portfolio Empresarial, o chatbot continua:

- operacional no Maxbot;
- testavel localmente no simulador da Meta;
- com envio real da Cloud API desativado.

Nenhuma migracao do numero deve ocorrer nesta fase.
