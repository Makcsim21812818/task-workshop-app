from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель задачи — это описание таблицы в базе данных
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)          # уникальный номер
    title = db.Column(db.String(200), nullable=False)     # что сделать
    assignee = db.Column(db.String(50), nullable=False)   # кому
    deadline = db.Column(db.String(20))                   # срок
    status = db.Column(db.String(20), default='новая')    # новая / в работе / готово
    priority = db.Column(db.String(20), default='обычный')   # ← новая строка
    created = db.Column(db.DateTime, default=datetime.utcnow)  # когда создали


# Создать таблицы при первом запуске
with app.app_context():
    db.create_all()

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Редактирование задачи."""
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.title = request.form['title']
        task.assignee = request.form['assignee']
        task.deadline = request.form['deadline']
        task.priority = request.form.get('priority', 'обычный')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', task=task)

@app.route('/')
def index():
    """Главная страница — список всех задач."""
    tasks = Task.query.order_by(Task.created.desc()).all()
    return render_template('index.html', tasks=tasks)


@app.route('/add', methods=['GET', 'POST'])
def add():
    """Добавление новой задачи."""
    if request.method == 'POST':
        task = Task(
            title=request.form['title'],
            assignee=request.form['assignee'],
            deadline=request.form['deadline'],
            priority=request.form.get('priority', 'обычный')
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/status/<int:id>/<status>')
def change_status(id, status):
    """Смена статуса задачи."""
    task = Task.query.get_or_404(id)
    task.status = status
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete(id):
    """Удаление задачи."""
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)