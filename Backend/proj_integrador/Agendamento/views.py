import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Agendamento.models import Appointment, Service, Customer


# Create your views here.
def get_request_data(request):
    if request.method == 'POST':
        return request.POST
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON")
        return None


@csrf_exempt
def agendamento(request):
    if request.method == 'POST':
        return criar_agendamento(request)
    return None


def criar_agendamento(request):
    data = json.loads(request.body)

    customer_id = data['customer_id']
    scheduled_at_str = data['scheduled_at']
    location = data['location']
    service_name = data['service_name']

    if not all([customer_id, scheduled_at_str, location, service_name]):
        return JsonResponse({'error': 'Dados incompletos'}, status=400)

    scheduled_at = datetime.fromisoformat(scheduled_at_str)
    customer = Customer.objects.buscar_usuario_por_id(customer_id)
    service = Service.objects.get(name=service_name)

    if customer is None:
        return JsonResponse({'error': 'Cliente não encontrado'}, status=404)
    if service is None:
        return JsonResponse({'error': 'Serviço não encontrado'}, status=404)

    Appointment.objects.marcar_agendamento(customer, scheduled_at, location, [service])
    return JsonResponse({'message': 'Agendamento criado com sucesso!'}, status=200)

def excluir_agendamento(request):
    pass