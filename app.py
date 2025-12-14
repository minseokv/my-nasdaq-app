import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

# 2. 정밀 디자인 CSS
st.markdown("""
<style>
    /* 전체 배경 */
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }

    /* [1] 제목: 🦁 민석이의 아래에 나스닥100 투자 수직 정렬 */
    .title-area { margin-bottom: 25px; text-align: left; }
    .title-row1 { display: flex; align-items: center; gap: 10px; font-size: 26px; font-weight: 800; }
    .title-row2 { padding-left: 38px; font-size: 26px; font-weight: 800; margin-top: -5px; display: block; }

    /* [2] 점수 산출 근거: 3열 그리드 */
    .basis-container {
        display: grid; grid-template-columns: repeat(3, 1fr);
        background-color: #161618; border: 1px solid #333; border-radius: 12px; margin-bottom: 20px;
    }
    .basis-item { padding: 10px 0; text-align: center; border-right: 1px solid #222; }
    .basis-item:last-child { border-right: none; }
    .basis-label { font-size: 11px; color: #888; margin-bottom: 4px; }
    .basis-value { font-size: 16px; font-weight: bold; color: #00FFD1; }

    /* [3] ★ 캘린더 네비게이션: 한 줄 중앙 배치 + 여유로운 간격 ★ */
    .cal-nav-area div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: center !important; /* 중앙 정렬 */
        gap: 15px !important; /* 버튼 간격 여유 */
        width: 100% !important;
    }
    
    /* 라디오 버튼 동그라미 숨기기 */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    .cal-nav-area div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #1E1E1E !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
        padding: 8px 15px !important; /* 내부 여백으로 널찍하게 */
        font-size: 15px !important;
        font-weight: bold !important;
        white-space: nowrap !important;
        min-width: 50px;
        text-align: center;
    }

    /* 날짜가 써있는 가운데 버튼만 더 길게 */
    .cal-nav-area div[data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(2) {
        flex: 2 !important;
        min-width: 150px !important;
    }

    /* 강조 색상 (민트) */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-baseweb="radio"] {
        border-color: #00FFD1 !important;
        color: #00FFD1 !important;
    }

    /* [4] 흐름 분석: 민석님이 건들지 말라고 했을 때의 예쁜 한 줄 배치로 복구 */
    .chart-period-box div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: flex-start !important;
        gap: 8px !important;
    }
    .chart-period-box div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: none !important;
        width: auto !important;
        padding: 6px 12px !important;
    }

    /* 달력 본체 폭 고정 */
    .cal-wrapper { max-width: 380px; margin: 0 auto; }

    @media (max-width: 768px) {
        .combined-score-container { flex-direction: column !important; }
        .score-part { border-right: none !important; border-bottom: 1px solid #333 !important; }
        .score-part span:last-child { font-size: 60px !important; }
        .cal-wrapper { max-width: 100% !important; }
    }

    .point-red { color: #EF5350 !important; font-weight: bold !important; }
    .combined-score-container { display: flex; background-color: #161618; border: 2px solid #333; border-radius: 15px; overflow: hidden; margin-bottom: 20px; }
    .score-part { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #1E1E1E; padding: 20px; }
    .guide-part { flex: 2; padding: 20px; display: flex; flex-direction: column; justify-content: center; }
    .strategy-table { width: 100%; border-collapse: collapse; background-color: #161618; border-radius: 10px; border: 1px solid #333; }
    .strategy-table th { background-color: #262730; color: #888; padding: 10px; font-size: 12px; }
    .strategy-table td { padding: 12px 5px; text-align: center; color: #E0E0E0; font-size: 13px; border-bottom: 1px solid #333; }
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
last_row = df.iloc[-1]
curr_score = int(last_row['Score'])

# 4. 화면 구성 시작
st.markdown(f'<div class="title-area"><div class="title-row1">🦁 민석이의</div><div class="title-row2">나스닥100 투자</div></div>', unsafe_allow_html=True)

# [상단 박스]
if curr_score <= 20: g_t, g_d, g_c = "🚨 인생 역전 기회", "시장이 공포에 질렸습니다.<br><span class='point-red'>TQQQ 50% 매수</span>!!!", "#4CAF50"
elif curr_score <= 30: g_t, g_d, g_c = "🛒 강력 매수", "확실한 저가 매수 찬스입니다.<br><span class='point-red'>TQQQ 30% 매수</span>!!", "#81C784"
elif curr_score <= 40: g_t, g_d, g_c = "🌱 가벼운 매수", "건강한 조정 구간입니다.<br><span class='point-red'>TQQQ 10% 매수</span>!", "#A5D6A7"
elif curr_score >= 85: g_t, g_d, g_c = "📉 수익 실현 권장", "상승의 끝자락일 수 있습니다.<br><span class='point-red'>20% 매도</span>해 현금을 확보하세요.", "#EF5350"
else: g_t, g_d, g_c = "💤 적립 유지", "평범한 우상향 구간입니다.<br>매일 QLD 만원 적립을 유지하세요.", "#00FFD1"

st.markdown(f"""<div class="combined-score-container"><div class="score-part"><span style="color:#888; font-size:13px;">현재 AI 점수</span><span style="color:#00FFD1; font-size:70px; font-weight:bold; line-height:1;">{curr_score}</span></div><div class="guide-part"><h3 style="margin:0; color:{g_c} !important;">{g_t}</h3><p style="margin-top:8px; color:#BBB; font-size:15px; line-height:1.5;">{g_d}</p></div></div>""", unsafe_allow_html=True)

# [근거 그리드]
st.markdown(f"""<div class="basis-container"><div class="basis-item"><div class="basis-label">심리(RSI)</div><div class="basis-value">{last_row['RSI']:.1f}</div></div><div class="basis-item"><div class="basis-label">자금(MFI)</div><div class="basis-value">{last_row['MFI']:.1f}</div></div><div class="basis-item"><div class="basis-label">밴드위치</div><div class="basis-value">{last_row['PctB']:.1f}%</div></div></div>""", unsafe_allow_html=True)

# 5. 달력 & 차트 섹션
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
def move_cal(d):
    st.session_state.cal_month += d
    if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
    elif st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1

col_left, col_right = st.columns([1, 1.6], gap="medium")

with col_left:
    st.subheader("🗓️ 점수 캘린더")
    
    # [달력 네비게이션] ◀      2025년 12월      ▶
    st.markdown('<div class="cal-nav-area">', unsafe_allow_html=True)
    current_label = f"{st.session_state.cal_year}년 {st.session_state.cal_month}월"
    nav_pick = st.radio("cal_nav", [" ◀ ", current_label, " ▶ "], horizontal=True, label_visibility="collapsed", index=1)
    
    if nav_pick == " ◀ ":
        st.session_state.cal_month -= 1
        if st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        st.rerun()
    elif nav_pick == " ▶ ":
        st.session_state.cal_month += 1
        if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cal-wrapper">', unsafe_allow_html=True)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    h = f'<div style="background-color:#161618; border-radius:15px; padding:12px; border:1px solid #333; margin-top:5px;"><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:4px; text-align:center; font-size:10px;"><div style="color:#FF5252;">일</div><div>월</div><div>화</div><div>수</div><div>목</div><div>금</div><div style="color:#5C9DFF;">토</div></div><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:4px; margin-top:5px;">'
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

with col_right:
    st.subheader("📈 흐름 분석")
    st.markdown('<div class="chart-period-box">', unsafe_allow_html=True)
    period = st.radio("P", ["1개월", "3개월", "6개월", "3년", "5년"], horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    cdf = df.tail({"1개월":22, "3개월":63, "6개월":126, "3년":756, "5년":1260}[period])
    b_d, s_d = len(cdf[cdf['Score'] <= 40]), len(cdf[cdf['Score'] >= 85])
    st.markdown(f'<div style="font-size:12px; color:#AAA; text-align:right; margin-bottom:5px;">💰 40↓: <b style="color:#4CAF50;">{b_d}회</b> | 🔥 85↑: <b style="color:#EF5350;">{s_d}회</b></div>', unsafe_allow_html=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가", line=dict(color='#FF5252', width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.1)', line=dict(color='rgba(76, 175, 80, 0.4)')), secondary_y=True)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=10,b=0), height=350, showlegend=False, xaxis=dict(gridcolor='#333', tickformat='%y-%m'), yaxis=dict(gridcolor='#333'), yaxis2=dict(range=[0, 100], showgrid=False), hovermode="x unified", dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 하단 가이드
st.divider()
st.subheader("📋 실전 운용 전략 가이드")
st.markdown("""<table class="strategy-table"><thead><tr><th>구간</th><th>상태</th><th>Action Plan</th></tr></thead><tbody><tr><td style="color:#4CAF50;">0~20</td><td>🚨공황</td><td>인생역전: <span class="point-red">TQQQ 50% 매수</span></td></tr><tr><td style="color:#81C784;">21~30</td><td>🛒침체</td><td>저가매수: <span class="point-red">TQQQ 30% 매수</span></td></tr><tr><td style="color:#A5D6A7;">31~40</td><td>🌱조정</td><td>가벼운매수: <span class="point-red">TQQQ 10% 매수</span></td></tr><tr><td style="color:#00FFD1;">41~84</td><td>💤중립</td><td><b>QLD 적립 유지</b></td></tr><tr><td style="color:#EF5350;">85~100</td><td>🔥과열</td><td>수익실현: <span class="point-red">20% 매도</span></td></tr></tbody></table>""", unsafe_allow_html=True)
