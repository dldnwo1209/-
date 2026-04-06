import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일
DB_CONFIG = 'config.csv'
LOG_FILE = 'transactions.csv'

# 권한별 비밀번호 설정
PASSWORDS = {
    "교사": "1209",
    "총무": "1357",
    "부장": "2468",
    "감사원": "1111"
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
            '지출액': [0] * (len(depts) + 1)
        })
    
    if os.path.exists(LOG_FILE):
        req_df = pd.read_csv(LOG_FILE)
    else:
        req_df = pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '반려사유'])
    
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# --- UI 레이아웃 ---
st.set_page_config(page_title="학급 정부 회계 시스템", layout="wide")
st.title("⚖️ 보안형 학급 정부 예산 관리 시스템")

# 사이드바 로그인 시스템
st.sidebar.header("🔐 권한 인증")
user_role = st.sidebar.selectbox("내 역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
user_pw = st.sidebar.text_input("비밀번호 입력", type="password")

# 인증 확인 함수
def check_auth(role):
    if user_role == role and user_pw == PASSWORDS[role]:
        return True
    return False

# 메인 화면 안내
if user_role == "선택하세요" or not user_pw:
    st.info("왼쪽 사이드바에서 역할을 선택하고 비밀번호를 입력해주세요.")
    st.image("https://img.icons8.com/illustrations/external-fauzidea-flat-fauzidea/128/external-login-ecommerce-fauzidea-flat-fauzidea.png")

# --- 1. 교사 탭 ---
elif check_auth("교사"):
    st.header("👨‍🏫 교사 전용: 학급 총액 편성")
    current_total = st.session_state.config.loc[st.session_state.config['항목'] == '학급총액', '금액'].values[0]
    new_total = st.number_input("이번 달 학급 전체 예산(원)", min_value=0, value=int(current_total))
    
    if st.button("총액 확정"):
        st.session_state.config.loc[st.session_state.config['항목'] == '학급총액', '금액'] = new_total
        save_data(st.session_state.config, st.session_state.requests)
        st.success("총액 설정 완료")

# --- 2. 총무 탭 ---
elif check_auth("총무"):
    st.header("👩‍💼 총무 전용: 예산 배정 및 결재")
    total_limit = st.session_state.config.loc[st.session_state.config['항목'] == '학급총액', '금액'].values[0]
    st.write(f"**현재 학급 총액 가이드라인:** {total_limit:,}원")
    
    with st.expander("부처별 예산 배정"):
        dept_list = st.session_state.config[st.session_state.config['항목'] != '학급총액']
        edited_dept = st.data_editor(dept_list[['항목', '금액']], key="dept_editor")
        if st.button("배정액 저장"):
            if edited_dept['금액'].sum() > total_limit:
                st.error("총액을 초구하여 배정할 수 없습니다.")
            else:
                for idx, row in edited_dept.iterrows():
                    st.session_state.config.loc[st.session_state.config['항목'] == row['항목'], '금액'] = row['금액']
                save_data(st.session_state.config, st.session_state.requests)
                st.success("배정 완료")

    st.subheader("📥 결재 대기 함")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for idx, row in pending.iterrows():
        c1, c2, c3 = st.columns([3,1,1])
        reason = c1.text_input(f"[{row['부처명']}] {row['항목']} 사유", key=idx)
        if c2.button("승인", key=f"a{idx}"):
            st.session_state.requests.at[idx, '상태'] = '승인'
            st.session_state.config.loc[st.session_state.config['항목'] == row['부처명'], '지출액'] += row['금액']
            save_data(st.session_state.config, st.session_state.requests); st.rerun()
        if c3.button("반려", key=f"r{idx}"):
            st.session_state.requests.at[idx, '상태'] = '반려'
            st.session_state.requests.at[idx, '반려사유'] = reason
            save_data(st.session_state.config, st.session_state.requests); st.rerun()

# --- 3. 부장 탭 ---
elif check_auth("부장"):
    st.header("🧑‍💻 부장 전용: 예산 품의")
    depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()
    with st.form("req"):
        d = st.selectbox("소속 부처", depts)
        i = st.text_input("항목")
        a = st.number_input("금액", min_value=0)
        if st.form_submit_button("신청"):
            limit = st.session_state.config.loc[st.session_state.config['항목'] == d, '금액'].values[0]
            spent = st.session_state.config.loc[st.session_state.config['항목'] == d, '지출액'].values[0]
            if a > (limit - spent): st.error("잔액 부족")
            else:
                new = {'날짜': datetime.now().strftime("%Y-%m-%d"), '부처명': d, '항목': i, '금액': a, '상태': '대기', '반려사유': ''}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
                save_data(st.session_state.config, st.session_state.requests); st.success("제출 완료")

# --- 4. 감사원 탭 ---
elif check_auth("감사원"):
    st.header("🔍 공수처(감찰부) 전용: 감사 시스템")
    st.subheader("📊 부처별 사용량 점검")
    report = st.session_state.config[st.session_state.config['항목'] != '학급총액'].copy()
    st.dataframe(report, use_container_width=True)
    st.subheader("📋 전체 거래 이력")
    st.dataframe(st.session_state.requests, use_container_width=True)

else:
    st.error("비밀번호가 일치하지 않습니다. 다시 확인해주세요.")
