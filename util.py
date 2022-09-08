import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
from gnews import GNews
from datetime import datetime
from dateutil import tz
import numpy as np
from datetime import timedelta
import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from twython import Twython
import time
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')

def get_ticker_data(ticker_symbol, data_period, data_interval):
    ticker_data = yf.download(tickers=ticker_symbol,
                              period=data_period, interval=data_interval)

    if len(ticker_data) == 0:
        st.write("tidak ditemukan data emiten")
    else:
        ticker_data.index = ticker_data.index.strftime("%d-%m-%Y %H:%M")
    
    return ticker_data

def search_key(word, period):
    google_news = GNews(language='id', country='ID', period=period, exclude_websites=None)

    news = google_news.get_news(word+'%20')

    my_bar = st.progress(0)

    for i in range (len(news)):
        time.sleep(0.1)
        article = google_news.get_full_article(news[i]['url'])
        news[i]['description'] = article.text
        my_bar.progress(i + 1)
    return news

def convert_date(gmt_date):
    from_zone = tz.gettz('GMT')
    #to_zone = tz.gettz('US/Eastern')
    gmt = datetime.strptime(gmt_date, '%a, %d %b %Y %H:%M:%S GMT')
    gmt = gmt.replace(tzinfo=from_zone)
    gmt = gmt.strftime('%Y-%m-%d')
    
    return gmt

def format_date(df):
    tanggal_emiten = []
    for i in range(len(df.index)):
        tgl = df.index[i].split(' ')[0].split('-')
        tgl = tgl[2] + '-' + tgl[1] + '-' + tgl[0]
        tanggal_emiten.append(tgl)

    return tanggal_emiten  

def plot(df, namakolom1, namakolom2):
    df['batas_atas'] = df[namakolom1].mean()+(1.64*df[namakolom1].std())
    df['nilai_tengah'] = df[namakolom1].mean()
    df['batas_bawah'] = df[namakolom1].mean()-(1.64*df[namakolom1].std())
    df[namakolom1] = df[namakolom1]*2

    layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)')

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Scatter(x=df[namakolom2], 
                        y=df[namakolom1], 
                        name='Emiten'))
    fig.add_trace(go.Scatter(x=df[namakolom2], 
                        y=df['batas_atas'], 
                        marker=dict(color="green"), 
                        name='Batas Atas'))
    fig.add_trace(go.Scatter(x=df[namakolom2], 
                        y=df['nilai_tengah'], 
                        marker=dict(color="red"), 
                        name='Nilai Tengah'))
    fig.add_trace(go.Scatter(x=df[namakolom2], 
                        y=df['batas_bawah'],  
                        marker=dict(color="green"), 
                        name='Batas Bawah'))
    fig.update_layout(height=540)
    fig.update_layout(width=960)

    return fig
     
def plot_normal(df, namakolom1, namakolom2):
    df['nilai_tengah'] = df[namakolom1].mean()

    layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)')

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Scatter(x=df[namakolom2], 
                        y=df[namakolom1], 
                        name='Emiten'))
    fig.add_trace(go.Scatter(x=df[namakolom2], 
                        y=df['nilai_tengah'], 
                        marker=dict(color="red"), 
                        name='Nilai Tengah'))
    fig.update_layout(height=540)
    fig.update_layout(width=960)
    
    return fig

def create_sentimen(df, namakolom):
    sentiments = []
    for i in range (len(df)):
        if(df[namakolom].iloc[i] > df['batas_atas'].iloc[i]):
            sentiments.append('positif')
        elif(df[namakolom].iloc[i] < df['batas_bawah'].iloc[i]):
            sentiments.append('negatif')
        else:
            sentiments.append('netral')

    return sentiments

def form_date_mingguan(df, start_date, namakolom):
    tgl = []
    val = []

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    delta = timedelta(days=365)
    end_date = start_date + delta

    delta = timedelta(days=1)
    
    while (start_date <= end_date):
        if (not start_date.strftime('%Y-%m-%d') in list(df[namakolom])):
            tgl.append(start_date.strftime('%Y-%m-%d'))
            val.append(np.NaN)
        start_date += delta

    return tgl, val

def calculate_weekly_berita(df1, df2 , namakolom1, namakolom2):
    # df1 = berita
    # df2 = saham
  
    totals = []
    tanggals = []
  
    for i in range(len(df1) - 7):
        tgl = df1[namakolom1].iloc[i].split('-')
        if ((datetime(int(tgl[0]), int(tgl[1]), int(tgl[2])).isoweekday() < 6) and (df1[namakolom1].iloc[i+7] in list(df2[namakolom2]))):
            
            total = 0     
            
            for j in range(i,i+7):
                if (not np.isnan(df1['nilaisentimen'].iloc[j])):
                    total += df1['nilaisentimen'].iloc[j]
            totals.append(total)
            tanggals.append(df1[namakolom1].iloc[i])

    return totals, tanggals

def calculate_weekly_saham(df, namakolom):
    weekly_sahams = []
    tanggals = []
    
    for i in range(len(df)-5):
        if ((df[namakolom].iloc[i] == 0)): # x/0
            weekly_saham = -1
        else:
            weekly_saham = ((df[namakolom].iloc[i+5]-df[namakolom].iloc[i])/df[namakolom].iloc[i])
            
        tanggals.append(df['tanggal'].iloc[i+5])
        weekly_sahams.append(weekly_saham)

    return tanggals, weekly_sahams

def calculate_score(df, namakolom1, namakolom2):
    cocok = 0

    for i in range (len(df)):
        if (df[namakolom1].iloc[i] == df[namakolom2].iloc[i]):
            cocok += 1

    nilai = (cocok/len(df))*100

    return nilai

def stemmingText(text): 
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    text = stemmer.stem(text)
    return text

def filteringText(text):
    listStopwords = set(stopwords.words('indonesian'))
    filtered = ''
    for txt in text:
        if txt not in listStopwords:
            #filtered.append(txt)
            filtered+=txt
    text = filtered 
    return text

def get_access_token():
    APP_KEY = 'jDoiK1NQq8BvLfGKxZOmRlCq2'
    APP_SECRET = 'rJSajv6auDx9SAOyktZLgN9JJq4rSqgxKPlFBWST7hT1MgbE3d'
    twitter = Twython(APP_KEY, APP_SECRET, oauth_version=2)
    ACCESS_TOKEN = twitter.obtain_access_token()
    twitter = Twython(APP_KEY, access_token=ACCESS_TOKEN)

    return twitter

def search_tweets(keyword):
    twitter = get_access_token()
    search_result = twitter.search(q=keyword, count=2000)

    return search_result

def process_tweets(search_result):
    tweets = search_result['statuses']

    ids = []

    ids = [tweet['id_str'] for tweet in tweets]
    texts = [tweet['text'] for tweet in tweets]
    times = [tweet['retweet_count'] for tweet in tweets]
    favtimes = [tweet['favorite_count'] for tweet in tweets]
    follower_count = [tweet['user']['followers_count'] for tweet in tweets]
    location = [tweet['user']['location'] for tweet in tweets]
    lang = [tweet['lang'] for tweet in tweets]
    date = [tweet['created_at'] for tweet in tweets]

    pl = pd.DataFrame(
        {'id': ids,
        'Tweet': texts,
        'Tanggal':date,
        'Jumlah Retweet': times,
        'Jumlah Favourite':favtimes,
        'Lokasi':location,
        'Bahasa':lang
        }
    )

    return pl
