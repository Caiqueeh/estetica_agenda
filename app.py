import os
import psycopg2
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta

app = Flask(__name__)

# URL do PostgreSQL fornecida pelo Render
DATABASE_URL = os.environ.get("DATABASE_URL")

# ---------- Funções auxiliares ----------
def get_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def criar_tabela():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id SERIAL PRIMARY KEY,
            dia TEXT,
            hora TEXT,
            cliente TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def criar_banco():
    conn = sqlite3.connect("agenda.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT,
            hora TEXT,
            cliente TEXT
        )
    """)
    conn.commit()
    conn.close()

def criar_agenda_padrao():
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    conn = get_connection()
    cursor = conn.cursor()
    for dia in dias:
        hora = datetime.strptime("08:00", "%H:%M")
        fim = datetime.strptime("18:00", "%H:%M")
        while hora <= fim:
            hora_str = hora.strftime("%H:%M")
            cursor.execute("SELECT * FROM horarios WHERE dia=%s AND hora=%s", (dia, hora_str))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO horarios (dia, hora, cliente) VALUES (%s, %s, %s)", (dia, hora_str, None))
            hora += timedelta(hours=1)
    conn.commit()
    cursor.close()
    conn.close()

def get_agenda(dia):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, hora, cliente FROM horarios WHERE dia=%s ORDER BY hora", (dia,))
    horarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return horarios

def marcar_horario(id_horario, cliente):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE horarios SET cliente=%s WHERE id=%s", (cliente, id_horario))
    conn.commit()
    cursor.close()
    conn.close()

def cancelar_horario(id_horario):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE horarios SET cliente=NULL WHERE id=%s", (id_horario,))
    conn.commit()
    cursor.close()
    conn.close()

def buscar_cliente(nome):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dia, hora, cliente FROM horarios WHERE cliente ILIKE %s", ('%' + nome + '%',))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


# ---------- Rotas ----------
@app.route("/buscar", methods=["POST"])
def buscar():
    nome = request.form["nome"]
    resultados = buscar_cliente(nome)
    return render_template("buscar.html", nome=nome, resultados=resultados)

@app.route("/")
def index():
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return render_template("index.html", dias=dias)

@app.route("/agenda/<dia>")
def agenda(dia):
    filtro = request.args.get("filtro", "todos")
    horarios = get_agenda(dia)
    if filtro == "livres":
        horarios = [h for h in horarios if h[2] is None]
    return render_template("marcar.html", dia=dia, horarios=horarios, filtro=filtro)
@app.route("/marcar/<int:id_horario>", methods=["POST"])
def marcar(id_horario):
    cliente = request.form["cliente"]
    marcar_horario(id_horario, cliente)
    return redirect(request.referrer)

@app.route("/cancelar/<int:id_horario>")
def cancelar(id_horario):
    cancelar_horario(id_horario)
    return redirect(request.referrer)

# ---------- Inicialização ----------
if __name__ == "__main__":
    criar_tabela()
    criar_agenda_padrao()
    app.run(host="0.0.0.0", port=5000)
