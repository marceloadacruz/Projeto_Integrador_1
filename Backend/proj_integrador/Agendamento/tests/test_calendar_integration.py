from django.test import TestCase
from unittest.mock import patch
from Agendamento.models import Customer, Appointment  # Adicionado 'Agendamento.' aqui
from datetime import date, time

class IntegracaoCalendarTest(TestCase):
    def setUp(self):
        # 1. Preparação: O Django cria um banco de dados temporário e limpo só para os testes
        self.cliente = Customer.objects.create(
            name="Cliente de Teste", 
            phone="11988887777"
        )

    # 2. O MOCK: Alterado para 'Agendamento.models...'
    @patch('Agendamento.calendar_utils.criar_evento_google_calendar')
    def test_agendamento_confirmado_chama_google_calendar(self, mock_google_calendar):
        mock_google_calendar.return_value = 'id_falso_do_google_123'

        # 3. Ação: Criamos um agendamento e definimos como CONFIRMADO
        agendamento = Appointment(
            customer=self.cliente,
            date=date.today(),
            time=time(14, 0),
            status='confirmado'
        )
        agendamento.save() 

        # 4. Verificação (Asserts): 
        mock_google_calendar.assert_called_once_with(agendamento)
        self.assertEqual(agendamento.google_event_id, 'id_falso_do_google_123')

    # Alterado para 'Agendamento.models...' aqui também
    @patch('Agendamento.calendar_utils.criar_evento_google_calendar')
    def test_agendamento_pendente_nao_chama_google(self, mock_google_calendar):
        agendamento = Appointment(
            customer=self.cliente,
            date=date.today(),
            time=time(15, 0),
            status='pendente'
        )
        agendamento.save()

        mock_google_calendar.assert_not_called()