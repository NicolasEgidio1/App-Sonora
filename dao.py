import mysql.connector as banco
import base64
from selenium import webdriver
import bcrypt
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import mysql.connector
import mysql.connector
from mysql.connector import Error  # Importando a classe Error corretamente

def obter_conexao():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="admin", 
        database="sonora1"
    )

 
class Criptografia:
    def criptografar(self, texto):
        salt = bcrypt.gensalt()
        hash_valor = bcrypt.hashpw(texto.encode('utf-8'), salt)
        return hash_valor
    
    def verifica_criptografia(self, senha, senha_hash):
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

class usuario: 
    def buscar_todos_comentarios_do_usuario(id_usuario):
        query = """
            SELECT c.comentario, c.data_criacao, c.trecho, c.musica, c.artista
            FROM comentarios c
            WHERE c.id_usuario = %s
            ORDER BY c.data_criacao DESC
        """
        try:
            with obter_conexao() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (id_usuario,))
                    return cursor.fetchall()
        except Exception as e:
            print("Erro ao buscar comentários do usuário:", e)
            return []

    def adicionar_comentario(id_usuario, artista, musica, trecho, comentario):
        query = """
            INSERT INTO comentarios (id_usuario, artista, musica, trecho, comentario)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        # Obtém a conexão
        connection = obter_conexao()
        cursor = connection.cursor()

        # Executa a query
        cursor.execute(query, (id_usuario, artista, musica, trecho, comentario))

        # Confirma a transação no banco de dados
        connection.commit()

        # Fecha a conexão
        cursor.close()
        connection.close()

    def buscar_comentarios_por_musica(artista, musica, trecho):
        query = """
            SELECT c.comentario, c.data_criacao, c.trecho, u.nome, u.imagem
            FROM comentarios c
            JOIN usuario u ON c.id_usuario = u.id
            WHERE c.artista = %s AND c.musica = %s AND c.trecho = %s
            ORDER BY c.data_criacao DESC
        """
        try:
            with obter_conexao() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (artista, musica, trecho))
                    comentarios = cursor.fetchall()
            # Não formate a data aqui, só retorne o resultado cru
            return comentarios

        except Error as e:
            print(f"Erro ao buscar comentários: {e}")
            return []


    def realiza_login(email, senha):
        sql_select = "SELECT id, nome, senha FROM usuario WHERE email = %s"
        connection = banco.connect(
            host="localhost", 
            user="root", 
            password="admin", 
            database="sonora1"
        )
        cursor = connection.cursor()
        cursor.execute(sql_select, (email,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result is None:
            return None  # Usuário não encontrado
        
        id_usuario, nome, senha_hash = result
        cripto = Criptografia()
        
        if cripto.verifica_criptografia(senha, senha_hash):
            return id_usuario  # Retorna o id do usuário após login bem-sucedido
        
        return None  # Senha incorreta
    
    def buscar_usuario_por_id(id_usuario):
        conexao=banco.connect(host="localhost", user="root", password="admin", database="sonora1")
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, sexo, descricao, imagem FROM usuario WHERE id = %s", (id_usuario,))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario
    
    def insere_usuario(nome, sexo, telefone, cpf, email, senha):
        # Corrigindo a query SQL
        sql_insert = "INSERT INTO usuario (nome, sexo, telefone, cpf, email, senha) VALUES (%s, %s, %s, %s, %s, %s)"
        
        # Conexão com o banco de dados
        connection = banco.connect(
            host="localhost", 
            user="root", 
            password="admin", 
            database="sonora1"
        )
        
        # Criptografando a senha antes de salvar
        cripto = Criptografia()
        senha_hash = cripto.criptografar(senha)
        
        # Criando o cursor para executar a query
        cursor = connection.cursor()

        # Incluindo o código do país no telefone
        telefone_com_ddd = f"55{telefone}"

        # Executando a query com os valores fornecidos
        cursor.execute(sql_insert, (nome, sexo, telefone_com_ddd, cpf, email, senha_hash))
        
        # Confirmando a inserção no banco de dados
        connection.commit()
        
        # Fechando a conexão e o cursor
        cursor.close()
        connection.close()

    def favoritar_musica(id_usuario, artista, musica):
        conexao=banco.connect(host="localhost", user="root", password="admin", database="sonora1")
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO favoritos (id_usuario, artista, musica)
            VALUES (%s, %s, %s)
        """, (id_usuario, artista, musica))

        conexao.commit()
        cursor.close()
        conexao.close()


    def listar_favoritos(id_usuario):
        conexao=banco.connect(host="localhost", user="root", password="admin", database="sonora1")
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM favoritos WHERE id_usuario = %s", (id_usuario,))
        favoritos = cursor.fetchall()
        cursor.close()
        conexao.close()
        return favoritos
    
    def atualizar_perfil(id_usuario, nome, sexo, descricao):
        conexao=banco.connect(host="localhost", user="root", password="admin", database="sonora1")
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE usuario 
            SET nome = %s, sexo = %s, descricao = %s 
            WHERE id = %s
        """, (nome, sexo, descricao, id_usuario))
        conexao.commit()
        cursor.close()

    def atualizar_imagem_usuario(id_usuario, imagem_bytes):
        try:
            conexao = banco.connect(host='localhost', user='root', password='admin', database='sonora1')
            cursor = conexao.cursor()

            sql = "UPDATE usuario SET imagem = %s WHERE id = %s"
            cursor.execute(sql, (imagem_bytes, id_usuario))  # Passando os bytes da imagem
            conexao.commit()  # Confirma a transação

            cursor.close()
            conexao.close()

        except Exception as e:
            print(f"Erro ao atualizar imagem: {e}")
            raise  # Levanta o erro para diagnóstico

    def buscar_imagem_por_id(id_usuario):
        try:
            conexao = banco.connect(host='localhost', user='root', password='admin', database='sonora1')
            cursor = conexao.cursor()

            sql = "SELECT imagem FROM usuario WHERE id = %s"
            cursor.execute(sql, (id_usuario,))
            resultado = cursor.fetchone()

            cursor.close()
            conexao.close()

            if resultado and resultado[0]:
                return resultado[0]  # Retorna os bytes da imagem
            else:
                return None
        except Exception as e:
            print(f"Erro ao buscar imagem: {e}")
            return None
# No arquivo dao/usuario.py

    def verificar_favorito(id_usuario, artista, musica):
            # Conecta ao banco de dados
            conexao = banco.connect(
                host="localhost", 
                user="root", 
                password="admin", 
                database="sonora1"
            )
            cursor = conexao.cursor(dictionary=True)

            # Consulta para verificar se a música já está favoritada pelo usuário
            cursor.execute("""
                SELECT * FROM favoritos 
                WHERE id_usuario = %s AND artista = %s AND musica = %s
            """, (id_usuario, artista, musica))

            # Verifica se algum resultado foi retornado
            favorito = cursor.fetchone()

            cursor.close()
            conexao.close()

            return favorito  # Retorna o registro encontrado ou None se não encontrar

    def favoritar_musica(id_usuario, artista, musica):
            # Verifica se a música já está nos favoritos
            if usuario.verificar_favorito(id_usuario, artista, musica):
                print("Esta música já está nos favoritos.")
                return

            # Conecta ao banco de dados
            conexao = banco.connect(
                host="localhost", 
                user="root", 
                password="admin", 
                database="sonora1"
            )
            cursor = conexao.cursor()

            # Insere o novo favorito
            cursor.execute("""
                INSERT INTO favoritos (id_usuario, artista, musica)
                VALUES (%s, %s, %s)
            """, (id_usuario, artista, musica))

            conexao.commit()
            cursor.close()
            conexao.close()

class Chat:
    def redirect_to_whatsapp(telefone):
        conexao=banco.connect(host="localhost", user="root", password="admin", database="sonora1")
        with conexao.cursor() as cursor:
            cursor.execute("SELECT telefone FROM usuario WHERE id = 1")
            result = cursor.fetchone()
        if result:
            telefone = result[0]
        else:
            print("Não foi possível encontrar o número de telefone do destinatário.")    # ...

    def cadastrar_descricao(self, id_usuario, descricao):
        conexao=banco.connect(host="localhost", user="root", password="admin", database="sonora1")
        cursor = conexao.cursor()
        query = "SELECT descricao FROM usuario WHERE nome like %s"
        cursor.execute(query, (id_usuario,))
        result = cursor.fetchone()

        if result:
            # Se já houver uma descrição para o artista, atualiza a descrição existente
            query = "UPDATE artistas SET descricao = %s WHERE nome like %s"
            cursor.execute(query, (descricao, id_usuario))
            conexao.commit()
        else:
            # Se não houver uma descrição para o artista, insere uma nova descrição
            query = "INSERT INTO usuario (descricao) VALUES (%s) WHERE nome like %s"
            cursor.execute(query, (descricao, id_usuario))

        conexao.commit()


GENIUS_TOKEN = "bearer PhQVxOQ-ZqeZsPDTONc2NJN7KmhdPFn8zZsox3WOlZ2Y1ildP5A3GKt_lu2m6OPm"
headers = {'Authorization': f'Bearer {GENIUS_TOKEN}'}

def buscar_letra_genius(artista, musica):
    search_url = "https://api.genius.com/search"
    headers = {"Authorization": GENIUS_TOKEN}
    params = {"q": f"{musica} {artista}"}

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code != 200:
        return "Erro ao buscar na Genius."

    data = response.json()
    hits = data.get("response", {}).get("hits", [])

    if not hits:
        return "Letra não encontrada."

    song_url = hits[0]["result"]["url"]
    song_response = requests.get(song_url)
    if song_response.status_code != 200:
        return "Erro ao acessar a página da música."

    html = BeautifulSoup(song_response.text, "lxml")
    letra_divs = html.find_all("div", class_=lambda c: c and "Lyrics__Container" in c)

    if not letra_divs:
        return f"Letra não encontrada automaticamente. Veja aqui: {song_url}"

    partes_letra = [div.get_text(separator="\n") for div in letra_divs]
    letra = "\n\n".join(partes_letra).strip()

    # 🧽 Limpeza da letra
    linhas_filtradas = []
    for linha in letra.splitlines():
        if any(p in linha for p in ["Contributors", "Lyrics"]):
            continue
        if re.match(r"\[Letra de", linha):
            continue
        linhas_filtradas.append(linha.strip())

    letra_limpa = "\n".join(linhas_filtradas).strip()

    # 🔧 Opcional: remover [Refrão], [Verso 1], etc.
    letra_limpa = re.sub(r"\[.*?\]", "", letra_limpa).strip()

    return letra_limpa

def buscar_musicas_parecidas(nome_musica):
    # Exemplo com banco fictício ou API simulada
    musicas_exemplo = [
        {"artista": "Djavan", "musica": "Oceano"},
        {"artista": "Alok", "musica": "Oceano"},
        {"artista": "Ana Carolina", "musica": "Oceano"},
    ]

    # Aqui você pode fazer uma busca real no banco ou na API, retornando várias
    sugestoes = [m for m in musicas_exemplo if nome_musica.lower() in m["musica"].lower()]
    return sugestoes