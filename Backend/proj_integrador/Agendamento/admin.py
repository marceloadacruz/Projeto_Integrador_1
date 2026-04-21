from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import format_html

from .models import Appointment, AppointmentxService, Customer, Service


class AppointmentxServiceInline(admin.TabularInline):
    model = AppointmentxService
    extra = 1
    autocomplete_fields = ['service']
    verbose_name = "Serviço"
    verbose_name_plural = "Serviços aplicados"


class AppointmentAdminForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        widgets = {
            'scheduled_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_at'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_scheduled_at(self):
        data = self.cleaned_data['scheduled_at']
        criando = self.instance.pk is None
        status_novo = self.cleaned_data.get('status', 'scheduled')
        if criando and status_novo == 'scheduled' and data < timezone.now():
            raise ValidationError("Não é possível criar agendamento para uma data no passado.")
        return data


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'deleted')
    list_filter = ('deleted',)
    search_fields = ('name', 'phone', 'email')
    fields = ('name', 'email', 'phone', 'deleted')
    ordering = ('name',)

    def get_queryset(self, request):
        return Customer.active_objects.all()


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_formatado', 'duration')
    search_fields = ('name',)
    ordering = ('name',)

    @admin.display(description='Preço', ordering='price')
    def price_formatado(self, obj):
        return f"R$ {obj.price:.2f}".replace('.', ',')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm
    list_display = (
        'customer',
        'scheduled_at',
        'status_badge',
        'location',
        'google_sync_icon',
    )
    list_filter = ('status', 'scheduled_at')
    search_fields = ('customer__name', 'customer__phone')
    date_hierarchy = 'scheduled_at'
    autocomplete_fields = ['customer']
    readonly_fields = ('google_event_id',)
    inlines = [AppointmentxServiceInline]
    actions = ['cancelar_agendamentos', 'marcar_como_concluidos']
    fieldsets = (
        (None, {
            'fields': ('customer', 'scheduled_at', 'status', 'location'),
        }),
        ('Integração Google Calendar', {
            'classes': ('collapse',),
            'fields': ('google_event_id',),
        }),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        cores = {
            'scheduled': ('#0ea5e9', 'Agendado'),
            'completed': ('#16a34a', 'Concluído'),
            'canceled': ('#dc2626', 'Cancelado'),
        }
        cor, label = cores.get(obj.status, ('#6b7280', obj.status))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            cor, label,
        )

    @admin.display(description='Google', boolean=True)
    def google_sync_icon(self, obj):
        return bool(obj.google_event_id)

    @admin.action(description='Cancelar agendamentos selecionados')
    def cancelar_agendamentos(self, request, queryset):
        atualizados = 0
        for agendamento in queryset.exclude(status='canceled'):
            agendamento.status = 'canceled'
            agendamento.save(update_fields=['status'])
            atualizados += 1
        self.message_user(request, f'{atualizados} agendamento(s) cancelado(s).')

    @admin.action(description='Marcar como concluídos')
    def marcar_como_concluidos(self, request, queryset):
        atualizados = queryset.update(status='completed')
        self.message_user(request, f'{atualizados} agendamento(s) concluído(s).')


admin.site.site_header = "Agenda Trancista — Administração"
admin.site.site_title = "Agenda Trancista"
admin.site.index_title = "Painel de controle"
