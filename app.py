import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일
DB_CONFIG = 'config_v4.csv'
LOG_FILE = 'transactions_v4.csv'

# 권한 및 부처 비밀번호
PASSWORDS = {"교사": "1209", "총무": "1357", "부장": "2468", "감사원": "1111"}
DEPT_PASSWORDS = {"인성예절부": "24278", "봉사부": "848", "선교부": "398"}

def load_data():
    depts = ['여당(회장)', '야당(회장)', '감찰부(서기)', '총무부', '인성예절부', 
             '환경부', '체육부', '교육부', '발명부', '선교부', '봉사부']
    if os.path.exists(DB_CONFIG):
        config_df = pd.read_csv(DB_CONFIG)
    else:
        config_df = pd.DataFrame({
            '항목': ['학급총액'] + depts,
            '금액': [0] * (len(depts) + 1),
            '지출액': [0] * (len(depts) + 1),
            '벌금': [0] * (len(depts) + 1)
        })
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '비고'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# --- 모바일 최적화 설정 ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; margin-bottom: 5px; }
    div[data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# --- 1. 로그인 체크 ---
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("1차 비밀번호", type="password")
    
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# --- 2. 역할별 기능 ---

# (1) 교사 모드
if user_role == "교사":
    st.header("👨‍🏫 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_val = st.number_input("학급 총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💰 총액 저장"):
        st.session_state.config.at[idx, '금액'] = total_val
        save_data(st.session_state.config, st.session_state.requests)
        st.success("총액이 반영되었습니다.")

# (2) 총무 모드
elif user_role == "총무":
    st.header("👩‍💼 총무 행정 시스템")
    
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    
    st.metric("학급 총 예산", f"{total_budget:,}원", f"잔액: {total_budget - assigned_sum:,}원")

    with st.expander("➕ 부처별 예산 배정", expanded=True):
        target_dept = st.selectbox("부처 선택", all_depts)
        current_val = st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'].values[0]
        new_val = st.number_input("배정 금액", value=int(current_val), step=1000)
        if st.button("📍 예산 저장"):
            st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'] = new_val
            save_data(st.session_state.config, st.session_state.requests)
            st.success("배정 완료"); st.rerun()

    st.subheader("📝 결재 대기")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        st.info(f"**[{r['부처명']}]** {r['항목']}\n{r['금액']:,}원")
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인", key=f"app_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(st.session_state.config, st.session_state.requests); st.rerun()
        if c2.button("❌ 반려", key=f"rej_{i}"):
            st.session_state.requests.at[i, '상태'] = '반려'
            save_data(st.session_state.config, st.session_state.requests); st.rerun()

# (3) 부장 모드
elif user_role == "부장":
    st.header("🧑‍💻 부처 행정")
    my_dept = st.selectbox("부처 선택", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    
    st.markdown(f"### 📊 {my_dept} 현황")
    c1, c2, c3 = st.columns(3)
    c1.metric("배정", f"{int(dept_data['금액']//1000)}k")
    c2.metric("사용", f"{int(dept_data['지출액']//1000)}k")
    c3.metric("벌금", f"{int(dept_data['벌금']//1000)}k")

    if my_dept in DEPT_PASSWORDS:
        with st.expander("🔐 2차 보안 기능"):
            dept_pw = st.text_input("2차 비번", type="password")
            if dept_pw == DEPT_PASSWORDS[my_dept]:
                st.success("인증 성공")
                # 벌금/사면 로직 등 추가 가능
    
    st.subheader("💰 예산 신청")
    with st.form("req_form"):
        item = st.text_input("품목"); amt = st.number_input("금액", step=100)
        if st.form_submit_button("신청하기"):
            new = {'날짜': datetime.now().strftime("%m-%d"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기'}
            st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
            save_data(st.session_state.config, st.session_state.requests); st.success("제출됨")

# (4) 감사원 모드
elif user_role == "감사원":
    st.header("🔍 감찰 리포트")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        with st.expander(f"📍 {r['항목']} ({int(r['지출액']):,}원)"):
            st.write(f"배정: {int(r['금액']):,}원 / 벌금: {int(r['벌금']):,}원")
    
    st.subheader("📜 전체 로그")
    for i, row in st.session_state.requests.iloc[::-1].iterrows():
        st.markdown(f"**{row['부처명']}** | {row['항목']} ({row['상태']})")
        st.caption(f"{row['날짜']} | {row['금액']:,}원")
        st.write("---")

# 로그아웃 버튼 (사이드바)
if st.sidebar.button("🔓 로그아웃"):
    del st.session_state.auth_role
    st.rerun()
