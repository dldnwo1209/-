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

# --- 모바일 가독성 및 강제 색상 고정 (다크모드 완벽 대응) ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")

st.markdown("""
    <style>
    /* 상단 메트릭 카드 색상 강제 고정 */
    [data-testid="stMetric"] {
        background-color: #1E293B !important; 
        border: 2px solid #3B82F6 !important;
        padding: 15px !important;
        border-radius: 15px !important;
    }
    [data-testid="stMetricLabel"] div { color: #CBD5E1 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FACC15 !important; font-size: 1.8rem !important; font-weight: 900 !important; }

    /* 버튼 공통 스타일 */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.8em;
        font-weight: bold !important; font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# --- 1. 로그인 로직 ---
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else:
            st.error("비밀번호 불일치")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# --- 2. 부장 모드 (선교부 할렐루야 버튼 포함) ---
if user_role == "부장":
    st.header("🧑‍💻 부처 행정 시스템")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    
    st.metric(f"📊 {my_dept} 현재 잔액", f"{int(dept_data['금액'] - dept_data['지출액']):,}원")

    if my_dept in DEPT_PASSWORDS:
        st.write("---")
        with st.expander(f"🔐 {my_dept} 특수 권한 인증", expanded=True):
            dept_pw = st.text_input(f"{my_dept} 2차 보안", type="password", key=f"pw_{my_dept}")
            if dept_pw == DEPT_PASSWORDS[my_dept]:
                st.success(f"{my_dept} 권한 활성화")
                
                # --- 선교부 전용: 할렐루야!! 사면 로직 ---
                if my_dept == "선교부":
                    st.markdown("### ✨ 자비의 벌금 사면")
                    amnesty_target = st.selectbox("사면할 부서 선택", all_depts)
                    current_fine = st.session_state.config.loc[st.session_state.config['항목'] == amnesty_target, '벌금'].values[0]
                    st.write(f"현재 {amnesty_target} 벌금: **{int(current_fine):,}원**")
                    
                    if st.button(f"🙌 {amnesty_target} 사면: 할렐루야!!"):
                        if current_fine > 0:
                            st.session_state.config.loc[st.session_state.config['항목'] == amnesty_target, '벌금'] = 0
                            save_data(st.session_state.config, st.session_state.requests)
                            st.success(f"🎊 은혜로다! {amnesty_target}의 벌금이 사면되었습니다.")
                            st.balloons() # 축하 풍선 효과
                            st.rerun()
                        else:
                            st.warning("이미 벌금이 없는 깨끗한 상태입니다.")
                
                # --- 인성예절부 / 봉사부 로직 생략 (기존과 동일) ---
                elif my_dept == "인성예절부":
                    target = st.selectbox("벌금 부과 대상", all_depts)
                    amt = st.number_input("금액", step=500)
                    if st.button("⚖️ 벌금 부과 확정"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = amt
                        save_data(st.session_state.config, st.session_state.requests); st.rerun()

    st.divider()
    st.subheader("💰 예산 신청")
    with st.form("req_form", clear_on_submit=True):
        item = st.text_input("항목"); amt = st.number_input("금액", step=100)
        if st.form_submit_button("🚀 결재 신청"):
            new = {'날짜': datetime.now().strftime("%m-%d"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기'}
            st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
            save_data(st.session_state.config, st.session_state.requests); st.success("제출 완료")

# (기존 교사, 총무, 감사원 로직 유지)
elif user_role == "교사":
    st.header("👨‍🏫 예산 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    val = st.number_input("총액", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 저장"):
        st.session_state.config.at[idx, '금액'] = val
        save_data(st.session_state.config, st.session_state.requests); st.success("완료")

elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    # ... (생략: 기존 가독성 개선된 총무 로직)

elif user_role == "감사원":
    st.header("🔍 감찰 시스템")
    # ... (생략: 기존 가독성 개선된 감사원 로직)
