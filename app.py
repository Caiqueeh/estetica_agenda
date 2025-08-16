from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------- Funções auxiliares ----------
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
    conn = sqlite3.connect("agenda.db")
    cursor = conn.cursor()
    for dia in dias:
        hora = datetime.strptime("07:00", "%H:%M")
        fim = datetime.strptime("21:00", "%H:%M")
        while hora <= fim:
            hora_str = hora.strftime("%H:%M")
            cursor.execute("SELECT * FROM horarios WHERE dia=? AND hora=?", (dia, hora_str))
            if cursor.fetchone() is None:  # só insere se não existir
                cursor.execute("INSERT INTO horarios (dia, hora, cliente) VALUES (?, ?, ?)", (dia, hora_str, None))
            hora += timedelta(hours=1)
    conn.commit()
    conn.close()

def get_agenda(dia):
    conn = sqlite3.connect("agenda.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, hora, cliente FROM horarios WHERE dia=? ORDER BY hora", (dia,))
    horarios = cursor.fetchall()
    conn.close()
    return horarios

def marcar_horario(id_horario, cliente):
    conn = sqlite3.connect("agenda.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE horarios SET cliente=? WHERE id=?", (cliente, id_horario))
    conn.commit()
    conn.close()

def cancelar_horario(id_horario):
    conn = sqlite3.connect("agenda.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE horarios SET cliente=NULL WHERE id=?", (id_horario,))
    conn.commit()
    conn.close()

def buscar_cliente(nome):
    conn = sqlite3.connect("agenda.db")
    cursor = conn.cursor()
    cursor.execute("SELECT dia, hora, cliente FROM horarios WHERE cliente LIKE ?", ('%' + nome + '%',))
    resultados = cursor.fetchall()
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
    criar_banco()
    criar_agenda_padrao()
    app.run(host="0.0.0.0", port=5000)