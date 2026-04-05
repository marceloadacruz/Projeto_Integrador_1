SHELL := /bin/bash
VENV := .venv

ifeq ($(OS),Windows_NT)
PY := $(VENV)\\Scripts\\python.exe
UV_CMD := $(VENV)\\Scripts\\uv.exe
ACTIVATE_CMD := & $(VENV)\\Scripts\\Activate.ps1
RM := cmd /C rmdir /S /Q
else
PY := $(VENV)/bin/python
UV_CMD := $(VENV)/bin/uv
ACTIVATE_CMD := source $(VENV)/bin/activate
RM := rm -rf
endif

.PHONY: help setup install venv activate migrate makemigrations runserver createsuperuser update-requirements clean

help:
	@echo ""
	@echo "Projeto Integrador I - Comandos Disponiveis"
	@echo "=============================================="
	@echo ""
	@echo "INICIAR (escolha um):"
	@echo "  make setup              Prepara tudo (cria Python isolado e instala dependências)"
	@echo "  make venv               Apenas cria a pasta '$(VENV)' com Python isolado"
	@echo "  make install            Apenas instala dependências com uv (precisa já ter 'uv')"
	@echo ""
	@echo "ATIVAR AMBIENTE:"
	@echo "  make activate           Mostra o comando para ativar o Python isolado"
	@echo ""
	@echo "EXECUTAR PROJETO:"
	@echo "  make migrate            Prepara o banco de dados"
	@echo "  make runserver          Inicia o servidor (acesse http://localhost:8000)"
	@echo "  make createsuperuser    Cria conta de administrador"
	@echo ""
	@echo "MANUTENÇÃO:"
	@echo "  make update-requirements Atualiza requirements.txt com uv"
	@echo "  make clean              Remove Python isolado e arquivos temporários"
	@echo ""

venv:
	@echo "Preparando Python isolado em '$(VENV)'..."
	@python -m venv $(VENV)
	@echo "Instalando uv (gerenciador de pacotes moderno)..."
	@$(PY) -m pip install --upgrade uv

install: venv
	@echo ""
	@echo "Instalando dependencias com uv..."
	@$(UV_CMD) pip install -r requirements.txt || echo "AVISO: requirements.txt nao encontrado ou vazio, pulando instalacao"

setup: install
	@echo ""
	@echo "Configuracao concluida!"
	@echo ""
	@echo "Para ativar o ambiente, execute:"
	@echo "   make activate"
	@echo ""

activate:
	@echo "Ativando o ambiente virtual em uma nova sessao do terminal..."
ifeq ($(OS),Windows_NT)
	@cmd /k "$(VENV)\\Scripts\\activate.bat"
else
	@bash -c "source $(VENV)/bin/activate && exec bash"
endif

migrate:
	@echo "Preparando banco de dados..."
	@$(PY) Backend/proj_integrador/manage.py migrate
	@echo "Banco pronto!"

makemigrations:
	@echo "Criando migrations..."
	@$(PY) Backend/proj_integrador/manage.py makemigrations

runserver:
	@echo ""
	@echo "Iniciando servidor Django..."
	@echo "   Acesse: http://localhost:8000"
	@echo "   Para parar: pressione Ctrl+C"
	@echo ""
	@$(PY) Backend/proj_integrador/manage.py runserver

createsuperuser:
	@echo ""
	@echo "Criando conta de administrador..."
	@echo "   Voce sera solicitado a digitar nome de usuario, email e senha."
	@echo ""
	@$(PY) Backend/proj_integrador/manage.py createsuperuser
	@echo ""
	@echo "Conta criada! Acesse em: http://localhost:8000/admin"
	@echo ""

update-requirements:
	@echo "Atualizando requirements.txt com uv..."
	@$(UV_CMD) pip freeze > requirements.txt
	@echo "requirements.txt atualizado"

clean:
	@echo "Limpando..."
	@echo "   Removendo Python isolado 'uv'..."
	@$(RM) $(VENV) || true
	@echo "   Removendo arquivos de cache Python..."
	@python -c "import os, shutil; [shutil.rmtree(os.path.join(r, d), ignore_errors=True) for r, dirs, f in os.walk('.') for d in dirs if d == '__pycache__']" || true
	@echo "Limpeza concluida"
	@echo ""
	@echo "Para recomecar, execute: make setup"
	@echo ""
