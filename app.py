import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests # İnternetten veri çekmek için

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Cep Borsa Pro", page_icon="📊", layout="centered")

st.title("📊 Canlı Borsa Analiz Robotu")
st.markdown("Borsa İstanbul'daki **tüm hisseleri** otomatik tarar.")

# --- FONKSİYON: TÜM HİSSELERİ ÇEK (CANLI VERİTABANI) ---
@st.cache_data # Bu listeyi hafızaya al, her defasında tekrar çekip yavaşlatma
def hisse_listesi_getir():
    try:
        # İş Yatırım'ın tüm hisseleri tuttuğu kaynak
        url = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseTekil"
        cevap = requests.get(url)
        json_verisi = cevap.json()
        
        # Sadece hisse kodlarını al ve sonuna .IS ekle (Yahoo Finance formatı için)
        hisseler = [x['CODE'] + ".IS" for x in json_verisi['value']]
        hisseler.sort() # Alfabetik sırala
        return hisseler
    except:
        st.error("Hisse listesi çekilemedi! Manuel liste kullanılıyor.")
        return ["ASTOR.IS", "THYAO.IS", "GARAN.IS"] # Yedek liste

# Listeyi getir
tum_hisseler = hisse_listesi_getir()

# --- YAN MENÜ ---
st.sidebar.header("Ayarlar")
# Artık listede 500+ hisse var!
hisse_kodu = st.sidebar.selectbox("Hisse Seçin:", tum_hisseler, index=tum_hisseler.index("THYAO.IS") if "THYAO.IS" in tum_hisseler else 0)
analiz_butonu = st.sidebar.button("ANALİZİ BAŞLAT 🚀")

def analiz_yap(sembol):
    try:
        hisse = yf.Ticker(sembol)
        # Son 1 yılı çekiyoruz
        df = hisse.history(period="1y")
        bilgi = hisse.info
        
        if df.empty:
            st.error("Veri alınamadı! (Yahoo Finance'te bu hisse olmayabilir)")
            return
    except:
        st.error("Bağlantı hatası.")
        return

    # --- HESAPLAMALAR ---
    df['RSI'] = df.ta.rsi(length=14)
    df['SMA50'] = df.ta.sma(length=50)
    df['SMA200'] = df.ta.sma(length=200)
    df['ATR'] = df.ta.atr(length=14)
    
    # Bollinger Bantları
    bb = df.ta.bbands(length=20, std=2)
    if bb is not None:
        df['BB_Upper'] = bb.iloc[:, 2]
        df['BB_Lower'] = bb.iloc[:, 0]

    # Destek & Direnç (Son 1 Ay)
    son_20_gun = df[-20:]
    direnc = son_20_gun['High'].max()
    destek = son_20_gun['Low'].min()
    
    son = df.iloc[-1]
    
    # --- SONUÇ EKRANI ---
    st.divider()
    
    # Başlık ve Fiyat
    st.header(f"{sembol} Analiz Raporu")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Fiyat", f"{son['Close']:.2f} TL")
    
    # RSI Renkli Gösterge
    rsi_durum = "NÖTR"
    if son['RSI'] < 30: 
        rsi_durum = "UCUZ (AL)"
        c2.success(f"RSI: {son['RSI']:.2f}")
    elif son['RSI'] > 70: 
        rsi_durum = "PAHALI (SAT)"
        c2.error(f"RSI: {son['RSI']:.2f}")
    else: 
        c2.metric("RSI", f"{son['RSI']:.2f}")
        
    c3.metric("Durum", rsi_durum)

    # Grafik
    st.line_chart(df['Close'].tail(180))

    # Detaylı Tablolar
    col_sol, col_sag = st.columns(2)
    
    with col_sol:
        st.info("📊 TEMEL GÖSTERGELER")
        fk = bilgi.get('trailingPE')
        pddd = bilgi.get('priceToBook')
        
        if fk:
            yorum = "✅ Ucuz" if fk < 10 else ("⚠️ Pahalı" if fk > 20 else "✅ Makul")
            st.write(f"**F/K:** {fk:.2f} ({yorum})")
        else:
            st.write("**F/K:** Veri Yok")
            
        if pddd:
            st.write(f"**PD/DD:** {pddd:.2f}")
        else:
            st.write("**PD/DD:** Veri Yok")
            
        # Golden Cross
        if son['SMA50'] > son['SMA200']:
            st.success("🌟 GOLDEN CROSS: Yükseliş Trendi")
        else:
            st.warning("❄️ TREND: Düşüş veya Yatay")

    with col_sag:
        st.info("🛡️ DESTEK & STOP")
        st.write(f"**Tavan (Direnç):** {direnc:.2f} TL")
        st.write(f"**Taban (Destek):** {destek:.2f} TL")
        
        stop = destek * 0.99
        st.error(f"**Önerilen Stop:** {stop:.2f} TL")
        
    # Hacim Uyarısı
    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
    if son['Volume'] > vol_avg * 1.5:
        st.warning("🔥 **DİKKAT:** Hacim patlaması var! Sert hareket olabilir.")

if analiz_butonu:
    with st.spinner(f'{hisse_kodu} verileri indiriliyor...'):
        analiz_yap(hisse_kodu)

