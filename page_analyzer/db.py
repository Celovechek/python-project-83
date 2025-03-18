import psycopg2
import psycopg2.extras
from datetime import datetime


def close(conn):
    conn.close()


def create_connection(DATABASE_URL):
    return psycopg2.connect(DATABASE_URL)


def get_url_by_name(conn, url):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:

        cur.execute("""
            SELECT * FROM urls
            WHERE name = %s;
            """,
                    (url, ))
        url = cur.fetchone()

    return url


def add_url(conn, url):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
            (url, datetime.now())
        )
        id = cur.fetchone()[0]
        conn.commit()
    return id


def get_url(conn, id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
    return url


def get_urls(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
        urls = cur.fetchall()
    return urls
