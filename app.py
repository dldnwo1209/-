import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일 경로 (GitHub 배포 시 세션 유지용)
DB_FILE = 'budget_data.csv'
LOG_FILE = 'transaction_log.csv'

# 1. 데이터 로드 및 초기화 함수
def load_data():
    if os.path.exists(DB_FILE):
        budget_df = pd.read_csv(DB_FILE)
    else:
        # 초기 데이터 설정
        budget_df = pd.DataFrame({
            '부처명': ['체육부', '미화부', '도서부', '학생회'],
            '배정예산': [100000, 100000, 100000, 200000],
            '지출액': [0, 0, 0, 0]
        })
    
    if os.path.exists(LOG_FILE):
        requests_df = pd.read_csv(LOG_FILE)
    else:
        requests_df = pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '반려사유'])
    
    return budget_df, requests_df

def save_data(budget_df, requests_df):
    budget_df.to_csv(DB_FILE, index=False)
    requests_df.to_csv(LOG_FILE, index=False)

# 세션 상태 관리
if 'budget_db' not in st.session_state or 'requests' not in st.session_state:
    st.session_state.budget_db, st.session_state.requests = load_data()

# --- UI 레이아웃 설정 ---
st.set_page_config(page_title="학급 회계 시스템 v2.0", layout="wide")
st.title("🏫 스마트 학급 회계 관리 시스템")
st.markdown("---")

# 4개 집단 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["👨‍🏫 교사 (관리)", "👩‍💼 총무 (결재)", "🧑‍💻 부장 (품의)", "🔍 감사원 (감사)"])

# --- 1. 교사 탭: 예산 편성 및 총괄 ---
with tab1:
    st.header("📌 예산 가이드라인 설정")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        with st.form("budget_setting"):
            target_dept = st.selectbox("수정할 부처", st.session_state.budget_db['부처명'])
            new_val = st.number_input("배정 금액 설정(원)", min_value=0, step=1000)
            if st.form_submit_button("예산 확정"):
                st.session_state.budget_db.loc[st.session_state.budget_db['부처명'] == target_dept, '배정예산'] = new_val
                save_data(st.session_state.budget_db, st.session_state.requests)
                st.success(f"{target_dept} 예산 변경 완료!")
    
    with col_b:
        st.subheader("현재 부처별 예산 현황")
        current_view = st.session_state.budget_db.copy()
        current_view['잔액'] = current_view['배정예산'] - current_view['지출액']
        st.table(current_view)

# --- 2. 총무 탭: 결재 관리 ---
with tab2:
    st.header("⚖️ 품의서 결재함")
    reqs = st.session_state.requests
    pending = reqs[reqs['상태'] == '대기']

    if not pending.empty:
        for idx, row in pending.iterrows():
            with st.expander(f"📦 [{row['부처명']}] {row['항목']} - {format(row['금액'], ',')}원", expanded=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                reject_reason = c1.text_input("반려 시 사유 입력", key=f"reason_{idx}")
                
                if c2.button("✅ 승인", key=f"app_{idx}", use_container_width=True):
                    st.session_state.requests.at[idx, '상태'] = '승인'
                    st.session_state.budget_db.loc[st.session_state.budget_db['부처명'] == row['부처명'], '지출액'] += row['금액']
                    save_data(st.session_state.budget_db, st.session_state.requests)
                    st.rerun()
                
                if c3.button("❌ 반려", key=f"rej_{idx}", use_container_width=True):
                    st.session_state.requests.at[idx, '상태'] = '반려'
                    st.session_state.requests.at[idx, '반려사유'] = reject_reason if reject_reason else "사유 미기재"
                    save_data(st.session_state.budget_db, st.session_state.requests)
                    st.rerun()
    else:
        st.info("결재 대기 중인 항목이 없습니다.")

# --- 3. 부장 탭: 예산 품의 신청 ---
with tab3:
    st.header("📝 예산 사용 신청")
    with st.form("request_form"):
        my_dept = st.selectbox("우리 부처", st.session_state.budget_db['부처명'])
        my_item = st.text_input("사용 목적 및 품목")
        my_amt = st.number_input("소요 예산(원)", min_value=0, step=100)
        
        if st.form_submit_button("품의서 제출"):
            # 잔액 확인 로직
            dept_info = st.session_state.budget_db[st.session_state.budget_db['부처명'] == my_dept].iloc[0]
            balance = dept_info['배정예산'] - dept_info['지출액']
            
            if my_amt > balance:
                st.error(f"잔액 부족! (현재 가능 금액: {format(balance, ',')}원)")
            elif my_item:
                new_req = {
                    '날짜': datetime.now().strftime("%Y-%m-%d"),
                    '부처명': my_dept, '항목': my_item, '금액': my_amt, 
                    '상태': '대기', '반려사유': ''
                }
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new_req])], ignore_index=True)
                save_data(st.session_state.budget_db, st.session_state.requests)
                st.success("품의서가 제출되었습니다.")
    
    st.subheader("우리 부처 신청 결과 확인")
    st.dataframe(st.session_state.requests[st.session_state.requests['부처명'] == my_dept], use_container_width=True)

# --- 4. 감사원 탭: 회계 감사 ---
with tab4:
    st.header("🕵️ 회계 투명성 감사")
    
    # 요약 지표
    m1, m2, m3 = st.columns(3)
    total_b = st.session_state.budget_db['배정예산'].sum()
    total_s = st.session_state.budget_db['지출액'].sum()
    m1.metric("학급 총 예산", f"{total_b:,}원")
    m2.metric("총 집행액", f"{total_s:,}원")
    m3.metric("예산 잔액", f"{total_b - total_s:,}원")

    st.subheader("📊 부처별 예산 사용 그래프")
    chart_df = st.session_state.budget_db.set_index('부처명')
    st.bar_chart(chart_df[['배정예산', '지출액']])

    st.subheader("📋 전체 결재 프로세스 이력")
    st.dataframe(st.session_state.requests, use_container_width=True)