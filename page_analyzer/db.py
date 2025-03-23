import psycopg2
import psycopg2.extras
from datetime import datetime


def close(conn):
    """Закрывает подключение к базе данных"""
    conn.close()


def connect(database_url):
    """Создает подключение к базе данных"""
    return psycopg2.connect(database_url)


def find_url_with_name(conn, url: str) -> dict:
    """Ищет url в БД по ссылке"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE name = %s;", (url, ))
        url = cur.fetchone()
    return url


def add_url(conn, url: str) -> int:
    """Добавляет url в БД и возвращает id"""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
            (url, datetime.now())
        )
        id = cur.fetchone()[0]
        conn.commit()
    return id


def find_url(conn, id: int) -> dict:
    """Ищет url в БД по id"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
    return url


def find_urls(conn):
    """Выводит список словарей со всеми сайтами, которые находятся в БД"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
        urls = cur.fetchall()
    return urls


def add_url_check(conn, check_data: dict) -> None:
    """Добавляет информацию о проверке в таблицу url_checks"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO url_checks (
                    url_id,
                    status_code,
                    h1,
                    title,
                    description,
                    created_at)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
                    (check_data['url_id'],
                     check_data['status_code'],
                     check_data['h1'],
                     check_data['title'],
                     check_data['description'],
                     datetime.now()),
                    )
        conn.commit()


def find_url_checks(conn, url_id: int) -> dict:
    """Ищет информацию о провероках url по id в таблице url_checks"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""SELECT * FROM url_checks WHERE url_id = %s
                       ORDER BY created_at DESC;""",
                    (url_id, )
                    )
        checks = cur.fetchall()
    return checks
