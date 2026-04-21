from django.db import migrations, models
from django.utils import timezone


def combinar_data_e_hora(apps, schema_editor):
    Appointment = apps.get_model('Agendamento', 'Appointment')
    tz = timezone.get_current_timezone()
    for ag in Appointment.objects.all():
        if ag.date and ag.time:
            dt = timezone.datetime.combine(ag.date, ag.time)
            ag.scheduled_at = timezone.make_aware(dt, tz)
            ag.save(update_fields=['scheduled_at'])


def separar_data_e_hora(apps, schema_editor):
    Appointment = apps.get_model('Agendamento', 'Appointment')
    for ag in Appointment.objects.all():
        if ag.scheduled_at:
            ag.date = ag.scheduled_at.date()
            ag.time = ag.scheduled_at.time()
            ag.save(update_fields=['date', 'time'])


class Migration(migrations.Migration):

    dependencies = [
        ('Agendamento', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='scheduled_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(combinar_data_e_hora, separar_data_e_hora),
        migrations.AlterField(
            model_name='appointment',
            name='scheduled_at',
            field=models.DateTimeField(),
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='date',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='time',
        ),
        migrations.AlterModelOptions(
            name='appointment',
            options={'ordering': ['scheduled_at']},
        ),
        migrations.AlterField(
            model_name='appointment',
            name='customer',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='appointments',
                to='Agendamento.customer',
            ),
        ),
    ]
