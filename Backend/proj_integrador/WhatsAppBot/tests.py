from unittest.mock import patch, MagicMock

from django.test import TestCase

from .engine import processar_mensagem, get_conversation
from .enum import Status
from .helper import conversations, MensagemBOT


# Create your tests here.
class StateMachineIntegrationTest(TestCase):
    def setUp(self):
        conversations.clear()
        self.usuario_telefone = "+5511999999999"
        self.nome_usuario = "Test User"
        self.bot_telefone = "+5511888888888"
        self.mock_enviar = MagicMock()

    def clear(self):
        conversations.clear()

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_usuario_existente_deve_marcar_agendamento(self, mock_enviar):

        # 1 - Initial state
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.VALIDANDO_USUARIO)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.BOAS_VINDAS,
            self.bot_telefone
        )

        # 2 - Send valid Name (it's validated by name, not CPF in engine.py)
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Fulano de Tal", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.AGUARDANDO_OPCAO_MENU)

        # 3 - Choose option 1 (Agendar)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.DEFININDO_DATA)

        # 4 - Choose a date (option 1)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.LOCAL_ATENDIMENTO)

        # 5 - Choose local (option 2 - Salao)
        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.CONFIRMANDO_AGENDAMENTO)

        # 6 - Confirm the appointment
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)

        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.AGENDAMENTO_CONFIRMADO,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_usuario_recusa_criar_conta(self, mock_enviar):
        # Start conversation
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # User doesn't exist
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=False):
            processar_mensagem("Novo Usuario", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.SOLICITACAO_PARA_CRIAR_CONTA)
        
        # User declines account creation (option 2)
        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        
        self.assertEqual(conv.state, Status.INICIAL)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.SAIR,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_agendamento_a_domicilio_com_endereco(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("João Silva", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose Agendar
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose a date
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.LOCAL_ATENDIMENTO)
        
        # Choose A Domicílio (option 1)
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        
        self.assertEqual(conv.state, Status.AGUARDANDO_ENDERECO)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.INFORMAR_ENDERECO,
            self.bot_telefone
        )
        
        # Provide address
        endereco = "Rua Teste, 123, Apto 45, CEP: 12345-678, Bairro Centro"
        processar_mensagem(endereco, self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CONFIRMANDO_AGENDAMENTO)
        self.assertEqual(conv.data["endereco"], endereco)
        
        # Confirm appointment
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        
        self.assertEqual(conv.state, Status.IDLE)

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_cancelar_agendamento_com_sucesso(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Maria Santos", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Mock user has appointments
        mock_agendamentos = [
            {"data": "05/04/2026", "horario": "10:00"},
            {"data": "06/04/2026", "horario": "14:00"}
        ]
        
        # Choose option 2 (Cancelar)
        with patch('WhatsAppBot.engine.buscarAgendamentosPorTelefoneMock', return_value=mock_agendamentos):
            processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CANCELAMENTO)
        
        # Select first appointment to cancel
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        
        self.assertEqual(conv.state, Status.CONFIRMANDO_CANCELAMENTO)
        self.assertEqual(conv.data["agendamento_para_cancelar"], mock_agendamentos[0])
        
        # Confirm cancellation
        processar_mensagem("sim", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        
        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.CANCELAMENTO_CONFIRMADO,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_abortar_cancelamento(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Pedro Costa", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        mock_agendamentos = [{"data": "05/04/2026", "horario": "10:00"}]
        
        # Choose option 2 (Cancelar)
        with patch('WhatsAppBot.engine.buscarAgendamentosPorTelefoneMock', return_value=mock_agendamentos):
            processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Select appointment
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CONFIRMANDO_CANCELAMENTO)
        
        # Abort cancellation
        processar_mensagem("não", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        
        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.CANCELAMENTO_ABORTADO,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_consultar_agendamentos_com_sucesso(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Ana Lima", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        mock_agendamentos = [
            {"data": "05/04/2026", "horario": "10:00"},
            {"data": "08/04/2026", "horario": "15:00"}
        ]
        
        # Choose option 3 (Consultar)
        with patch('WhatsAppBot.engine.buscarAgendamentosPorTelefoneMock', return_value=mock_agendamentos):
            processar_mensagem("3", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.IDLE)

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_consultar_sem_agendamentos(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Carlos Souza", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose option 3 (Consultar) with no appointments
        with patch('WhatsAppBot.engine.buscarAgendamentosPorTelefoneMock', return_value=[]):
            processar_mensagem("3", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.listar_agendamentos([]),
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_validacao_nome_invalido(self, mock_enviar):
        # Start conversation
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Try to send just numbers
        processar_mensagem("123", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.VALIDANDO_USUARIO)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.NOME_NAO_INFORMADO,
            self.bot_telefone
        )
        
        # Try empty name
        processar_mensagem("", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.VALIDANDO_USUARIO)

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_opcao_invalida_no_menu_principal(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Usuario Teste", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Try invalid menu option
        processar_mensagem("99", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.OPCAO_INVALIDA,
            self.bot_telefone
        )
        
        # Try non-numeric input
        processar_mensagem("abc", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.OPCAO_INVALIDA,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_abortar_agendamento_na_confirmacao(self, mock_enviar):
        # Setup and go through appointment flow
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Teste Abortar", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose Agendar
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose date
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose Salão
        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.CONFIRMANDO_AGENDAMENTO)
        
        # Decline appointment (option 2)
        processar_mensagem("2", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.IDLE)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.CANCELAMENTO_CONFIRMADO,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_sair_do_menu_principal(self, mock_enviar):
        # Setup existing user
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Usuario Sair", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        # Choose option 4 (Sair)
        processar_mensagem("4", self.bot_telefone, self.usuario_telefone, self.nome_usuario)
        
        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.IDLE)
        self.assertEqual(len(conv.data), 0)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.SAIR,
            self.bot_telefone
        )

    @patch('WhatsAppBot.engine.enviar_mensagem')
    def test_selecao_data_invalida(self, mock_enviar):
        # Setup
        processar_mensagem("Oi", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        with patch('WhatsAppBot.engine.checarSeUsuarioExistePorTelefoneMock', return_value=True):
            processar_mensagem("Usuario Teste", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        # Choose Agendar
        processar_mensagem("1", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.DEFININDO_DATA)

        # Try invalid date selection (out of range)
        processar_mensagem("99", self.bot_telefone, self.usuario_telefone, self.nome_usuario)

        conv = get_conversation(self.usuario_telefone)
        self.assertEqual(conv.state, Status.DEFININDO_DATA)
        mock_enviar.assert_called_with(
            self.usuario_telefone,
            MensagemBOT.OPCAO_INVALIDA,
            self.bot_telefone
        )