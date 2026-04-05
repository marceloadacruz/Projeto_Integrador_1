# Projeto Integrador I

Sistema web para agendamento e gerenciamento de usuários, desenvolvido em Django como parte do Projeto Integrador I da Univesp.

---

## 🛠️ Stack Utilizado

- **Python 3.8+** — linguagem de programação
- **Django 6.0** — framework web
- **SQLite** — banco de dados (padrão do Django)
- **uv** — gerenciador de pacotes e ambientes
- **Make** — automação de tarefas

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado em sua máquina:
- **Python 3.8+** para criar o ambiente.
- **Make** para executar os comandos de automação.

---

## 🚀 Instalação e Configuração

Clone o repositório e execute o comando abaixo na raiz do projeto:

```bash
make setup              # Prepara o ambiente virtual isolado e instala as dependências
```

Após o setup, ative o ambiente virtual:

```bash
make activate           # Ativa o ambiente em uma nova sessão do terminal
```

Quando ativado, você verá `(.venv)` no início do terminal. Para sair do ambiente, basta digitar `exit`.

---

## ⚙️ Executando o Projeto

Com o ambiente ativado (`make activate`), você pode gerenciar a aplicação utilizando os comandos abaixo:

```bash
make migrate              # Prepara o banco de dados
make runserver            # Inicia o servidor em http://localhost:8000
make createsuperuser      # Cria conta de administrador
make update-requirements  # Atualiza arquivo de dependências
make clean                # Remove o ambiente e arquivos temporários
```

> **Nota:** Para ver a lista completa de comandos disponíveis a qualquer momento, execute `make help`.

---

## 📁 Estrutura

```
Projeto_Integrador_I/
├── Backend/
│   └── proj_integrador/
│       ├── Agendamento/      # App para agendamentos
│       ├── Usuario/          # App para usuários
│       ├── config/           # Configurações do Django
│       └── manage.py         # Comando principal do Django
├── Makefile                  # Automação (comandos com 'make')
└── requirements.txt          # Lista de dependências Python
```

---


## 💡 Dicas Práticas

1. **Sempre ative o ambiente** antes de rodar comandos
   - Você saberá que está ativado se vir `(.venv)` no início do terminal

2. **Erro "comando não encontrado"?**
   - Verifique se o ambiente está ativado: deve ter `(.venv)` no começo da linha

3. **Para limpar tudo:**
   ```bash
   make clean
   ```
   Depois, recomece com `make setup`.
