import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 데이터 설정 및 로드
DB_CONFIG = 'config_v4.csv'
LOG_FILE = 'transactions_v4.csv'
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
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# 2. 모바일 가독성 스타일 (색상 고정)
st.set_page_config(page_title="학급 보안 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1E293B !important; 
        border: 2px solid #3B82F6 !important;
        padding: 15px !important;
        border-radius: 15px !important;
    }
    [data-testid="stMetricLabel"] div { color: #CBD5E1 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FACC15 !important; font-size: 1.8rem !important; font-weight: 900 !important; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# 3. 로그인 시스템
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# 4. 역할별 기능 구현
if user_role == "교사":
    st.header("👨‍🏫 예산 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    val = st.number_input("학급 총 운영비", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 설정 저장"):
        st.session_state.config.at[idx, '금액'] = val
        save_data(st.session_state.config, st.session_state.requests)
        st.success("반영되었습니다.")

elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    st.metric("학급 총 예산", f"{total_budget:,}원", f"배정 가능 잔액: {total_budget - assigned_sum:,}원")
    
    with st.expander("➕ 부처별 예산 배정", expanded=True):
        target = st.selectbox("부처 선택", all_depts)
        curr_v = st.session_state.config.loc[st.session_state.config['항목'] == target, '금액'].values[0]
        new_v = st.number_input("금액", value=int(curr_v), step=1000)
        if st.button("📍 배정 저장"):
            st.session_state.config.loc[st.session_state.config['항목'] == target, '금액'] = new_v
            save_data(st.session_state.config, st.session_state.requests); st.rerun()

    st.subheader("📝 결재 대기")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        st.info(f"**[{r['부처명']}]** {r['항목']} ({r['금액']:,}원)")
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인", key=f"a_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(st.session_state.config, st.session_state.requests); st.rerun()
        if c2.button("❌ 반려", key=f"r_{i}"):
            st.session_state.requests.at[i, '상태'] = '반려'
            save_data(st.session_state.config, st.session_state.requests); st.rerun()

elif user_role == "부장":
    st.header("🧑‍💻 부처 업무 시스템")
    my_dept = st.selectbox("내 부처", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    st.metric(f"📊 {my_dept} 잔액", f"{int(dept_data['금액'] - dept_data['지출액'] - dept_data['벌금']):,}원")

    if my_dept in DEPT_PASSWORDS:
        with st.expander("🔐 부처 특수 권한 인증", expanded=True):
            dpw = st.text_input("2차 보안 비밀번호", type="password", key=f"pw_{my_dept}")
            if dpw == DEPT_PASSWORDS[my_dept]:
                st.success(f"{my_dept} 인증 성공")
                
                # --- [수정] 선교부 전용: 특정 부서 할렐루야 사면 ---
                if my_dept == "선교부":
                    target = st.selectbox("사면할 부서 선택", all_depts, key="amnesty_select")
                    current_fine = st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'].values[0]
                    st.write(f"현재 {target} 벌금: **{int(current_fine):,}원**")
                    if st.button(f"🙌 {target} 사면: 할렐루야!!"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = 0
                        save_data(st.session_state.config, st.session_state.requests)
                        st.success(f"🎊 {target}의 벌금이 사면되었습니다!"); st.balloons(); st.rerun()
                
                # --- 기존 권한 유지 (인성예절부, 봉사부) ---
                else:
                    target = st.selectbox("대상 부처 선택", all_depts, key="special_target")
                    amt = st.number_input("금액 입력", step=500, key="special_amt")
                    if my_dept == "인성예절부" and st.button("⚖️ 벌금 부과"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] += amt
                        save_data(st.session_state.config, st.session_state.requests); st.rerun()
                    elif my_dept == "봉사부" and st.button("🎁 벌금 탕감"):
                        cur_f = st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'].values[0]
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = max(0, cur_f - amt)
                        save_data(st.session_state.config, st.session_state.requests); st.rerun()

    st.divider()
    st.subheader("💰 예산 신청")
    with st.form("req_form", clear_on_submit=True):
        item = st.text_input("구입 항목"); req_amt = st.number_input("신청 금액", step=100)
        if st.form_submit_button("🚀 신청하기"):
            new = {'날짜': datetime.now().strftime("%m-%d"), '부처명': my_dept, '항목': item, '금액': req_amt, '상태': '대기'}
            st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
            save_data(st.session_state.config, st.session_state.requests); st.success("제출 완료")

elif user_role == "감사원":
    st.header("🔍 감찰 리포트")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        st.metric(f"📍 {r['항목']}", f"{int(r['지출액']):,}원 사용", f"벌금: {int(r['벌금']):,}원", delta_color="inverse")

if st.sidebar.button("🔓 로그아웃"):
    del st.session_state.auth_role
    st.rerun()
