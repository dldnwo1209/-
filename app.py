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

# --- 모바일 최적화 및 강제 가독성 테마 ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")

st.markdown("""
    <style>
    /* 메트릭 카드: 어두운 배경 + 파란 테두리 */
    [data-testid="stMetric"] {
        background-color: #0F172A !important;
        border: 2px solid #3B82F6 !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    /* 라벨: 연한 회색 */
    [data-testid="stMetricLabel"] div {
        color: #94A3B8 !important;
        font-weight: 600 !important;
    }
    /* 숫자: 선명한 노란색 */
    [data-testid="stMetricValue"] div {
        color: #FDE047 !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
    }
    /* 변동폭: 초록색 */
    [data-testid="stMetricDelta"] div {
        color: #4ADE80 !important;
        font-weight: bold !important;
    }
    /* 일반 버튼 스타일 */
    .stButton>button {
        background-color: #2563EB !important;
        color: white !important;
        border-radius: 12px;
        height: 3.8em;
        font-size: 1rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# --- 1. 로그인 (이전 동일) ---
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

# --- 2. 총무 모드 (잔액 마이너스 방지 로직 추가) ---
if user_role == "총무":
    st.header("👩‍💼 총무 행정")
    
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    
    # 현재 다른 모든 부서에 배정된 금액 합계 (단, 수정 중인 부서의 기존 금액은 제외해야 함)
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    available_balance = total_budget - assigned_sum
    
    # 상단 대시보드
    st.metric("💰 학급 총 예산", f"{total_budget:,}원", f"배정 가능 잔액: {available_balance:,}원")

    st.write("---")
    with st.expander("➕ 부처별 예산 배정", expanded=True):
        target_dept = st.selectbox("배정할 부처 선택", all_depts)
        
        # 선택한 부처의 현재 배정액
        current_dept_val = st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'].values[0]
        
        # 수정 가능한 최대치 계산 (현재 잔액 + 이 부서가 이미 갖고 있던 돈)
        max_assignable = available_balance + current_dept_val
        
        st.write(f"ℹ️ {target_dept}에 최대 **{int(max_assignable):,}원**까지 배정 가능합니다.")
        
        new_val = st.number_input(f"{target_dept} 배정 금액", value=int(current_dept_val), step=1000, min_value=0)
        
        if st.button("📍 예산 확정 저장"):
            # 실시간 검증: 새로 입력한 값이 최대 허용치를 넘는지 확인
            if new_val > max_assignable:
                st.error(f"🚨 배정 실패! 총 예산을 초과했습니다. (초과액: {int(new_val - max_assignable):,}원)")
            else:
                st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'] = new_val
                save_data(st.session_state.config, st.session_state.requests)
                st.success(f"✅ {target_dept} 예산이 {new_val:,}원으로 변경되었습니다.")
                st.rerun()

    st.divider()
    # 결재 대기 로직 (생략 - 이전과 동일)
    st.subheader("📝 결재 대기")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    if not pending.empty:
        for i, r in pending.iterrows():
            st.info(f"**[{r['부처명']}]** {r['항목']} ({r['금액']:,}원)")
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인", key=f"app_{i}"):
                st.session_state.requests.at[i, '상태'] = '승인'
                st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
                save_data(st.session_state.config, st.session_state.requests); st.rerun()
            if c2.button("❌ 반려", key=f"rej_{i}"):
                st.session_state.requests.at[i, '상태'] = '반려'
                save_data(st.session_state.config, st.session_state.requests); st.rerun()

# --- 3. 나머지 모드 (이전 코드 유지) ---
elif user_role == "교사":
    st.header("👨‍🏫 교사: 예산 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    val = st.number_input("학급 총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 저장"):
        st.session_state.config.at[idx, '금액'] = val
        save_data(st.session_state.config, st.session_state.requests); st.success("저장됨")

elif user_role == "부장":
    st.header("🧑‍💻 부처 업무")
    my_dept = st.selectbox("부처 선택", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    st.metric("📉 가용 예산", f"{int(dept_data['금액'] - dept_data['지출액']):,}원")
    # ... 품의 신청 로직 ...

elif user_role == "감사원":
    st.header("🔍 감찰 시스템")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        st.metric(f"📍 {r['항목']}", f"{int(r['지출액']):,}원 사용")
