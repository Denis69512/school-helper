from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Перевіряємо, чи існує файл index.html
    if os.path.exists('index.html'):
        return send_file('index.html')
    else:
        return "Файл index.html не знайдено. Переконайтеся, що він є в репозиторії."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
