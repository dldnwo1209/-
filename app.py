import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일
DB_CONFIG = 'config_v4.csv'
LOG_FILE = 'transactions_v4.csv'

# 권한 비밀번호
PASSWORDS = {"교사": "1209", "총무": "1357", "부장": "2468", "감사원": "1111"}

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

# --- 모바일 최적화 및 강제 가독성 부여 ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")

st.markdown("""
    <style>
    /* 1. 상단 카드 (메트릭) 강제 색상 지정 */
    [data-testid="stMetric"] {
        background-color: #1E293B !important; /* 아주 어두운 남색 */
        border: 2px solid #3B82F6 !important; /* 파란색 테두리 */
        padding: 15px !important;
        border-radius: 15px !important;
    }
    
    /* 2. 카드 내부 라벨 (학급 총 예산 등) */
    [data-testid="stMetricLabel"] div {
        color: #CBD5E1 !important; /* 밝은 회색 */
        font-weight: bold !important;
        font-size: 1rem !important;
    }
    
    /* 3. 카드 내부 숫자 (28,000원 등) - 가장 중요 */
    [data-testid="stMetricValue"] div {
        color: #FACC15 !important; /* 선명한 노란색 */
        font-size: 1.8rem !important;
        font-weight: 900 !important;
    }
    
    /* 4. 변동폭 (잔액 등) */
    [data-testid="stMetricDelta"] div {
        color: #4ADE80 !important; /* 밝은 연두색 */
        font-weight: bold !important;
    }

    /* 5. 버튼 가독성 */
    .stButton>button {
        background-color: #3B82F6 !important;
        color: white !important;
        border-radius: 10px;
        height: 3.5em;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# --- 1. 로그인 (이전과 동일) ---
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("1차 비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else:
            st.error("비밀번호 불일치")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# --- 2. 총무 모드 예시 (나머지 역할도 자동 적용됨) ---
if user_role == "총무":
    st.header("👩‍💼 총무 행정")
    
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    
    # 이제 이 부분이 어두운 배경에 노란 글씨로 보일 겁니다.
    st.metric("💰 학급 총 예산", f"{total_budget:,}원", f"남은 잔액: {total_budget - assigned_sum:,}원")

    st.write("---")
    with st.expander("➕ 부처별 예산 배정", expanded=True):
        target_dept = st.selectbox("부처 선택", all_depts)
        current_val = st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'].values[0]
        new_val = st.number_input("배정 금액", value=int(current_val), step=1000)
        if st.button("📍 예산 저장"):
            st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'] = new_val
            save_data(st.session_state.config, st.session_state.requests)
            st.success(f"{target_dept} 저장 완료"); st.rerun()

# --- 교사, 부장, 감사원 코드는 이전과 동일하되 위 스타일이 자동 적용됩니다 ---
# (생략된 부분은 기존 로직을 그대로 쓰시면 됩니다)
elif user_role == "교사":
    st.header("👨‍🏫 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_val = st.number_input("총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 저장"):
        st.session_state.config.at[idx, '금액'] = total_val
        save_data(st.session_state.config, st.session_state.requests); st.success("반영됨")

elif user_role == "부장":
    st.header("🧑‍💻 부처 업무")
    my_dept = st.selectbox("부처 선택", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    st.metric("📉 부서 잔액", f"{int(dept_data['금액'] - dept_data['지출액']):,}원")
    # ... 신청 폼 로직 ...

elif user_role == "감사원":
    st.header("🔍 감찰 시스템")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        st.metric(f"📍 {r['항목']}", f"{int(r['지출액']):,}원 사용")
