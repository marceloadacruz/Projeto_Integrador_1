from django.urls import path
from Usuario import views

urlpatterns = [
    path('usuario/', views.usuario, name='usuario'),
]