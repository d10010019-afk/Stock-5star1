import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # 確保這裡是用底線
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 頁面設定
st.set_page_config(page_title="五星共振量化系統", layout="wide")
st.title("🌟 五星共振量化選股系統 (資深設計師版)")
st.sidebar.header("參數設定")

# 2. 輸入參數
symbol = st.sidebar.text_input("輸入股票代碼 (例: 2330.TW, 0050.TW)", "2330.TW")
period = st.sidebar.selectbox("資料範圍", ["3mo", "6mo", "1y"], index=0)

# 3. 抓取資料與計算指標
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period=period, interval="1d")
    # 計算 5日均線
    df['MA5'] = ta.sma(df['Close'], length=5)
    # 計算 MACD
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1)
    # 計算 RSI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    return df

try:
    df = get_data(symbol)
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    # 4. 五星共振邏輯判定
    score = 0
    checks = []

    # 星 1: K棒與5日線
    if last_row['Close'] > last_row['MA5']:
        score += 1
        checks.append("✅ 股價在5日線上 (趨勢偏多)")
    else:
        checks.append("❌ 股價在5日線下 (趨勢轉弱)")

    # 星 2: MACD 動能
    if last_row['MACDH_12_26_9'] > 0 and last_row['MACDH_12_26_9'] > prev_row['MACDH_12_26_9']:
        score += 1
        checks.append("✅ MACD 紅柱增長 (動能強勁)")
    else:
        checks.append("❌ MACD 動能不足")

    # 星 3: RSI 拐點
    if 40 < last_row['RSI'] < 75:
        score += 1
        checks.append(f"✅ RSI 分數 {last_row['RSI']:.1f} (健康區間)")
    else:
        checks.append(f"❌ RSI 過高或過低 ({last_row['RSI']:.1f})")

    # 星 4: 成交量顏色
    if last_row['Close'] > last_row['Open']:
        score += 1
        checks.append("✅ 當日量能收紅 (多頭攻擊)")
    else:
        checks.append("❌ 當日量能收綠")

    # 星 5: 量能爆發 (今日量 > 5日均量)
    avg_vol = df['Volume'].tail(5).mean()
    if last_row['Volume'] > avg_vol:
        score += 1
        checks.append("✅ 量能超過5日均量 (有效突破)")
    else:
        checks.append("❌ 量能萎縮 (動能不足)")

    # 5. 顯示結果儀表板
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("量化評分結果")
        st.metric(label="五星共振總分", value=f"{score} / 5")
        for c in checks:
            st.write(c)
        
        if score >= 4:
            st.success("🔥 強烈建議進場：多頭共振確立！")
        elif score >= 2:
            st.warning("⚖️ 觀望或小量佈局：指標尚未一致。")
        else:
            st.error("❄️ 絕對禁區：趨勢走弱，請勿接刀。")

    # 6. 繪製互動式圖表
    with col2:
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.5, 0.25, 0.25])

        # K線與5日線
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                     low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='orange', width=2), name='5日線'), row=1, col=1)

        # MACD
        colors = ['red' if val > 0 else 'green' for val in df['MACDH_12_26_9']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACDH_12_26_9'], marker_color=colors, name='MACD柱狀體'), row=2, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

        fig.update_layout(height=600, template='plotly_dark', showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"無法取得資料，請檢查代碼是否正確。錯誤原因: {e}")

