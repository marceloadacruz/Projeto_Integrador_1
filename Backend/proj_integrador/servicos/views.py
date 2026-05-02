from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Agendamento.models import Service

@csrf_exempt
def servicos(request):
    if request.method == 'GET':
        return listar_servicos(request)

def listar_servicos(request):
    return JsonResponse(Service.objects.listar_servicos(), safe=False)