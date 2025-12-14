import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="민석이의 나스닥100 투자", page_icon="🦁", layout="wide")

# 2. 고강도 PC 가독성 스타일 (이름을 다 바꿔서 브라우저 캐시를 무력화합니다)
st.markdown("""
<style>
    /* 전체 배경 */
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, span, div, label { color: #E0E0E0 !important; }

    /* [1] 제목: 🦁 민석이의 '민'자와 아래 '나'자 수직 라인 정밀 정렬 */
    .title-box { margin-bottom: 30px; text-align: left; }
    .title-row1 { display: flex; align-items: center; gap: 10px; font-size: 30px; font-weight: 800; }
    .title-row2 { padding-left: 42px; font-size: 30px; font-weight: 800; margin-top: -5px; display: block; }

    /* [2] 점수 산출 근거: 3열 박스 */
    .basis-grid {
        display: grid; grid-template-columns: repeat(3, 1fr);
        background-color: #161618; border: 1px solid #333; border-radius: 15px; margin-bottom: 25px;
    }
    .basis-cell { padding: 15px 0; text-align: center; border-right: 1px solid #222; }
    .basis-cell:last-child { border-right: none; }
    .basis-tag { font-size: 14px; color: #888; margin-bottom: 8px; }
    .basis-val { font-size: 22px; font-weight: bold; color: #00FFD1; }

    /* [3] ★ PC 달력 가독성 끝판왕 ★ */
    .cal-main-container { max-width: 480px; margin: 0 auto; }
    .day-box { 
        aspect-ratio: 1.1; background-color: #262730; border-radius: 10px; 
        position: relative; display: flex; align-items: center; justify-content: center;
        border: 1px solid #333;
    }
    .day-number { font-size: 13px; color: #666; position: absolute; top: 8px; left: 10px; }
    .score-number { font-size: 22px !important; font-weight: 900 !important; } /* 점수 크기 대폭 상향 */

    /* [4] 버튼 스타일 */
    div.stRadio > div[role="radiogroup"] {
        display: flex !important; flex-direction: row !important;
        flex-wrap: nowrap !important; gap: 8px !important;
    }
    div.stRadio > div[role="radiogroup"] > label {
        flex: 1 !important; white-space: nowrap !important;
        background-color: #1E1E1E !important; border: 1px solid #444 !important;
        padding: 10px 15px !important; font-size: 15px !important; text-align: center;
    }
    .stButton > button {
        background-color: #1E1E1E !important; color: #00FFD1 !important;
        border: 1px solid #00FFD1 !important; border-radius: 10px !important;
        font-weight: bold !important; height: 45px !important; font-size: 18px !important;
    }

    .point-red { color: #EF5350 !important; font-weight: bold !important; }
    .combined-score-box { display: flex; background-color: #161618; border: 2px solid #333; border-radius: 20px; overflow: hidden; margin-bottom: 25px; }
    .part-score { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #1E1E1E; padding: 30px; }
    .part-guide { flex: 2; padding: 30px; display: flex; flex-direction: column; justify-content: center; }

    @media (max-width: 768px) {
        .combined-score-box { flex-direction: column !important; }
        .part-score { border-right: none !important; border-bottom: 1px solid #333 !important; }
        .cal-main-container { max-width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 처리 로직
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

df = get_market_data(); last_row = df.iloc[-1]; curr_score = int(last_row['Score'])

# 4. 가이드 문구
if curr_score <= 20: g_t, g_d, g_c = "🚨 인생 역전 기회", "시장이 공포에 질렸습니다.<br><span class='point-red'>TQQQ 50% 매수</span>!!!", "#4CAF50"
elif curr_score <= 30: g_t, g_d, g_c = "🛒 강력 매수", "확실한 저가 매수 찬스입니다.<br><span class='point-red'>TQQQ 30% 매수</span>!!", "#81C784"
elif curr_score <= 40: g_t, g_d, g_c = "🌱 가벼운 매수", "건강한 조정 구간입니다.<br><span class='point-red'>TQQQ 10% 매수</span>!", "#A5D6A7"
elif curr_score >= 85: g_t, g_d, g_c = "📉 수익 실현 권장", "상승의 끝자락일 수 있습니다.<br><span class='point-red'>20% 매도</span>해 현금을 확보하세요.", "#EF5350"
else: g_t, g_d, g_c = "💤 적립 유지", "평범한 우상향 구간입니다.<br>매일 QLD 만원 적립을 유지하세요.", "#00FFD1"

# 5. 화면 출력
# [제목] 수직 라인 정렬 (PC에서 큼직하게)
st.markdown(f'<div class="title-box"><div class="title-row1">🦁 민석이의</div><div class="title-row2">나스닥100 투자</div></div>', unsafe_allow_html=True)

# [상단 박스]
st.markdown(f"""<div class="combined-score-box"><div class="part-score"><span style="color:#888; font-size:16px;">현재 AI 점수</span><span style="color:#00FFD1; font-size:90px; font-weight:bold; line-height:1;">{curr_score}</span></div><div class="part-guide"><h2 style="margin:0; color:{g_c} !important; font-size:32px;">{g_t}</h2><p style="margin-top:15px; color:#BBB; font-size:20px; line-height:1.6;">{g_d}</p></div></div>""", unsafe_allow_html=True)

# [근거 그리드]
st.markdown(f"""<div class="basis-grid"><div class="basis-cell"><div class="basis-tag">심리(RSI)</div><div class="basis-val">{last_row['RSI']:.1f}</div></div><div class="basis-cell"><div class="basis-tag">자금(MFI)</div><div class="basis-val">{last_row['MFI']:.1f}</div></div><div class="basis-cell"><div class="basis-tag">밴드위치</div><div class="basis-val">{last_row['PctB']:.1f}%</div></div></div>""", unsafe_allow_html=True)

# 6. 달력 & 차트 섹션 (PC 가로 배치)
col_left, col_right = st.columns([1, 1.4], gap="large")

with col_left:
    st.subheader("🗓️ 점수 캘린더")
    if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
    if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
    def move_c(d):
        st.session_state.cal_month += d
        if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        elif st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1

    c1, c2, c3 = st.columns([1, 3, 1])
    with c1: st.button("◀", key="prev_pc", on_click=move_c, args=(-1,))
    with c2: st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:22px; line-height:45px;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</div>", unsafe_allow_html=True)
    with c3: st.button("▶", key="next_pc", on_click=move_c, args=(1,))

    st.markdown('<div class="cal-main-container">', unsafe_allow_html=True)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    h = f'<div style="background-color:#161618; border-radius:20px; padding:20px; border:1px solid #333;"><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:10px; text-align:center; font-size:14px; font-weight:bold; margin-bottom:15px;"><div style="color:#FF5252;">일</div><div>월</div><div>화</div><div>수</div><div>목</div><div>금</div><div style="color:#5C9DFF;">토</div></div><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:8px;">'
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
            # 날짜와 점수 크기 강화된 셀
            h += f'<div class="day-box" style="background-color:{bg};"><span class="day-number">{day}</span><span class="score-number" style="color:{sc};">{stxt}</span></div>'
    st.markdown(h + '</div></div></div>', unsafe_allow_html=True)

with col_right:
    st.subheader("📈 흐름 분석")
    period = st.radio("P", ["1개월", "3개월", "6개월", "1년", "3년", "5년"], horizontal=True, label_visibility="collapsed")
    cdf = df.tail({"1개월":22, "3개월":63, "6개월":126, "1년":252, "3년":756, "5년":1260}[period])
    b_d, s_d = len(cdf[cdf['Score'] <= 40]), len(cdf[cdf['Score'] >= 85])
    st.markdown(f'<div style="font-size:16px; color:#AAA; text-align:right; margin-bottom:10px;">💰 40↓: <b style="color:#4CAF50;">{b_d}회</b> | 🔥 85↑: <b style="color:#EF5350;">{s_d}회</b></div>', unsafe_allow_html=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Close'], name="주가", line=dict(color='#FF5252', width=3)), secondary_y=False)
    fig.add_trace(go.Scatter(x=cdf.index, y=cdf['Score'], name="점수", fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.1)', line=dict(color='rgba(76, 175, 80, 0.4)')), secondary_y=True)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=10,b=0), height=450, showlegend=False, xaxis=dict(gridcolor='#333', tickformat='%y-%m'), yaxis=dict(gridcolor='#333'), yaxis2=dict(range=[0, 100], showgrid=False), hovermode="x unified", dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 하단 가이드
st.divider()
st.subheader("📋 실전 운용 전략 가이드")
st.markdown("""<table class="strategy-table" style="width:100%; border-collapse:collapse; background:#161618; border-radius:15px; overflow:hidden;"><thead><tr style="background:#262730; color:#888;"><th>구간</th><th>상태</th><th>대응 전략</th></tr></thead><tbody style="text-align:center; font-size:16px;"><tr><td style="color:#4CAF50; padding:15px;">0~20</td><td>🚨공황</td><td>인생역전: <span class="point-red">TQQQ 50% 매수</span></td></tr><tr><td style="color:#81C784; padding:15px;">21~30</td><td>🛒침체</td><td>저가매수: <span class="point-red">TQQQ 30% 매수</span></td></tr><tr><td style="color:#A5D6A7; padding:15px;">31~40</td><td>🌱조정</td><td>가벼운매수: <span class="point-red">TQQQ 10% 매수</span></td></tr><tr><td style="color:#00FFD1; padding:15px;">41~84</td><td>💤중립</td><td><b>QLD 적립 유지</b></td></tr><tr><td style="color:#EF5350; padding:15px;">85~100</td><td>🔥과열</td><td>수익실현: <span class="point-red">20% 매도</span></td></tr></tbody></table>""", unsafe_allow_html=True)
