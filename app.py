import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g, send_from_directory

DB_PATH = "appfit.db"

app = Flask(__name__, static_folder="static", static_url_path="")

MET = {
    "Corrida (5:35 min/km)": 10.5,
    "Caminhada": 4.0,
    "Natação": 8.0,
    "Ciclismo": 7.0,
}

# ---------------------------------------------------------------- DB setup

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nm_usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            altura REAL NOT NULL,
            peso REAL NOT NULL,
            idade INTEGER NOT NULL,
            sexo TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS treino (
            id_treino INTEGER PRIMARY KEY AUTOINCREMENT,
            exercicio TEXT NOT NULL,
            atv_peso REAL,
            repeticoes INTEGER,
            series INTEGER,
            tempo TEXT,
            gasto_calorico REAL NOT NULL,
            id_usuario INTEGER NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
        );

        CREATE TABLE IF NOT EXISTS atv_cardio (
            cardio_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nm_exercicio TEXT NOT NULL,
            tempo_atv TEXT,
            ritimo_medio TEXT,
            gasto_calorico REAL NOT NULL,
            id_usuario INTEGER NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
        );

        CREATE TABLE IF NOT EXISTS historico (
            id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL,
            id_treino INTEGER,
            cardio_id INTEGER,
            id_usuario INTEGER NOT NULL,
            FOREIGN KEY (id_treino) REFERENCES treino(id_treino),
            FOREIGN KEY (cardio_id) REFERENCES atv_cardio(cardio_id),
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
        );
        """
    )
    db.commit()
    db.close()


def registrar_historico(db, tipo, last_id, id_usuario):
    dia = datetime.now().isoformat(timespec="seconds")
    if tipo == "cardio":
        db.execute(
            "INSERT INTO historico (dia, cardio_id, id_usuario) VALUES (?, ?, ?)",
            (dia, last_id, id_usuario),
        )
    else:
        db.execute(
            "INSERT INTO historico (dia, id_treino, id_usuario) VALUES (?, ?, ?)",
            (dia, last_id, id_usuario),
        )
    db.commit()


def usuario_publico(row):
    return {
        "id_usuario": row["id_usuario"],
        "nm_usuario": row["nm_usuario"],
        "altura": row["altura"],
        "peso": row["peso"],
        "idade": row["idade"],
        "sexo": row["sexo"],
    }


# ---------------------------------------------------------------- Auth

@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    nome = (data.get("nm_usuario") or "").strip()
    senha = (data.get("senha") or "").strip()
    db = get_db()
    row = db.execute(
        "SELECT * FROM usuario WHERE nm_usuario = ? AND senha = ?", (nome, senha)
    ).fetchone()
    if not row:
        return jsonify({"erro": "Usuário ou senha incorretos"}), 401
    return jsonify(usuario_publico(row))


@app.post("/api/registrar")
def registrar():
    data = request.get_json(force=True)
    nome = (data.get("nm_usuario") or "").strip()
    senha = (data.get("senha") or "").strip()
    try:
        altura = float(data.get("altura"))
        peso = float(data.get("peso"))
        idade = int(data.get("idade"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Altura, peso e idade precisam ser números válidos"}), 400
    sexo = (data.get("sexo") or "").strip().capitalize()
    if sexo not in ("Masculino", "Feminino"):
        return jsonify({"erro": "Sexo inválido"}), 400
    if not nome or not senha:
        return jsonify({"erro": "Nome e senha são obrigatórios"}), 400
    if not (0.5 <= altura <= 2.5):
        return jsonify({"erro": "Altura precisa estar em metros, entre 0.5 e 2.5 (ex: 1.75)"}), 400
    if not (20 <= peso <= 400):
        return jsonify({"erro": "Peso precisa estar em quilos, entre 20 e 400"}), 400
    if not (5 <= idade <= 120):
        return jsonify({"erro": "Idade inválida"}), 400

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO usuario (nm_usuario, senha, altura, peso, idade, sexo) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, senha, altura, peso, idade, sexo),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Esse nome de usuário já existe"}), 409

    row = db.execute(
        "SELECT * FROM usuario WHERE id_usuario = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(usuario_publico(row)), 201


# ---------------------------------------------------------------- Exercícios

@app.post("/api/cardio")
def registrar_cardio():
    data = request.get_json(force=True)
    id_usuario = data.get("id_usuario")
    nome_exercicio = data.get("nm_exercicio")
    if nome_exercicio not in MET:
        return jsonify({"erro": "Exercício de cardio inválido"}), 400
    try:
        duracao = float(data.get("duracao"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Duração inválida"}), 400
    ritmo = (data.get("ritmo") or "").strip()

    db = get_db()
    peso_row = db.execute(
        "SELECT peso FROM usuario WHERE id_usuario = ?", (id_usuario,)
    ).fetchone()
    if not peso_row:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    peso = peso_row["peso"]

    min_totais = int(duracao)
    duracao_formatada = f"{min_totais // 60:02}:{min_totais % 60:02}:00"

    try:
        r_min, r_sec = ritmo.split(":")
        r_min, r_sec = int(r_min), int(r_sec)
        ritmo_formatado = f"{r_min // 60:02}:{r_min % 60:02}:{r_sec:02}"
    except Exception:
        ritmo_formatado = "00:00:00"

    gasto_calorico = (MET[nome_exercicio] * peso * duracao) / 60

    cur = db.execute(
        "INSERT INTO atv_cardio (nm_exercicio, tempo_atv, ritimo_medio, gasto_calorico, id_usuario) VALUES (?, ?, ?, ?, ?)",
        (nome_exercicio, duracao_formatada, ritmo_formatado, gasto_calorico, id_usuario),
    )
    db.commit()
    registrar_historico(db, "cardio", cur.lastrowid, id_usuario)
    return jsonify({"nm_exercicio": nome_exercicio, "gasto_calorico": round(gasto_calorico, 2)}), 201


@app.post("/api/musculacao")
def registrar_musculacao():
    data = request.get_json(force=True)
    id_usuario = data.get("id_usuario")
    exercicio = (data.get("exercicio") or "").strip()
    if not exercicio:
        return jsonify({"erro": "Nome do exercício é obrigatório"}), 400
    try:
        peso_exerc = float(data.get("peso_exerc"))
        repeticoes = int(data.get("repeticoes"))
        series = int(data.get("series"))
        tempo_treino = float(data.get("tempo_treino"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Valores numéricos inválidos"}), 400

    db = get_db()
    peso_row = db.execute(
        "SELECT peso FROM usuario WHERE id_usuario = ?", (id_usuario,)
    ).fetchone()
    if not peso_row:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    peso = peso_row["peso"]

    min_totais = int(tempo_treino)
    tempo_formatado = f"{min_totais // 60:02}:{min_totais % 60:02}:00"
    gasto_calorico = 6.0 * peso * (tempo_treino / 60)

    cur = db.execute(
        "INSERT INTO treino (exercicio, atv_peso, repeticoes, series, tempo, gasto_calorico, id_usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (exercicio, peso_exerc, repeticoes, series, tempo_formatado, gasto_calorico, id_usuario),
    )
    db.commit()
    registrar_historico(db, "musculacao", cur.lastrowid, id_usuario)
    return jsonify({"exercicio": exercicio, "gasto_calorico": round(gasto_calorico, 2)}), 201


# ---------------------------------------------------------------- IMC / TMB

@app.get("/api/imc/<int:id_usuario>")
def calcular_imc(id_usuario):
    db = get_db()
    row = db.execute(
        "SELECT peso, altura FROM usuario WHERE id_usuario = ?", (id_usuario,)
    ).fetchone()
    if not row:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    imc = row["peso"] / (row["altura"] ** 2)
    if imc < 18.5:
        classificacao = "Abaixo do peso ideal"
    elif imc < 24.9:
        classificacao = "Peso ideal"
    elif imc < 29.9:
        classificacao = "Sobrepeso"
    elif imc < 34.9:
        classificacao = "Obesidade Grau I"
    elif imc < 39.9:
        classificacao = "Obesidade Grau II"
    else:
        classificacao = "Obesidade Grau III"
    return jsonify({"imc": round(imc, 2), "classificacao": classificacao})


@app.post("/api/tmb")
def calcular_tmb():
    data = request.get_json(force=True)
    id_usuario = data.get("id_usuario")
    try:
        exerc_p_semana = int(data.get("exerc_p_semana"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Frequência semanal inválida"}), 400

    db = get_db()
    row = db.execute(
        "SELECT peso, altura, idade, sexo FROM usuario WHERE id_usuario = ?", (id_usuario,)
    ).fetchone()
    if not row:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    peso, altura, idade, sexo = row["peso"], row["altura"], row["idade"], row["sexo"]
    if sexo == "Masculino":
        tmb = 66 + (13.7 * peso) + (5 * altura * 100) - (6.8 * idade)
    else:
        tmb = 655 + (9.6 * peso) + (1.8 * altura * 100) - (4.7 * idade)

    if exerc_p_semana <= 2:
        f_ativ = 1.2
    elif exerc_p_semana <= 4:
        f_ativ = 1.35
    elif exerc_p_semana <= 6:
        f_ativ = 1.55
    else:
        f_ativ = 1.7

    gasto_diario = tmb * f_ativ
    return jsonify({"tmb": round(tmb, 2), "gasto_diario": round(gasto_diario)})


# ---------------------------------------------------------------- Histórico

@app.get("/api/historico/<int:id_usuario>")
def historico(id_usuario):
    db = get_db()
    rows = db.execute(
        """
        SELECT
            h.dia,
            t.exercicio, t.atv_peso, t.repeticoes, t.series, t.gasto_calorico AS t_gasto,
            c.nm_exercicio, c.tempo_atv, c.ritimo_medio, c.gasto_calorico AS c_gasto
        FROM historico h
        LEFT JOIN treino t ON t.id_treino = h.id_treino
        LEFT JOIN atv_cardio c ON c.cardio_id = h.cardio_id
        WHERE h.id_usuario = ?
        ORDER BY h.dia DESC
        LIMIT 10
        """,
        (id_usuario,),
    ).fetchall()

    resultado = []
    for row in rows:
        if row["exercicio"] is not None:
            resultado.append(
                {
                    "tipo": "musculacao",
                    "dia": row["dia"],
                    "exercicio": row["exercicio"],
                    "peso": row["atv_peso"],
                    "repeticoes": row["repeticoes"],
                    "series": row["series"],
                    "gasto_calorico": round(row["t_gasto"], 2) if row["t_gasto"] else 0,
                }
            )
        else:
            resultado.append(
                {
                    "tipo": "cardio",
                    "dia": row["dia"],
                    "exercicio": row["nm_exercicio"],
                    "tempo": row["tempo_atv"],
                    "ritmo": row["ritimo_medio"],
                    "gasto_calorico": round(row["c_gasto"], 2) if row["c_gasto"] else 0,
                }
            )
    return jsonify(resultado)


# ---------------------------------------------------------------- Frontend

@app.get("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)