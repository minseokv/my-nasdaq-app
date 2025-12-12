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
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }
    
    /* 상단 통합 박스 (1:2 분할 + 반응형) */
    .combined-score-container {
        display: flex;
        flex-direction: row;
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
        text-align: left;
    }

    /* 갤럭시 S24 등 모바일 환경 최적화 */
    @media (max-width: 768px) {
        .combined-score-container { flex-direction: column; }
        .score-part { border-right: none; border-bottom: 1px solid #333; padding: 20px; }
        .score-part span:last-child { font-size: 65px !important; }
        .guide-part { padding: 20px; }
        .guide-part h3 { font-size: 1.3rem !important; }
        .strategy-table td, .strategy-table th { padding: 10px 5px !important; font-size: 12px !important; }
    }

    /* 버튼 스타일 */
    div.stRadio > div[role="radiogroup"] { gap: 5px; }
    div.stRadio > div[role="radiogroup"] > label {
        background-color: #1E1E1E !important; border: 1px solid #444 !important;
        color: #AAA !important; border-radius: 4px !important; padding: 4px 12px !important; font-size: 12px !important;
    }
    div.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] {
        background-color: #262730 !important; border: 1px solid #00FFD1 !important; color: #00FFD1 !important;
    }

    .point-red { color: #EF5350 !important; font-weight: bold !important; }

    /* 전략 가이드 테이블 */
    .strategy-table {
        width: 100%; border-collapse: collapse; background-color: #161618;
        border-radius: 10px; overflow: hidden; border: 1px solid #333;
    }
    .strategy-table th { background-color: #262730; color: #888; padding: 12px; text-align: center; border-bottom: 1px solid #333; }
    .strategy-table td { padding: 15px; border-bottom: 1px solid #333; text-align: center; color: #E0E0E0; }

    /* 달력 버튼 */
    .stButton>button { width: 100%; background-color: #1E1E1E !important; border: 1px solid #444 !important; color: white !important; }
    .stButton>button:hover { border-color: #00FFD1 !important; color: #00FFD1 !important; }
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
# 3. 위젯 모드 (?view=widget)
# ---------------------------------------------------------
if curr_score <= 20: g_t, g_d, g_c = "🚨 인생 역전 기회", "시장이 공포에 질렸습니다.<br><span class='point-red'>TQQQ 50% 매수</span>!!!", "#4CAF50"
elif curr_score <= 30: g_t, g_d, g_c = "🛒 강력 매수", "확실한 저가 매수 찬스입니다.<br><span class='point-red'>TQQQ 30% 매수</span>!!", "#81C784"
elif curr_score <= 40: g_t, g_d, g_c = "🌱 가벼운 매수", "건강한 조정 구간입니다.<br><span class='point-red'>TQQQ 10% 매수</span>!", "#A5D6A7"
elif curr_score >= 85: g_t, g_d, g_c = "📉 수익 실현 권장", "상승의 끝자락일 수 있습니다.<br><span class='point-red'>20% 매도</span>해 현금을 확보하세요.", "#EF5350"
else: g_t, g_d, g_c = "💤 적립 유지", "평범한 우상향 구간입니다.<br>매일 QLD 만원 적립을 유지하세요.", "#00FFD1"

if st.query_params.get("view") == "widget":
    st.markdown(f"""
    <div style="text-align: center; background-color: #161618; padding: 40px 20px; border-radius: 20px; border: 3px solid #333;">
        <p style="color:#888; font-size:18px; margin-bottom:5px;">나스닥 AI 점수</p>
        <h1 style="font-size:110px; color:#00FFD1; margin:0; line-height:1;">{curr_score}</h1>
        <p style="font-size:26px; color:{g_c}; font-weight:bold; margin-top:20px;">{g_t}</p>
        <p style="font-size:14px; color:#555; margin-top:10px;">{datetime.now().strftime('%H:%M')} Update</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------
# 4. 전체 사이트 UI 구성
# ---------------------------------------------------------
rsi, mfi, pb = last_row['RSI'], last_row['MFI'], last_row['PctB']

st.title("🦁 민석이의 나스닥100 투자")
st.markdown("---")

# 상단 레이아웃 (1:2 분할 유지)
c_top_L, c_top_R = st.columns([1.2, 1.3])
with c_top_L:
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
with c_top_R:
    st.subheader("📊 점수 산출 근거 (Why?)")
    cw1, cw2, cw3 = st.columns(3)
    cw1.metric("심리(RSI) 30%", f"{rsi:.1f}")
    cw2.metric("자금(MFI) 30%", f"{mfi:.1f}")
    cw3.metric("밴드위치 40%", f"{pb:.1f}%")
    st.info("RSI, MFI, 밴드위치를 종합 분석한 통계값입니다.")

st.write("")

# 달력 로직
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
def move_calendar(delta):
    st.session_state.cal_month += delta
    if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
    elif st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1

def make_calendar_html(df, year, month):
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)
    today_str = datetime.now().strftime('%Y-%m-%d')
    h = f'<div style="background-color:#161618;border-radius:15px;padding:20px;border:1px solid #333;max-width:450px;margin:0 auto;"><div style="text-align:center;font-size:20px;font-weight:bold;margin-bottom:15px;color:#FFF;">{year}년 {month}월</div>'
    h += '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:10px;text-align:center;font-size:12px;font-weight:bold;"><div style="color:#FF5252;">일</div><div style="color:#888;">월</div><div style="color:#888;">화</div><div style="color:#888;">수</div><div style="color:#888;">목</div><div style="color:#888;">금</div><div style="color:#5C9DFF;">토</div></div>'
    h += '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;">'
    for week in cal:
        for day in week:
            if day == 0: h += '<div></div>'; continue
            d_str = f"{year}-{month:02d}-{day:02d}"
            bg, brd, sc, stxt = "#262730", "1px solid #333", "#AAA", ""
            try:
                row = df[df.index.strftime('%Y-%m-%d') == d_str]
                if not row.empty:
                    val = int(row['Score'].iloc[0]); chg = row['Change'].iloc[0]; stxt = str(val)
                    if chg >= 0: bg, brd, sc = "#1B3320", "1px solid #2E7D32", "#4CAF50"
                    else: bg, brd, sc = "#331B1B", "1px solid #C62828", "#EF5350"
                    if d_str == today_str: brd = "2px solid #FFFFFF"
            except: pass
            h += f'<div style="aspect-ratio:1;background-color:{bg};border:{brd};border-radius:8px;position:relative;display:flex;align-items:center;justify-content:center;"><div style="position:absolute;top:4px;left:6px;font-size:11px;color:#888;">{day}</div><div style="font-size:18px;font-weight:bold;color:{sc};margin-top:10px;">{stxt}</div></div>'
    h += '</div><div style="margin-top:15px;text-align:right;font-size:12px;color:#888;"><span style="height:10px;width:10px;background-color:#4CAF50;border-radius:50%;display:inline-block;margin-right:5px;"></span>상승 <span style="height:10px;width:10px;background-color:#EF5350;border-radius:50%;display:inline-block;margin-right:5px;margin-left:10px;"></span>하락</div></div>'
    return h

# 달력 & 차트 섹션
col_cal, col_chart = st.columns([1, 1.5], gap="large")
with col_cal:
    st.subheader("🗓️ 점수 캘린더")
    nc1, nc2, nc3 = st.columns([1, 3, 1])
    with nc1: 
        if st.button("◀", key="prev"): move_calendar(-1)
    with nc3: 
        if st.button("▶", key="next"): move_calendar(1)
    st.markdown(make_calendar_html(df, st.session_state.cal_year, st.session_state.cal_month), unsafe_allow_html=True)
with col_chart:
    st.subheader("📈 흐름 분석")
    cr1, cr2 = st.columns([4, 2])
    with cr1: period = st.radio("P", ["1개월", "3개월", "6개월", "1년", "3년"], horizontal=True, label_visibility="collapsed")
    cdf = df.tail({"1개월":22, "3개월":63, "6개월":126, "1년":252, "3년":756}[period])
    b_d, s_d = len(cdf[cdf['Score'] <= 40]), len(cdf[cdf['Score'] >= 85])
    with cr2: st.markdown(f'<div style="padding-top:7px; font-size:15px; color:#AAA; text-align:right; white-space:nowrap;">💰 40↓: <b style="color:#4CAF50;">{b_d}회</b> | 🔥 85↑: <b style="color:#EF5350;">{s_d}회</b></div>', unsafe_allow_html=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가", line=dict(color='#FF5252', width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.2)', line=dict(color='rgba(76, 175, 80, 0.5)')), secondary_y=True)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), height=400, showlegend=False, xaxis=dict(gridcolor='#333', color='#888', tickformat='%y-%m'), yaxis=dict(gridcolor='#333', color='#AAA', title="주가($)"), yaxis2=dict(showgrid=False, color='#AAA', title="점수", range=[0, 100]), hovermode="x unified", dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 하단 가이드
st.divider()
st.subheader("📊 지표 상세 가이드")
e1, e2, e3 = st.columns(3)
c_css = 'background:#161618; padding:20px; border-radius:12px; border-left:4px solid #00FFD1; min-height:140px;'
with e1: st.markdown(f'<div style="{c_css}"><h4>🧠 심리 (RSI)</h4><p style="font-size:15px; color:#AAA; margin-top:8px;">시장의 과열 정도를 측정합니다. <br>주가가 너무 빠르게 오르면 점수가 높아져 주의를 요합니다.</p></div>', unsafe_allow_html=True)
with e2: st.markdown(f'<div style="{c_css}"><h4>💰 자금 (MFI)</h4><p style="font-size:15px; color:#AAA; margin-top:8px;">거래량을 포함한 자금 유입 지표입니다. <br>상승 시 거래량이 동반되는지 확인하여 신뢰도를 평가합니다.</p></div>', unsafe_allow_html=True)
with e3: st.markdown(f'<div style="{c_css}"><h4>📏 밴드위치 (%B)</h4><p style="font-size:15px; color:#AAA; margin-top:8px;">최근 평균 가격 대비 현재 주가의 통계적 위치입니다. <br>0%에 가까울수록 저점, 100%에 가까울수록 고점입니다.</p></div>', unsafe_allow_html=True)

st.write("")
st.subheader("📋 점수대별 실전 운용 전략 가이드")
st.markdown("""
<table class="strategy-table">
    <thead><tr><th style="width:20%;">점수 구간</th><th style="width:20%;">시장 상태</th><th style="width:60%;">대응 전략 (Action Plan)</th></tr></thead>
    <tbody>
        <tr><td style="color:#4CAF50; font-weight:bold;">0 ~ 20점</td><td>🚨 공황 (Panic)</td><td><b>인생 역전 기회:</b> <span class="point-red">TQQQ 50% 매수</span></td></tr>
        <tr><td style="color:#81C784; font-weight:bold;">21 ~ 30점</td><td>🛒 침체 (Fear)</td><td><b>확실한 저가 매수:</b> <span class="point-red">TQQQ 30% 매수</span></td></tr>
        <tr><td style="color:#A5D6A7; font-weight:bold;">31 ~ 40점</td><td>🌱 조정 (Healthy Dip)</td><td><b>건강한 조정:</b> <span class="point-red">TQQQ 10% 매수</span></td></tr>
        <tr><td style="color:#00FFD1; font-weight:bold;">41 ~ 84점</td><td>💤 중립 (Neutral)</td><td><b>QLD 적립 유지</b></td></tr>
        <tr><td style="color:#EF5350; font-weight:bold;">85 ~ 100점</td><td>🔥 과열 (Greed)</td><td><b>수익 실현:</b> <span class="point-red">20% 매도</span></td></tr>
    </tbody>
</table>
""", unsafe_allow_html=True)
st.caption("※ 위 전략은 과거 5년 백테스팅 결과를 기반으로 한 가이드이며, 최종 투자 판단은 본인에게 있습니다.")

st.markdown("""
<div style="background-color: #161618; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-top: 10px;">
    <p style="margin: 0; font-size: 14px; color: #E0E0E0; font-weight: bold;">🇺🇸 미국 증시 영업시간 (월요일 밤 ~ 토요일 새벽)</p>
    <div style="display: flex; gap: 20px; margin-top: 8px;">
        <div style="flex: 1; font-size: 13px; color: #AAA;"><span style="color: #00FFD1;">●</span> <b>서머타임 (3월~11월)</b><br>- 정규장: 22:30 ~ 05:00<br>- 프리마켓: 17:00 ~ 22:30</div>
        <div style="flex: 1; font-size: 13px; color: #AAA;"><span style="color: #EF5350;">●</span> <b>평시 (11월~3월)</b><br>- 정규장: 23:30 ~ 06:00<br>- 프리마켓: 18:00 ~ 23:30</div>
    </div>
</div>
""", unsafe_allow_html=True)
