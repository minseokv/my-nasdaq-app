import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

# 2. 반응형 CSS 설정 (PC와 S24 동시 최적화)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }

    /* --- [핵심] 모바일/PC 반응형 레이아웃 --- */
    .combined-score-container {
        display: flex;
        flex-direction: row; /* 기본 PC: 가로 배치 */
        background-color: #161618;
        border: 2px solid #333;
        border-radius: 15px;
        overflow: hidden;
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
        padding: 20px;
    }

    .guide-part {
        flex: 2;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 갤럭시 S24 등 모바일 환경 (가로폭 768px 이하) */
    @media (max-width: 768px) {
        .combined-score-container {
            flex-direction: column; /* 폰에서는 세로로 쌓기 */
        }
        .score-part {
            border-right: none;
            border-bottom: 1px solid #333;
            padding: 15px;
        }
        .score-part span:last-child {
            font-size: 60px !important; /* 점수 크기 약간 축소 */
        }
        .guide-part h3 {
            font-size: 1.2rem !important;
        }
        .guide-part p {
            font-size: 14px !important;
        }
        .strategy-table td, .strategy-table th {
            padding: 8px !important; /* 표 간격 축소 */
            font-size: 12px !important;
        }
    }

    /* 공통 스타일 */
    .point-red { color: #EF5350 !important; font-weight: bold !important; }
    .strategy-table { width: 100%; border-collapse: collapse; background-color: #161618; border-radius: 10px; overflow: hidden; border: 1px solid #333; }
    .strategy-table th { background-color: #262730; color: #888; padding: 12px; text-align: center; border-bottom: 1px solid #333; }
    .strategy-table td { padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0; }
    div.stRadio > div[role="radiogroup"] { gap: 5px; }
    div.stRadio > div[role="radiogroup"] > label { background-color: #1E1E1E !important; border: 1px solid #444 !important; color: #AAA !important; border-radius: 4px !important; padding: 4px 10px !important; font-size: 11px !important; }
    div.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] { background-color: #262730 !important; border: 1px solid #00FFD1 !important; }
    .stButton>button { width: 100%; background-color: #1E1E1E !important; border: 1px solid #444 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 처리
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

df = get_market_data()
last_row = df.iloc[-1]
curr_score = int(last_row['Score'])

# 가이드 텍스트 설정
if curr_score <= 20: g_t, g_d, g_c = "🚨 인생 역전", "공포 구간입니다.<br><span class='point-red'>TQQQ 50% 매수</span>!!!", "#4CAF50"
elif curr_score <= 30: g_t, g_d, g_c = "🛒 강력 매수", "저가 매수 기회!<br><span class='point-red'>TQQQ 30% 매수</span>!!", "#81C784"
elif curr_score <= 40: g_t, g_d, g_c = "🌱 가벼운 매수", "조정 구간입니다.<br><span class='point-red'>TQQQ 10% 매수</span>!", "#A5D6A7"
elif curr_score >= 85: g_t, g_d, g_c = "📉 수익 실현", "과열되었습니다.<br><span class='point-red'>20% 매도</span>해 현금 확보", "#EF5350"
else: g_t, g_d, g_c = "💤 적립 유지", "평범한 중립 구간입니다.<br>QLD 적립을 유지하세요.", "#00FFD1"

# --- [위젯 모드] ---
if st.query_params.get("view") == "widget":
    st.markdown(f"""
    <div style="text-align: center; background-color: #161618; padding: 40px 20px; border-radius: 20px; border: 3px solid #333;">
        <p style="color:#888; font-size:18px;">나스닥 AI 점수</p>
        <h1 style="font-size:110px; color:#00FFD1; margin:0;">{curr_score}</h1>
        <p style="font-size:26px; color:{g_c}; font-weight:bold;">{g_t}</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 4. 일반 화면 UI
st.title("🦁 민석이의 나스닥100 투자")
st.markdown("---")

col_top_L, col_top_R = st.columns([1, 1]) # 폰에서는 어차피 한 줄씩 나옴
with col_top_L:
    st.markdown(f"""
    <div class="combined-score-container">
        <div class="score-part">
            <span style="color:#888; font-size:13px;">현재 AI 점수</span>
            <span style="color:#00FFD1; font-size:75px; font-weight:bold; line-height:1;">{curr_score}</span>
        </div>
        <div class="guide-part">
            <h3 style="margin:0; color:{g_c} !important;">{g_t}</h3>
            <p style="margin-top:8px; color:#BBB; font-size:15px;">{g_d}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_top_R:
    st.subheader("📊 점수 산출 근거")
    cw1, cw2, cw3 = st.columns(3)
    cw1.metric("심리", f"{last_row['RSI']:.1f}"); cw2.metric("자금", f"{last_row['MFI']:.1f}"); cw3.metric("밴드", f"{last_row['PctB']:.1f}%")

# 달력 & 차트
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
def move_calendar(delta):
    st.session_state.cal_month += delta
    if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
    elif st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1

def make_calendar_html(df, year, month):
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)
    h = f'<div style="background-color:#161618;border-radius:15px;padding:15px;border:1px solid #333;width:100%;"><div style="text-align:center;font-weight:bold;margin-bottom:10px;">{year}년 {month}월</div>'
    h += '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;text-align:center;font-size:10px;"><div style="color:#FF5252;">일</div><div>월</div><div>화</div><div>수</div><div>목</div><div>금</div><div style="color:#5C9DFF;">토</div></div>'
    h += '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:5px;">'
    for week in cal:
        for day in week:
            if day == 0: h += '<div></div>'; continue
            d_str = f"{year}-{month:02d}-{day:02d}"
            bg, sc, stxt = "#262730", "#AAA", ""
            try:
                row = df[df.index.strftime('%Y-%m-%d') == d_str]
                if not row.empty:
                    val = int(row['Score'].iloc[0]); stxt = str(val)
                    bg = "#1B3320" if row['Change'].iloc[0] >= 0 else "#331B1B"
                    sc = "#4CAF50" if row['Change'].iloc[0] >= 0 else "#EF5350"
            except: pass
            h += f'<div style="aspect-ratio:1;background-color:{bg};border-radius:5px;display:flex;flex-direction:column;align-items:center;justify-content:center;"><span style="font-size:8px;color:#666;">{day}</span><span style="font-size:12px;font-weight:bold;color:{sc};">{stxt}</span></div>'
    return h + '</div></div>'

col_cal, col_chart = st.columns([1, 1.5])
with col_cal:
    st.subheader("🗓️ 점수 캘린더")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: st.button("◀", key="p", on_click=move_calendar, args=(-1,))
    with c3: st.button("▶", key="n", on_click=move_calendar, args=(1,))
    st.markdown(make_calendar_html(df, st.session_state.cal_year, st.session_state.cal_month), unsafe_allow_html=True)
with col_chart:
    st.subheader("📈 흐름 분석")
    period = st.radio("P", ["1개월", "3개월", "6개월", "1년", "3년"], horizontal=True, label_visibility="collapsed")
    cdf = df.tail({"1개월":22, "3개월":63, "6개월":126, "1년":252, "3년":756}[period])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가", line=dict(color='#FF5252', width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.2)', line=dict(color='rgba(76, 175, 80, 0.5)')), secondary_y=True)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=300, showlegend=False, xaxis=dict(gridcolor='#333', tickformat='%y-%m'), yaxis=dict(gridcolor='#333'), yaxis2=dict(range=[0, 100], showgrid=False), hovermode="x unified", dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 하단 가이드 테이블
st.write("")
st.subheader("📋 실전 운용 가이드")
st.markdown("""
<table class="strategy-table">
    <thead><tr><th>구간</th><th>상태</th><th>Action Plan</th></tr></thead>
    <tbody>
        <tr><td style="color:#4CAF50;">0~20</td><td>🚨공황</td><td>보유 현금의 <span class="point-red">50% TQQQ 매수</span></td></tr>
        <tr><td style="color:#81C784;">21~30</td><td>🛒침체</td><td>보유 현금의 <span class="point-red">30% TQQQ 매수</span></td></tr>
        <tr><td style="color:#A5D6A7;">31~40</td><td>🌱조정</td><td>보유 현금의 <span class="point-red">10% TQQQ 매수</span></td></tr>
        <tr><td style="color:#00FFD1;">41~84</td><td>💤중립</td><td><b>QLD 적립 유지</b></td></tr>
        <tr><td style="color:#EF5350;">85~100</td><td>🔥과열</td><td>보유 수량의 <span class="point-red">20% 매도</span></td></tr>
    </tbody>
</table>
<div style="background-color:#161618; padding:10px; border-radius:10px; border:1px solid #333; margin-top:10px; font-size:11px; color:#AAA;">
    🇺🇸 미국 증시 (한국기준): 월 밤 ~ 토 새벽 (23:30~06:00 / 서머타임 22:30~05:00)
</div>
""", unsafe_allow_html=True)
