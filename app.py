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

# 세션 초기화
if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# --- 모바일 최적화 레이아웃 ---
st.set_page_config(page_title="학급 보안 시스템", layout="centered")

# 모바일용 대형 버튼 스타일
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; margin-bottom: 5px; }
    .approve-btn { background-color: #28a745 !important; color: white !important; }
    .reject-btn { background-color: #dc3545 !important; color: white !important; }
    div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# --- 1단계: 모바일 로그인 (사이드바 대신 메인 화면 사용) ---
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

# 로그인 성공 시
user_role = st.session_state.auth_role
st.caption(f"접속 권한: {user_role} | [로그아웃](javascript:window.location.reload())")
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# --- 2단계: 역할별 모바일 화면 ---

# 1. 교사 모드
if user_role == "교사":
    st.header("👨‍🏫 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_val = st.number_input("학급 총 예산 세팅", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💰 총액 저장"):
        st.session_state.config.at[idx, '금액'] = total_val
        save_data(st.session_state.config, st.session_state.requests)
        st.success("반영 완료")

# 2. 총무 모드 (결재 버튼 강화)
elif user_role == "총무":
    st.header("👩‍💼 예산 결재 시스템")
    
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    if not pending.empty:
        st.subheader(f"대기 중인 결재 ({len(pending)}건)")
        for i, r in pending.iterrows():
            with st.container():
                st.info(f"**[{r['부처명']}]** {r['항목']}\n\n신청 금액: **{r['금액']:,}원**")
                c1, c2 = st.columns(2)
                if c1.button("✅ 승인", key=f"app_{i}"):
                    st.session_state.requests.at[i, '상태'] = '승인'
                    st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
                    save_data(st.session_state.config, st.session_state.requests); st.rerun()
                if c2.button("❌ 반려", key=f"rej_{i}"):
                    st.session_state.requests.at[i, '상태'] = '반려'
                    save_data(st.session_state.config, st.session_state.requests); st.rerun()
                st.write("---")
    else:
        st.write("✅ 처리할 결재가 없습니다.")

# 3. 부장 모드 (2차 보안 및 카드형 신청)
elif user_role == "부장":
    st.header("🧑‍💻 부처 업무")
    my_dept = st.selectbox("부처 선택", all_depts)
    
    if my_dept in DEPT_PASSWORDS:
        st.subheader("🔑 2차 보안 인증")
        dept_pw = st.text_input("전용 비번", type="password")
        if dept_pw != DEPT_PASSWORDS[my_dept]:
            st.warning("2차 비밀번호를 입력해야 특수 기능이 열립니다.")
            st.stop()
        st.success(f"{my_dept} 인증 성공")
        
        # 특수 기능 (가독성을 위해 expander 사용)
        with st.expander(f"✨ {my_dept} 전용 특수 권한"):
            if my_dept == "인성예절부":
                target = st.selectbox("벌금 부과", all_depts); amt = st.number_input("벌금", step=500)
                if st.button("⚖️ 벌금 확정"):
                    st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = amt
                    save_data(st.session_state.config, st.session_state.requests); st.warning("부과됨")
            # ... (봉사부, 선교부 로직 동일)

    st.divider()
    with st.expander("💰 예산 품의 신청", expanded=True):
        item = st.text_input("품목 명칭"); amt = st.number_input("신청 금액", step=100)
        if st.button("🚀 결재 신청 보내기"):
            new = {'날짜': datetime.now().strftime("%m-%d"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기'}
            st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
            save_data(st.session_state.config, st.session_state.requests); st.success("총무에게 전송됨")

# 4. 감사원 모드 (표 대신 리포트 형식)
elif user_role == "감사원":
    st.header("🔍 감찰 리포트")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        with st.expander(f"📊 {r['항목']} 현황"):
            st.write(f"배정 예산: {r['금액']:,}원")
            st.write(f"사용 금액: {r['지출액']:,}원")
            st.error(f"미납 벌금: {r['벌금']:,}원")
