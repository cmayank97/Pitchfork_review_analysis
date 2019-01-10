import sqlite3
import seaborn as sns
import pandas as pd
import io
import base64
from matplotlib import pyplot as plt


class Graph:

    def artists_avg(self):
        conn = sqlite3.connect('pitchfork.sqlite')
        df = pd.read_sql_query(
            "select artist, avg(score) from reviews group by artist having count(reviewid) > 4 order by avg(score) desc",
            conn)
        conn.close()
        fig, ax = plt.subplots()
        ax.tick_params(axis='x', labelsize='small')
        df['artist'] = df['artist'].apply(lambda x: x[:15] + '...' if len(x) >= 15 else x)
        df = df.head(5).append(df.tail(5))

        clrs = ['orange' if index < 5 else 'yellow' for index, item in enumerate(df.artist)]
        g = sns.barplot(df['artist'], df['avg(score)'], data=df, palette=clrs)

        r = range(0, 10)
        j = 0
        for row in df.head(10).itertuples():
            g.text(x=r[j], y=row[2], s='{:4.2f}'.format(row[2]), color='black', ha='center')
            j += 1

        plt.xticks(rotation=60)
        plt.tight_layout()
        return self.create_graph(plt)

    def weekday_score(self):
        conn = sqlite3.connect('pitchfork.sqlite')
        df = pd.read_sql_query(
            "select pub_weekday, avg(score) from reviews group by pub_weekday order by pub_weekday asc", conn)
        conn.close()

        g = sns.barplot(df['pub_weekday'], df['avg(score)'], data=df)
        g.set(xticklabels=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

        r = range(0, 7)
        j = 0
        for row in df.itertuples():
            g.text(x=r[j], y=row[2], s='{:4.2f}'.format(row[2]), color='black', ha='center')
            j += 1

        plt.tight_layout()
        return self.create_graph(plt)

    def genre_change(self):
        conn = sqlite3.connect('pitchfork.sqlite')
        df = pd.read_sql_query("select genres.reviewid, genres.genre, reviews.pub_"
                               "year from genres inner join reviews on genres.reviewid=reviews.reviewid", conn)
        conn.close()
        df = df.dropna(axis=0, how='any')
        fig, ax = plt.subplots(figsize=(15, 7))
        df.groupby(by=['pub_year', 'genre']).count()['reviewid'].unstack().plot(ax=ax)
        plt.xticks(range(2000, 2020, 5))
        plt.tight_layout()
        return self.create_graph(plt)

    def genre_avg(self):
        conn = sqlite3.connect('pitchfork.sqlite')
        df = pd.read_sql_query("select g.genre, avg(r.score) from genres g, reviews r "
                               "where g.reviewid = r.reviewid group by g.genre order by avg(r.score) desc", conn)
        conn.close()
        df = df.drop(index=4)
        plt.figure(figsize=(8, 6))
        g = sns.barplot(df['avg(r.score)'], df['genre'], data=df)
        r = range(0, 10)
        j = 0
        for row in df.itertuples():
            g.text(x=row[2] + 0.2, y=j, s='{:4.2f}'.format(row[2]), color='black', ha='center')
            j += 1

        plt.tight_layout()
        return self.create_graph(plt)

    def author_avg(self):
        conn = sqlite3.connect('pitchfork.sqlite')
        df = pd.read_sql_query("select author, avg(score) from reviews group by "
                               "author having count(reviewid) > 100 order by avg(score) desc", conn)
        conn.close()
        df = df.head(5).append(df.tail(5))
        class_list = ['high' if index < 5 else 'low' for index, item in enumerate(df.author)]
        df['class'] = class_list
        clrs = ['orange' if index < 5 else 'yellow' for index, item in enumerate(df.author)]
        g = sns.barplot('author', 'avg(score)', data=df, palette=clrs)
        plt.xticks(rotation=60)
        plt.tight_layout()
        return self.create_graph(plt)

    def create_graph(self, plt):
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return f'data:image/png;base64,{graph_url}'

    def all_graphs(self):
        graphs = {'artists_avg': self.artists_avg(), 'weekday_score': self.weekday_score(), 'genre_change': self.genre_change(),
                  'genre_avg': self.genre_avg(), 'author_avg': self.author_avg()}
        return graphs



