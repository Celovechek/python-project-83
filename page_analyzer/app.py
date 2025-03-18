from flask import Flask, render_template, request, redirect, url_for, flash, \
    get_flashed_messages
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import validators
from page_analyzer import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw_url = request.form['url']

        parsed_url = urlparse(raw_url)
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        errors = validate_url(normalized_url)
        if errors:
            for error in errors:
                flash(error, 'danger')
            messages = get_flashed_messages(with_categories=True)
            return render_template(
                'index.html',
                messages=messages,
            ), 422
        conn = db.create_connection(DATABASE_URL)
        url = db.get_url_by_name(conn, normalized_url)
        if url:
            flash('URL уже существует', 'info')
            id = url.id
        else:
            id = db.add_url(conn, normalized_url)
            db.close(conn)

            flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=id))
    return render_template('index.html')


@app.route('/urls/<int:id>')
def show_url(id):
    conn = db.create_connection(DATABASE_URL)
    url = db.get_url(conn, id)
    db.close(conn)

    if not url:
        flash('Запись не найдена', 'danger')
        return redirect(url_for('index'))

    return render_template('show_url.html', url=url)


@app.route('/urls')
def show_urls():
    conn = db.create_connection(DATABASE_URL)
    urls = db.get_urls(conn)
    db.close(conn)
    return render_template('urls.html', urls=urls)


def validate_url(url: str):
    errors = []

    if not url:
        return ['URL обязателен']
    if not validators.url(url):
        errors.append('Некорректный URL')
    if len(url) > 255:
        errors.append('Длина URl превышает 255 символов')

    return errors
