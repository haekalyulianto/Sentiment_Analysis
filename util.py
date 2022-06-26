import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
import streamlit as st
from gnews import GNews
from datetime import datetime
from dateutil import tz
import numpy as np

def get_ticker_data(ticker_symbol, data_period, data_interval):
    ticker_data = yf.download(tickers=ticker_symbol,
                              period=data_period, interval=data_interval)

    if len(ticker_data) == 0:
        st.write("tidak ditemukan data emiten")
    else:
        ticker_data.index = ticker_data.index.strftime("%d-%m-%Y %H:%M")
    
    return ticker_data

def search_key(word):
    google_news = GNews(language='id', country='ID', period='1y', exclude_websites=None)

    news = google_news.get_news(word)
    
    return news

def date_convert(gmt_date):
    from_zone = tz.gettz('GMT')
    to_zone = tz.gettz('US/Eastern')
    gmt = datetime.strptime(gmt_date, '%a, %d %b %Y %H:%M:%S GMT')
    gmt = gmt.replace(tzinfo=from_zone)
    gmt = gmt.strftime('%Y-%m-%d')
    
    return gmt

def format_tanggal(df):
    tanggal_emiten = []
    for i in range(len(df.index)):
        tgl = df.index[i].split(' ')[0].split('-')
        tgl = tgl[2] + '-' + tgl[1] + '-' + tgl[0]
        tanggal_emiten.append(tgl)

    return tanggal_emiten  

def create_t(df, namakolom, start_idx):
    time_idx = []

    date_time_str1 = df[namakolom].iloc[0]
    date_time_obj1 = datetime.strptime(date_time_str1, '%Y-%m-%d')

    for i in range (start_idx,len(df)):
        date_time_str2 = df[namakolom].iloc[i]
        date_time_obj2 = datetime.strptime(date_time_str2, '%Y-%m-%d')

        deltadays = (date_time_obj2 - date_time_obj1).days
        time_idx.append('t+'+str(deltadays))

    return time_idx

def detrend(df, namakolom):
    X=df[namakolom].values
    diff = list()
    for i in range(1, len(X)):
        value = X[i] - X[i - 1]
        diff.append(value)

    return diff

def plot_detrend(df, namakolom):
    df['batas_atas'] = df[namakolom].mean()+(1.03*df[namakolom].std())
    df['nilai_tengah'] = df[namakolom].mean()
    df['batas_bawah'] = df[namakolom].mean()-(1.03*df[namakolom].std())
    df[namakolom] = df[namakolom]*2
    
    layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)')

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Scatter(x=df['index'], 
                        y=df[namakolom], 
                        name='Emiten'))
    fig.add_trace(go.Scatter(x=df['index'], 
                        y=df['batas_atas'], 
                        marker=dict(color="green"), 
                        name='Batas Atas'))
    fig.add_trace(go.Scatter(x=df['index'], 
                        y=df['nilai_tengah'], 
                        marker=dict(color="red"), 
                        name='Nilai Tengah'))
    fig.add_trace(go.Scatter(x=df['index'], 
                        y=df['batas_bawah'],  
                        marker=dict(color="green"), 
                        name='Batas Bawah'))
    fig.update_layout(height=540)
    fig.update_layout(width=960)
    
    return fig

def plot_normal(df, namakolom):
    df['nilai_tengah'] = df[namakolom].mean()

    layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)')

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Scatter(x=df['index'], 
                        y=df[namakolom], 
                        name='Emiten'))
    fig.add_trace(go.Scatter(x=df['index'], 
                        y=df['nilai_tengah'], 
                        marker=dict(color="red"), 
                        name='Nilai Tengah'))
    fig.update_layout(height=540)
    fig.update_layout(width=960)
    
    return fig

def create_sentimen_detrend(df, namakolom):
    sentiments = []
    for i in range (len(df)):
        if(df[namakolom].iloc[i] > df['batas_atas'].iloc[i]):
            sentiments.append('positif')
        elif(df[namakolom].iloc[i] < df['batas_bawah'].iloc[i]):
            sentiments.append('negatif')
        else:
            sentiments.append('netral')

    return sentiments

def create_sentimen(df, namakolom):
    sentiments = []
    for i in range (len(df)):
        if(df[namakolom].iloc[i] > 0.0):
            sentiments.append('positif')
        elif(df[namakolom].iloc[i] < 0.0):
            sentiments.append('negatif')
        else:
            sentiments.append('netral')

    return sentiments

def form_date(df1, df2, namakolom1, namakolom2):
    tgl = []
    val = []
    for i in range(len(df1)):
        if (not df1[namakolom1].iloc[i] in list(df2[namakolom2])):
            tgl.append(df1[namakolom1].iloc[i])
            val.append(np.NaN)

    return tgl, val

def remove_holiday(df1, df2, namakolom1, namakolom2, namakolom3):
    tgl = []
    val = []

    for i in range(len(df1)):
        if (df1[namakolom1].iloc[i] in list(df2[namakolom3])):
            tgl.append(df1[namakolom1].iloc[i])
            val.append(df1[namakolom2].iloc[i])

    return tgl, val
