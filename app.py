import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

# 2. S24 전용 정밀 디자인 CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }

    /* [1] 제목: 호랑이 옆 '민' 자와 '나' 자의 수직 라인 정밀 정렬 */
    .main-title {
        font-size: 26px;
        font-weight: 800;
        line-height: 1.4;
        margin-bottom: 20px;
    }
    .indented-line {
        margin-left: 34px; /* 호랑이(🦁) 아이콘의 너비를 정밀 계산하여 들여쓰기 */
        display: block;
    }

    /* [2] 점수 산출 근거: 2단 그리드 (상단:라벨, 하단:수치) */
    .basis-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        background-color: #161618;
        border: 1px solid #333;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .basis-item {
        padding: 10px 0;
        text-align: center;
        border-right: 1px solid #222;
    }
    .basis-item:last-child { border-right: none; }
    .basis-label { font-size: 11px; color: #888; margin-bottom: 4px; }
    .basis-value { font-size: 16px; font-weight: bold; color: #00FFD1; }

    /* [3] 달력 내비게이션: S24 화면 폭 탈출 방지 및 한 줄 고정 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* 무조건 한 줄 */
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
    }
    
    /* 화살표 버튼 크기 고정 */
    div[data-testid="column"]:nth-of-type(1), 
    div[data-testid="column"]:nth-of-type(3) {
        width: 50px !important;
        flex: none !important;
    }
    
    /* 년도/월 텍스트 공간 확보 */
    div[data-testid="column"]:nth-of-type(2) {
        flex: 1 !important;
        min-width: 150px !important;
    }

    .stButton>button {
        background-color: #1E1E1E !important;
        color: #00FFD1 !important;
        border: 1px solid #00FFD1 !important;
        padding: 2px !important;
        height: 35px !important;
    }

    /* [4] 달력/차트 크기 최적화 (PC에서 비대해지는 현상 방지) */
    .cal-wrapper {
        max-width: 380px; /* PC/폰 공통 가장 보기 좋은 사이즈 */
        margin: 0 auto;
    }

    /* [5] 흐름 분석 라디오 버튼 그리드 (3x2 정렬) */
    div.stRadio > div[role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 6px !important;
    }
    div.stRadio > div[role="radiogroup"] > label {
        background-color: #1E1E1E !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
        padding: 8px 0 !important;
        font-size: 12px !important;
        justify-content: center !important;
    }

    /* 모바일 전용 미세 조정 */
    @media (max-width: 768px) {
        .combined-score-container { flex-direction: column; }
        .score-part { border-right: none; border-bottom: 1px solid #333; padding: 15px; }
        .score-part span:last-child { font-size: 60px !important; }
        .strategy-table td, .strategy-table th { font-size: 11px !important; padding: 10px 2px !important; }
    }

    .point-red { color: #EF5350 !important; font-weight: bold !important; }
    .combined-score-container { display: flex; background-color: #161618; border: 2px solid #333; border-radius: 15px; overflow: hidden; margin-bottom: 20px; }
    .score-part { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #1E1E1E; }
    .guide-part { flex: 2; padding: 20px; display: flex; flex-direction: column; justify-content: center; }
    .strategy-table { width: 100%; border-collapse: collapse; background-color: #161618; border-radius: 10px; overflow: hidden; border: 1px solid #333; }
    .strategy-table th { background-color: #262730; color: #888; padding: 8px; font-size: 12px; }
    .strategy-table td { padding: 12px 5px; text-align: center; color: #E0E0E0; border-bottom: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 및 로직 (기존 로직 유지)
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
    pos_f = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_f = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + pos_f / neg_f))
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Std'] = df['Close'].rolling(20).std()
    df['PctB'] = (df['Close'] - (df['MA20'] - 2*df['Std'])) / (4*df['Std']) * 100
    df['Score'] = (df['RSI'] * 0.3) + (df['MFI'] * 0.3) + (df['PctB'] * 0.4)
    df['Prev_Score'] = df['Score'].shift(1)
    df['Change'] = df['Score'] - df['Prev_Score']
    return df.dropna()

df = get_market_data()
last_row = df.iloc[-1]
curr_score = int(last_row['Score'])

# ---------------------------------------------------------
# 3. 화면 구성
# ---------------------------------------------------------
# [제목] 호랑이 아이콘 정렬 수정
st.markdown(f"""
<div class="main-title">
    🦁 민석이의<br>
    <span class="indented-line">나스닥100 투자</span>
</div>
""", unsafe_allow_html=True)

# [상단] AI 점수 통합 박스
if curr_score <= 20: g_t, g_d, g_c = "🚨 인생 역전 기회", "시장이 공포에 질렸습니다.<br><span class='point-red'>TQQQ 50% 매수</span>!!!", "#4CAF50"
elif curr_score <= 30: g_t, g_d, g_c = "🛒 강력 매수", "확실한 저가 매수 찬스입니다.<br><span class='point-red'>TQQQ 30% 매수</span>!!", "#81C784"
elif curr_score <= 40: g_t, g_d, g_c = "🌱 가벼운 매수", "건강한 조정 구간입니다.<br><span class='point-red'>TQQQ 10% 매수</span>!", "#A5D6A7"
elif curr_score >= 85: g_t, g_d, g_c = "📉 수익 실현 권장", "상승의 끝자락일 수 있습니다.<br><span class='point-red'>20% 매도</span>해 현금을 확보하세요.", "#EF5350"
else: g_t, g_d, g_c = "💤 적립 유지", "평범한 우상향 구간입니다.<br>매일 QLD 만원 적립을 유지하세요.", "#00FFD1"

st.markdown(f"""
<div class="combined-score-container">
    <div class="score-part">
        <span style="color:#888; font-size:13px;">현재 AI 점수</span>
        <span style="color:#00FFD1; font-size:75px; font-weight:bold; line-height:1;">{curr_score}</span>
    </div>
    <div class="guide-part">
        <h3 style="margin:0; color:{g_c} !important;">{g_t}</h3>
        <p style="margin-top:8px; color:#BBB; font-size:15px; line-height:1.5;">{g_d}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# [중단] 점수 산출 근거 (2단 레이아웃)
st.markdown(f"""
<div class="basis-container">
    <div class="basis-item"><div class="basis-label">심리(RSI)</div><div class="basis-value">{last_row['RSI']:.1f}</div></div>
    <div class="basis-item"><div class="basis-label">자금(MFI)</div><div class="basis-value">{last_row['MFI']:.1f}</div></div>
    <div class="basis-item"><div class="basis-label">밴드위치</div><div class="basis-value">{last_row['PctB']:.1f}%</div></div>
</div>
""", unsafe_allow_html=True)

# [점수 캘린더]
st.subheader("🗓️ 점수 캘린더")
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
def move_calendar(delta):
    st.session_state.cal_month += delta
    if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
    elif st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1

# 달력 내비게이션 (S24 정밀 정렬)
c_nav_col1, c_nav_col2, c_nav_col3 = st.columns([1, 4, 1])
with c_nav_col1: st.button("◀", key="prev_cal", on_click=move_calendar, args=(-1,))
with c_nav_col2: st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:18px; line-height:35px;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</div>", unsafe_allow_html=True)
with c_nav_col3: st.button("▶", key="next_cal", on_click=move_calendar, args=(1,))

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
                val = int(row['Score'].iloc[0]); stxt = str(val)
                bg = "#1B3320" if chg >= 0 else "#331B1B"
                sc = "#4CAF50" if chg >= 0 else "#EF5350"
                if d_str == datetime.now().strftime('%Y-%m-%d'): h += f'<div style="aspect-ratio:1; background-color:{bg}; border:1.5px solid #FFF; border-radius:5px; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
                else: h += f'<div style="aspect-ratio:1; background-color:{bg}; border-radius:5px; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
            else: h += f'<div style="aspect-ratio:1; background-color:#262730; border-radius:5px; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
        except: h += f'<div style="aspect-ratio:1; background-color:#262730; border-radius:5px; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
        h += f'<span style="font-size:8px; color:#666;">{day}</span><span style="font-size:12px; font-weight:bold; color:{sc};">{stxt}</span></div>'
st.markdown(h + '</div></div></div>', unsafe_allow_html=True)

# [흐름 분석]
st.write("")
st.subheader("📈 흐름 분석")
period = st.radio("P", ["1개월", "3개월", "6개월", "3년", "5년"], horizontal=True, label_visibility="collapsed")
cdf = df.tail({"1개월":22, "3개월":63, "6개월":126, "3년":756, "5년":1260}[period])
b_d, s_d = len(cdf[cdf['Score'] <= 40]), len(cdf[cdf['Score'] >= 85])
st.markdown(f'<div style="font-size:12px; color:#AAA; text-align:right; margin-bottom:5px;">💰 40↓: <b style="color:#4CAF50;">{b_d}회</b> | 🔥 85↑: <b style="color:#EF5350;">{s_d}회</b></div>', unsafe_allow_html=True)

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가", line=dict(color='#FF5252', width=2)), secondary_y=False)
fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.1)', line=dict(color='rgba(76, 175, 80, 0.4)')), secondary_y=True)
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=10,b=0), height=350, showlegend=False, xaxis=dict(gridcolor='#333', tickformat='%y-%m'), yaxis=dict(gridcolor='#333'), yaxis2=dict(range=[0, 100], showgrid=False), hovermode="x unified", dragmode=False)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# [하단 가이드]
st.divider()
st.subheader("📋 실전 운용 전략 가이드")
st.markdown("""
<table class="strategy-table">
    <thead><tr><th>구간</th><th>상태</th><th>Action Plan</th></tr></thead>
    <tbody>
        <tr><td style="color:#4CAF50;">0~20</td><td>🚨공황</td><td>인생역전: 보유 현금 <span class="point-red">50% TQQQ 매수</span></td></tr>
        <tr><td style="color:#81C784;">21~30</td><td>🛒침체</td><td>저가매수: 보유 현금 <span class="point-red">30% TQQQ 매수</span></td></tr>
        <tr><td style="color:#A5D6A7;">31~40</td><td>🌱조정</td><td>가벼운매수: 보유 현금 <span class="point-red">10% TQQQ 매수</span></td></tr>
        <tr><td style="color:#00FFD1;">41~84</td><td>💤중립</td><td><b>QLD 적립 유지</b></td></tr>
        <tr><td style="color:#EF5350;">85~100</td><td>🔥과열</td><td>수익실현: 보유 수량 <span class="point-red">20% 매도</span></td></tr>
    </tbody>
</table>
<div style="background-color: #161618; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-top: 15px;">
    <p style="margin: 0; font-size: 13px; color: #E0E0E0; font-weight: bold;">🇺🇸 미국 증시 영업시간 (한국시간)</p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #AAA;">
        - 정규장: 23:30 ~ 06:00 (서머타임 22:30 ~ 05:00)<br>
        - 프리마켓: 18:00 ~ 23:30 (서머타임 17:00 ~ 22:30)
    </p>
</div>
""", unsafe_allow_html=True)
