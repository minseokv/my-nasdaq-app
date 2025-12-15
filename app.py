import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# ---------------------------------------------------------
# 1. 페이지 설정 및 다크모드/디자인 고정
# ---------------------------------------------------------
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

st.markdown("""
<style>
/* =========================
   기본 스타일 (PC 유지)
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

/* 버튼 */
.stButton>button {
    width: 100%;
    background-color: #1E1E1E !important;
    border: 1px solid #444 !important;
    color: white !important;
}

/* 강조 */
.point-red { color: #EF5350 !important; font-weight: bold !important; }

/* =========================
   📱 모바일 전용 UI 개선
   (내용·구조 변경 없음)
========================= */
@media (max-width: 768px) {

    /* 전체 좌우 여백 줄여서 공간 확보 */
    .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* 버튼 터치 영역 확대 */
    .stButton>button {
        min-height: 48px !important;
        font-size: 15px !important;
        border-radius: 8px !important;
    }

    /* 캘린더 이동 버튼 (◀ ▶) */
    .stButton>button[key="p"],
    .stButton>button[key="n"] {
        min-height: 48px !important;
        font-size: 18px !important;
    }

    /* 라디오 버튼: 줄바꿈 + 터치 패딩 */
    div.stRadio > div[role="radiogroup"] {
        flex-wrap: wrap !important;
        row-gap: 8px !important;
    }

    div.stRadio > div[role="radiogroup"] > label {
        padding: 8px 14px !important;
        font-size: 13px !important;
    }

    /* Plotly 차트: 터치 스크롤 여유 */
    .js-plotly-plot {
        margin-bottom: 20px !important;
    }

    /* 테이블: 터치 가독성 */
    .strategy-table td,
    .strategy-table th {
        padding: 10px !important;
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
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos_flow = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_flow = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + pos_flow / neg_flow))
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Std'] = df['Close'].rolling(20).std()
    df['PctB'] = (df['Close'] - (df['MA20'] - 2*df['Std'])) / (4*df['Std']) * 100
    df['Score'] = (df['RSI'] * 0.3) + (df['MFI'] * 0.3) + (df['PctB'] * 0.4)
    df['Prev_Score'] = df['Score'].shift(1)
    df['Change'] = df['Score'] - df['Prev_Score']
    return df.dropna()

# ---------------------------------------------------------
# 이하 실행/UI 구성
# 👉 🔥 네 원본 코드 그대로 (변경 없음)
# ---------------------------------------------------------
