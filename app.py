from flask import Flask, render_template, request, redirect, url_for, flash, session
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

    def __init__(self, servico, descricao, status, matriculaComum, data, prioridade):
        self.servico = servico
        self.descricao = descricao
        self.status = status
        self.matriculaComum = matriculaComum
        self.data = data or datetime.now()
        self.prioridade = prioridade

with app.app_context(): #cria o banco de dados
    db.create_all()

admin = False #variavel para verificar se o usuario é admin ou não

@app.route('/')
def index():
    global admin #variavel global para verificar se o usuario é admin ou não
    admin = False 
    return render_template('login.html')

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
    if request.method == 'POST':
        servico = request.form['servico']
        descricao = request.form['descricao']
        status = "Aberto" #status padrão
        matriculaComum = session.get('matricula_atual') #matricula do usuario logado
        data = datetime.now()
        prioridade = request.form['prioridade']
        novo_chamado = Chamados(servico, descricao, status, matriculaComum, data, prioridade)
        db.session.add(novo_chamado)
        db.session.commit()
        flash('Chamado adicionado com sucesso!', 'success')
        return redirect(url_for('chamados'))

    return render_template('add.html')

@app.route('/excluir/<int:id>') #exclui o chamado
def excluir(id):
    matricula_atual = session.get('matricula_atual')
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
    matricula_atual = session.get('matricula_atual')
    chamado = Chamados.query.get(id)

    if request.method == 'POST' and matricula_atual == '9999': #se o usuario for admin, permite editar todos os campos
        chamado.servico = request.form['servico']
        chamado.descricao = request.form['descricao']
        chamado.prioridade = request.form['prioridade']
        chamado.status = request.form['status'] #altera o status somente para o adm

        db.session.commit()
        flash('Chamado editado com sucesso!', 'success')
        return redirect(url_for('chamados'))
    
    elif request.method == 'POST' and (str(chamado.matriculaComum) == matricula_atual): #usuario criador do chamado
        chamado.servico = request.form['servico']
        chamado.descricao = request.form['descricao']
        chamado.prioridade = request.form['prioridade']

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