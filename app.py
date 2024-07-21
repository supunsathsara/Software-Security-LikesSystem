from flask import Flask, request, render_template, redirect, url_for, make_response
import sqlite3
import uuid

app = Flask(__name__)
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
        key TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        key TEXT UNIQUE PRIMARY KEY
    )""")
    db.commit()

def new_session(db):
    key = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions (key) VALUES (?)", (key,))
    db.commit()
    response = make_response()
    response.set_cookie(COOKIE_NAME, key)
    return key, response

def get_session(db):
    key = request.cookies.get(COOKIE_NAME)
    cursor = db.cursor()
    cursor.execute("SELECT key FROM sessions WHERE key=?", (key,))
    row = cursor.fetchone()
    if row is None:
        key, response = new_session(db)
        return key, response
    return key, None

def store_like(db, key, like):
    cursor = db.cursor()
    cursor.execute("INSERT INTO likes (thing, key) VALUES (?, ?)", (like, key))
    db.commit()

def get_likes(db, key):
    cursor = db.cursor()
    cursor.execute("SELECT thing FROM likes WHERE key=?", (key,))
    result = [row['thing'] for row in cursor.fetchall()]
    return result

def forget_me(db, key):
    cursor = db.cursor()
    cursor.execute("DELETE FROM sessions WHERE key=?", (key,))
    cursor.execute("DELETE FROM likes WHERE key=?", (key,))
    db.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    #create_tables(db)  # Ensure tables are created
    key, response = get_session(db)
    print(key,response)
    if request.method == 'POST':
        like = request.form.get('likes')
        if like:
            store_like(db, key, like)
        return redirect(url_for('index'))

    likes = get_likes(db, key)
    print(likes)
    if response:
        response = make_response(render_template('index.html', title='Like System', likes=likes))
        response.set_cookie(COOKIE_NAME, key)
        return response
    return render_template('index.html', title='Like System', likes=likes)

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