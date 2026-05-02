from django.urls import path
from Usuario import views

urlpatterns = [
    path('usuario/', views.usuario, name='usuario'),
    path('usuario/email/', views.buscar_usuario_por_email),
    path('usuario/id/', views.buscar_usuario_por_id)
]