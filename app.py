import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일
DB_CONFIG = 'config_v4.csv'
LOG_FILE = 'transactions_v4.csv'

# 권한별 비밀번호 설정
PASSWORDS = {
    "교사": "1209", "총무": "1357", "부장": "2468", "감사원": "1111"
}

# 부처별 2차 비밀번호 설정
DEPT_PASSWORDS = {
    "인성예절부": "24278",
    "봉사부": "848",
    "선교부": "398"
}

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
    if os.path.exists(LOG_FILE):
        req_df = pd.read_csv(LOG_FILE)
    else:
        req_df = pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '비고'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

st.set_page_config(page_title="보안 강화 학급 시스템", layout="wide")
st.title("🛡️ 2차 보안 적용 학급 정부 시스템")

# 1단계: 사이드바 로그인
st.sidebar.header("🔐 1차 권한 인증")
user_role = st.sidebar.selectbox("내 역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
user_pw = st.sidebar.text_input("1차 비밀번호", type="password")

def check_auth(role):
    return user_role == role and user_pw == PASSWORDS[role]

if user_role == "선택하세요" or not user_pw:
    st.info("왼쪽에서 역할을 선택하고 로그인하세요.")
elif not check_auth(user_role):
    st.error("비밀번호가 일치하지 않습니다.")
else:
    all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

    # --- 1. 교사 ---
    if user_role == "교사":
        st.header("👨‍🏫 교사: 예산 총액 관리")
        idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
        val = st.number_input("총액", value=int(st.session_state.config.at[idx, '금액']))
        if st.button("저장"):
            st.session_state.config.at[idx, '금액'] = val
            save_data(st.session_state.config, st.session_state.requests); st.success("반영됨")

    # --- 2. 총무 ---
    elif user_role == "총무":
        st.header("👩‍💼 총무: 배정 및 결재")
        # (기존 총무 로직 동일...)
        with st.expander("예산 배정"):
            dept_edit = st.data_editor(st.session_state.config[st.session_state.config['항목'] != '학급총액'][['항목', '금액']])
            if st.button("저장"):
                for _, r in dept_edit.iterrows():
                    st.session_state.config.loc[st.session_state.config['항목'] == r['항목'], '금액'] = r['금액']
                save_data(st.session_state.config, st.session_state.requests); st.success("저장됨")
        
        pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
        for i, r in pending.iterrows():
            c1, c2, c3 = st.columns([3,1,1])
            c1.write(f"[{r['부처명']}] {r['항목']} ({r['금액']:,}원)")
            if c2.button("승인", key=f"a{i}"):
                st.session_state.requests.at[i, '상태'] = '승인'
                st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
                save_data(st.session_state.config, st.session_state.requests); st.rerun()
            if c3.button("반려", key=f"r{i}"):
                st.session_state.requests.at[i, '상태'] = '반려'
                save_data(st.session_state.config, st.session_state.requests); st.rerun()

    # --- 3. 부장 (2차 보안 적용) ---
    elif user_role == "부장":
        st.header("🧑‍💻 부처별 행정 업무")
        my_dept = st.selectbox("내 부처 선택", all_depts)
        
        # 특수 부처인 경우 2차 비번 확인
        if my_dept in DEPT_PASSWORDS:
            st.subheader(f"🔑 {my_dept} 전용 2차 인증")
            dept_pw = st.text_input(f"{my_dept} 전용 비밀번호", type="password", key="dept_pw_input")
            
            if dept_pw == DEPT_PASSWORDS[my_dept]:
                st.success(f"{my_dept} 권한이 인증되었습니다.")
                # 인성예절부 기능
                if my_dept == "인성예절부":
                    target = st.selectbox("벌금 부과 대상", all_depts)
                    amt = st.number_input("벌금액", min_value=0)
                    if st.button("벌금 부과"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = amt
                        save_data(st.session_state.config, st.session_state.requests); st.warning("부과 완료")
                # 봉사부 기능
                elif my_dept == "봉사부":
                    target = st.selectbox("지원 대상", all_depts)
                    supp = st.number_input("지원액", min_value=0)
                    if st.button("복지금 집행"):
                        cur = st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'].values[0]
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = max(0, cur - supp)
                        save_data(st.session_state.config, st.session_state.requests); st.success("탕감 완료")
                # 선교부 기능
                elif my_dept == "선교부":
                    target = st.selectbox("사면 대상", all_depts)
                    if st.button("면죄부 발행"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = 0
                        save_data(st.session_state.config, st.session_state.requests); st.info("전액 사면")
            elif dept_pw != "":
                st.error("2차 비밀번호가 틀렸습니다.")
        
        # 공통 품의 신청
        st.divider()
        st.subheader("💰 예산 품의 신청 (공통)")
        with st.form("req"):
            item = st.text_input("품목"); amt = st.number_input("금액", min_value=0)
            if st.form_submit_button("신청"):
                new = {'날짜': datetime.now().strftime("%Y-%m-%d"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기'}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
                save_data(st.session_state.config, st.session_state.requests); st.success("제출됨")

    # --- 4. 감사원 ---
    elif user_role == "감사원":
        st.header("🔍 공수처 감찰 시스템")
        report = st.session_state.config[st.session_state.config['항목'] != '학급총액'].copy()
        st.dataframe(report[['항목', '금액', '지출액', '벌금']], use_container_width=True)
        st.subheader("📋 전체 로그")
        st.dataframe(st.session_state.requests, use_container_width=True)
