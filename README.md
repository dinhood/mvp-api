# MVP - API (Backend)

API para controle de despesas, desenvolvida em **Python + Flask**, com persistência em **SQLite**.  
Este projeto faz parte do MVP (Minimum Viable Product) de controle de despesas.

---

## Tecnologias
- Python 3.13
- Flask
- Flask-CORS
- Flasgger (Swagger para documentação)
- SQLite

---

## Estrutura
- `app.py` → código principal da API
- `dados.db` → banco de dados SQLite
- `requirements.txt` → dependências do projeto
- `run_server.bat` → script para rodar o servidor localmente
- `venv/` → ambiente virtual (não versionado)

---

## Como rodar localmente

1. **Clone este repositório**
   git clone https://github.com/dinhood/mvp-api.git
   cd mvp-api

   Crie o ambiente virtual e ative

python -m venv venv
.\venv\Scripts\activate


Instale as dependências

pip install -r requirements.txt


Inicie o servidor

python app.py


A API estará disponível em: http://127.0.0.1:5000

 Documentação Swagger

Depois que o servidor estiver rodando, acesse:
 http://127.0.0.1:5000/apidocs