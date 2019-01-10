from flask import Flask, render_template, redirect, request, url_for, g, flash
import json
import os
import sqlite3 as sql
from sentiment import get_artist, review_content, get_score, conf_mat, predictor, compare_models, important_features
from graphs import *


app = Flask(__name__)
app.secret_key = "key_pitchfork"


@app.before_request
def before_request():
    g.db = sql.connect("pitchfork.sqlite")


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
def index():
    genres = []
    for row in g.db.execute('select distinct(genre) from genres'):
        if row[0] is not None:
            genres.append(row[0].title())
    return render_template('index.html', genre=genres)


@app.route("/search")
def search():
    text = request.args['searchText']
    text = text + "%"
    result = []
    for row in g.db.execute('select distinct(artist) from artists where artist like "%s" '%(text)):
        result.append(row[0].title())
    return json.dumps({"results": result[:6]})


@app.route('/artist_stats', methods=['GET', 'POST'])
def artist_stats():
    name = request.form['name']
    albums, graph = get_artist(name)
    return render_template('search.html', name=name, albums=albums, graph=graph)


@app.route('/get_review', methods=['GET', 'POST'])
def get_review():
    id = request.get_json()['id']
    content = review_content(int(id))
    return json.dumps({'status': 'OK', 'data': content})


@app.route('/prediction')
def prediction():
    return render_template('prediction.html')


@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        s = request.form['review']
        res = str(predictor(s)[0])
        flash(f'PREDICTED SCORE : {res}')
        return redirect(url_for('prediction'))


@app.route('/models/<name>', methods=['POST', 'GET'])
def models(name):
    score = get_score(name)
    graph = conf_mat(name)
    return render_template(f'{name}.html', score=score, graph=graph)


@app.route('/insights', methods=['GET', 'POST'])
def insights():
    p = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(p, "./", "description.json")
    data = json.load(open(json_url))
    graphs = Graph().all_graphs()
    return render_template('graphs.html', graphs=graphs, data=data)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/genre_albums', methods=['GET', 'POST'])
def genre_albums():
    name = request.form['Genre']
    albums = g.db.execute('select r.title, r.artist, r.score from reviews r, genres g where '
                          'r.reviewid = g.reviewid and g.genre = ? order by r.score desc limit 100',
                          (name.lower(),))
    albums = [[item.title() if isinstance(item, type('')) else item for item in row] for row in albums]
    return render_template('albums.html', albums=albums)


@app.route('/comparison', methods=['GET', 'POST'])
def comparison():
    scores = compare_models()
    return render_template('comparison.html', scores=scores)


@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    tfidf = important_features()
    return render_template('analysis.html', tfidf=tfidf)


if __name__ == "__main__":
    app.run(debug=True)
