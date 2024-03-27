from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import re
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(6), unique=True, nullable=False)
    password = db.Column(db.String(6), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task = db.Column(db.String(2000), nullable=False)
    done = db.Column(db.Boolean, default=False)

@app.route("/", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash("Credenciales incorrectas. Inténtalo de nuevo.", "error")
    return render_template('login.html')



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Validar el formato de la contraseña
        if len(password) < 6 or not any(char.isupper() for char in password):
            flash("La contraseña debe tener al menos 6 caracteres y contener al menos una letra mayúscula.", "error")
            return redirect(url_for('signup'))

        try:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash("Usuario registrado correctamente. Por favor inicia sesión.", "success")
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash("El nombre de usuario ya está en uso.", "error")
    return render_template('signup.html')

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route("/index")
def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user_todos = Todo.query.filter_by(user_id=user_id).all()
    return render_template('index.html', todos=user_todos)

@app.route("/agregar", methods=["POST"])
def agregar():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    todo_text = request.form['todo']
    todo = Todo(user_id=user_id, task=todo_text)
    db.session.add(todo)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    user_id = session.get('user_id')
    todo = Todo.query.get(id)
    if todo.user_id != user_id:
        flash("No tienes permiso para editar esta tarea.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        todo.task = request.form.get("todo")
        db.session.commit()
        return redirect(url_for("index"))
    else:
        return render_template("editar.html", todo=todo)

@app.route("/check/<int:id>")
def check(id):
    user_id = session.get('user_id')
    todo = Todo.query.get(id)
    if todo.user_id == user_id:
        todo.done = not todo.done
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/eliminar/<int:id>")
def eliminar(id):
    user_id = session.get('user_id')
    todo = Todo.query.get(id)
    if todo.user_id == user_id:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for("index"))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
