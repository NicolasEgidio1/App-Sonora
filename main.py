from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash, jsonify, Response
from datetime import datetime
from dao import usuario
import base64
import dao
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()
from translate import Translator  # Adicione essa linha
from flask import session


app = Flask(__name__)
app.secret_key = '777'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        id_usuario = dao.usuario.realiza_login(email, senha)
        if id_usuario is not None:
            session['id_usuario'] = id_usuario
            return redirect('/home')
        else:
            flash('E-mail ou senha inválidos')
    return render_template('login.html')

@app.route("/upload_imagem", methods=["POST"])
def upload_imagem():
    if "id_usuario" not in session:
        return redirect(url_for("login"))
    
    imagem = request.files["imagem"]
    if imagem:
        imagem_bytes = imagem.read()
        dao.usuario.atualizar_imagem_usuario(session["id_usuario"], imagem_bytes)
    
    return redirect("/perfil")

@app.route("/imagem/<int:id_usuario>")
def imagem_usuario(id_usuario):
    imagem = dao.usuario.buscar_imagem_por_id(id_usuario)
    if imagem:
        return Response(imagem, mimetype='image/jpeg')  # Pode ser 'image/png' ou outro tipo, dependendo do formato
    return "Imagem não encontrada", 404

@app.route('/comentarios')
def comentarios_usuario():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']
    try:
        comentarios = dao.usuario.buscar_todos_comentarios_do_usuario(id_usuario)
        return render_template('comentarios.html', comentarios=comentarios)
    except Exception as e:
        flash(f'Erro ao carregar seus comentários: {str(e)}')
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da sua conta.")
    return redirect(url_for('login'))
from base64 import b64encode

@app.route("/perfil", methods=['GET', 'POST'])
def abre_perfil():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))  # Se o usuário não estiver logado, redireciona

    id_usuario = session['id_usuario']

    if request.method == 'POST':
        nome = request.form.get('nome')
        sexo = request.form.get('sexo')
        descricao = request.form.get('descricao')
        foto = request.files.get('foto')  # Aqui você recebe o arquivo de imagem

        try:
            if foto and foto.filename != "":
                imagem_bytes = foto.read()  # Lê os bytes da imagem
                dao.usuario.atualizar_imagem_usuario(id_usuario, imagem_bytes)  # Atualiza a imagem no banco
            dao.usuario.atualizar_perfil(id_usuario, nome, sexo, descricao)
            mensagem = 'Perfil atualizado com sucesso!'
        except Exception as e:
            mensagem = f'Erro ao atualizar perfil: {e}'
    else:
        mensagem = None

    # Recuperar as informações do usuário
    usuario_info = dao.usuario.buscar_usuario_por_id(id_usuario)

    # Recuperar a imagem em binário e converter para base64 (se houver)
    imagem_binaria = dao.usuario.buscar_imagem_por_id(id_usuario)
    if imagem_binaria:
        imagem_base64 = b64encode(imagem_binaria).decode('utf-8')  # Converte bytes para string base64
        usuario_info['imagem'] = imagem_base64
    else:
        usuario_info['imagem'] = None  # Ou coloque uma imagem padrão

    favoritos = dao.usuario.listar_favoritos(id_usuario)

    return render_template('meuperfil.html', mensagem=mensagem, usuario=usuario_info, favoritos=favoritos)

def formatar_data(data):
    if isinstance(data, str):
        # Data já é string, retorna direto
        return data
    elif hasattr(data, 'strftime'):
        # Data é datetime, formata
        return data.strftime('%d/%m/%Y %H:%M')
    else:
        # Qualquer outro caso, retorna como string
        return str(data)


@app.route('/comentarios-trecho', methods=['GET'])
def comentarios_trecho():
    if 'id_usuario' not in session:
        return jsonify({'erro': 'Usuário não autenticado'}), 401

    trecho = request.args.get('trecho')
    musica = request.args.get('musica')
    artista = request.args.get('artista')

    try:
        comentarios_raw = dao.usuario.buscar_comentarios_por_musica(artista, musica, trecho)
        comentarios = []
        for c in comentarios_raw:
            data = c['data_criacao']
            # Se for datetime, formata; se for string, deixa como está
            if hasattr(data, 'strftime'):
                data_formatada = data.strftime('%d/%m/%Y %H:%M')
            else:
                data_formatada = data

            comentarios.append({
                'nome': c['nome'],
                'comentario': c['comentario'],
                'data_criacao': data_formatada,
                'foto': base64.b64encode(c['imagem']).decode('utf-8') if c.get('imagem') else None
            })

        return jsonify({'comentarios': comentarios})

    except Exception as e:
        print("❌ Erro ao buscar comentários:", e)
        return jsonify({'erro': f'Erro ao buscar comentários: {str(e)}'}), 500




@app.route('/adicionar_comentario', methods=['POST'])
def adicionar_comentario_route():
    if 'id_usuario' not in session:
        return jsonify({'erro': 'Usuário não autenticado'}), 401

    id_usuario = session['id_usuario']
    data = request.get_json()  # Pega os dados que vierem via JSON
    
    artista = data.get('artista')
    musica = data.get('musica')
    trecho = data.get('trecho')
    comentario = data.get('comentario')

    if not (artista and musica and trecho and comentario):
        return jsonify({'erro': 'Dados incompletos'}), 400

    try:
        dao.usuario.adicionar_comentario(id_usuario, artista, musica, trecho, comentario)
        return jsonify({'mensagem': 'Comentário adicionado com sucesso! 🎉'})
    except Exception as e:
        return jsonify({'erro': f'Erro ao adicionar comentário: {str(e)}'}), 500


    

@app.route('/entra_criar_conta')
def criar_conta():
    return render_template('criar_conta.html')

@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def salva_login_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        sexo = request.form['sexo']
        telefone = request.form['telefone']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']

        if not nome or not sexo or not telefone or not cpf or not email or not senha:
            return render_template('criar_conta.html', error_message="Por favor, preencha todos os campos do formulário.")

        try:
            dao.usuario.insere_usuario(nome, sexo, telefone, cpf, email, senha)
            success_message = "Usuário cadastrado com sucesso!"
        except Exception as e:
            error_message = f"Erro ao cadastrar usuário: {str(e)}"
            return render_template('criar_conta.html', error_message=error_message)

        id_usuario = dao.usuario.realiza_login(email, senha)
        if id_usuario:
            session['id_usuario'] = id_usuario
            return redirect(url_for('home'))
        else:
            error_message = "Erro ao fazer login após cadastro. Verifique as credenciais."
            return render_template('criar_conta.html', error_message=error_message)

    return render_template('criar_conta.html')

@app.route('/home')
def home():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

import requests

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])

    headers = {'Authorization': 'Bearer M2xaz2A21FYesXytcPU8iwAupIBlQLT2YCYDKvVJK76fRz2oSb-rpib5qyjfy8OU'}
    response = requests.get(f'https://api.genius.com/search?q={query}', headers=headers)

    if response.status_code != 200:
        print("Erro na API Genius:", response.status_code)
        return jsonify([])

    resultados = response.json()
    sugestoes = []
    for hit in resultados['response']['hits']:
        titulo = hit['result']['title']
        artista = hit['result']['primary_artist']['name']
        sugestoes.append({'titulo': titulo, 'artista': artista})

    return jsonify(sugestoes)

@app.route('/sugerir_musicas', methods=['POST'])
def sugerir_musicas():
    nome_musica = request.form.get('musica')
    resultados = []

    if nome_musica:
        url = f"https://api.genius.com/search?q={nome_musica}"
        headers = {'Authorization': 'Bearer M2xaz2A21FYesXytcPU8iwAupIBlQLT2YCYDKvVJK76fRz2oSb-rpib5qyjfy8OU'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            for hit in data['response']['hits']:
                resultados.append({
                    'titulo': hit['result']['title'],
                    'artista': hit['result']['primary_artist']['name'],
                    'url': hit['result']['url']
                })

    return jsonify(resultados)
from urllib.parse import quote_plus

@app.route('/buscar_letra')
def buscar_letra():
    artista = request.args.get('artista', '')
    musica = request.args.get('musica', '')
    
    letra = dao.buscar_letra_genius(artista, musica)

    # Monta a busca do YouTube para embed de resultados
    if artista and musica:
        query = quote_plus(f"{musica} {artista} clipe oficial")
        video_url = f"https://www.youtube.com/embed?listType=search&list={query}"
    else:
        video_url = None

    return render_template(
        'buscar_letra.html',
        letra=letra,
        artista=artista,
        musica=musica,
        video_url=video_url
    )


@app.route('/traduzir', methods=['POST'])
def traduzir_letra():
    texto = request.json.get('texto')
    if not texto:
        return jsonify({'erro': 'Texto vazio'}), 400

    try:
        # Divide em partes menores para evitar erro de tamanho
        limite = 500
        partes = [texto[i:i+limite] for i in range(0, len(texto), limite)]
        translator = Translator(to_lang="pt")

        traducao_final = ""
        for parte in partes:
            traducao = translator.translate(parte)
            traducao_final += traducao + "\n"

        return jsonify({'traducao': traducao_final.strip()})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/favoritar', methods=['POST'])
def favoritar():
    if 'id_usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado para favoritar músicas'}), 401

    dados = request.get_json()
    artista = dados.get('artista')
    musica = dados.get('musica')
    id_usuario = session['id_usuario']

    if artista and musica:
        try:
            favorito_existente = dao.usuario.verificar_favorito(id_usuario, artista, musica)
            
            if favorito_existente:
                return jsonify({'mensagem': 'Esta música já está nos seus favoritos'}), 200
            
            dao.usuario.favoritar_musica(int(id_usuario), artista, musica)
            return jsonify({'mensagem': 'Música favoritada com sucesso! 🎉'}), 200
        
        except Exception as e:
            return jsonify({'erro': f'Erro ao favoritar: {str(e)}'}), 500
    else:
        return jsonify({'erro': 'Dados incompletos. Certifique-se de que artista e música foram fornecidos.'}), 400



@app.route('/favoritos')
def favoritos():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))  # Redireciona se o usuário não estiver logado

    id_usuario = session['id_usuario']
    try:
        favoritos = dao.usuario.listar_favoritos(id_usuario)  # Lista os favoritos do usuário
        return render_template('favoritos.html', favoritos=favoritos)  # Envia para a página favoritos.html
    except Exception as e:
        flash(f'Erro ao carregar favoritos: {str(e)}')
        return redirect(url_for('home'))  # Em caso de erro, redireciona para a home

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/imagens/<filename>')
def imagens(filename):
    return send_from_directory(os.path.join(app.root_path, 'imagens'), filename)

@app.route('/dark_mode_on')
def dark_mode_on():
    session['dark_mode'] = True
    return redirect(url_for('home'))

@app.route('/dark_mode_off')
def dark_mode_off():
    session['dark_mode'] = False
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
