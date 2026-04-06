import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일
DB_CONFIG = 'config_v3.csv'
LOG_FILE = 'transactions_v3.csv'

# 권한별 비밀번호
PASSWORDS = {
    "교사": "1209", "총무": "1357", "부장": "2468", "감사원": "1111"
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

st.set_page_config(page_title="학급 정부 통합 시스템", layout="wide")
st.title("⚖️ 학급 정부 예산 및 사법 통제 시스템")

# 사이드바 로그인
st.sidebar.header("🔐 권한 인증")
user_role = st.sidebar.selectbox("내 역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
user_pw = st.sidebar.text_input("비밀번호 입력", type="password")

def check_auth(role):
    return user_role == role and user_pw == PASSWORDS[role]

if user_role == "선택하세요" or not user_pw:
    st.info("왼쪽 사이드바에서 역할을 선택하고 로그인해주세요.")
elif not check_auth(user_role):
    st.error("비밀번호가 일치하지 않습니다.")
else:
    # --- 공통 데이터 처리 ---
    all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

    # 1. 교사 탭
    if user_role == "교사":
        st.header("👨‍🏫 교사: 학급 총액 편성")
        idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
        new_total = st.number_input("총 예산(원)", value=int(st.session_state.config.at[idx, '금액']))
        if st.button("확정"):
            st.session_state.config.at[idx, '금액'] = new_total
            save_data(st.session_state.config, st.session_state.requests); st.success("설정 완료")

    # 2. 총무 탭
    elif user_role == "총무":
        st.header("👩‍💼 총무: 예산 배정 및 결재")
        with st.expander("부처별 예산 배정"):
            dept_edit = st.data_editor(st.session_state.config[st.session_state.config['항목'] != '학급총액'][['항목', '금액']])
            if st.button("배정 저장"):
                for _, r in dept_edit.iterrows():
                    st.session_state.config.loc[st.session_state.config['항목'] == r['항목'], '금액'] = r['금액']
                save_data(st.session_state.config, st.session_state.requests); st.success("저장됨")
        
        st.subheader("📥 일반 품의 결재")
        pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
        for i, r in pending.iterrows():
            c1, c2, c3 = st.columns([3,1,1])
            if c2.button("승인", key=f"a{i}"):
                st.session_state.requests.at[i, '상태'] = '승인'
                st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
                save_data(st.session_state.config, st.session_state.requests); st.rerun()
            if c3.button("반려", key=f"r{i}"):
                st.session_state.requests.at[i, '상태'] = '반려'
                save_data(st.session_state.config, st.session_state.requests); st.rerun()

    # 3. 부장 탭 (특수 권한 포함)
    elif user_role == "부장":
        st.header("🧑‍💻 부처별 행정 업무")
        my_dept = st.selectbox("내 부처 선택", all_depts)
        
        # (1) 인성예절부: 벌금 부과
        if my_dept == "인성예절부":
            st.subheader("🔨 학급재판: 벌금 부과")
            target = st.selectbox("벌금 부과 대상", all_depts, key="fine_target")
            fine_amt = st.number_input("벌금 액수", min_value=0)
            if st.button("벌금 확정/수정"):
                st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = fine_amt
                save_data(st.session_state.config, st.session_state.requests); st.warning(f"{target}에 벌금 {fine_amt:,}원 부과")

        # (2) 봉사부: 복지금 지원
        elif my_dept == "봉사부":
            st.subheader("🤝 복지금 지원 (벌금 탕감)")
            target = st.selectbox("지원 대상 부처", all_depts)
            support = st.number_input("지원액", min_value=0)
            if st.button("복지금 집행"):
                current_fine = st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'].values[0]
                st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = max(0, current_fine - support)
                save_data(st.session_state.config, st.session_state.requests); st.success("탕감 완료")

        # (3) 선교부: 면죄부 발행
        elif my_dept == "선교부":
            st.subheader("🕊️ 면죄부 발행 (벌금 사면)")
            target = st.selectbox("사면 대상 부처", all_depts)
            if st.button("면죄부 발행"):
                st.session_state.config.loc[st.session_state.config['항목'] == target, '벌금'] = 0
                save_data(st.session_state.config, st.session_state.requests); st.info(f"{target} 벌금 전액 사면")

        # (공통) 일반 예산 품의
        st.divider()
        st.subheader("💰 일반 예산 품의 신청")
        with st.form("req"):
            item = st.text_input("품목"); amt = st.number_input("금액", min_value=0)
            if st.form_submit_button("신청"):
                new = {'날짜': datetime.now().strftime("%Y-%m-%d"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기', '비고': ''}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
                save_data(st.session_state.config, st.session_state.requests); st.success("제출됨")

    # 4. 감사원 탭
    elif user_role == "감사원":
        st.header("🔍 공수처 감찰 시스템")
        report = st.session_state.config[st.session_state.config['항목'] != '학급총액'].copy()
        report['잔여예산'] = report['금액'] - report['지출액']
        st.subheader("🚩 부처별 재정/벌금 현황")
        st.dataframe(report[['항목', '금액', '지출액', '잔여예산', '벌금']], use_container_width=True)
        st.subheader("📋 전체 로그")
        st.dataframe(st.session_state.requests, use_container_width=True)
