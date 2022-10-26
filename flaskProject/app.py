import sqlite3
from processing import Processing, GetData
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    q = request.args.get('q')
    if q:
        conn = sqlite3.connect('poems_corpus.db')
        q = request.args.get('q')
        my = Processing(q)
        new_q = my.main_search()
        if type(new_q) == str:
            error = new_q
            results = ''
        else:
            data = GetData(new_q, conn)
            ids = data.sort_sentences()
            results = data.get_sentences(ids)
            error = ''
            print(results)
    else:
        results = ''
        error = ''
    return render_template('index.html', error=error, results=results)

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/about')
def about():
    persons = {'Ксения Шерман - сбор копуса': 'ksenia.shermanv@gmail.com',
               'Элина Камаева - морфологическая разметка': 'elinkamaeva@gmail.com',
               'Мария Островская - разработка поиска': 'ostrovskaya.ms@mail.ru',
               'Мария Сухарева - сборка сайта': 'maryleyas@gmail.com'}
    return render_template('about.html', persons=persons)

if __name__ == '__main__':
    app.run()
