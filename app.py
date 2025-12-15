import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

st.markdown("""
<style>
/* =========================
   기본 다크모드 (PC 유지)
========================= */
[data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
[data-testid="stHeader"] { background-color: #0E1117 !important; }
h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }

/* 상단 통합 박스 */
.combined-score-container {
    display: flex;
    background-color: #161618;
    border: 2px solid #333;
    border-radius: 15px;
    overflow: hidden;
    min-height: 160px;
    margin-bottom: 25px;
}
.score-part {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-right: 1px solid #333;
    background-color: #1E1E1E;
}
.guide-part {
    flex: 2;
    padding: 25px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

/* 라디오 버튼 */
div.stRadio > div[role="radiogroup"] { gap: 5px; }
div.stRadio > div[role="radiogroup"] > label {
    background-color: #1E1E1E !important;
    border: 1px solid #444 !important;
    color: #AAA !important;
    border-radius: 4px !important;
    padding: 4px 12px !important;
    font-size: 12px !important;
}
div.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] {
    background-color: #262730 !important;
    border: 1px solid #00FFD1 !important;
    color: #00FFD1 !important;
}

/* 강조 */
.point-red { color: #EF5350 !important; font-weight: bold !important; }

/* 전략 테이블 */
.strategy-table {
    width: 100%;
    border-collapse: collapse;
    background-color: #161618;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #333;
}
.strategy-table th {
    background-color: #262730;
    padding: 12px;
    border-bottom: 1px solid #333;
}
.strategy-table td {
    padding: 15px;
    border-bottom: 1px solid #333;
}

/* 버튼 */
.stButton>button {
    width: 100%;
    background-color: #1E1E1E !important;
    border: 1px solid #444 !important;
    color: white !important;
}

/* =========================
   📱 모바일 대응 (768px 이하)
========================= */
@media (max-width: 768px) {

    .block-container {
        padding: 1rem 0.7rem !important;
    }

    /* 상단 점수 박스 → 세로 */
    .combined-score-container {
        flex-direction: column !important;
        min-height: auto !important;
    }

    .score-part {
        border-right: none !important;
        border-bottom: 1px solid #333 !important;
        padding: 20px 0;
    }

    .score-part span:nth-child(2) {
        font-size: 52px !important;
    }

    .guide-part h3 {
        font-size: 18px !important;
    }

    .guide-part p {
        font-size: 14px !important;
    }

    /* 라디오 줄바꿈 */
    div.stRadio > div[role="radiogroup"] {
        flex-wrap: wrap !important;
    }

    div.stRadio > div[role="radiogroup"] > label {
        font-size: 11px !important;
        padding: 4px 8px !important;
    }

    /* 차트 높이 축소 */
    .js-plotly-plot {
        height: 300px !important;
    }

    /* 테이블 가독성 */
    .strategy-table th,
    .strategy-table td {
        font-size: 12px !important;
        padding: 8px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 처리
# ---------------------------------------------------------
@st.cache_data
def get_market_data(ticker="QQQ"):
    df = yf.Ticker(ticker).history(period="5y")
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + pos / neg))

    df['MA20'] = df['Close'].rolling(20).mean()
    df['Std'] = df['Close'].rolling(20).std()
    df['PctB'] = (df['Close'] - (df['MA20'] - 2*df['Std'])) / (4*df['Std']) * 100

    df['Score'] = df['RSI']*0.3 + df['MFI']*0.3 + df['PctB']*0.4
    df['Change'] = df['Score'] - df['Score'].shift(1)
    return df.dropna()

# ---------------------------------------------------------
# 3. 실행
# ---------------------------------------------------------
df = get_market_data()
last = df.iloc[-1]
score = int(last['Score'])

st.title("🦁 민석이의 나스닥100 투자")
st.markdown("---")

st.markdown(f"""
<div class="combined-score-container">
    <div class="score-part">
        <span style="font-size:13px;color:#888;">현재 AI 점수</span>
        <span style="font-size:75px;font-weight:bold;color:#00FFD1;">{score}</span>
    </div>
    <div class="guide-part">
        <h3>📊 투자 판단 가이드</h3>
        <p>점수 기반으로 매수·매도 판단을 제공합니다.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.subheader("📈 점수 흐름")
period = st.radio("기간", ["1개월", "3개월", "6개월", "1년"], horizontal=True)
cdf = df.tail({"1개월":22,"3개월":63,"6개월":126,"1년":252}[period])

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가"), secondary_y=False)
fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy'), secondary_y=True)
fig.update_layout(height=400, showlegend=False)

st.plotly_chart(fig, use_container_width=True)
