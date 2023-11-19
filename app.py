from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'

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
    status = db.Column(db.String)
    matriculaComum = db.Column(db.Integer, db.ForeignKey('login_usuario_comum.matricula'))
    usuarioComum = db.relationship('LoginUsuarioComum', foreign_keys=matriculaComum)
    data = db.Column(db.DateTime, default=datetime.now())
    prioridade = db.Column(db.String)

    def __init__(self, servico, status, matriculaComum, data, prioridade):
        self.servico = servico
        self.status = status
        self.matriculaComum = matriculaComum
        self.data = data or datetime.now()
        self.prioridade = prioridade

with app.app_context(): #cria o banco de dados
    db.create_all() 

@app.route('/chamados') #rota para a pagina de chamados
def chamados():
    chamados = Chamados.query.all()
    return render_template('chamados.html', chamados=chamados)

@app.route('/chamados/add', methods=['GET', 'POST']) #rota para adicionar chamados
def add():
    if request.method == 'POST':
        servico = request.form['servico']
        status = "Aberto"
        matriculaComum = int(request.form['matriculaComum'])
        data = datetime.now()
        prioridade = request.form['prioridade']
        ok = Chamados(servico, status, matriculaComum, data, prioridade)
        db.session.add(ok)
        db.session.commit()
        return redirect(url_for('chamados'))

    return render_template('add.html')

@app.route('/excluir/<int:id>')
def excluir(id):
    chamado = Chamados.query.filter_by(id=id).first()
    db.session.delete(chamado)
    db.session.commit()
    chamado = Chamados.query.all()
    return render_template('chamados.html', chamados=chamado)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    chamado = Chamados.query.get(id)
    if request.method == 'POST':
        chamado.servico = request.form['servico']
        chamado.prioridade = request.form['prioridade']
        chamado.status = request.form['status']

        db.session.commit()
        return redirect(url_for('chamados'))

    return render_template('editar.html', chamado=chamado)

@app.route('/voltar')
def voltar():
    return redirect(url_for('chamados'))




if __name__ == '__main__':
    app.run(debug=True) #debug = true é para o servidor atualizar automaticamente quando salvar o arquivo