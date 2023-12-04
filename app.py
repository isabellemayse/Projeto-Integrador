from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'
app.config['SECRET_KEY'] = 'senha' #chave para a sessão do usuario logado
db = SQLAlchemy(app)

class LoginUsuarioComum(db.Model): #classe para o login do usuario comum
    __tablename__ = 'login_usuario_comum' #nome da tabela

    matricula = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    senha = db.Column(db.String)

    def __init__(self, matricula, nome, senha):
        self.matricula = matricula
        self.nome = nome
        self.senha = senha

class Categoria(db.Model): #classe para as categorias
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    subcategorias = db.relationship('Subcategoria', backref='categoria', lazy=True) #relacionamento com a tabela subcategorias

    def __init__(self, nome):
        self.nome = nome

class Subcategoria(db.Model): #classe para as subcategorias
    __tablename__ = 'subcategorias'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False) #relacionamento com a tabela categorias
    Subcategoria2 = db.relationship('Subcategoria2', backref='subcategoria', lazy=True) #relacionamento com a tabela subcategorias2

    def __init__(self, nome, categoria_id):
        self.nome = nome
        self.categoria_id = categoria_id 

class Subcategoria2(db.Model): #classe para as subcategorias 2
    __tablename__ = 'subcategorias2'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategorias.id'), nullable=False) #relacionamento com a tabela subcategorias

    def __init__(self, nome, subcategoria_id):
        self.nome = nome
        self.subcategoria_id = subcategoria_id

class Chamados(db.Model): #classe para os chamados
    __tablename__ = 'chamados'

    id = db.Column(db.Integer, primary_key=True)
    servico = db.Column(db.String)
    descricao = db.Column(db.String)
    status = db.Column(db.String)
    matriculaComum = db.Column(db.Integer, db.ForeignKey('login_usuario_comum.matricula'))
    usuarioComum = db.relationship('LoginUsuarioComum', foreign_keys=matriculaComum)
    data = db.Column(db.DateTime, default=datetime.now())
    prioridade = db.Column(db.String)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategorias.id'), nullable=False)
    subcategoria2_id = db.Column(db.Integer, db.ForeignKey('subcategorias2.id'), nullable=False)

    categoria = db.relationship('Categoria', foreign_keys=categoria_id) #relacionamento com a tabela categorias
    subcategoria = db.relationship('Subcategoria', foreign_keys=subcategoria_id) #relacionamento com a tabela subcategorias
    subcategoria2 = db.relationship('Subcategoria2', foreign_keys=subcategoria2_id) #relacionamento com a tabela subcategorias2

    def __init__(self, servico, descricao, status, matriculaComum, data, prioridade, categoria_id, subcategoria_id, subcategoria2_id):
        self.servico = servico
        self.descricao = descricao
        self.status = status
        self.matriculaComum = matriculaComum
        self.data = data or datetime.now()
        self.prioridade = prioridade
        self.categoria_id = categoria_id
        self.subcategoria_id = subcategoria_id
        self.subcategoria2_id = subcategoria2_id

    @staticmethod
    def calcular_pontuacao(categoria_id, subcategoria_id, subcategoria2_id): #função para calcular a pontuação do chamado
        pontuacao = 0 #pontuação inicial

        categoria_id = int(categoria_id) #converte para inteiro
        subcategoria_id = int(subcategoria_id)
        subcategoria2_id = int(subcategoria2_id)

        # Lógica de pontuação para a tabela de categoria
        if categoria_id == 1:
            pontuacao += 20
        elif categoria_id == 2:
            pontuacao += 20

        # Lógica de pontuação para a tabela de subcategoria
        if subcategoria_id == 22 or subcategoria_id == 12:
            pontuacao += 30
        elif subcategoria_id == 21 or subcategoria_id == 11 or subcategoria_id == 13 or subcategoria_id == 23:
            pontuacao += 20
        elif subcategoria_id == 24 or subcategoria_id == 25:
            pontuacao += 10

        # Lógica de pontuação para a tabela de subcategoria2
        if subcategoria2_id in [216, 217, 218, 111,113,114,116,117,211,212,213,215,216,217,218]:
            pontuacao += 20
        elif subcategoria2_id in [112, 115, 214]:
            pontuacao += 30
        elif subcategoria2_id in [219,220]:
            pontuacao += 10

        print(f"Após Categoria: {pontuacao}") #so pra eu conferir como ficnou

        return pontuacao

with app.app_context(): #cria o banco de dados
    db.create_all()

admin = False #variavel para verificar se o usuario é admin ou não

def calcular_prioridade(valores_formulario): #função para calcular a prioridade do chamado
    pontuacao = Chamados.calcular_pontuacao( #chama a função calcular_pontuacao
        valores_formulario['categoria_id'],
        valores_formulario['subcategoria_id'],
        valores_formulario['subcategoria2_id']
    )

    if pontuacao >= 80: #verifica a pontuação e retorna a prioridade
        return 'Alta'
    elif 50 <= pontuacao <= 70:
        return 'Média'
    else:
        return 'Baixa'

@app.route('/')
def index():
    global admin #variavel global para verificar se o usuario é admin ou não
    admin = False 
    return render_template('login.html') #pagina inicial

@app.route('/login', methods=['GET', 'POST'])
def login():
    global admin
    if request.method == 'POST': 
        matricula = request.form['matricula']
        senha = request.form['senha']
        
        usuario = LoginUsuarioComum.query.filter_by(matricula=matricula).first() #verifica se a matricula existe no banco de dados
        if usuario:
            if usuario.senha == senha:
                session['matricula_atual'] = str(matricula)
                return redirect(url_for('chamados'))
            else:
                flash('Senha incorreta', 'error')
                return render_template('login.html', erro='Senha incorreta')

        elif matricula == '9999' and senha == 'admin': #verifica se o usuario é admin
            session['admin'] = True
            return redirect(url_for('chamados'))
            
    return render_template('login.html')

@app.route('/chamados', methods=['GET']) 
def chamados():
    prioridade_filtro = request.args.get('prioridade', '') #variavel para o filtro de prioridade
    status_filtro = request.args.get('status', '') #variavel para o filtro de status

    chamados = Chamados.query #pegar todos os chamados

    if prioridade_filtro:
        chamados = chamados.filter_by(prioridade=prioridade_filtro) #filtra por prioridade

    if status_filtro: #filtra por status
        chamados = chamados.filter_by(status=status_filtro)

    chamados = chamados.all() 

    nome_usuario = None #variavel para o nome do usuario logado
    matricula_atual = session.get('matricula_atual')
    if matricula_atual:
        usuario = LoginUsuarioComum.query.filter_by(matricula=matricula_atual).first() #pegar do banco de dados
        if usuario:
            nome_usuario = usuario.nome

    return render_template('chamados.html', chamados=chamados, is_admin=session.get('admin'), matricula_atual=matricula_atual, nome_usuario=nome_usuario)


@app.route('/chamados/add', methods=['GET', 'POST'])
def add():
    categorias = Categoria.query.all() #pega todas as categorias do banco de dados

    if request.method == 'POST': #se o metodo for post, adiciona o chamado no banco de dados
        servico = request.form['servico'] #pega os dados do formulario
        descricao = request.form['descricao'] 
        status = "Aberto"
        matriculaComum = session.get('matricula_atual')
        data = datetime.now()

        # Altere esta parte para garantir que você está passando os dados corretos
        categoria_id = request.form['categoria']
        subcategoria_id = request.form['subcategoria']
        subcategoria2_id = request.form.get('subcategoria2')

        prioridade = calcular_prioridade({ #chama a função calcular_prioridade
            'categoria_id': categoria_id,
            'subcategoria_id': subcategoria_id,
            'subcategoria2_id': subcategoria2_id
        })

        novo_chamado = Chamados(
            servico, descricao, status, matriculaComum, data, prioridade, categoria_id, subcategoria_id, subcategoria2_id
        ) #cria o novo chamado
        db.session.add(novo_chamado)
        db.session.commit()
        flash('Chamado adicionado com sucesso!', 'success')
        return redirect(url_for('chamados'))

    return render_template('add.html', categorias=categorias)


@app.route('/get_categorias') #obtem as categorias
def get_categorias():
    try: 
        categorias = Categoria.query.all() #pega todas as categorias do banco de dados
        categorias_data = [{'id': cat.id, 'nome': cat.nome} for cat in categorias] #cria um dicionario com as categorias
        return jsonify(categorias_data) #retorna as categorias em formato json
    except Exception as e: 
        print(f"Erro ao obter categorias: {e}") #se der erro, retorna uma mensagem de erro
        return jsonify({'error': 'Erro interno do servidor'}), 500 #retorna o erro 500

@app.route('/get_subcategorias/<int:categoria_id>') #obtem as subcategorias
def get_subcategorias(categoria_id): 
    subcategorias = Subcategoria.query.filter_by(categoria_id=categoria_id).all() #pega todas as subcategorias do banco de dados
    subcategorias_data = [{'id': sub.id, 'nome': sub.nome} for sub in subcategorias] #cria um dicionario com as subcategorias
    return jsonify(subcategorias_data) #retorna as subcategorias em formato json

@app.route('/get_subcategoria2/<int:subcategoria_id>') #obtem as subcategorias2
def get_subcategorias2(subcategoria_id):
    try:
        subcategoria2 = Subcategoria2.query.filter_by(subcategoria_id=subcategoria_id).all() #pega todas as subcategorias2 do banco de dados
        return jsonify([{'id': sub2.id, 'nome': sub2.nome} for sub2 in subcategoria2]) #cria um dicionario com as subcategorias2 e retorna em formato json
    except Exception as e:
        print(f"Erro ao obter subcategorias2: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/excluir/<int:id>') #exclui o chamado
def excluir(id):
    matricula_atual = session.get('matricula_atual') #matricula do usuario logado
    chamado = Chamados.query.get(id)
   
    if matricula_atual == '9999': #verifica se o usuario é admin, se for deve excluir qkla chamado
        db.session.delete(chamado)
        db.session.commit()
        flash('Chamado excluído com sucesso!', 'success')

    elif str(chamado.matriculaComum) == matricula_atual: #verifica se o usuario é o criador do chamado p excluir
        db.session.delete(chamado)
        db.session.commit()
        flash('Chamado excluído com sucesso!', 'success')
    else:
        flash('Você não tem permissão para excluir esse chamado', 'error')

    return redirect(url_for('chamados'))

@app.route('/editar/<int:id>', methods=['GET', 'POST']) #edita o chamado
def editar(id):
    matricula_atual = session.get('matricula_atual') #matricula do usuario logado
    chamado = Chamados.query.get(id) #pega o chamado do banco de dados

    if request.method == 'POST' and matricula_atual == '9999': #se o usuario for admin, permite editar todos os campos
        chamado.servico = request.form['servico']
        chamado.prioridade = request.form['prioridade']
        chamado.descricao = request.form['descricao']
        chamado.categoria_id = request.form['categoria']
        chamado.subcategoria_id = request.form['subcategoria']
        chamado.subcategoria2_id = request.form['subcategoria2']
        chamado.status = request.form['status'] #altera o status somente para o adm

        chamado.prioridade = calcular_prioridade({
            'categoria_id': chamado.categoria_id,
            'subcategoria_id': chamado.subcategoria_id,
            'subcategoria2_id': chamado.subcategoria2_id
        })

        db.session.commit()
        flash('Chamado editado com sucesso!', 'success')
        return redirect(url_for('chamados'))
    
    elif request.method == 'POST' and (str(chamado.matriculaComum) == matricula_atual): #usuario criador do chamado
        chamado.servico = request.form['servico']
        chamado.prioridade = request.form['prioridade']
        chamado.descricao = request.form['descricao']
        chamado.categoria_id = request.form['categoria']
        chamado.subcategoria_id = request.form['subcategoria']
        chamado.subcategoria2_id = request.form['subcategoria2']

        chamado.prioridade = calcular_prioridade({
            'categoria_id': chamado.categoria_id,
            'subcategoria_id': chamado.subcategoria_id,
            'subcategoria2_id': chamado.subcategoria2_id
        })

        db.session.commit()
        flash('Chamado editado com sucesso!', 'success')
        return redirect(url_for('chamados'))

    # Se o usuário não for o administrador e não for o criador do chamado, sem permissão
    if matricula_atual != '9999' and str(chamado.matriculaComum) != matricula_atual:
        flash('Você não tem permissão para editar esse chamado', 'error')
        return redirect(url_for('chamados'))

    return render_template('editar.html', chamado=chamado)

@app.route('/voltar')
def voltar():
    return redirect(url_for('chamados'))

@app.route('/logout')
def logout():
    global admin 
    admin = False #reseta a variavel admin
    session.clear()  # Limpa todas as chaves da sessão
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)