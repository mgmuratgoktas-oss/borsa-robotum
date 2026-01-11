import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Cep Borsa Pro", page_icon="📊", layout="centered")

st.title("📊 Canlı Borsa Analiz Robotu")

# --- FONKSİYON: HİSSELERİ ÇEK (GÜÇLENDİRİLMİŞ VERSİYON) ---
@st.cache_data
def hisse_listesi_getir():
    try:
        url = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseTekil"
        
        # ROBOT OLMADIĞIMIZI KANITLAYAN KİMLİK (User-Agent)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        cevap = requests.get(url, headers=headers, timeout=10)
        
        if cevap.status_code == 200:
            json_verisi = cevap.json()
            hisseler = [x['CODE'] + ".IS" for x in json_verisi['value']]
            hisseler.sort()
            return hisseler
        else:
            raise Exception("Site engelledi.")
            
    except Exception as e:
        # EĞER ÇEKEMEZSE BU YEDEK LİSTEYİ KULLAN (En Hacimli 50 Hisse)
        st.warning("Otomatik liste çekilemedi, yedek liste yüklendi.")
        yedek_liste = [
            "THYAO.IS", "ASTOR.IS", "EREGL.IS", "ASELS.IS", "SASA.IS", 
            "SISE.IS", "TUPRS.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS",
            "YKBNK.IS", "ISCTR.IS", "BIMAS.IS", "HEKTS.IS", "KOZAL.IS",
            "PETKM.IS", "KRDMD.IS", "SAHOL.IS", "FROTO.IS", "TOASO.IS",
            "KONTR.IS", "ODAS.IS", "GUBRF.IS", "ENKAI.IS", "VESTL.IS",
            "TCELL.IS", "TTKOM.IS", "SOKM.IS", "MGROS.IS", "AEFES.IS",
            "ALARK.IS", "PGSUS.IS", "TAVHL.IS", "EKGYO.IS", "DOHOL.IS",
            "TRHOL.IS", "TERA.IS", "SMRTG.IS", "EUPWR.IS", "CVKMD.IS"
        ]
        yedek_liste.sort()
        return yedek_liste

# Listeyi al
tum_hisseler = hisse_listesi_getir()

# --- YAN MENÜ ---
st.sidebar.header("Ayarlar")
hisse_kodu = st.sidebar.selectbox("Hisse Seçin:", tum_hisseler)
analiz_butonu = st.sidebar.button("ANALİZİ BAŞLAT 🚀")

def analiz_yap(sembol):
    try:
        hisse = yf.Ticker(sembol)
        df = hisse.history(period="1y")
        bilgi = hisse.info
        
        if df.empty:
            st.error("Veri alınamadı! Yahoo Finance sunucusu yanıt vermedi.")
            return
    except:
        st.error("Bağlantı hatası.")
        return

    # --- HESAPLAMALAR ---
    df['RSI'] = df.ta.rsi(length=14)
    df['SMA50'] = df.ta.sma(length=50)
    df['SMA200'] = df.ta.sma(length=200)
    df['ATR'] = df.ta.atr(length=14)
    
    # Bollinger
    bb = df.ta.bbands(length=20, std=2)
    if bb is not None:
        df['BB_Upper'] = bb.iloc[:, 2]
        df['BB_Lower'] = bb.iloc[:, 0]

    # Destek & Direnç
    son_20_gun = df[-20:]
    direnc = son_20_gun['High'].max()
    destek = son_20_gun['Low'].min()
    
    son = df.iloc[-1]
    
    # --- SONUÇ EKRANI ---
    st.divider()
    st.header(f"{sembol} Analiz Raporu")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Fiyat", f"{son['Close']:.2f} TL")
    
    # RSI Durumu
    if son['RSI'] < 30: 
        c2.success(f"RSI: {son['RSI']:.2f} (AL)")
    elif son['RSI'] > 70: 
        c2.error(f"RSI: {son['RSI']:.2f} (SAT)")
    else: 
        c2.metric("RSI", f"{son['RSI']:.2f}")

    # Trend Durumu
    if son['SMA50'] > son['SMA200']:
        c3.success("TREND: YÜKSELİŞ (Boğa)")
    else:
        c3.warning("TREND: DÜŞÜŞ/YATAY")

    # Grafik
    st.line_chart(df['Close'].tail(180))

    # Detaylar
    col_sol, col_sag = st.columns(2)
    
    with col_sol:
        st.info("📊 FİNANSAL DURUM")
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

    with col_sag:
        st.info("🛡️ SEVİYELER")
        st.write(f"**Direnç:** {direnc:.2f} TL")
        st.write(f"**Destek:** {destek:.2f} TL")
        st.error(f"**Stop-Loss:** {destek * 0.99:.2f} TL")

if analiz_butonu:
    with st.spinner('Veriler analiz ediliyor...'):
        analiz_yap(hisse_kodu)
