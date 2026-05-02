from django.urls import path
from Agendamento import views

urlpatterns = [
    path('agendamento/', views.agendamento, name='agendamento'),
]