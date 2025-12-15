import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

# 2. 강력한 모바일 전용 디자인 CSS
st.markdown("""
<style>
    /* [기본 배경] */
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }

    /* [제목] 🦁 아이콘 기준 수직 라인 정렬 */
    .ms-title-top { font-size: 26px; font-weight: 800; display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
    .ms-title-bottom { padding-left: 38px; font-size: 26px; font-weight: 800; margin-top: -10px; display: block; margin-bottom: 25px;}

    /* [★ 공통 라디오 버튼: 형광초록 테두리 & 선택 시 빨강 ★] */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* 폰에서 줄바꿈 절대 방지 */
        justify-content: center !important; /* 중앙 정렬 */
        gap: 10px !important;
        width: 100% !important;
    }
    
    /* 라디오 동그라미 숨기기 */
    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }

    /* 모든 버튼 기본 스타일 (형광 초록 테두리) */
    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        background-color: #1E1E1E !important;
        border: 1px solid #00FFD1 !important; /* 형광 초록 테두리 */
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        color: #AAA !important;
        cursor: pointer;
        min-width: 50px;
        text-align: center;
    }

    /* 선택 시 스타일 (빨간색 테두리 및 글씨) */
    div[data-testid="stRadio"] div[role="radiogroup"] > label[data-baseweb="radio"] {
        border-color: #EF5350 !important;
        color: #EF5350 !important;
        background-color: rgba(239, 83, 80, 0.1) !important;
    }

    /* [3] ★ 캘린더 네비게이션 전용: 여유로운 간격 ★ */
    .cal-nav-area div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 30px !important; /* ◀   날짜   ▶ 간 여유 */
    }
    .cal-nav-area div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2) {
        min-width: 160px !important; /* 날짜 영역 확보 */
    }

    /* [4] ★ 흐름 분석: 폰에서 버튼이 너무 작아지면 자동으로 2줄 허용 ★ */
    @media (max-width: 768px) {
        .chart-period-box div[data-testid="stRadio"] > div[role="radiogroup"] {
            flex-wrap: wrap !important; /* 폰에서 기간 버튼은 자연스럽게 줄바꿈 */
            justify-content: flex-start !important;
        }
        .score-part { border-right: none !important; border-bottom: 1px solid #333 !important; }
        .combined-score-container { flex-direction: column !important; }
    }

    /* 달력 본체 폭 고정 */
    .cal-wrapper { max-width: 380px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 처리
@st.cache_data
def get_market_data(ticker="QQQ"):
    df = yf.Ticker(ticker).history(period="5y")
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss; df['RSI'] = 100 - (100 / (1 + rs))
    tp = (df['High'] + df['Low'] + df['Close']) / 3; mf = tp * df['Volume']
    pos_f = mf.where(tp > tp.shift(1), 0).rolling(14).sum(); neg_f = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + pos_f / neg_f))
    df['MA20'] = df['Close'].rolling(20).mean(); df['Std'] = df['Close'].rolling(20).std()
    df['PctB'] = (df['Close'] - (df['MA20'] - 2*df['Std'])) / (4*df['Std']) * 100
    df['Score'] = (df['RSI'] * 0.3) + (df['MFI'] * 0.3) + (df['PctB'] * 0.4)
    df['Prev_Score'] = df['Score'].shift(1); df['Change'] = df['Score'] - df['Prev_Score']
    return df.dropna()

df = get_market_data()
last_row = df.iloc[-1]; curr_score = int(last_row['Score'])

# 4. 화면 구성
st.markdown(f'<div class="ms-title-top">🦁 민석이의</div><div class="ms-title-bottom">나스닥100 투자</div>', unsafe_allow_html=True)

# [상단 스코어 박스]
if curr_score <= 20: g_t, g_d, g_c = "🚨 인생 역전 기회", "시장이 공포에 질렸습니다.<br><span class='point-red'>TQQQ 50% 매수</span>!!!", "#4CAF50"
elif curr_score <= 30: g_t, g_d, g_c = "🛒 강력 매수", "확실한 저가 매수 찬스입니다.<br><span class='point-red'>TQQQ 30% 매수</span>!!", "#81C784"
elif curr_score <= 40: g_t, g_d, g_c = "🌱 가벼운 매수", "건강한 조정 구간입니다.<br><span class='point-red'>TQQQ 10% 매수</span>!", "#A5D6A7"
elif curr_score >= 85: g_t, g_d, g_c = "📉 수익 실현 권장", "상승의 끝자락일 수 있습니다.<br><span class='point-red'>20% 매도</span>해 현금을 확보하세요.", "#EF5350"
else: g_t, g_d, g_c = "💤 적립 유지", "평범한 우상향 구간입니다.<br>매일 QLD 만원 적립을 유지하세요.", "#00FFD1"

st.markdown(f"""
<div style="display: flex; background-color: #161618; border: 2px solid #333; border-radius: 15px; overflow: hidden; margin-bottom: 25px;" class="combined-score-container">
    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #1E1E1E; padding: 20px;" class="score-part">
        <span style="color:#888; font-size:13px;">현재 AI 점수</span>
        <span style="color:#00FFD1; font-size:70px; font-weight:bold; line-height:1;">{curr_score}</span>
    </div>
    <div style="flex: 2; padding: 25px; display: flex; flex-direction: column; justify-content: center; text-align: left;">
        <h3 style="margin:0; color:{g_c} !important;">{g_t}</h3>
        <p style="margin-top:8px; color:#BBB; font-size:15px; line-height:1.5;">{g_d}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. 달력 & 차트 레이아웃
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month

col_l, col_r = st.columns([1, 1.5], gap="large")

with col_l:
    st.subheader("🗓️ 점수 캘린더")
    # [달력 버튼 전용 영역]
    st.markdown('<div class="cal-nav-area">', unsafe_allow_html=True)
    curr_lab = f"{st.session_state.cal_year}년 {st.session_state.cal_month}월"
    nav_sel = st.radio("cal_nav", [" ◀ ", curr_lab, " ▶ "], horizontal=True, label_visibility="collapsed", index=1)
    if nav_sel == " ◀ ":
        st.session_state.cal_month -= 1
        if st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        st.rerun()
    elif nav_sel == " ▶ ":
        st.session_state.cal_month += 1
        if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cal-wrapper">', unsafe_allow_html=True)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    h = f'<div style="background-color:#161618; border-radius:15px; padding:12px; border:1px solid #333;"><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:4px; text-align:center; font-size:10px;"><div style="color:#FF5252;">일</div><div>월</div><div>화</div><div>수</div><div>목</div><div>금</div><div style="color:#5C9DFF;">토</div></div><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:4px; margin-top:5px;">'
    for week in cal:
        for day in week:
            if day == 0: h += '<div></div>'; continue
            d_str = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{day:02d}"
            bg, sc, stxt = "#262730", "#AAA", ""
            try:
                row = df[df.index.strftime('%Y-%m-%d') == d_str]
                if not row.empty:
                    val = int(row['Score'].iloc[0]); chg = row['Change'].iloc[0]; stxt = str(val)
                    bg, sc = ("#1B3320", "#4CAF50") if chg >= 0 else ("#331B1B", "#EF5350")
            except: pass
            h += f'<div style="aspect-ratio:1; background-color:{bg}; border-radius:5px; display:flex; flex-direction:column; align-items:center; justify-content:center;"><span style="font-size:8px; color:#666;">{day}</span><span style="font-size:12px; font-weight:bold; color:{sc};">{stxt}</span></div>'
    st.markdown(h + '</div></div></div>', unsafe_allow_html=True)

with col_r:
    st.subheader("📈 흐름 분석")
    st.markdown('<div class="chart-period-box">', unsafe_allow_html=True)
    # [흐름 분석 버튼] 1년 추가, 3년 제거
    period = st.radio("P", ["1개월", "3개월", "6개월", "1년", "5년"], horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    cdf = df.tail({"1개월":22, "3개월":63, "6개월":126, "1년":252, "5년":1260}[period])
    b_d, s_d = len(cdf[cdf['Score'] <= 40]), len(cdf[cdf['Score'] >= 85])
    st.markdown(f'<div style="font-size:12px; color:#AAA; text-align:right; margin-bottom:5px;">💰 40↓: <b style="color:#4CAF50;">{b_d}회</b> | 🔥 85↑: <b style="color:#EF5350;">{s_d}회</b></div>', unsafe_allow_html=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가", line=dict(color='#FF5252', width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.1)', line=dict(color='rgba(76, 175, 80, 0.4)')), secondary_y=True)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=10,b=0), height=350, showlegend=False, xaxis=dict(gridcolor='#333', tickformat='%y-%m'), yaxis=dict(gridcolor='#333'), yaxis2=dict(range=[0, 100], showgrid=False), hovermode="x unified", dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 하단 테이블 생략 (제공해주신 코드와 동일)
st.divider()
st.subheader("📋 실전 운용 전략 가이드")
st.markdown("""<table style="width:100%; border-collapse: collapse; background-color: #161618; border-radius: 10px; overflow: hidden; border: 1px solid #333;"><thead><tr><th style="background-color: #262730; color: #888; padding: 12px; border-bottom: 1px solid #333;">구간</th><th style="background-color: #262730; color: #888; padding: 12px; border-bottom: 1px solid #333;">상태</th><th style="background-color: #262730; color: #888; padding: 12px; border-bottom: 1px solid #333;">Action Plan</th></tr></thead><tbody><tr><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #4CAF50; font-weight: bold;">0~20</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">🚨공황</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">인생역전: <span style="color: #EF5350; font-weight: bold;">TQQQ 50% 매수</span></td></tr><tr><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #81C784; font-weight: bold;">21~30</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">🛒침체</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">저가매수: <span style="color: #EF5350; font-weight: bold;">TQQQ 30% 매수</span></td></tr><tr><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #A5D6A7; font-weight: bold;">31~40</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">🌱조정</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">가벼운매수: <span style="color: #EF5350; font-weight: bold;">TQQQ 10% 매수</span></td></tr><tr><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #00FFD1; font-weight: bold;">41~84</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">💤중립</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;"><b>QLD 적립 유지</b></td></tr><tr><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #EF5350; font-weight: bold;">85~100</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">🔥과열</td><td style="padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0;">수익실현: <span style="color: #EF5350; font-weight: bold;">20% 매도</span></td></tr></tbody></table>""", unsafe_allow_html=True)
