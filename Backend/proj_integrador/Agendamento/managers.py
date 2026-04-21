from datetime import datetime, timedelta, time

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db import models


class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

    def checar_se_usuario_existe_por_telefone(self, numero_telefone: str) -> bool:
        return self.filter(phone=numero_telefone).exists()

    def cadastrar_usuario(self, nome: str, email: str, numero_telefone: str, senha: str) -> 'Customer':
        return self.create(name=nome, email=email, phone=numero_telefone, senha=make_password(senha))

    def editar_usuario(self, numero_telefone_atual: str, nome: str | None, email: str | None,
                       novo_numero_telefone: str | None, senha: str | None) -> int:
        updates = {}
        if nome is not None:
            updates['name'] = nome
        if email is not None:
            updates['email'] = email
        if novo_numero_telefone is not None:
            updates['phone'] = novo_numero_telefone
        if senha is not None:
            updates['senha'] = make_password(senha)

        if not updates:
            return 0

        return self.filter(phone=numero_telefone_atual).update(**updates)

    def deletar_usuario(self, numero_telefone: str) -> int:
        linhas_alteradas = self.filter(phone=numero_telefone).update(deleted=True)
        return linhas_alteradas > 0

    def buscar_usuario_por_telefone(self, numero_telefone: str) -> 'Customer | None':
        return self.filter(phone=numero_telefone).first()

    def buscar_usuarios_nao_deletados(self) -> list['Customer']:
        return list(self.filter(deleted=False))

    def verificar_senha(self, numero_telefone: str, senha: str):
        usuario = self.buscar_usuario_por_telefone(numero_telefone)

        if usuario:
            return usuario.check_password(senha)
        return False


class AppointmentsManager(models.Manager):
    HORARIO_PADRAO = time(11, 0)

    def buscar_agendamentos_disponiveis_no_periodo(self, total_dias: int = 20) -> list:
        hoje = timezone.now().date()

        if timezone.now().hour >= 10:
            data_inicio = hoje + timedelta(days=1)
        else:
            data_inicio = hoje

        data_final = data_inicio + timedelta(days=total_dias)

        dias_ocupados = set(
            self.filter(
                scheduled_at__date__range=[data_inicio, data_final],
                status='scheduled',
            ).values_list('scheduled_at__date', flat=True)
        )

        possiveis_dias = [data_inicio + timedelta(days=i) for i in range(total_dias)]
        return [dia for dia in possiveis_dias if dia not in dias_ocupados]

    def buscar_agendamentos_por_numero_telefone(self, numero_telefone: str) -> list['Appointment']:
        query = self.filter(customer__phone=numero_telefone, status='scheduled')
        return list(query)

    def marcar_agendamento(self, customer: 'Customer', scheduled_at: datetime, location: str,
                           services: list['Service']) -> 'Appointment':
        from .models import AppointmentxService

        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at, timezone.get_current_timezone())

        appointment = self.create(
            customer=customer,
            scheduled_at=scheduled_at,
            status='scheduled',
            location=location,
        )

        for service in services:
            AppointmentxService.objects.create(
                appointment=appointment,
                service=service,
                applied_price=service.price,
            )

        return appointment

    def cancelar_agendamento(self, appointment: 'Appointment') -> 'Appointment':
        appointment.status = 'canceled'
        appointment.save(update_fields=['status'])
        return appointment

    def checar_se_data_esta_em_uso(self, data) -> bool:
        return self.filter(scheduled_at__date=data, status='scheduled').exists()
