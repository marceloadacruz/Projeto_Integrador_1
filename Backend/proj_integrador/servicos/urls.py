from django.urls import path
from servicos import views

urlpatterns = [
    path('servicos/listar', views.servicos, name='servicos'),
]