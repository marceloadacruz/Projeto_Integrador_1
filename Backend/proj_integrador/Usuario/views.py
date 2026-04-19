import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from Agendamento.models import Customer
from Usuario.validacoes import validar_usuario

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
def usuario(request):
    if request.method == 'POST':
        return criar_usuario(request)

    elif request.method == 'DELETE':
        return deletar_usuario(request)

    elif request.method == 'PUT':
        return atualizar_usuario(request)

    elif request.method == 'GET' and not request.GET.get('numero_telefone'):
        return listar_usuarios()

    elif request.method == 'GET' and request.GET.get('numero_telefone'):
        return buscar_usuario_por_numero_telefone(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def criar_usuario(request):
    data = request.POST

    if not validar_usuario(data):
        return JsonResponse({"error": "Dados inválidos"}, status=400)

    usuario_nome = data['nome']
    usuario_email = data['email']
    usuario_telefone = data['telefone']
    usuario_senha = data['senha']

    Customer.objects.cadastrar_usuario(usuario_nome, usuario_email, usuario_telefone, usuario_senha)
    return JsonResponse({"message": "Sucesso: Usuário criado"}, status=201)


def deletar_usuario(request):
    telefone = str(get_request_data(request))

    if not Customer.objects.checar_se_usuario_existe_por_telefone(telefone):
        return JsonResponse({"error": "Erro: Usuário não encontrado"}, status=404)

    Customer.objects.deletar_usuario(telefone)
    return JsonResponse({"message": "Sucesso: Usuário deletado"}, status=200)


def atualizar_usuario(request):
    data = get_request_data(request)

    if not data or not data.get('telefone'):
        return JsonResponse({"error": "Telefone não informado"}, status=400)

    if not Customer.objects.checar_se_usuario_existe_por_telefone(data.get('telefone')):
        return JsonResponse({"error": "Erro: Usuário não encontrado"}, status=404)

    numero_telefone_atual = data.get('telefone')
    nome = data.get('nome')
    email = data.get('email')
    novo_telefone = data.get('novo_telefone')
    senha = data.get('senha')

    Customer.objects.editar_usuario(numero_telefone_atual, nome, email, novo_telefone, senha)
    return JsonResponse({"message": "Sucesso: Usuário atualizado"}, status=200)

def listar_usuarios():
    usuarios = Customer.objects.buscar_usuarios_nao_deletados()

    usuarios_data = [
        {
            'id': usuario.id,
            'nome': usuario.name,
            'email': usuario.email,
            'telefone': usuario.phone,
        }
        for usuario in usuarios
    ]

    return JsonResponse(usuarios_data, safe=False)


def buscar_usuario_por_numero_telefone(request):
    numero_telefone = request.GET.get('numero_telefone')

    if not numero_telefone:
        return JsonResponse({"error": "Número de telefone não informado"}, status=400)

    usuario = Customer.objects.buscar_usuario_por_telefone(numero_telefone)

    if usuario:
        return JsonResponse({
            'id': usuario.id,
            'nome': usuario.name,
            'email': usuario.email,
            'telefone': usuario.phone,
        })
    return JsonResponse({"error": "Usuário não encontrado"}, status=404)
