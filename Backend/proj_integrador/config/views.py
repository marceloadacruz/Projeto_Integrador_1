from django.shortcuts import render
from config import settings


def home(request):
    return render(request, 'home.html')

def agendar(request):
    return render(request, 'agendar.html',{
        'API_BASE_URL': settings.API_BASE_URL,
    })