from flask import Flask, request, render_template, redirect, url_for, make_response, flash
import sqlite3
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'NIBM123'
COOKIE_NAME = 'session_id'


def get_db():
    db = sqlite3.connect('data.db')
    db.row_factory = sqlite3.Row
    return db


def create_tables(db):
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        thing TEXT,
        username TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        key TEXT UNIQUE PRIMARY KEY,
        username TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT UNIQUE PRIMARY KEY,
        password TEXT
    )""")
    db.commit()


def new_session(db, username):
    key = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions (key, username) VALUES (?, ?)", (key, username))
    db.commit()
    response = make_response(redirect(url_for('index')))
    response.set_cookie(COOKIE_NAME, key)
    return key, response


def get_session(db):
    key = request.cookies.get(COOKIE_NAME)
    if not key:
        return None, None
    cursor = db.cursor()
    cursor.execute("SELECT key, username FROM sessions WHERE key=?", (key,))
    row = cursor.fetchone()
    if row is None:
        return None, None
    return row['username'], None


def store_like(db, username, like):
    cursor = db.cursor()
    cursor.execute("INSERT INTO likes (thing, username) VALUES (?, ?)", (like, username))
    db.commit()


def get_likes(db, username):
    cursor = db.cursor()
    cursor.execute("SELECT thing FROM likes WHERE username=?", (username,))
    result = [row['thing'] for row in cursor.fetchall()]
    return result


def forget_me(db, key):
    cursor = db.cursor()
    cursor.execute("DELETE FROM sessions WHERE key=?", (key,))
    db.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    create_tables(db)
    key = request.cookies.get(COOKIE_NAME)
    username, response = get_session(db)
    if username is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        like = request.form.get('likes')
        if like:
            store_like(db, username, like)
        return redirect(url_for('index'))

    likes = get_likes(db, username)
    if response:
        response = make_response(render_template('index.html', title='Like System', likes=likes))
        response.set_cookie(COOKIE_NAME, key)
        return response
    return render_template('index.html', title='Like System', likes=likes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            key, response = new_session(db, username)
            return response if response else redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout', methods=['POST'])
def logout():
    db = get_db()
    key = request.cookies.get(COOKIE_NAME)
    if key:
        cursor = db.cursor()
        cursor.execute("DELETE FROM sessions WHERE key=?", (key,))
        db.commit()
    response = make_response(redirect(url_for('login')))
    response.delete_cookie(COOKIE_NAME)
    return response


@app.route('/forget', methods=['POST'])
def forget():
    db = get_db()
    key = request.cookies.get(COOKIE_NAME)
    if key:
        forget_me(db, key)
    response = make_response(redirect(url_for('index')))
    response.delete_cookie(COOKIE_NAME)
    return response


if __name__ == '__main__':
    db = get_db()
    create_tables(db)
    app.run(debug=True)