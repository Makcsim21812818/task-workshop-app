from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///workshop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'workshop-secret-key-change-me')
db = SQLAlchemy(app)

# Модель задачи — это описание таблицы в базе данных
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)          # уникальный номер
    title = db.Column(db.String(200), nullable=False)     # что сделать
    assignee = db.Column(db.String(50), nullable=False)   # кому
    deadline = db.Column(db.String(20))                   # срок
    status = db.Column(db.String(20), default='новая')    # новая / в работе / готово
    priority = db.Column(db.String(20), default='обычный')   # ← новая строка
    weight = db.Column(db.Integer, default=0)   # ← вес 1 шт в граммах (для продукции)
    created = db.Column(db.DateTime, default=datetime.utcnow)  # когда создали

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    color = db.Column(db.String(20), default='белый')
    quantity = db.Column(db.Integer, default=0)
    weight = db.Column(db.Integer, default=0)     # ← ЭТА строка должна быть здесь
    created = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)   # что печатать
    color = db.Column(db.String(20), default='белый')          # цвет
    quantity = db.Column(db.Integer, nullable=False, default=1) # сколько штук
    filament_grams = db.Column(db.Integer, nullable=False, default=0)  # всего грамм филамента
    deadline = db.Column(db.String(20))                        # срок
    status = db.Column(db.String(20), default='в очереди')     # в очереди / печатается / готово
    created = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)      # доход / расход
    category = db.Column(db.String(50), nullable=False)  # Ozon / Пластик / Электричество и т.д.
    amount = db.Column(db.Float, nullable=False)         # сумма в рублях
    date = db.Column(db.String(20))                      # дата операции
    description = db.Column(db.String(200))              # короткое описание (опционально)
    created = db.Column(db.DateTime, default=datetime.utcnow)

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

@app.route('/warehouse')
def warehouse():
    """Список всех позиций на складе."""
    materials = Material.query.order_by(Material.category, Material.name).all()
    return render_template('warehouse.html', materials=materials)


@app.route('/warehouse/add', methods=['GET', 'POST'])
def warehouse_add():
    """Добавление новой позиции."""
    if request.method == 'POST':
        material = Material(
    name=request.form['name'],
    category=request.form['category'],
    color=request.form.get('color', 'белый'),
    quantity=int(request.form.get('quantity', 0) or 0),
    weight=int(request.form.get('weight', 0) or 0)
)
        db.session.add(material)
        db.session.commit()
        return redirect(url_for('warehouse'))
    return render_template('warehouse_add.html')


@app.route('/warehouse/edit/<int:id>', methods=['GET', 'POST'])
def warehouse_edit(id):
    """Редактирование позиции."""
    material = Material.query.get_or_404(id)
    if request.method == 'POST':
        material.name = request.form['name']
        material.category = request.form['category']
        material.color = request.form.get('color', 'белый')
        material.quantity = int(request.form.get('quantity', 0) or 0)
        material.weight = int(request.form.get('weight', 0) or 0)
        db.session.commit()
        return redirect(url_for('warehouse'))
    return render_template('warehouse_edit.html', material=material)


@app.route('/warehouse/change/<int:id>/<delta>')
def warehouse_change(id, delta):
    """Быстрое изменение остатка на delta (может быть отрицательным)."""
    material = Material.query.get_or_404(id)
    try:
        delta_int = int(delta)   # превращаем текст в число
    except ValueError:
        delta_int = 0            # если пришло что-то нечисловое — считаем нулём
    material.quantity = max(0, material.quantity + delta_int)
    db.session.commit()
    return redirect(url_for('warehouse'))

@app.route('/warehouse/delete/<int:id>')
def warehouse_delete(id):
    """Удаление позиции."""
    material = Material.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    return redirect(url_for('warehouse'))

@app.route('/production')
def production():
    """Список заказов на печать."""
    orders = Order.query.all()
    priority = {'печатается': 0, 'в очереди': 1, 'готово': 2}
    orders.sort(key=lambda o: (priority.get(o.status, 9), o.created))
    return render_template('production.html', orders=orders)


@app.route('/production/add', methods=['GET', 'POST'])
def production_add():
    """Новый заказ."""
    if request.method == 'POST':
        order = Order(
            product_name=request.form['product_name'],
            color=request.form.get('color', 'белый'),
            quantity=int(request.form.get('quantity', 1) or 1),
            filament_grams=int(request.form.get('filament_grams', 0) or 0),
            deadline=request.form['deadline']
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for('production'))
    return render_template('production_add.html')


@app.route('/production/edit/<int:id>', methods=['GET', 'POST'])
def production_edit(id):
    """Редактирование заказа."""
    order = Order.query.get_or_404(id)
    if request.method == 'POST':
        order.product_name = request.form['product_name']
        order.color = request.form.get('color', 'белый')
        order.quantity = int(request.form.get('quantity', 1) or 1)
        order.filament_grams = int(request.form.get('filament_grams', 0) or 0)
        order.deadline = request.form['deadline']
        db.session.commit()
        return redirect(url_for('production'))
    return render_template('production_edit.html', order=order)


@app.route('/production/status/<int:id>/<status>')
def production_status(id, status):
    """Смена статуса. При 'готово' списываем филамент и пополняем склад."""
    order = Order.query.get_or_404(id)

    if status == 'готово':
        # 1. Ищем филамент нужного цвета
        filament = Material.query.filter_by(category='филамент', color=order.color).first()
        if not filament:
            flash(f'❌ На складе нет филамента цвета «{order.color}». Добавь филамент сначала.', 'error')
            return redirect(url_for('production'))

        # 2. Проверяем, хватает ли грамм
        if filament.quantity < order.filament_grams:
            flash(
                f'❌ Недостаточно {order.color}ого филамента: '
                f'нужно {order.filament_grams} г, на складе {filament.quantity} г.',
                'error'
            )
            return redirect(url_for('production'))

        # 3. Списываем филамент
        filament.quantity -= order.filament_grams

        # 4. Пополняем склад продукцией (или создаём новую позицию)
        product = Material.query.filter_by(
            category='продукция',
            name=order.product_name,
            color=order.color
        ).first()
        if product:
            product.quantity += order.quantity
        else:
            product = Material(
                name=order.product_name,
                category='продукция',
                color=order.color,
                quantity=order.quantity
            )
            db.session.add(product)

    order.status = status
    db.session.commit()
    return redirect(url_for('production'))


@app.route('/production/delete/<int:id>')
def production_delete(id):
    """Удаление заказа."""
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('production'))

@app.route('/finance')
def finance():
    """Страница финансов: список операций и итоги."""
    transactions = Transaction.query.order_by(Transaction.created.desc()).all()

    # Итоги по деньгам
    total_income = sum(t.amount for t in transactions if t.type == 'доход')
    total_expense = sum(t.amount for t in transactions if t.type == 'расход')
    balance = total_income - total_expense

    # Статистика филамента — берём из готовых заказов
    done_orders = Order.query.filter_by(status='готово').all()
    filament_grams = sum(o.filament_grams for o in done_orders)
    filament_cost = filament_grams * 0.841  # себестоимость грамма

    return render_template(
        'finance.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        filament_grams=filament_grams,
        filament_cost=filament_cost
    )


@app.route('/finance/add', methods=['GET', 'POST'])
def finance_add():
    """Новая операция."""
    if request.method == 'POST':
        transaction = Transaction(
            type=request.form['type'],
            category=request.form['category'],
            amount=float(request.form.get('amount', 0) or 0),
            date=request.form['date'],
            description=request.form.get('description', '')
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('finance'))
    return render_template('finance_add.html')


@app.route('/finance/delete/<int:id>')
def finance_delete(id):
    """Удаление операции."""
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('finance'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)