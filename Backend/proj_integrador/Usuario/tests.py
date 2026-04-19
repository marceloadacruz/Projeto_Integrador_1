import json
from faker import Faker
from django.test import TestCase, Client
from Agendamento.models import Customer

CRIAR_USUARIO = 'Usuario.views.criar_usuario'
DELETAR_USUARIO = 'Usuario.views.deletar_usuario'
ATUALIZAR_USUARIO = 'Usuario.views.atualizar_usuario'
fake = Faker('pt_BR')

# Create your tests here.
class UsuarioIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.base_url = '/usuario/'

        self.user_data = {
            'nome': 'João Silva',
            'email': 'joao@example.com',
            'telefone': '11999999999',
            'senha': 'senha_segura123',
            'confirmar_senha': 'senha_segura123'
        }

    def tearDown(self):
        Customer.objects.all().delete()

    def test_post_routes_to_criar_usuario(self):
        response = self.client.post(
            self.base_url,
            data=self.user_data,
        )

        self.assertEqual(response.status_code, 201)

        user = Customer.objects.filter(phone='11999999999').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'João Silva')
        self.assertEqual(user.email, 'joao@example.com')



    def test_usuario_delete_calls_deletar_usuario(self):
        Customer.objects.cadastrar_usuario(
            self.user_data.get('nome'),
            self.user_data.get('email'),
            self.user_data.get('telefone'),
            self.user_data.get('senha')
        )

        response = self.client.delete(self.base_url, data=self.user_data.get('telefone'))

        self.assertEqual(response.status_code, 200)

        user = Customer.objects.filter(phone='11999999999').first()
        self.assertIsNone(user)


    def test_usuario_put_calls_atualizar_usuario(self):
        Customer.objects.cadastrar_usuario(
            self.user_data.get('nome'),
            self.user_data.get('email'),
            self.user_data.get('telefone'),
            self.user_data.get('senha')
        )

        usuario_editado = {
            'email': 'joaob@example.com',
            'telefone': '11999999999',
            'senha': 'senha_segura123',
            'novo_telefone': '11000000000',
        }

        response = self.client.put(
            self.base_url,
            data=json.dumps(usuario_editado),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        user = Customer.objects.filter(phone='11000000000').first()
        self.assertIsNotNone(user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.name, self.user_data.get('nome'))
        self.assertEqual(user.email, usuario_editado.get('email'))
        self.assertEqual(user.phone, usuario_editado.get('novo_telefone'))

    def test_usuario_get_calls_listar_usuarios(self):
        users = generate_users(5)
        for user_data in users:
            Customer.objects.cadastrar_usuario(
                user_data.get('nome'),
                user_data.get('email'),
                user_data.get('telefone'),
                user_data.get('senha')
            )

        response = self.client.get(self.base_url)

        usuarios_db = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(usuarios_db), 5)

    def test_usuario_get_calls_buscar_usuario_por_numero_telefone(self):
        user = generate_users(1)[0]

        Customer.objects.cadastrar_usuario(user.get('nome'), user.get('email'), user.get('telefone'), user.get('senha'))

        response = self.client.get(self.base_url + f'?numero_telefone={user.get('telefone')}')
        usuario_db = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario_db.get('nome'), user.get('nome'))

def generate_users(count=5):
    users = []
    for _ in range(count):
        password = fake.password()
        user_data = {
            'nome': fake.name(),
            'email': fake.email(),
            'telefone': str(fake.random_number(digits=11, fix_len=True)),
            'senha': password,
            'confirmar_senha': password,
        }
        users.append(user_data)
    return users

