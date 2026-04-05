import os
import requests
from http.client import responses

# TODO: ACCESS_TOKEN está vazio
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

def enviar_mensagem(usuario_telefone: str, mensagemDoBot: str, bot_telefone: str):
    url = f"https://graph.facebook.com/v22.0/{bot_telefone}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": usuario_telefone,
        "text": {"body": mensagemDoBot}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Erro ao enviar mensagem para {usuario_telefone}. Resposta do servidor: {response.text} ({response.status_code})")
