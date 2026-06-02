from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "nova_chave_secreta_fretamento_florestal"

# Lista exata com os 36 itens do seu novo checklist técnico
ITENS_CHECKLIST = [
    "crlv_inspecao", "certificado_cronotacografo", "cintos_seguranca", "partida",
    "vazamento_oleo_agua_ar", "pneus", "tres_pontos_piso", "vazamento_combustivel",
    "sinalizacao_trava_radiador", "sinal_sonoro_re", "buzina", "extintor_incendio",
    "folga_direcao", "indicador_porca_keps", "ar_condicionado", "suspensao",
    "porcas_parafusos_rodas", "retrovisores_quebra_sol", "macaco_chave_triangulo",
    "suporte_extintor", "pedais_borrachas_estribos", "limpador_parabrisas",
    "parabrisas_vidros_laterais", "saida_emergencia_laterais", "sistema_iluminacao",
    "pneu_estepe", "assoalho_bancos", "faixas_refletivas", "protecao_polo_bateria",
    "cones_calcos", "camara_re", "dispositivo_limitacao_porta", "pino_reboco_trava"
]

# Dicionário de tradução para exibição amigável no HTML e futuros relatórios
TRADUCAO_ITENS = {
    "crlv_inspecao": "CRLV / Inspeção Eletromecânica",
    "certificado_cronotacografo": "Certificado Cronotacógrafo",
    "cintos_seguranca": "Cintos de Segurança (Motorista e Passageiros)",
    "partida": "Partida",
    "vazamento_oleo_agua_ar": "Vazamento de Óleo, Água, Ar (Sistemas de Freios)",
    "pneus": "Pneus",
    "tres_pontos_piso": "Três Pontos de Acesso / Piso Antiderrapante",
    "vazamento_combustivel": "Vazamento de Combustível",
    "sinalizacao_trava_radiador": "Sinalização / Trava da Tampa do Radiador",
    "sinal_sonoro_re": "Sinal Sonoro de Ré",
    "buzina": "Buzina",
    "extintor_incendio": "Extintor de Incêndio",
    "folga_direcao": "Folga na Direção",
    "indicador_porca_keps": "Indicador de Porca Solta (Keps)",
    "ar_condicionado": "Ar Condicionado",
    "suspensao": "Suspensão",
    "porcas_parafusos_rodas": "Porcas / Parafusos / Rodas",
    "retrovisores_quebra_sol": "Retrovisores / Quebra Sol",
    "macaco_chave_triangulo": "Macaco / Chave de Roda / Triângulo",
    "suporte_extintor": "Suporte do Extintor",
    "pedais_borrachas_estribos": "Pedais / Borrachas / Estribos",
    "limpador_parabrisas": "Limpador de Parabrisas",
    "parabrisas_vidros_laterais": "Para-brisas e Vidros Laterais",
    "saida_emergencia_laterais": "Saída de Emergência nas Duas Laterais",
    "sistema_iluminacao": "Sistema de Iluminação (Faróis/Lanternas)",
    "pneu_estepe": "Pneu Estepe",
    "assoalho_bancos": "Assoalho / Bancos",
    "faixas_refletivas": "Faixas Refletivas",
    "protecao_polo_bateria": "Proteção do Polo Positivo da Bateria",
    "cones_calcos": "Cones e Calços",
    "camara_re": "Câmara de Ré",
    "dispositivo_limitacao_porta": "Dispositivo de Limitação da Porta",
    "pino_reboco_trava": "Pino do Reboco e Trava de Segurança"
}

# Base de usuários em memória (Idêntico ao esquema anterior)
USUARIOS_CADASTRADOS = {
    "luciano": ("Luciano dos Santos", "M-10065796", "7480", "motorista"),
    "jeferson": ("Jeferson Aparecido", "M-10065798", "1234", "motorista"),
    "admin": ("Administrador", "ADM-01", "admin123", "admin")
}

def inicializar_banco():
    conn = sqlite3.connect("diario_bordo.db")
    cursor = conn.cursor()
    
    # 1. Tabela de Veículos/Frotas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frota TEXT UNIQUE,
            placa TEXT
        )
    """)
    
    # 2. Tabela de Clientes (Fretistas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    
    # 3. Tabela de Rotas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    
    # 4. Tabela de Diário de Viagens (Modificada para o novo escopo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motorista_nome TEXT,
            motorista_matricula TEXT,
            frota TEXT,
            placa TEXT,
            cliente TEXT,
            rota TEXT,
            data_saida TEXT,
            hora_saida TEXT,
            km_saida REAL,
            lat_saida TEXT,
            lon_saida TEXT,
            hora_chegada TEXT,
            km_chegada REAL,
            lat_chegada TEXT,
            lon_chegada TEXT,
            km_rodados REAL,
            status TEXT DEFAULT 'Em Andamento'
        )
    """)
    
    # 5. Tabela de Checklists estruturada dinamicamente por coluna
    colunas_sql = ", ".join([f"{item} TEXT" for item in ITENS_CHECKLIST])
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            viagem_id INTEGER,
            {colunas_sql},
            observacoes TEXT,
            FOREIGN KEY(viagem_id) REFERENCES viagens(id)
        )
    """)
    
    # Popula dados iniciais de teste caso o banco esteja vazio
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO veiculos (frota, placa) VALUES (?, ?)", [
            ("F-3001", "FXQ3964"), ("F-3002", "GBP8931"), ("F-3003", "GIS1563"), ("F-4390", "OPX2T11")
        ])
        cursor.executemany("INSERT INTO clientes (nome) VALUES (?)", [
            ("Bracell",), ("Suzano",), ("Gema",), ("Arauco",)
        ])
        cursor.executemany("INSERT INTO rotas (nome) VALUES (?)", [
            ("Plantio",), ("Formiga",), ("Colheita",), ("Silvicultura",)
        ])
        conn.commit()
        
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")
        
        if usuario in USUARIOS_CADASTRADOS and USUARIOS_CADASTRADOS[usuario][2] == senha:
            session['usuario'] = usuario
            session['nome'] = USUARIOS_CADASTRADOS[usuario][0]
            session['matricula'] = USUARIOS_CADASTRADOS[usuario][1]
            session['funcao'] = USUARIOS_CADASTRADOS[usuario][3]
            return redirect(url_for("diario"))
        else:
            flash("Usuário ou senha incorretos!", "erro")
            
    return render_template("login.html")

@app.route("/diario", methods=["GET", "POST"])
def diario():
    if "usuario" not in session:
        return redirect(url_for("login"))
        
    conn = sqlite3.connect("diario_bordo.db")
    cursor = conn.cursor()
    
    if request.method == "POST":
        acao = request.form.get("acao")
        
        if acao == "iniciar":
            # Coleta dados do formulário e metadados automáticos
            frota = request.form.get("frota")
            cliente = request.form.get("cliente")
            rota = request.form.get("rota")
            km_saida = float(request.form.get("km_saida"))
            lat_saida = request.form.get("lat_saida")
            lon_saida = request.form.get("lon_saida")
            
            # Puxa a placa automaticamente associada à frota
            cursor.execute("SELECT placa FROM veiculos WHERE frota = ?", (frota,))
            resultado_placa = cursor.fetchone()
            placa = resultado_placa[0] if resultado_placa else "N/A"
            
            data_atual = datetime.now().strftime("%d/%m/%Y")
            hora_atual = datetime.now().strftime("%H:%M:%S")
            
            cursor.execute("""
                INSERT INTO viagens (motorista_nome, motorista_matricula, frota, placa, cliente, rota, data_saida, hora_saida, km_saida, lat_saida, lon_saida, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Checklist Pendente')
            """, (session['nome'], session['matricula'], frota, placa, cliente, rota, data_atual, hora_atual, km_saida, lat_saida, lon_saida))
            
            viagem_id = cursor.lastrowid
            session['viagem_id_pendente'] = viagem_id
            conn.commit()
            conn.close()
            return redirect(url_for("checklist"))
            
        elif acao == "finalizar":
            viagem_id = request.form.get("viagem_id")
            km_chegada = float(request.form.get("km_chegada"))
            lat_chegada = request.form.get("lat_chegada")
            lon_chegada = request.form.get("lon_chegada")
            hora_chegada = datetime.now().strftime("%H:%M:%S")
            
            cursor.execute("SELECT km_saida FROM viagens WHERE id = ?", (viagem_id,))
            km_saida = cursor.fetchone()[0]
            km_rodados = km_chegada - km_saida
            
            cursor.execute("""
                UPDATE viagens 
                SET hora_chegada = ?, km_chegada = ?, lat_chegada = ?, lon_chegada = ?, km_rodados = ?, status = 'Finalizada'
                WHERE id = ?
            """, (hora_chegada, km_chegada, lat_chegada, lon_chegada, km_rodados, viagem_id))
            
            conn.commit()
            flash("Viagem finalizada e computada com sucesso!", "sucesso")

    # Carrega listas dinâmicas para os Dropdowns da Tela
    cursor.execute("SELECT frota, placa FROM veiculos")
    veiculos = cursor.fetchall()
    cursor.execute("SELECT nome FROM clientes")
    clientes = [c[0] for c in cursor.fetchall()]
    cursor.execute("SELECT nome FROM rotas")
    rotas = [r[0] for r in cursor.fetchall()]
    
    # Verifica se o motorista logado possui alguma viagem ativa (Em Andamento ou Pendente)
    cursor.execute("""
        SELECT id, frota, placa, cliente, rota, km_saida, data_saida, hora_saida 
        FROM viagens WHERE motorista_matricula = ? AND status = 'Em Andamento'
    """, (session['matricula'],))
    viagem_ativa = cursor.fetchone()
    
    conn.close()
    return render_template("diario.html", veiculos=veiculos, clientes=clientes, rotas=rotas, viagem=viagem_ativa)

@app.route("/checklist", methods=["GET", "POST"])
def checklist():
    if "usuario" not in session or 'viagem_id_pendente' not in session:
        return redirect(url_for("diario"))
        
    viagem_id = session['viagem_id_pendente']
    
    if request.method == "POST":
        conn = sqlite3.connect("diario_bordo.db")
        cursor = conn.cursor()
        
        # Lê a resposta de cada um dos 36 itens vindos do Form
        respostas = []
        for item in ITENS_CHECKLIST:
            status_item = request.form.get(f"item_{item}") # Retorna 'OK' ou 'Não OK'
            respostas.append(status_item if status_item else "Não OK")
            
        obs = request.form.get("observacoes")
        
        # Monta a query dinâmica de inserção
        colunas_str = ", ".join(ITENS_CHECKLIST)
        placeholders = ", ".join(["?"] * len(ITENS_CHECKLIST))
        
        cursor.execute(f"""
            INSERT INTO checklists (viagem_id, {colunas_str}, observacoes)
            VALUES (?, {placeholders}, ?)
        """, [viagem_id] + respostas + [obs])
        
        # Atualiza o status da viagem para ativa de verdade
        cursor.execute("UPDATE viagens SET status = 'Em Andamento' WHERE id = ?", (viagem_id,))
        
        conn.commit()
        conn.close()
        
        session.pop('viagem_id_pendente', None)
        flash("Checklist enviado. Boa viagem!", "sucesso")
        return redirect(url_for("diario"))
        
    return render_template("checklist.html", itens=ITENS_CHECKLIST, dicionario=TRADUCAO_ITENS)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    inicializar_banco()
    app.run(host="0.0.0.0", port=5000, debug=True)