import os
import threading
import random
import string
from flask import jsonify, request
from main import app, get_db_connection
from funcao import verificar_senha, criptografar
import smtplib
from email.message import EmailMessage

def enviando_email(destinatario, assunto, corpo):
    remetente = "SEU_EMAIL@gmail.com"
    senha = "SUA_SENHA_DE_APP"

    msg = EmailMessage()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content(corpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(remetente, senha)
        smtp.send_message(msg)

UPLOAD_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], "usuarios")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def gerar_codigo_confirmacao(tamanho=6):
    return ''.join(random.choices(string.digits, k=tamanho))


@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    con = get_db_connection()
    cur = con.cursor()

    try:
        dados = request.get_json(silent=True) or request.form

        nome = dados.get('nome')
        email = dados.get('email')
        telefone = dados.get('telefone')
        senha = dados.get('senha')
        cargo = dados.get('cargo')

        foto = request.files.get('foto')

        if not nome or not nome.strip():
            return jsonify({'erro': 'O nome é obrigatório.'}), 400

        if not email or not senha or not telefone or not cargo:
            return jsonify({'erro': 'Todos os campos são obrigatórios.'}), 400

        erro_senha = verificar_senha(senha)
        if erro_senha:
            return jsonify({'erro': erro_senha}), 400

        cur.execute("SELECT id_usuario FROM usuario WHERE email = ?", (email,))
        if cur.fetchone():
            return jsonify({'erro': 'Este e-mail já está cadastrado.'}), 409

        senha_hash = criptografar(senha)


        cur.execute("""
            INSERT INTO usuario (nome, email, telefone, senha, cargo)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id_usuario
        """, (nome, email, telefone, senha_hash, cargo))

        id_usuario = cur.fetchone()[0]

        if foto:
            extensao = os.path.splitext(foto.filename)[1]
            nome_arquivo = f"perfil_{id_usuario}{extensao}"
            foto.save(os.path.join(UPLOAD_FOLDER, nome_arquivo))


        codigo_confirmacao = gerar_codigo_confirmacao()


        cur.execute("""
            INSERT INTO confirmar_codigo (id_usuario, codigo, utilizado)
            VALUES (?, ?, 0)
        """, (id_usuario, codigo_confirmacao))

        con.commit()


        assunto = "Confirme seu cadastro"
        corpo = f"Seu código de confirmação é: {codigo_confirmacao}"

        threading.Thread(
            target=enviando_email,
            args=(email, assunto, corpo)
        ).start()

        return jsonify({
            "mensagem": "Usuário criado! Verifique seu e-mail.",
            "id_usuario": id_usuario
        }), 201

    except Exception as e:
        con.rollback()
        return jsonify({'erro': f"Erro no banco: {str(e)}"}), 500

    finally:
        cur.close()
        con.close()


@app.route('/confirmar_codigo', methods=['POST'])
def confirmar_codigo():
    con = get_db_connection()
    cur = con.cursor()

    try:
        dados = request.get_json()
        id_usuario = dados.get("id_usuario")
        codigo = dados.get("codigo")

        cur.execute("""
            SELECT id_confirmacao, utilizado
            FROM confirmar_codigo
            WHERE id_usuario = ? AND codigo = ?
        """, (id_usuario, codigo))

        resultado = cur.fetchone()

        if not resultado:
            return jsonify({"erro": "Código inválido"}), 400

        id_confirmacao, utilizado = resultado

        if utilizado == 1:
            return jsonify({"erro": "Esse código já foi usado"}), 400

        cur.execute("""
            UPDATE confirmar_codigo
            SET utilizado = 1
            WHERE id_confirmacao = ?
        """, (id_confirmacao,))

        con.commit()

        return jsonify({"mensagem": "Cadastro confirmado com sucesso!"}), 200

    except Exception as e:
        con.rollback()
        return jsonify({"erro": str(e)}), 500

    finally:
        cur.close()
        con.close()

@app.route('/excluir_usuario/<int:id_usuario>', methods=['DELETE'])
def excluir_usuario(id_usuario):
    con = get_db_connection()
    cur = con.cursor()

    try:

        cur.execute("SELECT id_usuario FROM usuario WHERE id_usuario = ?", (id_usuario,))
        if not cur.fetchone():
            return jsonify({"erro": "Usuário não encontrado"}), 404

        cur.execute("DELETE FROM comentario WHERE id_usuario = ?", (id_usuario,))

        cur.execute("DELETE FROM chamado WHERE id_usuario = ?", (id_usuario,))

        cur.execute("DELETE FROM confirmar_codigo WHERE id_usuario = ?", (id_usuario,))

        cur.execute("DELETE FROM usuario WHERE id_usuario = ?", (id_usuario,))

        con.commit()
        return jsonify({"mensagem": "Usuário excluído com sucesso!"}), 200

    except Exception as e:
        con.rollback()
        return jsonify({"erro": str(e)}), 500

    finally:
        cur.close()
        con.close()