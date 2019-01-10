from textblob import TextBlob
import pandas as pd
import sqlite3
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from nltk.corpus import stopwords
import string
from sklearn.metrics import confusion_matrix
import seaborn as sns
import time
import io
import base64
from wordcloud import WordCloud, ImageColorGenerator
import numpy as np
from PIL import Image
from graphs import Graph
from matplotlib import pyplot as plt


pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 200)

stop_words = set(stopwords.words('english') + list(string.punctuation))

models_simple = {
    'RandomForestClassifier': RandomForestClassifier(random_state=1),
    'LinearSVC': LinearSVC(random_state=1),
    'LogisticRegression': LogisticRegression(),
    'RidgeClassifier': RidgeClassifier(random_state=1),
    'MultinomialNB': MultinomialNB()
}

models = {
    'RandomForestClassifier': RandomForestClassifier(n_estimators=200, random_state=1),
    'LinearSVC': LinearSVC(multi_class='crammer_singer', random_state=1),
    'LogisticRegression': LogisticRegression(solver='newton-cg', multi_class='multinomial'),
    'RidgeClassifier': RidgeClassifier(random_state=1),
    'MultinomialNB': MultinomialNB()
}

with open('X_train', 'rb') as file, open('vectorizer(1)', 'rb') as vfile, open('dataframe', 'rb') as dfile:
    X_train = pickle.load(file)
    vectorizer = pickle.load(vfile)
    df = pickle.load(dfile)

train, test = train_test_split(df, test_size=0.25, stratify=df.rounded_score, random_state=1)
X_test = vectorizer.transform(test['processed'].tolist())
y_train = train['rounded_score'].tolist()
y_test = test['rounded_score'].tolist()


def get_score(model):
    with open(f'./models/{model}', 'rb') as file:
        loaded = pickle.load(file)
    return loaded.score(X_test, y_test)


def compare_models():
    scores = {}
    for model_name, model in models.items():
        result = training(X_train, y_train, model_name)
        scores[model_name] = result.score(X_test, y_test)
    return scores

    # entries = []
    # print('start', time.asctime())
    # for model_name, model in models_simple.items():
    #     accuracies = cross_val_score(model, X_train, y_train, scoring='accuracy', cv=3)
    #     for fold_idx, accuracy in enumerate(accuracies):
    #         entries.append((model_name, fold_idx, accuracy))
    #     print(model_name, 'done', time.asctime())
    # cv_df = pd.DataFrame(entries, columns=['model_name', 'fold_idx', 'accuracy'])
    # sns.boxplot(x='model_name', y='accuracy', data=cv_df)
    # sns.stripplot(x='model_name', y='accuracy', data=cv_df,nsize=8, jitter=True, edgecolor="gray", linewidth=2)


def training(x, y, model):
    try:
        with open(f'./models/{model}', 'rb') as file:
            loaded = pickle.load(file)
    except FileNotFoundError:
        with open(f'./models/{model}', 'wb') as file:
            current = models[model]
            current.fit(x, y)
            pickle.dump(current, file)
            loaded = current
    return loaded


def blobbing():
    # df = pd.read_sql_query("select c.reviewid, c.content, "
    #                        "r.score from content c, reviews r where c.reviewid = r.reviewid", conn)
    #
    # sentiment = []
    # rounded_scores = []

    with open('dataframe', 'rb') as file:
        df = pickle.load(file)

    # for index, row in df.iterrows():
    #     rounded_scores.append(round(row.score))
    #
    # df['rounded_score'] = rounded_scores
    #
    #
    # df['sentiment'] = sentiment
    # df['processed'] = df.content.apply(process, stop_words)
    # df = df[df['processed'].notnull()]
    #
    # with open('dataframe', 'wb') as file:
    #     pickle.dump(df, file)

    train, test = train_test_split(df, test_size=0.25, stratify=df.rounded_score, random_state=1)

    # vectorizer = TfidfVectorizer(sublinear_tf=True, ngram_range=(1,2), min_df=5, max_df=0.5)
    # X_train = vectorizer.fit_transform(train['processed'].tolist())
    # X_test = vectorizer.transform(test['processed'].tolist())
    # y_train = train['rounded_score'].tolist()
    # y_test = test['rounded_score'].tolist()


def conf_mat(model):
    with open(f'./models/{model}', 'rb') as file:
        loaded = pickle.load(file)
    predictor = loaded.predict(X_test)
    labels = range(11)
    conf_mat = confusion_matrix(y_test, predictor)
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.heatmap(conf_mat, annot=True, fmt='d',
                xticklabels=labels, yticklabels=labels)
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    return Graph().create_graph(plt)


def process(text):
    tokens = TextBlob(text).words
    tokens = [t.lemmatize() for t in tokens if t not in stop_words]
    tokens = [t for t in tokens if len(t) > 2]
    if len(tokens) > 0:
        return ' '.join(tokens)
    else:
        return None


def predictor(text):
    with open('models/LogisticRegression', 'rb') as mfile, open('vectorizer(1)', 'rb') as vfile:
        lr = pickle.load(mfile)
        vectorizer = pickle.load(vfile)
    return lr.predict(vectorizer.transform([process(text)]))


def get_artist(name):
    conn = sqlite3.connect('pitchfork.sqlite')
    df = pd.read_sql_query('select r.reviewid, r.title, r.score, r.pub_year, g.genre from reviews r, '
                           'genres g where artist = ? and r.reviewid = g.reviewid',
                           params=(name.lower(), ), con=conn)
    conn.close()
    df_grouped = df.groupby(['title'])
    new_df = pd.DataFrame(columns=['reviewid', 'title', 'score', 'genre'])

    album_list = []
    for title, group in df_grouped:
        genre = []
        for index, row in group.iterrows():
            genre.append(row['genre'].title())
            score = row['score']
            year = row['pub_year']
            reviewid = row['reviewid']
        d = {'reviewid': reviewid, 'title': title.title(), 'score': score, 'year': year, 'genre': genre}
        album_list.append(d)
        new_df = new_df.append(d, ignore_index=True)

    new_df['year'] = new_df['year'].apply(int)
    new_df = new_df.sort_values('year', axis=0).reset_index(drop=True)
    album_list.sort(key=lambda x: x['year'])
    new_df['title'] = new_df['title'].apply(lambda x: x[:15] + '...' if len(x) >= 15 else x)
    sns.barplot(new_df['title'], new_df['score'], alpha=0.3)
    sns.lineplot(new_df['title'], new_df['score'], sort=False)
    plt.xticks(rotation=60)
    plt.tight_layout()
    graph = Graph().create_graph(plt)
    return album_list, graph


def review_content(id):
    conn = sqlite3.connect('pitchfork.sqlite')
    c = conn.cursor()
    reviewid = (id,)
    c.execute('select content from content where reviewid = ?', reviewid)
    content = c.fetchone()[0]
    conn.close()
    return content


def display_scores():
    with open('X_train', 'rb') as file, open('vectorizer(1)', 'rb') as vfile:
        tfidf_result = pickle.load(file)
        vectorizer = pickle.load(vfile)

    scores = zip(vectorizer.get_feature_names(), np.asarray(tfidf_result.sum(axis=0)).ravel())
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    wave_mask = np.array(Image.open("./guitar2.png"))
    image_colors = ImageColorGenerator(wave_mask)
    wc = WordCloud(width=1280, height=720, mode='RGBA', background_color='white', max_words=2000, mask=wave_mask,
                   color_func=image_colors).fit_words(dict(sorted_scores))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")


def important_features():
    with open('X_train', 'rb') as file, open('vectorizer(1)', 'rb') as vfile:
        tfidf_result = pickle.load(file)
        vectorizer = pickle.load(vfile)

    scores = zip(vectorizer.get_feature_names(), np.asarray(tfidf_result.sum(axis=0)).ravel())
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    # wave_mask = np.array(Image.open("./guitar2.png"))
    # image_colors = ImageColorGenerator(wave_mask)
    # wc = WordCloud(width=1280, height=720, mode='RGBA', background_color='white', max_words=2000, mask=wave_mask,
    #                color_func=image_colors).fit_words(dict(sorted_scores))
    #
    # plt.imshow(wc, interpolation="bilinear")
    # plt.axis("off")
    # return Graph().create_graph(plt)
    return dict(sorted_scores[:50])
