import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('poems_corpus.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    q = request.args.get('q')
    if q:
        conn = get_db_connection()
        posts = conn.execute('SELECT poet, title FROM info WHERE poet = ?', (q,))
    else:
        posts = ''
    return render_template('index.html', posts=posts)

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/about')
def about():
    persons = {'Ксения Шерман - сбор копуса': 'почта',
               'Элина Камаева - морфологическая разметка': 'почта',
               'Мария Островская - разработка поиска': 'почта',
               'Мария Сухарева - сборка сайта': 'почта'}
    return render_template('about.html', persons=persons)

if __name__ == '__main__':
    app.run()
