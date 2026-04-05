import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

# 1. Configurações Iniciais
# Aponta para o arquivo JSON que está na mesma pasta do manage.py
CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'calendar_credentials.json')
CALENDAR_ID = 'agendatrancistabot@gmail.com' 
TEMPO_PROCEDIMENTO = 2                      # Duração fixa de 2 horas para cada procedimento (automatizar isso puxando a duração da tabela Service)

def criar_evento_google_calendar(agendamento):
    """
    Função que recebe um objeto Appointment do Django e cria um evento no Google.
    """
    # 2. Carregando o "crachá" do robô
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, 
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    # 3. Construindo a ponte de comunicação com a API v3 do Calendar
    service = build('calendar', 'v3', credentials=credentials)

    # 4. Arrumando as datas (O fuso horário é vital!)
    # Junta a data e a hora que vieram do banco de dados do Django
    inicio = datetime.combine(agendamento.date, agendamento.time)
    
    # Para esse MVP, vamos fixar a duração do evento em 2 horas. 
    fim = inicio + timedelta(hours=TEMPO_PROCEDIMENTO)

    # 5. Montando o Pacote de Dados (Payload)
    event_data = {
        'summary': f'Trança - {agendamento.customer.name}',
        'description': f'Telefone: {agendamento.customer.phone}\nServiço agendado via Bot.',
        'start': {
            'dateTime': inicio.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': fim.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
    }

    # 6. Enviando a requisição para o Google
    try:
        evento_criado = service.events().insert(calendarId=CALENDAR_ID, body=event_data).execute()
        print(f"Sucesso! Evento criado com ID: {evento_criado.get('id')}")
        return evento_criado.get('id')
    except Exception as e:
        print(f"Erro Crítico ao criar evento na agenda: {e}")
        return None