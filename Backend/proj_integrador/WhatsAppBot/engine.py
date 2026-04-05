from .bot.dtos import UsuarioContextoDTO, AgendamentoDTO
from .helper import MensagemBOT, Conversation, conversations
from .enum import Status, LocalAtendimento
from .mocks import buscarAgendamentosDisponiveisNoPeriodoMock, checarSeUsuarioExistePorTelefoneMock, buscarAgendamentosPorTelefoneMock
from .send_message import enviar_mensagem

def processar_mensagem(mensagem_do_usuario: str, bot_telefone: str, usuario_telefone: str, nome_usuario: str):
    conv = get_conversation(usuario_telefone)

    #TODO: substituir mocks por metodos com acesso ao banco
    endereco_padrao: str = "Rua Nelson Tigrão, 15, Vila Missionária, CEP: 04430-165"

    if conv.state == Status.IDLE and not conv.data:
        agendamentos = buscarAgendamentosDisponiveisNoPeriodoMock(20)
        conv.state = Status.INICIAL
        conv.data = {
            "usuario": UsuarioContextoDTO(wa_id=usuario_telefone, nome=nome_usuario),
            "agendamento": AgendamentoDTO(usuario_wa_id=usuario_telefone, datas_disponiveis=agendamentos),
            "LocalAtendimento": LocalAtendimento.SALAO
        }

    match conv.state:
        case Status.INICIAL:
            gerenciar_status_inicial(usuario_telefone, bot_telefone)

        case Status.VALIDANDO_USUARIO:
            gerenciar_validacao_usuario(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.SOLICITACAO_PARA_CRIAR_CONTA:
            gerenciar_solicitacao_para_criar_conta(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.AGUARDANDO_OPCAO_MENU:
            gerenciar_menu_principal(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.DEFININDO_DATA:
            gerenciar_escolha_data(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.LOCAL_ATENDIMENTO:
            gerenciar_local_atendimento(usuario_telefone, bot_telefone, mensagem_do_usuario, endereco_padrao)

        case Status.AGUARDANDO_ENDERECO:
            gerenciar_endereco(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.CONFIRMANDO_AGENDAMENTO:
            gerenciar_confirmacao_agendamento(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.CANCELAMENTO:
            gerenciar_cancelamento(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.CONFIRMANDO_CANCELAMENTO:
            gerenciar_confirmar_cancelamento(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.IDLE:
            enviar_mensagem(usuario_telefone, MensagemBOT.IDLE, bot_telefone)
            gerenciar_menu_principal(usuario_telefone, bot_telefone, mensagem_do_usuario)

        case Status.SAIR:
            reset_conversation(usuario_telefone)


def gerenciar_status_inicial(usuario_telefone: str, bot_telefone: str) -> None:
    enviar_mensagem(usuario_telefone, MensagemBOT.BOAS_VINDAS, bot_telefone)
    set_state(usuario_telefone, Status.VALIDANDO_USUARIO)


def gerenciar_validacao_usuario(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    mensagem = mensagem_do_usuario.strip()

    if not mensagem or mensagem.isdigit() or len(mensagem) < 2:
        enviar_mensagem(usuario_telefone, MensagemBOT.NOME_NAO_INFORMADO, bot_telefone)
        return

    conv = get_conversation(usuario_telefone)
    conv.data["usuario"].nome = mensagem_do_usuario

    usuario_existe: bool = checarSeUsuarioExistePorTelefoneMock(mensagem_do_usuario)

    if usuario_existe:
        enviar_mensagem(usuario_telefone, MensagemBOT.MENU_PRINCIPAL, bot_telefone)
        set_state(usuario_telefone, Status.AGUARDANDO_OPCAO_MENU)

    else:
        enviar_mensagem(usuario_telefone, MensagemBOT.NUMERO_NAO_CADASTRADO, bot_telefone)
        set_state(usuario_telefone, Status.SOLICITACAO_PARA_CRIAR_CONTA)


def gerenciar_solicitacao_para_criar_conta(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    if not mensagem_do_usuario.isdigit():
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    if mensagem_do_usuario == "1":
        enviar_mensagem(usuario_telefone, MensagemBOT.MENU_PRINCIPAL, bot_telefone)
        set_state(usuario_telefone, Status.AGUARDANDO_OPCAO_MENU)

    elif mensagem_do_usuario == "2":
        enviar_mensagem(usuario_telefone, MensagemBOT.SAIR, bot_telefone)
        set_state(usuario_telefone, Status.INICIAL)

    else:
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)


def gerenciar_menu_principal(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    if not mensagem_do_usuario.isdigit():
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    conv = get_conversation(usuario_telefone)

    if mensagem_do_usuario == "1": # Agendar
        agendamentos = conv.data["agendamento"].datas_disponiveis
        datas_disponiveis = MensagemBOT.informarDatasDisponiveis(agendamentos)
        enviar_mensagem(usuario_telefone, datas_disponiveis, bot_telefone)
        set_state(usuario_telefone, Status.DEFININDO_DATA)

    elif mensagem_do_usuario == "2": # Consultar
        agendamentos_do_usuario = buscarAgendamentosPorTelefoneMock(mensagem_do_usuario)

        if not agendamentos_do_usuario:
            enviar_mensagem(usuario_telefone, MensagemBOT.SEM_AGENDAMENTOS, bot_telefone)
            return

        msg = MensagemBOT.selecionar_agendamento(agendamentos_do_usuario)
        enviar_mensagem(usuario_telefone, msg, bot_telefone)

        conv.data["agendamentos"] = agendamentos_do_usuario

        set_state(usuario_telefone, Status.CANCELAMENTO)

    elif mensagem_do_usuario == "3": # Cancelar
        agendamentos_do_usuario = buscarAgendamentosPorTelefoneMock(mensagem_do_usuario)
        enviar_mensagem(usuario_telefone, MensagemBOT.listar_agendamentos(agendamentos_do_usuario), bot_telefone)
        set_state(usuario_telefone, Status.IDLE)

    elif mensagem_do_usuario == "4": # Sair
        conv = get_conversation(usuario_telefone)

        conv.data.clear()
        enviar_mensagem(usuario_telefone,MensagemBOT.SAIR, bot_telefone)
        set_state(usuario_telefone, Status.IDLE)

    else:
        enviar_mensagem(usuario_telefone,MensagemBOT.OPCAO_INVALIDA, bot_telefone)


#
def gerenciar_escolha_data(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    mensagem = mensagem_do_usuario.strip()
    conv = get_conversation(usuario_telefone)
    agendamentos = conv.data["agendamento"].datas_disponiveis

    if not mensagem.isdigit():
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    indice = int(mensagem)

    if indice < 0 or indice > len(agendamentos):
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    agendamento_escolhido = agendamentos[indice - 1]

    conv = get_conversation(usuario_telefone)
    conv.data["agendamento"].data_hora = agendamento_escolhido

    enviar_mensagem(usuario_telefone, MensagemBOT.LOCAL_ATENDIMENTO, bot_telefone)
    set_state(usuario_telefone, Status.LOCAL_ATENDIMENTO)


def gerenciar_local_atendimento(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str, endereco_padrao: str) -> None:
    mensagem = mensagem_do_usuario.strip()

    if not mensagem_do_usuario.isdigit():
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    conv = get_conversation(usuario_telefone)

    if mensagem == "1":
        conv.data["local_atendimento"] = LocalAtendimento.A_DOMICILIO
        enviar_mensagem(usuario_telefone, MensagemBOT.INFORMAR_ENDERECO, bot_telefone)
        set_state(usuario_telefone, Status.AGUARDANDO_ENDERECO)

    elif mensagem == "2":
        conv.data["local_atendimento"] = LocalAtendimento.SALAO
        conv.data["endereco"] = endereco_padrao
        agendamento = conv.data["agendamento"].data_hora
        nome_usuario = conv.data["usuario"].nome

        msg = MensagemBOT.confirmar_agendamento(nome_usuario, agendamento, endereco_padrao)
        enviar_mensagem(usuario_telefone, msg, bot_telefone)
        set_state(usuario_telefone, Status.CONFIRMANDO_AGENDAMENTO)

    else:
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)

def gerenciar_endereco(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    endereco = mensagem_do_usuario.strip()

    if not endereco:
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    conv = get_conversation(usuario_telefone)
    conv.data["endereco"] = endereco
    agendamento = conv.data["agendamento"].data_hora
    nome_usuario = conv.data["usuario"].nome

    msg = MensagemBOT.confirmar_agendamento(nome_usuario, agendamento, endereco)
    enviar_mensagem(usuario_telefone, msg, bot_telefone)
    set_state(usuario_telefone, Status.CONFIRMANDO_AGENDAMENTO)


def gerenciar_confirmacao_agendamento(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    mensagem = mensagem_do_usuario.strip()

    if not mensagem.isdigit():
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    if mensagem == "1":
        enviar_mensagem(usuario_telefone, MensagemBOT.AGENDAMENTO_CONFIRMADO, bot_telefone)
        set_state(usuario_telefone, Status.IDLE)

    elif mensagem == "2":
        enviar_mensagem(usuario_telefone, MensagemBOT.CANCELAMENTO_CONFIRMADO, bot_telefone)
        set_state(usuario_telefone, Status.IDLE)

    else:
        enviar_mensagem(usuario_telefone,MensagemBOT.OPCAO_INVALIDA, bot_telefone)


def gerenciar_cancelamento(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    mensagem = mensagem_do_usuario.strip()

    if not mensagem.isdigit():
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    indice = int(mensagem)

    conv = get_conversation(usuario_telefone)
    agendamentos = conv.data.get("agendamentos", [])

    if indice < 1 or indice > len(agendamentos):
        enviar_mensagem(usuario_telefone, MensagemBOT.OPCAO_INVALIDA, bot_telefone)
        return

    agendamento = agendamentos[indice - 1]
    conv.data["agendamento_para_cancelar"] = agendamento

    msg = MensagemBOT.confirmar_cancelamento(agendamento)
    enviar_mensagem(usuario_telefone, msg, bot_telefone)
    set_state(usuario_telefone, Status.CONFIRMANDO_CANCELAMENTO)


def gerenciar_confirmar_cancelamento(usuario_telefone: str, bot_telefone: str, mensagem_do_usuario: str) -> None:
    mensagem = mensagem_do_usuario.strip().lower()

    conv = get_conversation(usuario_telefone)
    agendamento = conv.data.get("agendamento_para_cancelar")

    if mensagem == "sim":
        MensagemBOT.confirmar_cancelamento(agendamento)
        enviar_mensagem(usuario_telefone, MensagemBOT.CANCELAMENTO_CONFIRMADO, bot_telefone)
        set_state(usuario_telefone, Status.IDLE)
        #TODO: adicionar metodo para cancelar agendamento no banco

    elif mensagem == "não":
        enviar_mensagem(usuario_telefone, MensagemBOT.CANCELAMENTO_ABORTADO, bot_telefone)
        set_state(usuario_telefone, Status.IDLE)

    else:
        enviar_mensagem(usuario_telefone,MensagemBOT.OPCAO_INVALIDA, bot_telefone)

def reset_conversation(phone: str):
    conv = get_conversation(phone)
    conv.data.clear()

def get_conversation(phone: str) -> Conversation:
    if phone not in conversations:
        conversations[phone] = Conversation()
    return conversations[phone]


def set_state(phone: str, new_state: Status):
    conv = get_conversation(phone)
    conv.state = new_state
