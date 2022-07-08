from operator import index
import string
import streamlit as st
import pandas as pd
import re  
from newspaper import Config
from textblob import TextBlob
from streamlit_option_menu import option_menu
import util
import altair as alt
import translators as ts
from scipy import stats
import warnings
warnings.simplefilter(action='ignore')

# Konfigurasi Halaman
st.set_page_config(page_title="Analisis Sentimen",
                   page_icon=":art:", layout="wide")

# Tombol Refresh
do_refresh = st.sidebar.button('Refresh')

# Konfigurasi Pilihan Menu
selected = option_menu(
    menu_title=None,
    options=["Sentimen Berita", "Sentimen Pasar", "Kesesuaian Sentimen"],
    icons=["newspaper", "bank", "graph-up"],
    menu_icon="cast",
    default_index=1,
    orientation="horizontal",
)

# Store Variable Nama Bank
if 'nama_bank' not in st.session_state:
    st.session_state['nama_bank'] = 'Bank Negara Indonesia'

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
            st.success(article_summary)
            st.write('Tanggal Berita :', published_date2)

            # Exception Handling
            try:
                news_properties = {}
                news_properties["title"] = article_title
                news_properties["tanggal"] = published_date2
                news_properties["isi_news"] = article_summary
            except Exception as e:
                print("error convert")
            
            # Tokenizing
            news_nilai = ' '.join(re.sub(
                "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|(\d+)", " ", str(article_summary)).split())
            
            # Case Folding
            news_nilai = news_nilai.lower()
            
            # Menghapus Whitepace
            news_nilai = news_nilai.strip()
            
            # Menghapus Tanda Baca
            news_nilai = news_nilai.translate(
                str.maketrans('', '', string.punctuation))

            st.write('Link Berita : ', base_url)
            analysis = TextBlob(news_nilai)

            # TextBlob
            try:
                analysis = ts.google(news_nilai, from_language='id', to_language='en')
            except Exception as e:
                print("")
            
            if TextBlob(analysis).sentiment.polarity > 0.0:
                news_properties['sentimen'] = "Positif"
                news_properties['param'] = TextBlob(analysis).sentiment.polarity
            elif TextBlob(analysis).sentiment.polarity == 0.0:
                news_properties['sentimen'] = "Netral"
                news_properties['param'] = TextBlob(analysis).sentiment.polarity
            else:
                news_properties['sentimen'] = "Negatif"
                news_properties['param'] = TextBlob(analysis).sentiment.polarity

            sentiment_dict = {'Polaritas' : TextBlob(analysis).sentiment.polarity, 'Subjektivitas' : TextBlob(analysis).sentiment.subjectivity}
            sentiment_df = pd.DataFrame(sentiment_dict.items(), columns=['Ukuran','Nilai'])
            st.write(sentiment_dict)
            
            c = alt.Chart(sentiment_df).mark_bar().encode(
                x='Ukuran',
                y='Nilai',
                color='Ukuran'
                )
                
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
    
    ticker_symbol = st.sidebar.text_input('Kode Saham :', 'BBNI')
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

    # Tambahan
    df_saham_temp = df_saham[['tanggal', 0]]
    start_date = df_saham['tanggal'].iloc[0]
    df_temp_3 = pd.DataFrame()
    df_temp_3['tanggal'], df_temp_3[0] = util.form_date_mingguan(df_saham, start_date, 'tanggal')
    df_temp_4 = df_saham_temp.append(df_temp_3)
    df_temp_4['tanggal'] = df_saham_temp['tanggal'].append(df_temp_3['tanggal'])
    df_saham_full = df_temp_4
    df_saham_full = df_saham_full.sort_values('tanggal')

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

    # df saham full
    df_saham_full = df_saham_full[['tanggal', 0]]
    df_saham_full = df_saham_full.rename(columns={'tanggal': 'Tanggal Saham', 0: 'Nilai Sentimen Saham'})
    df_saham_full = df_saham_full.reset_index(drop=True)
    
    df_berita_full = df_berita[['tanggal', 'nilaisentimen']]
    df_berita_full = df_berita_full.rename(columns={'tanggal': 'Tanggal Berita', 'nilaisentimen': 'Nilai Sentimen Berita'}) 
    df_berita_full = df_berita_full.reset_index(drop=True)

    df_gabungan_full = pd.concat([df_saham_full, df_berita_full], axis=1)
    df_gabungan_full.to_csv('df_gabungan_full.csv', index=False)
    df_gabungan_full.to_excel('df_gabungan_full.xlsx', index=False)
    
    # Memastikan Mulai di Baris yang Sama
    df_berita_weekly = df_berita_weekly[len(df_berita_weekly)-len(df_saham_weekly):]

    # Buat Sentimen Saham Mingguan
    df_saham_weekly['sentimen'] = util.create_sentimen(df_saham_weekly, 'sentimenweekly')
    df_saham_weekly.to_excel('df_saham_ver2.xlsx')

    # Format Data Saham Mingguan
    df_saham_mingguan = df_saham_weekly[['tanggal', 'sentimenweekly', 'sentimen']]
    df_saham_mingguan = df_saham_mingguan.rename(columns={'tanggal': 'Tanggal Saham', 'sentimenweekly': 'Nilai Sentimen Saham', 'sentimen': 'Sentimen Saham'})
    df_saham_mingguan = df_saham_mingguan.reset_index(drop=True)
    
    # Format Data Berita Mingguan
    df_berita_mingguan = df_berita_weekly[['tanggal', 'sentimenweekly', 'sentimen']]
    df_berita_mingguan = df_berita_mingguan.rename(columns={'tanggal': 'Tanggal Berita', 'sentimenweekly': 'Nilai Sentimen Berita', 'sentimen': 'Sentimen Berita'})
    df_berita_mingguan = df_berita_mingguan.reset_index(drop=True)

    # Data Gabungan Mingguan
    df_gabungan_mingguan = pd.concat([df_saham_mingguan, df_berita_mingguan], axis=1)
    df_gabungan_mingguan.to_csv('df_gabungan_mingguan.csv', index=False)
    df_gabungan_mingguan.to_excel('df_gabungan_mingguan.xlsx', index=False)

# Menu Kesesuaian Sentimen
if selected == "Kesesuaian Sentimen":
    
    # Sunting Sidebar
    st.sidebar.image("LPS.png", output_format='PNG')
    st.header("Analisis Kesesuaian Sentimen")

    # Ambil Data
    df_gabungan_mingguan = pd.read_csv('df_gabungan_mingguan.csv')
    df_gabungan_check = df_gabungan_mingguan[['Nilai Sentimen Saham', 'Nilai Sentimen Berita']]
    df_saham_weekly = pd.read_csv('df_saham_weekly.csv')
    df_berita_weekly = pd.read_csv('df_berita_weekly.csv')
    dicthari = {0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis', 4: 'Jumat'}
    hari = 0 # 0 = senin

    # Hari Senin
    df_gabungan_hari = df_gabungan_mingguan.copy()
    df_gabungan_hari["weekday"] = pd.to_datetime(df_gabungan_hari['Tanggal Saham']).dt.dayofweek
    df_gabungan_hari = df_gabungan_hari.loc[df_gabungan_hari["weekday"] == hari]
    df_gabungan_hari = df_gabungan_hari.reset_index(drop=True)
    df_gabungan_hari_check = df_gabungan_hari[['Nilai Sentimen Saham', 'Nilai Sentimen Berita']]

    # Hitung Lag Hari
    lag1 = 4
    df_gabungan_hari_check_lag = util.calculate_lag(df_gabungan_hari_check, lag1)

    # Hitung Kendalltau Normal
    tau1, p_value1 = stats.kendalltau(df_gabungan_check['Nilai Sentimen Saham'], df_gabungan_check['Nilai Sentimen Berita'])

    # Hitung Kendalltau Hari Lag
    tau2, p_value2 = stats.kendalltau(df_gabungan_hari_check_lag['Nilai Sentimen Saham'], df_gabungan_hari_check_lag['Nilai Sentimen Berita'])
    
    # Grafik Sentimen Saham dan Berita Mingguan
    st.success('Grafik Sentimen Saham Mingguan')
    st.write(util.plot(df_saham_weekly, 'sentimenweekly', 'tanggal'))
    st.success('Grafik Sentimen Berita Mingguan')
    st.write(util.plot(df_berita_weekly, 'sentimenweekly', 'tanggal'))

    # Tabel Kesesuaian Mingguan
    st.info('Kesesuaian Grafik Sentimen Saham dan Berita (Mingguan)')
    st.write(df_gabungan_mingguan)
    st.write('\n\n')
    st.write('\n\n')
    st.write('Skor Kesesuaian')
    st.write(str(util.calculate_score(df_gabungan_mingguan, 'Sentimen Saham', 'Sentimen Berita')))

    # Korelasi Minguan
    st.write('\n\n')
    st.write('\n\n')
    st.write('Skor Korelasi')
    st.write(df_gabungan_check.corr())

    # Korelasi Kendalltau Mingguan
    st.write('\n\n')
    st.write('\n\n')
    st.write('Skor Tau = ', str(tau1))
    st.write('Skor P-Value = ', str(p_value1))
    st.write('\n\n')
    st.write('\n\n')

    # Tabel Kesesuaian Hari Lag
    st.info('Kesesuaian Grafik Sentimen Saham dan Berita Hari ' + dicthari[hari] + ' (Bulanan)')
    st.write(df_gabungan_hari)
    st.write('\n\n')
    st.write('\n\n')
    st.write('Skor Kesesuaian')
    st.write(str(util.calculate_score(df_gabungan_hari, 'Sentimen Saham', 'Sentimen Berita')))
    
    # Korelasi Hari Lag
    st.write('\n\n')
    st.write('\n\n')
    st.write('Skor Korelasi')
    st.write(df_gabungan_hari_check_lag.corr())

    # Korelasi Kendalltau Hari Lag
    st.write('\n\n')
    st.write('\n\n')
    st.write('Skor Tau = ', str(tau2))
    st.write('Skor P-Value = ', str(p_value2))
