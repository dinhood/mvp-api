# app.py
# Backend Flask com usuários + despesas + metas
# Persistência usando SQLite
# NÃO usar em produção — apenas para desenvolvimento / MVP.

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3
from flasgger import Swagger

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "dados.db")


# -------------------------
# Inicialização do banco
# -------------------------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Tabela de usuários
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cpf TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        ''')

        # Tabela de despesas
        c.execute('''
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Tabela de metas
        c.execute('''
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                valor REAL NOT NULL,
                UNIQUE(user_id, ano, mes),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

init_db()

# -------------------------
# Usuários
# -------------------------
@app.route('/register', methods=['POST'])
def register():
    """
    Registrar um novo usuário
    ---
    tags:
      - Usuários
    description: Cria um usuário com nome, email, CPF e senha.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome
            - email
            - cpf
            - senha
          properties:
            nome:
              type: string
              example: "João Silva"
            email:
              type: string
              example: "joao@email.com"
            cpf:
              type: string
              example: "12345678900"
            senha:
              type: string
              example: "123456"
    responses:
      201:
        description: Usuário cadastrado com sucesso
      400:
        description: Campos obrigatórios ausentes ou duplicados
      500:
        description: Erro no banco de dados
    """
    data = request.get_json() or {}
    nome = data.get("nome")
    email = data.get("email")
    cpf = data.get("cpf")
    senha = data.get("senha")

    if not nome or not email or not cpf or not senha:
        return jsonify({"erro": "Campos 'nome', 'email', 'cpf' e 'senha' são obrigatórios"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            # Verifica duplicados
            c.execute("SELECT id FROM users WHERE email=? OR cpf=?", (email, cpf))
            if c.fetchone():
                return jsonify({"erro": "E-mail ou CPF já cadastrado"}), 400

            c.execute("INSERT INTO users (nome, email, cpf, senha) VALUES (?, ?, ?, ?)",
                      (nome, email, cpf, senha))
            user_id = c.lastrowid

        return jsonify({"message": "Usuário cadastrado com sucesso!",
                        "user": {"id": user_id, "nome": nome, "email": email, "cpf": cpf}}), 201

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

@app.route('/login', methods=['POST'])
def login():
    """
    Login de usuário
    ---
    tags:
      - Usuários
    description: Realiza login usando email ou CPF e senha.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - identificador
            - senha
          properties:
            identificador:
              type: string
              example: "joao@email.com"
              description: "Email ou CPF do usuário"
            senha:
              type: string
              example: "123456"
              description: "Senha do usuário"
    responses:
      200:
        description: Login realizado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Login OK"
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                nome:
                  type: string
                  example: "João Silva"
                email:
                  type: string
                  example: "joao@email.com"
                cpf:
                  type: string
                  example: "12345678900"
      400:
        description: Campos obrigatórios ausentes
      401:
        description: Usuário ou senha inválidos
      500:
        description: Erro no banco de dados
    """
    data = request.get_json() or {}
    identificador = data.get("identificador")
    senha = data.get("senha")
    if not identificador or not senha:
        return jsonify({"erro": "Campos 'identificador' e 'senha' são obrigatórios"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, nome, email, cpf FROM users WHERE (email=? OR cpf=?) AND senha=?",
                      (identificador, identificador, senha))
            row = c.fetchone()

        if row:
            user_safe = {"id": row[0], "nome": row[1], "email": row[2], "cpf": row[3]}
            return jsonify({"message": "Login OK", "user": user_safe}), 200
        return jsonify({"erro": "Usuário ou senha inválidos"}), 401

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

# -------------------------
# Despesas
# -------------------------
@app.route('/despesas', methods=['POST'])
def adicionar_despesa():
    """
    Adicionar uma nova despesa
    ---
    tags:
      - Despesas
    description: Cria uma despesa para um usuário.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - descricao
            - valor
            - data
          properties:
            user_id:
              type: integer
              example: 1
            descricao:
              type: string
              example: "Almoço"
            valor:
              type: number
              example: 25.50
            data:
              type: string
              example: "2025-09-22"
              description: "Formato YYYY-MM-DD"
    responses:
      201:
        description: Despesa criada com sucesso
      400:
        description: Campos obrigatórios ausentes ou inválidos
      404:
        description: Usuário não encontrado
      500:
        description: Erro no banco de dados
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    descricao = data.get("descricao")
    valor = data.get("valor")
    data_str = data.get("data")

    if user_id is None or descricao is None or valor is None or data_str is None:
        return jsonify({"erro": "Campos 'user_id', 'descricao', 'valor' e 'data' são obrigatórios"}), 400

    try:
        valor = float(valor)
        datetime.strptime(data_str, "%Y-%m-%d")
    except:
        return jsonify({"erro": "Valor deve ser numérico e data no formato YYYY-MM-DD"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE id=?", (user_id,))
            if not c.fetchone():
                return jsonify({"erro": "Usuário não encontrado"}), 404

            c.execute("INSERT INTO despesas (user_id, descricao, valor, data) VALUES (?, ?, ?, ?)",
                      (user_id, descricao, valor, data_str))
            despesa_id = c.lastrowid

        return jsonify({"message": "Despesa adicionada com sucesso!",
                        "despesa": {"id": despesa_id, "user_id": user_id,
                                    "descricao": descricao, "valor": valor, "data": data_str}}), 201

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

@app.route('/despesas', methods=['GET'])
def listar_despesas():
    """
    Listar despesas de um usuário
    ---
    tags:
      - Despesas
    description: Retorna todas as despesas de um usuário específico.
    parameters:
      - in: query
        name: user_id
        type: integer
        required: true
        description: ID do usuário cujas despesas serão listadas
        example: 1
    responses:
      200:
        description: Lista de despesas
        schema:
          type: object
          properties:
            despesas:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  descricao:
                    type: string
                    example: "Almoço"
                  valor:
                    type: number
                    example: 25.50
                  data:
                    type: string
                    example: "2025-09-22"
      400:
        description: Query param 'user_id' ausente
      500:
        description: Erro no banco de dados
    """
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"erro": "Query param 'user_id' é obrigatório"}), 400
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, descricao, valor, data FROM despesas WHERE user_id=?", (user_id,))
            rows = c.fetchall()
        despesas = [{"id": r[0], "descricao": r[1], "valor": r[2], "data": r[3]} for r in rows]
        return jsonify({"despesas": despesas}), 200
    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

@app.route('/despesas/<int:id>', methods=['PUT'])
def atualizar_despesa(id):
    """
    Atualizar uma despesa
    ---
    tags:
      - Despesas
    description: Atualiza os campos 'descricao' e/ou 'valor' de uma despesa específica de um usuário.
    consumes:
      - application/json
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID da despesa a ser atualizada
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
              description: ID do usuário dono da despesa
            descricao:
              type: string
              example: "Almoço com cliente"
              description: Nova descrição da despesa
            valor:
              type: number
              example: 35.00
              description: Novo valor da despesa
    responses:
      200:
        description: Despesa atualizada com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Despesa modificada com sucesso!"
            despesa:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                descricao:
                  type: string
                  example: "Almoço com cliente"
                valor:
                  type: number
                  example: 35.00
                data:
                  type: string
                  example: "2025-09-22"
      400:
        description: Campo 'user_id' ausente ou valores inválidos
      404:
        description: Despesa não encontrada
      500:
        description: Erro no banco de dados
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if user_id is None:
        return jsonify({"erro": "Campo 'user_id' obrigatório"}), 400

    descricao = data.get("descricao")
    valor = data.get("valor")

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM despesas WHERE id=? AND user_id=?", (id, user_id))
            if not c.fetchone():
                return jsonify({"erro": "Despesa não encontrada"}), 404

            if valor is not None:
                valor = float(valor)

            c.execute("""
                UPDATE despesas
                SET descricao = COALESCE(?, descricao),
                    valor = COALESCE(?, valor)
                WHERE id=? AND user_id=?
            """, (descricao, valor, id, user_id))
            c.execute("SELECT id, descricao, valor, data FROM despesas WHERE id=? AND user_id=?", (id, user_id))
            row = c.fetchone()

        return jsonify({"message": "Despesa modificada com sucesso!",
                        "despesa": {"id": row[0], "descricao": row[1],
                                    "valor": row[2], "data": row[3]}}), 200

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

@app.route('/despesas/<int:id>', methods=['DELETE'])
def deletar_despesa(id):
    """
    Deletar uma despesa
    ---
    tags:
      - Despesas
    description: Remove uma despesa específica de um usuário.
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID da despesa a ser removida
        example: 1
      - in: query
        name: user_id
        type: integer
        required: true
        description: ID do usuário dono da despesa
        example: 1
    responses:
      200:
        description: Despesa removida com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Despesa removida com sucesso!"
      400:
        description: Query param 'user_id' ausente
      404:
        description: Despesa não encontrada
      500:
        description: Erro no banco de dados
    """
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"erro": "Query param 'user_id' é obrigatório"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM despesas WHERE id=? AND user_id=?", (id, user_id))
            if not c.fetchone():
                return jsonify({"erro": "Despesa não encontrada"}), 404

            c.execute("DELETE FROM despesas WHERE id=? AND user_id=?", (id, user_id))

        return jsonify({"message": "Despesa removida com sucesso!"}), 200

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

@app.route('/despesas/<int:year>/<int:month>', methods=['GET'])
def despesas_por_mes(year, month):
    """
    Listar despesas de um usuário em um mês específico
    ---
    tags:
      - Despesas
    description: Retorna todas as despesas de um usuário em um mês e ano específicos, incluindo o total.
    parameters:
      - in: path
        name: year
        type: integer
        required: true
        description: Ano das despesas
        example: 2025
      - in: path
        name: month
        type: integer
        required: true
        description: Mês das despesas (1-12)
        example: 9
      - in: query
        name: user_id
        type: integer
        required: true
        description: ID do usuário cujas despesas serão listadas
        example: 1
    responses:
      200:
        description: Lista de despesas e total do mês
        schema:
          type: object
          properties:
            despesas:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  descricao:
                    type: string
                    example: "Almoço"
                  valor:
                    type: number
                    example: 25.50
                  data:
                    type: string
                    example: "2025-09-22"
            total:
              type: number
              example: 125.50
      400:
        description: Query param 'user_id' ausente
      500:
        description: Erro no banco de dados
    """
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"erro": "Query param 'user_id' é obrigatório"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, descricao, valor, data FROM despesas WHERE user_id=?", (user_id,))
            rows = c.fetchall()

        filtradas = []
        total = 0
        for r in rows:
            dt = datetime.strptime(r[3], "%Y-%m-%d")
            if dt.year == year and dt.month == month:
                filtradas.append({"id": r[0], "descricao": r[1], "valor": r[2], "data": r[3]})
                total += r[2]

        return jsonify({"despesas": filtradas, "total": total}), 200

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

# -------------------------
# Metas
# -------------------------
@app.route('/metas', methods=['POST'])
def criar_atualizar_meta():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    ano = data.get("ano")
    mes = data.get("mes")
    valor = data.get("valor")

    if user_id is None or ano is None or mes is None or valor is None:
        return jsonify({"erro": "Campos 'user_id', 'ano', 'mes' e 'valor' são obrigatórios"}), 400

    try:
        user_id = int(user_id)
        ano = int(ano)
        mes = int(mes)
        valor = float(valor)
    except:
        return jsonify({"erro": "Campos 'user_id', 'ano', 'mes' e 'valor' devem ser numéricos"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            # Verifica se já existe meta
            c.execute("SELECT id FROM metas WHERE user_id=? AND ano=? AND mes=?", (user_id, ano, mes))
            row = c.fetchone()
            if row:
                # Atualiza
                c.execute("UPDATE metas SET valor=? WHERE id=?", (valor, row[0]))
                return jsonify({"message": "Meta atualizada com sucesso!",
                                "meta": {"user_id": user_id, "ano": ano, "mes": mes, "valor": valor}}), 200
            else:
                # Cria nova
                c.execute("INSERT INTO metas (user_id, ano, mes, valor) VALUES (?, ?, ?, ?)", (user_id, ano, mes, valor))
                return jsonify({"message": "Meta criada com sucesso!",
                                "meta": {"user_id": user_id, "ano": ano, "mes": mes, "valor": valor}}), 201

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

# -------------------------
# Listar metas
# -------------------------
@app.route('/metas', methods=['GET'])
def listar_metas():
    """
    Listar todas as metas de um usuário
    ---
    tags:
      - Metas
    description: Retorna todas as metas cadastradas de um usuário.
    parameters:
      - in: query
        name: user_id
        type: integer
        required: true
        description: ID do usuário cujas metas serão listadas
        example: 1
    responses:
      200:
        description: Lista de metas
        schema:
          type: object
          properties:
            metas:
              type: array
              items:
                type: object
                properties:
                  ano:
                    type: integer
                    example: 2025
                  mes:
                    type: integer
                    example: 9
                  valor:
                    type: number
                    example: 1500.00
      400:
        description: Query param 'user_id' ausente
      500:
        description: Erro no banco de dados
    """
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"erro": "Query param 'user_id' é obrigatório"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT ano, mes, valor FROM metas WHERE user_id=?", (user_id,))
            rows = c.fetchall()

        metas = [{"ano": r[0], "mes": r[1], "valor": r[2]} for r in rows]
        return jsonify({"metas": metas}), 200

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

@app.route('/metas/<int:ano>/<int:mes>', methods=['GET'])
def meta_mes(ano, mes):
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"erro": "Query param 'user_id' é obrigatório"}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT valor FROM metas WHERE user_id=? AND ano=? AND mes=?", (user_id, ano, mes))
            row = c.fetchone()

        if row:
            return jsonify({"meta": {"user_id": user_id, "ano": ano, "mes": mes, "valor": row[0]}}), 200
        return jsonify({"erro": "Meta não encontrada"}), 404

    except sqlite3.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500

# -------------------------
# Run
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
