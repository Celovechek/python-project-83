from flask import Flask, render_template, request, redirect, url_for, flash
from psycopg2 import connect, errors
from datetime import datetime
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from validators import url as validate_url

# Загрузка переменных окружения
load_dotenv()

# Инициализация приложения
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


# Функция для подключения к базе данных
def get_db_connection():
    return connect(DATABASE_URL)


# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Получаем URL из формы
        raw_url = request.form['url']

        # Нормализуем URL
        parsed_url = urlparse(raw_url)
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Валидация URL
        if not validate_url(normalized_url):
            flash('Некорректный URL', 'danger')
            return render_template('index.html'), 422

        if len(normalized_url) > 255:
            flash('URL превышает 255 символов', 'danger')
            return render_template('index.html'), 422

        try:
            # Подключение к базе данных
            conn = get_db_connection()
            cur = conn.cursor()

            # Попытка добавить URL в базу данных и получить его ID
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            new_id = cur.fetchone()[0]  # Получаем ID новой записи
            conn.commit()
            cur.close()
            conn.close()

            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_detail', id=new_id))  # Редирект на страницу деталей
        except errors.UniqueViolation:
            # Если URL уже существует
            conn.rollback()
            cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
            existing_id = cur.fetchone()[0]
            cur.close()
            conn.close()

            flash('URL уже существует', 'info')
            return redirect(url_for('url_detail', id=existing_id))  # Редирект на существующий URL

    return render_template('index.html')


@app.route('/urls/<int:id>')
def url_detail(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
    url = cur.fetchone()
    cur.close()
    conn.close()

    if not url:
        flash('Запись не найдена', 'danger')
        return redirect(url_for('index'))

    url = {
        'id': url[0],
        'name': url[1],
        'created_at': url[2]
    }

    return render_template('url_detail.html', url=url)


@app.route('/urls')
def urls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
    urls_list = [{
        'id': url[0],
        'name': url[1],
        'created_at': url[2]
        }
        for url in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template('urls.html', urls=urls_list)
