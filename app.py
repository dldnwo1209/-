import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일 (기존 파일명 유지)
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

st.set_page_config(page_title="학급 보안 시스템", layout="centered")

# --- 1. 로그인 체크 (세션 관리) ---
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할", ["선택하세요", "교사", "총무", "부장", "감사원"])
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

# [총무 모드] 예산 배정 기능 대폭 수정
if user_role == "총무":
    st.header("👩‍💼 총무 행정 시스템")
    
    # 학급 총액 확인
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    
    st.metric("학급 총 예산", f"{total_budget:,}원", f"잔액: {total_budget - assigned_sum:,}원")

    # (개선) 드롭다운과 입력창을 이용한 예산 배정
    with st.expander("➕ 부처별 예산 배정/수정", expanded=True):
        target_dept = st.selectbox("배정할 부처 선택", all_depts)
        
        # 현재 해당 부처에 배정된 금액 표시
        current_val = st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'].values[0]
        new_val = st.number_input(f"{target_dept} 배정 금액", value=int(current_val), step=1000)
        
        if st.button("📍 예산 확정 저장"):
            # 잔액 체크 (선택 사항)
            diff = new_val - current_val
            if assigned_sum + diff > total_budget:
                st.error("학급 총 예산을 초과할 수 없습니다!")
            else:
                st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '금액'] = new_val
                save_data(st.session_state.config, st.session_state.requests)
                st.success(f"{target_dept}에 {new_val:,}원이 배정되었습니다.")
                st.rerun()

    st.divider()

    # 결재 대기 목록 (기존 버튼식 유지)
    st.subheader("📝 결재 대기 건")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    if not pending.empty:
        for i, r in pending.iterrows():
            st.info(f"**[{r['부처명']}]** {r['항목']}\n신청액: {r['금액']:,}원")
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인", key=f"app_{i}"):
                st.session_state.requests.at[i, '상태'] = '승인'
                st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
                save_data(st.session_state.config, st.session_state.requests); st.rerun()
            if c2.button("❌ 반려", key=f"rej_{i}"):
                st.session_state.requests.at[i, '상태'] = '반려'
                save_data(st.session_state.config, st.session_state.requests); st.rerun()
    else:
        st.write("처리할 결재가 없습니다.")

# [교사 모드]
elif user_role == "교사":
    st.header("👨‍🏫 교사: 예산 총액 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    val = st.number_input("학급 운영비 총액 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 총액 저장"):
        st.session_state.config.at[idx, '금액'] = val
        save_data(st.session_state.config, st.session_state.requests)
        st.success("저장되었습니다.")

# (나머지 부장, 감사원 로직은 이전 모바일 버전과 동일)
