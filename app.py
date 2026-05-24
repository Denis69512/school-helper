from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'sekretnyi_klyuch_school_helper'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== МОДЕЛІ БАЗИ ДАНИХ ==========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    class_name = db.Column(db.String(50), default='5-A')
    coins = db.Column(db.Integer, default=100)
    is_admin = db.Column(db.Boolean, default=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    executor_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== СТВОРЕННЯ БАЗИ ==========
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', coins=0, is_admin=True)
        db.session.add(admin)
        db.session.commit()

# ========== API ==========
@app.route('/')
def index():
    if os.path.exists('index.html'):
        return send_file('index.html')
    else:
        return "Файл index.html не знайдено. Переконайтеся, що він є в репозиторії."

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'User already exists'}), 400
    user = User(username=data['username'], password=data['password'], class_name=data.get('class', '5-A'))
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'coins': user.coins})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    return jsonify({'id': user.id, 'username': user.username, 'coins': user.coins, 'class': user.class_name, 'is_admin': user.is_admin})

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.filter_by(status='open').all()
    return jsonify([{
        'id': o.id,
        'title': o.title,
        'description': o.description,
        'price': o.price,
        'customer_id': o.customer_id
    } for o in orders])

@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    order = Order(
        title=data['title'],
        description=data['description'],
        price=data['price'],
        customer_id=data['customer_id']
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({'id': order.id})

@app.route('/take_order/<int:order_id>', methods=['POST'])
def take_order(order_id):
    data = request.json
    order = Order.query.get(order_id)
    if order and order.status == 'open':
        order.executor_id = data['executor_id']
        order.status = 'in_progress'
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Order not found'}), 400

@app.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    data = request.json
    order = Order.query.get(order_id)
    if order and order.customer_id == data['customer_id']:
        customer = User.query.get(order.customer_id)
        executor = User.query.get(order.executor_id)
        commission = int(order.price * 0.1)
        executor.coins += order.price
        customer.coins -= order.price
        order.status = 'completed'
        db.session.commit()
        return jsonify({'status': 'ok', 'commission': commission})
    return jsonify({'error': 'Cannot complete'}), 400

@app.route('/forum', methods=['GET'])
def get_forum():
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'content': p.content,
        'author_id': p.author_id,
        'created_at': p.created_at.isoformat()
    } for p in posts])

@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.json
    post = ForumPost(
        title=data['title'],
        content=data['content'],
        author_id=data['author_id']
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'id': post.id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
