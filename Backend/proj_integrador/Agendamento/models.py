from django.contrib.auth.hashers import make_password, check_password

from .managers import AppointmentsManager, CustomerManager

from django.db import models

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=99)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=19)
    senha = models.CharField(max_length=128, default='temp')
    deleted = models.BooleanField(default=False)

    objects = CustomerManager()
    active_objects = models.Manager()

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.senha = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.senha)


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.IntegerField(help_text="Duração em minutos")

    def __str__(self):
        return self.name
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('completed', 'Concluído'),
        ('canceled', 'Cancelado'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, default='Rua Nelson Tigrão, 15, Vila Missionária, CEP: 04430-165')

    objects = AppointmentsManager()

    def __str__(self):
        return f"{self.customer.name} - {self.date} às {self.time}"

    def save(self, *args, **kwargs):
        # Primeiro, verificamos se o agendamento já existe no banco e se já tem ID do Google
        ja_tem_id_google = bool(self.google_event_id)
        
        # Salvamos no SQLite primeiro (garantia de que o dado não se perde)
        super().save(*args, **kwargs) 

        # Se estiver confirmado e AINDA NÃO foi enviado para o Google...
        if self.status == 'confirmado' and not ja_tem_id_google:
            # Importamos a função que acabamos de criar
            from .calendar_utils import criar_evento_google_calendar
            
            # Executamos a integração
            id_gerado = criar_evento_google_calendar(self)
            
            if id_gerado:
                self.google_event_id = id_gerado
                # Salvamos de novo, mas agora apenas atualizando a coluna do ID do Google
                super().save(update_fields=['google_event_id'])

        #TODO: adicionar metodo para deletar do google calendar quando for 'cancelado'


class AppointmentxService(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    applied_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.appointment.customer.name} - {self.service.name} at {self.appointment.date} {self.appointment.time}"
