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

# --- 모바일 최적화 및 강제 가독성 스타일 ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")

st.markdown("""
    <style>
    /* 메트릭 카드 가독성 강제 고정 */
    [data-testid="stMetric"] {
        background-color: #1E293B !important; 
        border: 2px solid #3B82F6 !important;
        padding: 15px !important;
        border-radius: 15px !important;
    }
    [data-testid="stMetricLabel"] div { color: #CBD5E1 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FACC15 !important; font-size: 1.8rem !important; font-weight: 900 !important; }

    /* 버튼 스타일 */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# --- 1. 로그인 체크 ---
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else:
            st.error("비밀번호 오류")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# --- 2. 역할별 기능 ---

# (1) 부장 모드 (선교부 특정 부서 사면 포함)
if user_role == "부장":
    st.header("🧑‍💻 부처 행정 시스템")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    
    st.metric(f"📊 {my_dept} 현재 예산 잔액", f"{int(dept_data['금액'] - dept_data['지출액']):,}원")

    if my_dept in DEPT_PASSWORDS:
        st.write("---")
        with st.expander(f"🔐 {my_dept} 전용 특수 권한", expanded=True):
            dept_pw = st.text_input(f"{my_dept} 2차 보안", type="password")
            if dept_pw == DEPT_PASSWORDS[my_dept]:
                st.success(f"{my_dept} 인증 성공")
                
                # --- [수정] 선교부: 특정 부서 사면 기능 ---
                if my_dept == "선교부":
                    st.write("✨ **특정 부서 벌금 사면**")
                    target = st.selectbox("사면할 부서 선택", all_depts)
                    if st.button(f"🕊️ {target} 벌금 전액 사면"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = 0
                        save_data(st.session_state.config, st.session_state.requests)
                        st.success(f"🎊 {target}의 모든 벌금이 사면되었습니다!"); st.balloons(); st.rerun()
                
                # --- 인성예절부: 벌금 부과 ---
                elif my_dept == "인성예절부":
                    target = st.selectbox("벌금 부과 대상", all_depts)
                    amt = st.number_input("부과할 벌금액", step=500)
                    if st.button("⚖️ 벌금 확정 부과"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = amt
                        save_data(st.session_state.config, st.session_state.requests); st.warning(f"{target}에 벌금이 부과됨")
                
                # --- 봉사부: 벌금 일부 탕감 ---
                elif my_dept == "봉사부":
                    target = st.selectbox("탕감 대상 부서", all_depts)
                    supp = st.number_input("탕감할 금액", step=500)
                    if st.button("🎁 벌금 일부 탕감"):
                        cur = st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'].values[0]
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = max(0, cur - supp)
                        save_data(st.session_state.config, st.session_state.requests); st.success(f"{target} 탕감 완료")

    st.divider()
    st.subheader("💰 예산 품의 신청")
    with st.form("req_form", clear_on_submit=True):
        item = st.text_input("구입 품목"); amt = st.number_input("신청 금액", step=100)
        if st.form_submit_button("🚀 결재 신청하기"):
            new = {'날짜': datetime.now().strftime("%m-%d"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기'}
            st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
            save_data(st.session_state.config, st.session_state.requests); st.success("총무에게 제출되었습니다.")

# (교사, 총무, 감사원 로직은 이전과 동일)
elif user_role == "교사":
    st.header("👨‍🏫 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_val = st.number_input("학급 총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 총액 저장"):
        st.session_state.config.at[idx, '금액'] = total_val
        save_data(st.session_state.config, st.session_state.requests); st.success("반영 완료")

elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    st.metric("💰 학급 총 예산", f"{total_budget:,}원", f"배정 가능 잔액: {total_budget - assigned_sum:,}원")
    
    with st.expander("➕ 부처별 예산 배정", expanded=True):
        target_dept = st.selectbox("배정 부처", all_depts)
        curr = st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'].values[0]
        new_v = st.number_input("금액", value=int(curr), step=1000)
        if st.button("📍 배정 확정"):
            st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'] = new_v
            save_data(st.session_state.config, st.session_state.requests); st.rerun()

    st.subheader("📝 결재 대기 건")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
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

elif user_role == "감사원":
    st.header("🔍 감찰 리포트")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        st.metric(f"📍 {r['항목']}", f"{int(r['지출액']):,}원", f"현재 벌금: {int(r['벌금']):,}원", delta_color="inverse")
