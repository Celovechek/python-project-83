from flask import Flask, render_template, request, redirect, url_for, flash, \
    get_flashed_messages
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import validators
from page_analyzer import db
import requests
from requests.exceptions import SSLError, RequestException
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = db.connect(DATABASE_URL)


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

        conn = db.connect(DATABASE_URL)
        url = db.find_url_with_name(conn, normalized_url)
        if url:
            flash('Страница уже существует', 'info')
            id = url.get('id')
        else:
            id = db.add_url(conn, normalized_url)
            db.close(conn)
            flash('Страница успешно добавлена', 'success')

        return redirect(url_for('show_url', id=id))

    return render_template('index.html')


@app.route('/urls/<int:id>')
def show_url(id):
    conn = db.connect(DATABASE_URL)
    url = db.find_url(conn, id)
    checks = db.find_url_checks(conn, id)
    db.close(conn)

    if not url:
        flash('Запись не найдена', 'danger')
        return redirect(url_for('index'))

    return render_template('show_url.html', url=url, checks=checks)


@app.route('/urls')
def show_urls():
    conn = db.connect(DATABASE_URL)
    urls = db.find_urls(conn)
    checks_dict = {}
    for url in urls:
        try:
            checks_dict.update({url["id"]: db.find_url_checks(conn,
                                                              url["id"])[0]})
        except IndexError:
            checks_dict.update({'url_id': url["id"],
                                'status_code': '',
                                'created_at': ''})
    db.close(conn)
    return render_template('urls.html', urls=urls, checks=checks_dict)


@app.post('/urls/<id>/checks')
def checks(id):
    try:
        conn = db.connect(DATABASE_URL)
        url = db.find_url(conn, id)
        response = requests.get(url.get('name'), timeout=5)

        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.title.string if soup.title else ''
        description = soup.find(attrs={"name": "description"})
        description = description['content'] if description else ''
        check_data = {
            'url_id': id,
            'status_code': response.status_code,
            'h1': h1,
            'title': title,
            'description': description
        }

        flash('Страница успешно проверена', 'success')

        db.add_url_check(conn, check_data)
    except SSLError as e:
        flash(f'Ошибка SSL: {str(e)}', 'danger')
    except RequestException as e:
        flash('Произошла ошибка при проверке', 'danger')
    finally:
        db.close(conn)

    return redirect(url_for('show_url', id=id), 302)


def validate_url(url: str):
    errors = []

    if not url:
        return ['URL обязателен']
    if not validators.url(url):
        errors.append('Некорректный URL')
    if len(url) > 255:
        errors.append('Длина URl превышает 255 символов')

    return errors
