import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="Cep Borsa", page_icon="📱", layout="centered")

st.title("📱 Mobil Borsa Robotu")
st.info("Hisse adını listeden seçin, analizi aşağıda görün.")

# HİSSE LİSTESİ
populer_hisseler = [
    "ASTOR.IS", "THYAO.IS", "TERA.IS", "EREGL.IS", "ASELS.IS", 
    "SASA.IS", "HEKTS.IS", "SISE.IS", "TUPRS.IS", "GARAN.IS", 
    "KCHOL.IS", "BIMAS.IS", "AKBNK.IS", "YKBNK.IS", "KOZAL.IS",
    "KONTR.IS", "GUBRF.IS", "ODAS.IS", "PETKM.IS", "TRHOL.IS"
]

hisse_kodu = st.selectbox("Analiz edilecek hisseyi seçin:", populer_hisseler)
analiz_butonu = st.button("ANALİZİ BAŞLAT 🚀")

def analiz_yap(sembol):
    try:
        hisse = yf.Ticker(sembol)
        df = hisse.history(period="1y")
        bilgi = hisse.info
        if df.empty:
            st.error("Veri alınamadı!")
            return
    except:
        st.error("Veri çekme hatası.")
        return

    # HESAPLAMALAR
    df['RSI'] = df.ta.rsi(length=14)
    df['SMA50'] = df.ta.sma(length=50)
    df['SMA200'] = df.ta.sma(length=200)
    df['ATR'] = df.ta.atr(length=14)
    
    # Bollinger
    bb = df.ta.bbands(length=20, std=2)
    if bb is not None:
        df['BB_Upper'] = bb.iloc[:, 2]
        df['BB_Lower'] = bb.iloc[:, 0]

    son_20_gun = df[-20:]
    direnc = son_20_gun['High'].max()
    destek = son_20_gun['Low'].min()
    son = df.iloc[-1]
    
    # SONUÇ EKRANI
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Fiyat", f"{son['Close']:.2f} TL")
    
    if son['RSI'] < 30: c2.success(f"RSI: {son['RSI']:.2f} (UCUZ)")
    elif son['RSI'] > 70: c2.error(f"RSI: {son['RSI']:.2f} (PAHALI)")
    else: c2.metric("RSI", f"{son['RSI']:.2f}")

    st.subheader("📉 6 Aylık Grafik")
    st.line_chart(df['Close'].tail(180))

    st.subheader("🤖 Robotun Raporu")
    
    # F/K Yorum
    fk = bilgi.get('trailingPE')
    if fk:
        yorum = "✅ Ucuz" if fk < 10 else "⚠️ Pahalı"
        st.write(f"**Temel Analiz:** F/K {fk:.2f} -> *{yorum}*")
    
    # Golden Cross
    if son['SMA50'] > son['SMA200']:
        st.success("🌟 TREND: Golden Cross (Yükseliş) Var!")
    else:
        st.warning("❄️ TREND: Düşüş/Yatay")
        
    st.info(f"🧱 Destek: {destek:.2f} | Direnç: {direnc:.2f}")
    st.error(f"🛡️ Stop-Loss: {destek * 0.99:.2f} TL")

if analiz_butonu:
    with st.spinner('Analiz yapılıyor...'):
        analiz_yap(hisse_kodu)
