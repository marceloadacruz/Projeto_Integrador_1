import uuid
from unittest.mock import patch, MagicMock
from datetime import date, timedelta, time as dt_time

from django.test import TestCase

from Agendamento.models import Customer, Appointment
from .engine import processar_mensagem, get_conversation
from .bot_enums import Status
from .helper import conversations, MensagemBOT

MOCK_DATAS_DISPONIVEIS = [date.today() + timedelta(days=i) for i in range(1, 6)]
PATCH_ENVIAR_ENGINE = 'WhatsAppBot.engine.enviar_mensagem'
PATCH_ENVIAR_UTILS = 'WhatsAppBot.bot.utils.enviar_mensagem'
PATCH_BUSCAR_DATAS = 'Agendamento.managers.AppointmentsManager.buscar_agendamentos_disponiveis_no_periodo'
PATCH_CHECAR_USUARIO = 'Agendamento.managers.CustomerManager.checar_se_usuario_existe_por_telefone'
PATCH_BUSCAR_AGENDAMENTOS = 'Agendamento.managers.AppointmentsManager.buscar_agendamentos_por_numero_telefone'
PATCH_CHECAR_DATA_EM_USO = 'Agendamento.managers.AppointmentsManager.checar_se_data_esta_em_uso'
PATCH_MARCAR_AGENDAMENTO = 'Agendamento.managers.AppointmentsManager.marcar_agendamento'
PATCH_CANCELAR_AGENDAMENTO = 'Agendamento.managers.AppointmentsManager.cancelar_agendamento'
PATCH_BUSCAR_USUARIO_POR_TELEFONE = 'Agendamento.managers.CustomerManager.buscar_usuario_por_telefone'


class StateMachineIntegrationTest(TestCase):
    """
    Test case for testing the integration and state transitions of a StateMachine within
    a chatbot system. This test suite ensures that various workflows, including user
    authentication, scheduling, cancellation, address handling, and state transitions,
    function correctly.

    The tests involve simulated conversation flows with a mocked backend, including dependencies
    for user data, appointment data, and external integrations. Each test validates the
    state transitions and expected interactions with external systems, such as notifications.

    :ivar usuario_telefone: Phone number of the user participating in the chatbot conversation.
    :type usuario_telefone: str
    :ivar nome_usuario: Display name of the user.
    :type nome_usuario: str
    :ivar bot_telefone: Phone number of the bot used for communication.
    :type bot_telefone: str
    :ivar email: Unique email address generated for test purposes.
    :type email: str
    :ivar customer: Customer instance representing the user stored in the database for interaction validation.
    :type customer: Customer
    """
    def setUp(self):
        conversations.clear()
        self.usuario_telefone = "+5511999999999"
        self.nome_usuario = "Test User"
        self.bot_telefone = "+5511888888888"

        unique_id = uuid.uuid4()
        self.email = f"test_{unique_id}@example.com"

        self.customer = Customer.objects.create(
            name="Fulano de Tal",
            email=self.email,
            phone=self.usuario_telefone,
        )

    def clear(self):
        conversations.clear()

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_usuario_existente_deve_marcar_agendamento(self, mock_enviar, _mock_enviar_utils):
        # 1 - Initial state
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.AGUARDANDO_OPCAO_MENU)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.MENU_PRINCIPAL,
            self.bot_telefone
        )

        # 2 - Choose option 1 (Agendar)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.DEFININDO_DATA)

        # 3 - Choose a date (option 1) — mock availability check
        with patch(PATCH_CHECAR_DATA_EM_USO, return_value=False):
            processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.LOCAL_ATENDIMENTO)

        # 4 - Choose local (option 2 - Salao)
        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.CONFIRMANDO_AGENDAMENTO)

        # 5 - Confirm the appointment (real DB call to create appointment)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_any_call(
            self.usuario_telefone,
            MensagemBOT.AGENDAMENTO_CONFIRMADO,
            self.bot_telefone
        )

        # Verify the appointment was actually created in the DB
        appointment = Appointment.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.status, 'scheduled')
        self.assertEqual(appointment.date, MOCK_DATAS_DISPONIVEIS[0])



    @patch(PATCH_ENVIAR_ENGINE)
    def test_usuario_recusa_criar_conta(self, mock_enviar):
        Customer.objects.all().delete()

        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS) as mock_buscar_datas:
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("Novo Usuario", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.SOLICITACAO_PARA_CRIAR_CONTA)

        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.INICIAL)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.SAIR,
            self.bot_telefone
        )

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_agendamento_a_domicilio_com_endereco(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("João Silva", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.LOCAL_ATENDIMENTO)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.AGUARDANDO_ENDERECO)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.INFORMAR_ENDERECO,
            self.bot_telefone
        )

        endereco = "Rua Teste, 123, Apto 45, CEP: 12345-678, Bairro Centro"
        processar_mensagem(endereco, self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CONFIRMANDO_AGENDAMENTO)
        self.assertEqual(conv.data["agendamento"].local_atendimento, endereco)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.IDLE)

        appointment = Appointment.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(appointment)

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_cancelar_agendamento_com_sucesso(self, mock_enviar, _mock_enviar_utils):
        app1 = Appointment.objects.create(
            customer=self.customer,
            date=date.today() + timedelta(days=5),
            time=dt_time(10, 0),
            status="scheduled"
        )

        app2 = Appointment.objects.create(
            customer=self.customer,
            date=date.today() + timedelta(days=6),
            time=dt_time(14, 0),
            status="scheduled"
        )

        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("Maria Santos", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CANCELAMENTO)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.CONFIRMANDO_CANCELAMENTO)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_any_call(
            self.usuario_telefone,
            MensagemBOT.CANCELAMENTO_CONFIRMADO,
            self.bot_telefone
        )

        app1.refresh_from_db()
        self.assertEqual(app1.status, 'cancelled')

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_abortar_cancelamento(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Pedro Costa", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        mock_agendamentos = [
            MagicMock(
                date=date(2026, 4, 5),
                time="10:00",
                location="Rua Nelson Tigrão, 15, Vila Missionária, CEP: 04430-165"
            )
        ]

        with patch(PATCH_BUSCAR_AGENDAMENTOS, return_value=mock_agendamentos):
            processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CONFIRMANDO_CANCELAMENTO)

        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_any_call(
            self.usuario_telefone,
            MensagemBOT.CANCELAMENTO_ABORTADO,
            self.bot_telefone
        )

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_consultar_agendamentos_com_sucesso(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Ana Lima", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        mock_agendamentos = [
            MagicMock(
                date=date(2026, 4, 5),
                time="10:00",
                location="Rua Nelson Tigrão, 15, Vila Missionária, CEP: 04430-165"
            ),
            MagicMock(
                date=date(2026, 4, 15),
                time="10:00",
                location="Rua Nelson Tigrão, 15, Vila Missionária, CEP: 04430-165"
            )
        ]

        with patch(PATCH_BUSCAR_AGENDAMENTOS, return_value=mock_agendamentos):
            processar_mensagem("3", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.IDLE)

    @patch(PATCH_ENVIAR_ENGINE)
    @patch(PATCH_ENVIAR_UTILS)
    def test_consultar_sem_agendamentos(self, mock_enviar, mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Carlos Souza", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_BUSCAR_AGENDAMENTOS, return_value=[]):
            processar_mensagem("3", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        mock_enviar.assert_any_call(
            self.usuario_telefone,
            MensagemBOT.SEM_AGENDAMENTOS,
            self.bot_telefone
        )

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_validacao_nome_invalido(self, mock_enviar, _mock_enviar_utils):
        novo_usuario: str = "+551122222222"

        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, novo_usuario, self.nome_usuario)

        processar_mensagem("123", self.bot_telefone, novo_usuario, self.nome_usuario)

        conv = get_conversation(novo_usuario)
        self.assertEqual(conv.state, Status.VALIDANDO_USUARIO)
        mock_enviar.assert_any_call(
            novo_usuario,
            MensagemBOT.NOME_NAO_INFORMADO,
            self.bot_telefone
        )

        processar_mensagem("", self.bot_telefone, novo_usuario, self.nome_usuario)
        conv = get_conversation(novo_usuario)
        self.assertEqual(conv.state, Status.VALIDANDO_USUARIO)

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_opcao_invalida_no_menu_principal(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Usuario Teste", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("99", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.OPCAO_INVALIDA,
            self.bot_telefone
        )

        processar_mensagem("abc", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.OPCAO_INVALIDA,
            self.bot_telefone
        )

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_abortar_agendamento_na_confirmacao(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Teste Abortar", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_DATA_EM_USO, return_value=False):
            processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CONFIRMANDO_AGENDAMENTO)

        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_any_call(
            self.usuario_telefone,
            MensagemBOT.CANCELAMENTO_CONFIRMADO,
            self.bot_telefone
        )

    @patch(PATCH_ENVIAR_ENGINE)
    @patch(PATCH_ENVIAR_UTILS)
    def test_sair_do_menu_principal(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Usuario Sair", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("4", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.SAIR)
        self.assertEqual(len(conv.data), 0)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.SAIR,
            self.bot_telefone
        )

    @patch(PATCH_ENVIAR_UTILS)
    @patch(PATCH_ENVIAR_ENGINE)
    def test_selecao_data_invalida(self, mock_enviar, _mock_enviar_utils):
        with patch(PATCH_BUSCAR_DATAS, return_value=MOCK_DATAS_DISPONIVEIS):
            processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch(PATCH_CHECAR_USUARIO, return_value=True):
            processar_mensagem("Usuario Teste", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.DEFININDO_DATA)

        processar_mensagem("99", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.DEFININDO_DATA)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.OPCAO_INVALIDA,
            self.bot_telefone
        )