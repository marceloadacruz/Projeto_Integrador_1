from django.http import JsonResponse


def validar_usuario(data) -> bool:
    if not validar_email(data.get('email')):
        JsonResponse({ "message": "Erro: Email inválido" }, status=400)
        return False

    if not validar_telefone(data.get('telefone')):
        JsonResponse({ "message": "Erro: Telefone inválido" }, status=400)
        return False

    # if not validar_senha(data.get('senha'), data.get('confirmar_senha')):
    #     JsonResponse({ "message": "Erro: Senhas não conferem" }, status=400)
    #     return False

    return True


def validar_email(email: str) -> bool:
    return email is not None and "@" in email and "." in email

def validar_telefone(telefone: str) -> bool:
    return telefone is not None and len(telefone) == 11

def validar_senha(senha: str, confirmar_senha: str) -> bool:
    return None not in (senha, confirmar_senha) and senha == confirmar_senha



