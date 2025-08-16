import os
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta

app = Flask(__name__)

# Detecta se está no Render (PostgreSQL) ou local (SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None and DATABASE_URL != ""

if USE_POSTGRES:
    import psycopg2
else:
    import sqlite3

# ---------------- Funções de conexão ----------------
def get_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        return sqlite3.connect("agenda.db")

# ---------------- Criar tabela ----------------
def criar_tabela():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS horarios (
                    id SERIAL PRIMARY KEY,
                    dia TEXT,
                    hora TEXT,
                    cliente TEXT
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS horarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dia TEXT,
                    hora TEXT,
                    cliente TEXT
                )
            """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ---------------- Criar agenda padrão ----------------
def criar_agenda_padrao():
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for dia in dias:
            hora = datetime.strptime("08:00", "%H:%M")
            fim = datetime.strptime("18:00", "%H:%M")
            while hora <= fim:
                hora_str = hora.strftime("%H:%M")
                cursor.execute(
                    "SELECT * FROM horarios WHERE dia=? AND hora=?" if not USE_POSTGRES else
                    "SELECT * FROM horarios WHERE dia=%s AND hora=%s",
                    (dia, hora_str)
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO horarios (dia, hora, cliente) VALUES (?, ?, ?)" if not USE_POSTGRES else
                        "INSERT INTO horarios (dia, hora, cliente) VALUES (%s, %s, %s)",
                        (dia, hora_str, None)
                    )
                hora += timedelta(hours=1)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ---------------- Funções de CRUD ----------------
def get_agenda(dia):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, hora, cliente FROM horarios WHERE dia=? ORDER BY hora" if not USE_POSTGRES else
            "SELECT id, hora, cliente FROM horarios WHERE dia=%s ORDER BY hora",
            (dia,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def marcar_horario(id_horario, cliente):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE horarios SET cliente=? WHERE id=?" if not USE_POSTGRES else
            "UPDATE horarios SET cliente=%s WHERE id=%s",
            (cliente, id_horario)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def cancelar_horario(id_horario):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE horarios SET cliente=NULL WHERE id=?" if not USE_POSTGRES else
            "UPDATE horarios SET cliente=NULL WHERE id=%s",
            (id_horario,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def buscar_cliente(nome):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT dia, hora, cliente FROM horarios WHERE cliente LIKE ?" if not USE_POSTGRES else
            "SELECT dia, hora, cliente FROM horarios WHERE cliente ILIKE %s",
            ('%' + nome + '%',)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

# ---------------- Rotas Flask ----------------
@app.route("/init_db")
def init_db():
    try:
        criar_tabela()
        criar_agenda_padrao()
        return "Banco inicializado com sucesso!"
    except Exception as e:
        return f"Erro ao inicializar banco: {e}"

@app.route("/")
def index():
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return render_template("index.html", dias=dias)

@app.route("/agenda/<dia>")
def agenda(dia):
    print("Abrindo agenda para:", dia)
    print("USE_POSTGRES =", USE_POSTGRES)
    try:
        filtro = request.args.get("filtro", "todos")
        horarios = get_agenda(dia)
        if filtro == "livres":
            horarios = [h for h in horarios if h[2] is None]
        return render_template("marcar.html", dia=dia, horarios=horarios, filtro=filtro)
    except Exception as e:
        print("Erro ao buscar agenda:", e)
        return f"Erro ao abrir agenda: {e}"

@app.route("/marcar/<int:id_horario>", methods=["POST"])
def marcar(id_horario):
    cliente = request.form["cliente"]
    try:
        marcar_horario(id_horario, cliente)
        return redirect(request.referrer)
    except Exception as e:
        print("Erro ao marcar horário:", e)
        return f"Erro ao marcar horário: {e}"

@app.route("/cancelar/<int:id_horario>")
def cancelar(id_horario):
    try:
        cancelar_horario(id_horario)
        return redirect(request.referrer)
    except Exception as e:
        print("Erro ao cancelar horário:", e)
        return f"Erro ao cancelar horário: {e}"

@app.route("/buscar", methods=["POST"])
def buscar():
    nome = request.form["nome"]
    try:
        resultados = buscar_cliente(nome)
        return render_template("buscar.html", nome=nome, resultados=resultados)
    except Exception as e:
        print("Erro na busca:", e)
        return f"Erro na busca: {e}"

# ---------------- Inicialização ----------------
if __name__ == "__main__":
    criar_tabela()
    criar_agenda_padrao()
    app.run(host="0.0.0.0", port=5000)
