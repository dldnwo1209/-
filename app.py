import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 파일 설정
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
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '비고'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# --- UI 스타일 (가독성 고정) ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0F172A !important; border: 2px solid #3B82F6 !important; padding: 15px !important; border-radius: 15px !important; }
    [data-testid="stMetricLabel"] div { color: #94A3B8 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FDE047 !important; font-size: 1.8rem !important; font-weight: 900 !important; }
    .stButton>button { background-color: #2563EB !important; color: white !important; border-radius: 10px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 로그인 체크 ---
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("1차 비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else: st.error("비밀번호 오류")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# --- 2. 역할별 기능 ---

# [부장 모드] - 이 부분을 확인해주세요!
if user_role == "부장":
    st.header("🧑‍💻 부처 행정 시스템")
    
    # 부처 선택
    my_dept = st.selectbox("내 부처를 선택하세요", all_depts)
    dept_data = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    
    # 1. 현황판 (배정액 - 지출액 - 벌금 = 가용잔액)
    available = dept_data['금액'] - dept_data['지출액'] - dept_data['벌금']
    
    st.markdown(f"### 📊 {my_dept} 예산 현황")
    st.metric("💳 신청 가능 잔액", f"{int(available):,}원", f"총 배정액: {int(dept_data['금액']):,}원")
    
    if dept_data['벌금'] > 0:
        st.warning(f"⚠️ 현재 미납된 벌금 {int(dept_data['벌금']):,}원이 차감된 금액입니다.")

    st.divider()

    # 2. 예산 신청 폼 (추가 행동 가능)
    st.subheader("💰 지출 결재 신청")
    with st.form("request_form", clear_on_submit=True):
        st.write("총무에게 보낼 구매 내역을 작성하세요.")
        req_item = st.text_input("구입 항목 (예: 문구류, 간식 등)")
        req_amt = st.number_input("신청 금액", min_value=0, max_value=int(max(0, available)), step=100)
        
        submit_btn = st.form_submit_button("🚀 총무에게 승인 요청")
        
        if submit_btn:
            if not req_item:
                st.error("항목 이름을 입력해주세요.")
            elif req_amt <= 0:
                st.error("금액을 0원보다 크게 입력해주세요.")
            else:
                # 데이터 기록
                new_row = {
                    '날짜': datetime.now().strftime("%m-%d %H:%M"),
                    '부처명': my_dept,
                    '항목': req_item,
                    '금액': req_amt,
                    '상태': '대기',
                    '비고': ''
                }
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.config, st.session_state.requests)
                st.success(f"✅ {req_item} ({req_amt:,}원) 신청 완료! 총무의 결재를 기다리세요.")
                st.balloons()

    # 3. 내 부처 신청 기록 확인
    st.divider()
    st.subheader("📋 우리 부처 신청 기록")
    my_logs = st.session_state.requests[st.session_state.requests['부처명'] == my_dept].iloc[::-1]
    if not my_logs.empty:
        for _, log in my_logs.head(5).iterrows():
            status_icon = "🟢" if log['상태'] == "승인" else "🟡" if log['상태'] == "대기" else "🔴"
            st.text(f"{status_icon} {log['날짜']} | {log['항목']} | {int(log['금액']):,}원 ({log['상태']})")
    else:
        st.write("아직 신청한 내역이 없습니다.")

# [다른 역할들 - 기존 로직 유지]
elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    # (총무 로직 동일...)
    st.write("총무 기능을 수행하세요.") # 생략된 부분은 기존 코드와 동일

elif user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    # (교사 로직 동일...)

elif user_role == "감사원":
    st.header("🔍 감찰 기록")
    # (감사원 로직 동일...)

# 로그아웃
if st.sidebar.button("🔓 로그아웃"):
    del st.session_state.auth_role
    st.rerun()
