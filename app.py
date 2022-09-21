from operator import index
import string
import streamlit as st
import pandas as pd
import re  
from newspaper import Config
from streamlit_option_menu import option_menu
import util
import altair as alt
import translators as ts
import plotly.graph_objs as go
from scipy import stats
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import auth
warnings.simplefilter(action='ignore')

if auth.check_password():
    # Konfigurasi Halaman
    st.set_page_config(page_title="Analisis Sentimen",
                    page_icon=":art:", layout="wide")

    # Tombol Refresh
    do_refresh = st.sidebar.button('Refresh')

    # Konfigurasi Pilihan Menu
    selected = option_menu(
        menu_title=None,
        options=["Sentimen Berita", "Sentimen Pasar", "Kesesuaian Sentimen", "Twitter"],
        icons=["newspaper", "bank", "graph-up", "twitter"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

    # Store Variable Nama Bank
    if 'nama_bank' not in st.session_state:
        st.session_state['nama_bank'] = 'BBCA'

    # Menu Sentimen Berita
    if selected == "Sentimen Berita":
    
        # Sunting Sidebar
        st.sidebar.image("LPS.png", output_format='PNG')
        search = st.sidebar.text_input('Pencarian :', st.session_state.nama_bank)
        st.session_state.nama_bank = search
        options = st.sidebar.multiselect('Situs Pencarian  :', ['cnbcindonesia.com', 'cnnindonesia.com', 'ekonomi.bisnis.com', 'money.kompas.com'], ['cnbcindonesia.com', 'cnnindonesia.com', 'ekonomi.bisnis.com', 'money.kompas.com'])
        num_periode = '1y'
        data_period = st.sidebar.text_input('Periode :', num_periode)
            
        # Konfigurasi Web
        USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    
        # Menjalankan Analisis Sentimen Berita
        if st.sidebar.button('Run'):
            
            # Konfigurasi Browser
            config = Config()
            config.browser_user_agent = USER_AGENT
            config.request_timeout = 10

            hasilsearch = []

            try:
                for i in range(len(options)):
                    word = search+" site:"+options[i]
                    hasilsearch.extend(util.search_key(word, data_period))

            except Exception as e:
                st.write("")

            hasilanalisis = []

            st.header("Analisis Sentimen Berita")

            for indonesia_news in hasilsearch:

                # Nama Komponen Berita
                base_url = indonesia_news['url']
                published_date = indonesia_news["published date"]
                published_date2 = util.convert_date(published_date)
                article_title = indonesia_news["title"]
                article_summary = indonesia_news["description"]
            
                # Menampilkan Judul dan Tanggal Berita
                st.success(article_title)
                st.write('Tanggal Berita :', published_date2)

                # Exception Handling
                try:
                    news_properties = {}
                    news_properties["title"] = article_title
                    news_properties["tanggal"] = published_date2
                    news_properties["isi_news"] = article_summary
                except Exception as e:
                    print("Convert Error")
                
                # Tokenizing
                news_nilai = ' '.join(re.sub(
                    "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|(\d+)", " ", str(article_summary)).split())
                news_nilai2 = ' '.join(re.sub(
                    "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|(\d+)", " ", str(article_title)).split())
                
                # Case Folding
                news_nilai = news_nilai.lower()
                news_nilai2 = news_nilai2.lower()
                
                # Menghapus Whitepace
                news_nilai = news_nilai.strip()
                news_nilai2 = news_nilai2.strip()
                
                # Menghapus Tanda Baca
                news_nilai = news_nilai.translate(str.maketrans('', '', string.punctuation))
                news_nilai2 = news_nilai2.translate(str.maketrans('', '', string.punctuation))

                news_nilai = util.filteringText(news_nilai)
                news_nilai2 = util.filteringText(news_nilai2)
                
                news_nilai = util.stemmingText(news_nilai)
                news_nilai2 = util.stemmingText(news_nilai2)

                st.write('Link Berita : ', base_url)

                # Vader Sentiment Analysis
                news_nilai = news_nilai[:4000]
                analysis = ts.google(news_nilai, from_language='id', to_language='en')
                analysis2 = ts.google(news_nilai2, from_language='id', to_language='en')
                sia = SentimentIntensityAnalyzer()

                sias = sia.polarity_scores(analysis)
                sias2 = sia.polarity_scores(analysis2)

                if ((sias['compound']+sias2['compound'])/2) >= 0.05:
                    news_properties['sentimen'] = "Positif"
                    news_properties['param'] = (sias['compound']+sias2['compound'])/2
    
                elif ((sias['compound']+sias2['compound'])/2) <= 0.05:
                    news_properties['sentimen'] = "Negatif"
                    news_properties['param'] = (sias['compound']+sias2['compound'])/2
            
                else:
                    news_properties['sentimen'] = "Netral"
                    news_properties['param'] = (sias['compound']+sias2['compound'])/2

                sentiment_dict = {'Gabungan' : sias['compound'], 'Positivitas' : sias['pos'], 'Negativitas' : sias['neg'], 'Netralitas' : sias['neu']}
                sentiment_df = pd.DataFrame(sentiment_dict.items(), columns=['Ukuran', 'Nilai'])

                sentiment_dict2 = {'Gabungan' : sias2['compound'], 'Positivitas' : sias2['pos'], 'Negativitas' : sias2['neg'], 'Netralitas' : sias2['neu']}
                sentiment_df2 = pd.DataFrame(sentiment_dict2.items(), columns=['Ukuran', 'Nilai'])

                # Plot Chart Dictionary
                c = alt.Chart(sentiment_df).mark_bar().encode(
                    x='Ukuran',
                    y='Nilai',
                    color='Ukuran'
                    )

                c2 = alt.Chart(sentiment_df2).mark_bar().encode(
                    x='Ukuran',
                    y='Nilai',
                    color='Ukuran'
                    )
                
                st.write('Headline Berita')     
                st.altair_chart(c2, use_container_width=True)
                
                st.write('Konten Berita')     
                st.altair_chart(c, use_container_width=True)
                
                hasilanalisis.append(news_properties)
        
            # Membuat Data Berita
            df_news = pd.DataFrame(hasilanalisis)
            df_news_filter = df_news.dropna()
            df_filter1 = df_news_filter.loc[:, ['tanggal', 'sentimen', 'param']]  
            grouped_df = df_filter1.groupby(['tanggal', 'sentimen', 'param']).size().reset_index(name="count_sentimen")
            grouped_df['nilaisentimen'] = grouped_df['param']
            df_filter2 = grouped_df.loc[:, ['tanggal', 'nilaisentimen']]
            grouped_df2 = df_filter2.groupby(['tanggal']).mean().reset_index()
            grouped_df3 = df_filter2.groupby(['tanggal']).mean()
            grouped_df2.to_csv('file_sentimen.csv', index=False)
        
        else:
            st.header("Analisis Sentimen Berita")

            # Grafik Sentimen Berita
            df_berita = pd.read_csv("file_sentimen.csv")
            st.success('Grafik Sentimen Berita '+ st.session_state.nama_bank)
            st.write(util.plot_normal(df_berita, 'nilaisentimen', 'tanggal'))

    # Menu Sentimen Pasar
    if selected == "Sentimen Pasar":
        
        # Sunting Sidebar
        st.sidebar.image("LPS.png", output_format='PNG')
        st.header("Analisis Sentimen Pasar")
        
        # Ambil Data
        df_sentimen = pd.read_csv("file_sentimen.csv")

        num_periode = '1y'
        data_interval = '1d'
        
        ticker_symbol = st.sidebar.text_input('Kode Saham :', 'BBCA')
        data_period = st.sidebar.text_input('Periode :', num_periode)

        if ticker_symbol == '^JKSE' or ticker_symbol == '':
            ticker_symbol2 = '^JKSE'
        else:
            ticker_symbol2 = ticker_symbol+'.JK'
    
        ticker_data = util.get_ticker_data(ticker_symbol2, data_period, data_interval)
        df = ticker_data
        df['tanggal'] = util.format_date(df)
        df = df[['tanggal','Close']]
        df['Close'].astype(int)
        
        # Grafik Saham Normal
        df_saham = df
        st.success('Grafik Saham '+ticker_symbol)
        st.write(util.plot_normal(df, 'Close', 'tanggal'))
        
        # Grafik Saham Detrend
        df_saham[0] = df['Close'].pct_change()
        df_saham.to_excel('df_saham.xlsx', index=False) 
        st.success('Grafik Saham '+ticker_symbol+' (Detrend)')
        st.write(util.plot(df, 0, 'tanggal'))
        
        df_saham = df_saham[1:]

        df_saham = df_saham.drop(columns=['Close'])

        # Buat Sentimen Saham Harian
        df_saham['sentimen'] = util.create_sentimen(df_saham, 0)

        # Grafik Sentimen Berita
        df_berita = pd.read_csv("file_sentimen.csv")
        df_berita.to_excel('df_berita.xlsx', index=False)
        util.plot_normal(df_berita, 'nilaisentimen', 'tanggal')
        
        start_date = df_saham['tanggal'].iloc[0]

        # Isi Semua Tanggal pada Data Berita
        df_temp_1 = pd.DataFrame()
        df_temp_1['tanggal'], df_temp_1['nilaisentimen'] = util.form_date_mingguan(df_berita, start_date, 'tanggal')
        df_temp_2 = df_berita.append(df_temp_1)
        df_temp_2['tanggal'] = df_berita['tanggal'].append(df_temp_1['tanggal'])
        df_berita = df_temp_2
        df_berita = df_berita.sort_values('tanggal')

        # Hitung Sentimen Berita Mingguan
        totals, tanggals = util.calculate_weekly_berita(df_berita, df_saham, 'tanggal', 'tanggal')
        df_berita_weekly = pd.DataFrame({'tanggal': tanggals ,'sentimenweekly': totals})
        df_berita_weekly.to_csv('df_berita_weekly.csv', index=False)
        df_berita_weekly.to_excel('df_berita_weekly.xlsx', index=False)
        util.plot(df_berita_weekly, 'sentimenweekly', 'tanggal')
        df_berita_weekly['sentimen'] = util.create_sentimen(df_berita_weekly, 'sentimenweekly')
        
        # Hitung Sentimen Saham Mingguan
        df_saham_weekly = pd.DataFrame()
        df_saham_weekly['tanggal'], df_saham_weekly['sentimenweekly'] = util.calculate_weekly_saham(df_saham,0)
        df_saham_weekly.to_csv('df_saham_weekly.csv', index=False)
        df_saham_weekly.to_excel('df_saham_weekly.xlsx', index=False)
        util.plot(df_saham_weekly, 'sentimenweekly', 'tanggal')
        
        # Memastikan Mulai di Baris yang Sama
        df_berita_weekly = df_berita_weekly[len(df_berita_weekly)-len(df_saham_weekly):]

        # Buat Sentimen Saham Mingguan
        df_saham_weekly['sentimen'] = util.create_sentimen(df_saham_weekly, 'sentimenweekly')
        df_saham_weekly.to_excel('df_saham_ver2.xlsx')

        # Format Data Saham Mingguan
        df_saham_mingguan = df_saham_weekly[['tanggal', 'sentimenweekly', 'sentimen']]
        df_saham_mingguan = df_saham_mingguan.rename(columns={'tanggal': 'Tanggal Saham', 'sentimenweekly': 'Nilai Sentimen Saham', 'sentimen': 'Sentimen Saham'})
        df_saham_mingguan = df_saham_mingguan.reset_index(drop=True)
        df_saham_mingguan.to_csv('df_saham_mingguan.csv', index=False)
        
        # Format Data Berita Mingguan
        df_berita_mingguan = df_berita_weekly[['tanggal', 'sentimenweekly', 'sentimen']]
        df_berita_mingguan = df_berita_mingguan.rename(columns={'tanggal': 'Tanggal Berita', 'sentimenweekly': 'Nilai Sentimen Berita', 'sentimen': 'Sentimen Berita'})
        df_berita_mingguan = df_berita_mingguan.reset_index(drop=True)
        df_berita_mingguan.to_csv('df_berita_mingguan.csv', index=False)

        # Data Gabungan Mingguan
        df_gabungan_mingguan = pd.concat([df_saham_mingguan, df_berita_mingguan], axis=1)
        df_gabungan_mingguan.to_csv('df_gabungan_mingguan.csv', index=False)
        df_gabungan_mingguan.to_excel('df_gabungan_mingguan.xlsx', index=False)

    # Menu Kesesuaian Sentimen
    if selected == "Kesesuaian Sentimen":
        
        # Sunting Sidebar
        st.sidebar.image("LPS.png", output_format='PNG')
        st.header("Analisis Kesesuaian Sentimen")
        window = st.sidebar.number_input('Window : ', value = 30, step = 1)
        alpha = st.sidebar.number_input('Alpha : ', value = 0.1, step = 0.1)

        # Ambil Data Normal
        df_gabungan_mingguan = pd.read_csv('df_gabungan_mingguan.csv')
        df_gabungan_check = df_gabungan_mingguan[['Nilai Sentimen Saham', 'Nilai Sentimen Berita']]
        
        # Ambil Data EWM
        df_ewm_gabungan = df_gabungan_mingguan.copy()
        df_ewm_gabungan['Nilai Sentimen Saham'] = df_ewm_gabungan['Nilai Sentimen Saham'].ewm(alpha=alpha).mean()
        df_ewm_gabungan['Nilai Sentimen Berita'] = df_ewm_gabungan['Nilai Sentimen Berita'].ewm(alpha=alpha).mean()
        df_ewm_check = df_ewm_gabungan[['Nilai Sentimen Saham', 'Nilai Sentimen Berita']]
    
        # Ambil Data Rolling
        df_rolling_gabungan = df_gabungan_mingguan[['Tanggal Saham', 'Nilai Sentimen Saham', 'Tanggal Berita', 'Nilai Sentimen Berita']]
        df_rolling_gabungan['Nilai Sentimen Saham'] = df_rolling_gabungan['Nilai Sentimen Saham'].rolling(window=window).sum()
        df_rolling_gabungan['Nilai Sentimen Berita'] = df_rolling_gabungan['Nilai Sentimen Berita'].rolling(window=window).sum()
        df_rolling_gabungan = df_rolling_gabungan[window:]
        df_rolling_check = df_rolling_gabungan[['Nilai Sentimen Saham', 'Nilai Sentimen Berita']]

        # Hitung Kendalltau Normal
        tau0, p_value0 = stats.kendalltau(df_gabungan_check['Nilai Sentimen Saham'], df_gabungan_check['Nilai Sentimen Berita'])
    
        # Hitung Kendalltau EWM
        tau1, p_value1 = stats.kendalltau(df_ewm_check['Nilai Sentimen Saham'], df_ewm_check['Nilai Sentimen Berita'])

        # Hitung Kendalltau Rolling Window
        tau2, p_value2 = stats.kendalltau(df_rolling_check['Nilai Sentimen Saham'], df_rolling_check['Nilai Sentimen Berita'])

        # Grafik Sentimen Saham dan Berita Mingguan Normal
        st.success('Grafik Sentimen Saham (Mingguan) Normal')
        st.write(util.plot(df_gabungan_mingguan, 'Nilai Sentimen Saham', 'Tanggal Saham'))
        df_gabungan_mingguan['Sentimen Saham'] = util.create_sentimen(df_gabungan_mingguan, 'Nilai Sentimen Saham')
        st.success('Grafik Sentimen Berita (Mingguan) Normal')
        st.write(util.plot(df_gabungan_mingguan, 'Nilai Sentimen Berita', 'Tanggal Berita'))
        df_gabungan_mingguan['Sentimen Berita'] = util.create_sentimen(df_gabungan_mingguan, 'Nilai Sentimen Berita')

        # Tabel Kesesuaian Mingguan Normal
        st.info('Kesesuaian Grafik Sentimen Saham dan Berita (Mingguan)')
        st.write(df_gabungan_mingguan[['Tanggal Saham', 'Nilai Sentimen Saham', 'Sentimen Saham', 'Tanggal Berita', 'Nilai Sentimen Berita', 'Sentimen Berita']])
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Kesesuaian')
        st.write(str(util.calculate_score(df_gabungan_mingguan, 'Sentimen Saham', 'Sentimen Berita')))

        # Korelasi Minguan Normal
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Korelasi (Pearson)')
        st.write(df_gabungan_check.corr())

        # Korelasi Kendalltau Mingguan Normal
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Korelasi (Kendalltau) : ', str(tau0))
        st.write('Skor P-Value : ', str(p_value1))
        st.write('\n\n')
        st.write('\n\n')
        
        # Grafik Sentimen Saham dan Berita Mingguan EWM
        st.success('Grafik Sentimen Saham (Mingguan) EWM dengan Alpha : ' + str(round(alpha, 2)))
        st.write(util.plot(df_ewm_gabungan, 'Nilai Sentimen Saham', 'Tanggal Saham'))
        df_ewm_gabungan['Sentimen Saham'] = util.create_sentimen(df_ewm_gabungan, 'Nilai Sentimen Saham')
        st.success('Grafik Sentimen Berita (Mingguan) EWM dengan Alpha : ' + str(round(alpha, 2)))
        st.write(util.plot(df_ewm_gabungan, 'Nilai Sentimen Berita', 'Tanggal Berita'))
        df_ewm_gabungan['Sentimen Berita'] = util.create_sentimen(df_ewm_gabungan, 'Nilai Sentimen Berita')

        # Tabel Kesesuaian Mingguan EWM
        st.info('Kesesuaian Grafik Sentimen Saham dan Berita (Mingguan) EWM')
        st.write(df_ewm_gabungan[['Tanggal Saham', 'Nilai Sentimen Saham', 'Sentimen Saham', 'Tanggal Berita', 'Nilai Sentimen Berita', 'Sentimen Berita']])
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Kesesuaian')
        st.write(str(util.calculate_score(df_ewm_gabungan, 'Sentimen Saham', 'Sentimen Berita')))

        # Korelasi Minguan EWM
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Korelasi (Pearson)')
        st.write(df_ewm_check.corr())

        # Korelasi Kendalltau Mingguan EWM
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Korelasi (Kendalltau) : ', str(tau1))
        st.write('Skor P-Value : ', str(p_value1))
        st.write('\n\n')
        st.write('\n\n')

        # Grafik Sentimen Saham dan Berita Mingguan Rolling Window
        st.success('Grafik Sentimen Saham (Mingguan) Rolling Window : ' + str(round(window, 1)))
        st.write(util.plot(df_rolling_gabungan, 'Nilai Sentimen Saham', 'Tanggal Saham'))
        df_rolling_gabungan['Sentimen Saham'] = util.create_sentimen(df_rolling_gabungan, 'Nilai Sentimen Saham')
        st.success('Grafik Sentimen Berita (Mingguan) Rolling Window = ' + str(round(window, 1)))
        st.write(util.plot(df_rolling_gabungan, 'Nilai Sentimen Berita', 'Tanggal Berita'))
        df_rolling_gabungan['Sentimen Berita'] = util.create_sentimen(df_rolling_gabungan, 'Nilai Sentimen Berita')

        # Tabel Kesesuaian Mingguan Rolling Window
        st.info('Kesesuaian Grafik Sentimen Saham dan Berita (Mingguan) Rolling Window : ' + str(window))
        st.write(df_rolling_gabungan[['Tanggal Saham', 'Nilai Sentimen Saham', 'Sentimen Saham', 'Tanggal Berita', 'Nilai Sentimen Berita', 'Sentimen Berita']])
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Kesesuaian')
        st.write(str(util.calculate_score(df_rolling_gabungan, 'Sentimen Saham', 'Sentimen Berita')))

        # Korelasi Minguan Rolling Window
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Korelasi (Pearson)')
        st.write(df_rolling_check.corr())

        # Korelasi Kendalltau Mingguan Rolling Window
        st.write('\n\n')
        st.write('\n\n')
        st.write('Skor Korelasi (Kendalltau) : ', str(tau2))
        st.write('Skor P-Value : ', str(p_value2))
        st.write('\n\n')
        st.write('\n\n')

    # Menu Twitter
    if selected == "Twitter":
        # Sunting Sidebar
        st.sidebar.image("LPS.png", output_format='PNG')
        keyword = 'Dijamin LPS'
        keyword = st.sidebar.text_input('Pencarian :', keyword)
        
        # Sunting Header
        st.header("Analisis Tweet Twitter")
        
        # Menjalankan Analisis Sentimen Berita
        if st.sidebar.button('Run'):
            search_result = util.search_tweets(keyword)
            df_tweets = util.process_tweets(search_result)

            st.success('Hasil Pencarian Tweet')
            st.write(df_tweets)
            st.write('\n\n')
            st.write('\n\n')

            st.success('Deskripsi Statistik Hasil Pencarian Tweet')
            pd.set_option('display.float_format', lambda x: '%.2f' % x)
            st.write(df_tweets[['Jumlah Retweet','Jumlah Favourite']].describe().T)
            st.write('\n\n')
            st.write('\n\n')

            st.success('Grafik Jumlah Retweet terhadap Tweet')
            layout = go.Layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)')

            fig = go.Figure(layout=layout)

            fig.add_trace(go.Scatter(x=df_tweets['Tanggal'].str[:10], 
                                y=df_tweets['Jumlah Retweet'], 
                                name='Tweet'))
            
            fig.update_layout(height=540)
            fig.update_layout(width=960)
            st.write(fig)
            
            st.write('\n\n')
            st.write('\n\n')
        else:
            st.write('Tekan Run untuk menjalankan')
