import string
from gnews import GNews
import streamlit as st
import pandas as pd
import re  
from newspaper import Config
from newspaper import Article
from textblob import TextBlob
from textblob import Word
from dateutil import tz
import yfinance as yf
import numpy as np
from streamlit_option_menu import option_menu
import plotly.graph_objs as go
import plotly.express as px
import util
from datetime import datetime
import altair as alt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import translators as ts
from datetime import datetime

st.set_page_config(page_title="Analisis Sentimen",
                   page_icon=":art:", layout="wide")

do_refresh = st.sidebar.button('Refresh')

selected = option_menu(
    menu_title=None,
    options=["Sentimen Berita", "Sentimen Pasar"],
    icons=["search", "bank2"],
    menu_icon="cast",
    default_index=1,
    orientation="horizontal",
)

if 'nama_bank' not in st.session_state:
    st.session_state['nama_bank'] = 'Bank Negara Indonesia'

if selected == "Sentimen Berita":
    
    st.sidebar.image("LPS.png", output_format='PNG')
    search = st.sidebar.text_input('Pencarian :', st.session_state.nama_bank)
    st.session_state.nama_bank = search
    options = st.sidebar.multiselect(
        'Situs Pencarian  :',
        ['cnbcindonesia.com', 'cnnindonesia.com',
            'ekonomi.bisnis.com', 'money.kompas.com'],
        ['cnbcindonesia.com', 'cnnindonesia.com', 'ekonomi.bisnis.com', 'money.kompas.com'],)

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'

    if st.sidebar.button('Run'):
        config = Config()
        config.browser_user_agent = USER_AGENT
        config.request_timeout = 10

        hasilsearch = []

        try:
            for i in range(len(options)):
                word = search+" site:"+options[i]
                hasilsearch.extend(util.search_key(word))
        except Exception as e:
            st.write("")

        hasilanalisis = []

        st.header("Analisis Sentimen Berita")
        
        df_new = pd.DataFrame()
        titles = []
        descriptions = []
        sentimens = []

        for indonesia_news in hasilsearch:
            base_url = indonesia_news['url']

            published_date = indonesia_news["published date"]
            published_date2 = util.date_convert(published_date)
        
            article_title = indonesia_news["title"]
            titles.append(article_title)
            
            article_summary = indonesia_news["description"]
            descriptions.append(article_summary)
           
            st.success(article_summary)
            st.write('Tanggal Berita :', published_date2)

            try:
                news_properties = {}
                news_properties["title"] = article_title
                news_properties["tanggal"] = published_date2
                news_properties["isi_news"] = article_summary
            except Exception as e:
                print("error convert")
            
            #Tokenizing
            news_nilai = ' '.join(re.sub(
                "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|(\d+)", " ", str(article_summary)).split())
            #Case Folding
            news_nilai = news_nilai.lower()
            #Menghapus Whitepace
            news_nilai = news_nilai.strip()
            #Menghapus Tanda Baca
            news_nilai = news_nilai.translate(
                str.maketrans('', '', string.punctuation))

            st.write('Link Berita : ', base_url)
            analysis = TextBlob(news_nilai)

            try:
                analysis = ts.google(news_nilai, from_language='id', to_language='en')
            except Exception as e:
                print("")
            
            if TextBlob(analysis).sentiment.polarity > 0.0:
                news_properties['sentimen'] = "Positif"
            elif TextBlob(analysis).sentiment.polarity == 0.0:
                news_properties['sentimen'] = "Netral"
            else:
                news_properties['sentimen'] = "Negatif"
    
            if TextBlob(analysis).sentiment.polarity > 0.0:
                news_properties['param'] = TextBlob(analysis).sentiment.polarity
            elif TextBlob(analysis).sentiment.polarity == 0.0:
                news_properties['param'] = TextBlob(analysis).sentiment.polarity
            else:
                news_properties['param'] = TextBlob(analysis).sentiment.polarity
            sentimens.append(news_properties['sentimen'])

            st.write('Sentimen Berita : ', news_properties['sentimen'])

            sentiment_dict = {'Polaritas' : TextBlob(analysis).sentiment.polarity, 'Subjektivitas' : TextBlob(analysis).sentiment.subjectivity}
            sentiment_df = pd.DataFrame(sentiment_dict.items(), columns=['Ukuran','Nilai'])
            st.write(sentiment_dict)
            
            c = alt.Chart(sentiment_df).mark_bar().encode(
                x='Ukuran',
                y='Nilai',
                color='Ukuran'
                )
                
            st.altair_chart(c, use_container_width=True)
            
            analyzer = SentimentIntensityAnalyzer()
            pos_list = []
            neg_list = []
            neu_list = []
            res_total = 0
            for i in analysis.split():
                res = analyzer.polarity_scores(i)['compound']
                res_total = res_total + res
                if res > 0.1:
                    pos_list.append(i)
                    pos_list.append(res)
                elif res <= -0.1:
                    neg_list.append(i)
                    neg_list.append(res)
                else:
                    neu_list.append(i)
                
            
            result = {'Positif':pos_list, 'Negatif':neg_list, 'Netral':neu_list}
            result_res = res_total
            
            hasilanalisis.append(news_properties)

        news_positif = [t for t in hasilanalisis if t['sentimen']
                        == "Positif"]
        news_netral = [t for t in hasilanalisis if t['sentimen']
                    == "Netral"]
        news_negatif = [t for t in hasilanalisis if t['sentimen']
                        == "Negatif"]

        st.write('----------------------------------------------------------------')

        st.header("Hasil Persentase")
        try:
            st.write("Positif : ", str(len(news_positif)), "({} %)".format(
                100*len(news_positif)/len(hasilanalisis)))
            st.write("Netral : ", str(len(news_netral)), "({} %)".format(
                100*len(news_netral)/len(hasilanalisis)))
            st.write("Negatif : ", str(len(news_negatif)), "({} %)".format(
                100*len(news_negatif)/len(hasilanalisis)))
        except Exception as e:
            st.write("")

        df_news = pd.DataFrame(hasilanalisis)

        df_news_filter = df_news.dropna()

        df_filter1 = df_news_filter.loc[:, ['tanggal', 'sentimen', 'param']]
        
        grouped_df = df_filter1.groupby(['tanggal', 'sentimen', 'param']
                                        ).size().reset_index(name="count_sentimen")

        grouped_df['nilaisentimen'] = grouped_df['param'] * \
            grouped_df['count_sentimen']

        df_filter2 = grouped_df.loc[:, ['tanggal', 'nilaisentimen']]
        grouped_df2 = df_filter2.groupby(['tanggal']).mean().reset_index()
        grouped_df3 = df_filter2.groupby(['tanggal']).mean()
        df_filter2
        grouped_df2
        grouped_df2.to_csv('file_sentimen.csv', index=False)
       
        df_new['title'] = titles
        df_new['sentimen'] = sentimens
        
        df_new.to_csv('file_baru.csv')

        st.write('----------------------------------------------------------------')
        st.header("Chart Sentimen")
        st.line_chart(grouped_df3)

        num_rows = grouped_df2.shape[0]

if selected == "Sentimen Pasar":
    
    st.sidebar.image("LPS.png", output_format='PNG')
    st.header("Analisis Sentimen Pasar")
    df_sentimen = pd.read_csv("file_sentimen.csv")

    num_rows = 1

    ticker_symbol = st.sidebar.text_input('Kode Saham :', 'BBNI')
    data_period = st.sidebar.text_input('Periode :', str(num_rows)+'y')
    data_interval = st.sidebar.radio(
        'Interval', ['1d', '5d', '15m', '30m', '1h'])
    
    # Preprocessing
    sentimen_max = df_sentimen.loc[df_sentimen['nilaisentimen'].idxmax()]['nilaisentimen']
    sentimen_min = df_sentimen.loc[df_sentimen['nilaisentimen'].idxmin()]['nilaisentimen']

    if ticker_symbol == '^JKSE' or ticker_symbol == '':
        ticker_symbol2 = '^JKSE'
    else:
        ticker_symbol2 = ticker_symbol+'.JK'
   
    # ---------------------------- Start dari Google Colab ----------------------------
    ticker_data = util.get_ticker_data(ticker_symbol2, data_period, data_interval)
    df = ticker_data
    df['tanggal'] = util.format_tanggal(df)
    df = df[['tanggal','Close']]
    df['Close'].astype(int)
    df['index'] = util.create_t(df, 'tanggal', 0)    
    
    # ---------------------------- GRAFIK Saham----------------------------
    st.success('Grafik Saham '+ticker_symbol)
    st.write(util.plot_normal(df, 'Close'))
    df.to_excel('file_saham.xlsx')

    # ---------------------------- Lanjutan Google Colab ----------------------------
    df_saham_detrend = pd.DataFrame()
    df_saham_detrend[0] = df['Close'].pct_change()
    df_saham_detrend = df_saham_detrend[1:]
    df_saham_detrend['index'] = util.create_t(df, 'tanggal', 1)

    # ---------------------------- GRAFIK Saham Detrend ----------------------------
    st.success('Grafik Saham '+ticker_symbol+' (Detrend)')
    st.write(util.plote(df_saham_detrend, 0, 'index'))
    df_saham_detrend.to_excel('file_saham_detrend.xlsx')

    # ---------------------------- Lanjutan Google Colab ----------------------------
    df_saham_detrend['sentimen'] = util.create_sentimen_detrend(df_saham_detrend, 0)
    df_sentimen_berita = df_sentimen

    df_temp1 = pd.DataFrame()
    df_temp1['tanggal'], df_temp1['nilaisentimen'] = util.form_date_harian(df, df_sentimen_berita, 'tanggal', 'tanggal')

    df_temp2 = pd.concat([df_sentimen_berita, df_temp1])
    df_temp2['tanggal'] = pd.concat([df_sentimen_berita['tanggal'], df_temp1['tanggal']])

    df_sentimen_berita1 = pd.DataFrame()
    df_sentimen_berita1['tanggal'], df_sentimen_berita1['nilaisentimen'] = util.remove_holiday(df_temp2, df, 'tanggal', 'nilaisentimen', 'tanggal')

    df_sentimen_berita = df_sentimen_berita1
    df_sentimen_berita = df_sentimen_berita.sort_values('tanggal')

    #df_sentimen_berita = df_sentimen_berita.fillna(method='ffill')
    df_sentimen_berita = df_sentimen_berita.interpolate()

    df_sentimen_berita['index'] = util.create_t(df_sentimen_berita, 'tanggal', 0)
    
    # ---------------------------- GRAFIK Sentimen Berita ----------------------------
    st.success('Grafik Sentimen Berita '+ st.session_state.nama_bank)
    st.write(util.plot_normal(df_sentimen_berita, 'nilaisentimen'))
    df_sentimen_berita.to_excel('file_sentimen_berita.xlsx')

    # ---------------------------- Lanjutan Google Colab ----------------------------
    df_sentimen_berita_undetrend = df_sentimen_berita
    df_sentimen_berita_undetrend['index'] = util.create_t(df_sentimen_berita_undetrend, 'tanggal', 0)
    df_sentimen_berita_undetrend = df_sentimen_berita_undetrend.drop(df_sentimen_berita_undetrend.index[0])

    # ---------------------------- Lanjutan Google Colab ----------------------------
    df_sentimen_berita_undetrend['sentimen'] = util.create_sentimen(df_sentimen_berita_undetrend, 'nilaisentimen')

    df_berita_harian = df_sentimen_berita_undetrend[['index', 'sentimen', 'nilaisentimen']]
    df_berita_harian = df_berita_harian.rename(columns={'sentimen': 'sentimen_berita'})
    df_berita_harian = df_berita_harian.rename(columns={'nilaisentimen': 'nilai_sentimen_berita'})

    df_saham_harian = df_saham_detrend[['index', 'sentimen',  0]]
    df_saham_harian = df_saham_harian.rename(columns={'sentimen' : 'sentimen_saham'})
    df_saham_harian = df_saham_harian.rename(columns={0 : 'nilai_sentimen_saham'})

    df_gabungan_harian = pd.merge(df_saham_harian, df_berita_harian, on=['index'])
    
    # ---------------------------- Korelasi Harian  ----------------------------
    st.info('Korelasi Grafik Harga Saham '+ticker_symbol+' dan Sentimen Berita '+st.session_state.nama_bank+' (Harian)')
    st.write(df_gabungan_harian)
    
    st.write('\n\n')

    st.write('Nilai Koefisien Korelasi')
    st.write(df_gabungan_harian.corr())

    st.write('\n\n')

    # ---------------------------- Korelasi Mingguan  ----------------------------
    df_saham = df
    df_saham[0] = df['Close'].pct_change()
    df_saham = df_saham[1:]

    df_saham = df_saham.drop(columns=['Close'])

    df_saham['sentimen'] = util.create_sentimen_detrend(df_saham_detrend, 0)

    df_berita = pd.read_csv("file_sentimen.csv")
    start_date = df_saham['tanggal'].iloc[0]

    df_temp_1 = pd.DataFrame()
    df_temp_1['tanggal'], df_temp_1['nilaisentimen'] = util.form_date_mingguan(df_berita, start_date, 'tanggal')

    df_temp_2 = df_berita.append(df_temp_1)
    df_temp_2['tanggal'] = df_berita['tanggal'].append(df_temp_1['tanggal'])

    df_berita = df_temp_2
    df_berita = df_berita.sort_values('tanggal')

    #df_berita = df_berita.interpolate()

    totals, tanggals = util.calculate_weekly_berita(df_berita, df_saham, 'tanggal', 'tanggal')
    df_berita_weekly = pd.DataFrame({'tanggal': tanggals ,'sentimenweekly': totals})

    util.plote(df_berita_weekly, 'sentimenweekly', 'tanggal')
    
    df_berita_weekly['sentimen'] = util.create_sentimen_detrend(df_berita_weekly, 'sentimenweekly')

    df_saham_weekly = pd.DataFrame()
    df_saham_weekly['tanggal'], df_saham_weekly['sentimenweekly'] = util.calculate_weekly_saham(df_saham,0)

    df_berita_weekly = df_berita_weekly[len(df_berita_weekly)-len(df_saham_weekly):]

    util.plote(df_saham_weekly, 'sentimenweekly', 'tanggal')

    df_saham_weekly['sentimen'] = util.create_sentimen_detrend(df_saham_weekly, 'sentimenweekly')

    df_saham_mingguan = df_saham_weekly[['tanggal', 'sentimenweekly', 'sentimen']]
    df_saham_mingguan = df_saham_mingguan.rename(columns={'tanggal': 'Tanggal Saham', 'sentimenweekly': 'Nilai Sentimen Saham', 'sentimen': 'Sentimen Saham'})

    df_berita_mingguan = df_berita_weekly[['tanggal', 'sentimenweekly', 'sentimen']]
    df_berita_mingguan = df_berita_mingguan.rename(columns={'tanggal': 'Tanggal Berita', 'sentimenweekly': 'Nilai Sentimen Berita', 'sentimen': 'Sentimen Berita'})

    df_gabungan_mingguan = pd.merge(df_saham_mingguan, df_berita_mingguan, left_index=True, right_index=True)

    df_gabungan_check = df_gabungan_mingguan[['Nilai Sentimen Saham', 'Nilai Sentimen Berita']]

    # ---------------------------- Korelasi Harian  ----------------------------
    st.info('Korelasi Grafik Harga Saham '+ticker_symbol+' dan Sentimen Berita '+st.session_state.nama_bank+' (Mingguan)')
    st.write(df_gabungan_mingguan)
    
    st.write('\n\n')

    st.write('Nilai Koefisien Korelasi')
    st.write(df_gabungan_check.corr())

    st.write('\n\n')

    st.write('Skor Kesesuaian')
    st.write(str(util.calculate_score(df_gabungan_mingguan, 'Sentimen Saham', 'Sentimen Berita')))
