import logging
import os
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'calendar_credentials.json')
CALENDAR_ID = 'agendatrancistabot@gmail.com'
TEMPO_PROCEDIMENTO = 2  # TODO: puxar da tabela Service
PREFIXO_CANCELADO = '[CANCELADO] '
COR_CANCELADO = '11'  # Tomato


def _build_service():
    if not os.path.exists(CREDENTIALS_FILE):
        logger.warning(
            "calendar_credentials.json não encontrado em %s. Pulei integração com Google Calendar.",
            CREDENTIALS_FILE,
        )
        return None
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/calendar'],
        )
        return build('calendar', 'v3', credentials=credentials)
    except Exception:
        logger.exception("Falha ao inicializar cliente do Google Calendar.")
        return None


def criar_evento_google_calendar(agendamento):
    """Cria evento no Google Calendar a partir de um Appointment. Retorna o ID do evento ou None."""
    service = _build_service()
    if service is None:
        return None

    inicio = agendamento.scheduled_at
    fim = inicio + timedelta(hours=TEMPO_PROCEDIMENTO)

    event_data = {
        'summary': f'Trança - {agendamento.customer.name}',
        'description': f'Telefone: {agendamento.customer.phone}\nServiço agendado via Bot.',
        'start': {'dateTime': inicio.isoformat(), 'timeZone': settings.TIME_ZONE},
        'end': {'dateTime': fim.isoformat(), 'timeZone': settings.TIME_ZONE},
    }

    try:
        evento_criado = service.events().insert(calendarId=CALENDAR_ID, body=event_data).execute()
        logger.info("Evento Google Calendar criado com ID: %s", evento_criado.get('id'))
        return evento_criado.get('id')
    except Exception:
        logger.exception("Erro ao criar evento no Google Calendar.")
        return None


def cancelar_evento_google_calendar(agendamento):
    """Marca um evento como cancelado: prefixa título, anota data/hora do cancelamento na descrição e pinta em vermelho."""
    if not agendamento.google_event_id:
        return False

    service = _build_service()
    if service is None:
        return False

    try:
        evento = service.events().get(calendarId=CALENDAR_ID, eventId=agendamento.google_event_id).execute()
    except Exception:
        logger.exception("Erro ao buscar evento %s no Google Calendar.", agendamento.google_event_id)
        return False

    summary_atual = evento.get('summary', '')
    if not summary_atual.startswith(PREFIXO_CANCELADO):
        evento['summary'] = PREFIXO_CANCELADO + summary_atual

    timestamp = timezone.localtime().strftime('%d/%m/%Y %H:%M')
    linha_cancelamento = f'\n\n❌ Cancelado em {timestamp}'
    descricao_atual = evento.get('description', '')
    if linha_cancelamento.strip() not in descricao_atual:
        evento['description'] = descricao_atual + linha_cancelamento

    evento['colorId'] = COR_CANCELADO

    try:
        service.events().update(
            calendarId=CALENDAR_ID,
            eventId=agendamento.google_event_id,
            body=evento,
        ).execute()
        logger.info("Evento %s marcado como cancelado no Google Calendar.", agendamento.google_event_id)
        return True
    except Exception:
        logger.exception("Erro ao atualizar evento %s como cancelado.", agendamento.google_event_id)
        return False
