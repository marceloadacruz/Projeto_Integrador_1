from django.urls import path
from . import views

# Todo: adicionar ngrok
urlpatterns = [
    path('webhook', views.webhook, name='webhook')
]