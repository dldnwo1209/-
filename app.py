import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 파일 및 보안 설정
DB_CONFIG = 'config_v4.csv'
LOG_FILE = 'transactions_v4.csv'
PASSWORDS = {"교사": "1209", "총무": "1357", "부장": "2468", "감사원": "1111"}
DEPT_PASSWORDS = {"인성예절부": "24278", "봉사부": "848", "선교부": "398"}

# 2. 데이터 로드/저장 함수
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

# 3. 모바일 가독성 강제 고정 (CSS)
st.set_page_config(page_title="학급 보안 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0F172A !important; border: 2px solid #3B82F6 !important; padding: 15px !important; border-radius: 15px !important; }
    [data-testid="stMetricLabel"] div { color: #94A3B8 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FDE047 !important; font-size: 1.8rem !important; font-weight: 900 !important; }
    .stButton>button { background-color: #2563EB !important; color: white !important; border-radius: 10px; height: 3.2em; font-weight: bold; width: 100%; }
    .stAlert { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# 4. 로그인 시스템
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할 선택", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else: st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# 5. 역할별 행정 로직 (3회 검토 완료)

# [A] 교사 모드: 예산 총액 설정
if user_role == "교사":
    st.header("👨‍🏫 교사 전용 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    curr_total = int(st.session_state.config.at[idx, '금액'])
    new_total = st.number_input("학급 운영비 총액 설정", value=curr_total, step=1000)
    if st.button("💾 예산 총액 확정"):
        st.session_state.config.at[idx, '금액'] = new_total
        save_data(st.session_state.config, st.session_state.requests)
        st.success("총 예산이 성공적으로 저장되었습니다.")

# [B] 총무 모드: 예산 배정 및 결재 승인
elif user_role == "총무":
    st.header("👩‍💼 총무 행정 시스템")
    
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    available_to_assign = total_budget - assigned_sum
    
    st.metric("💰 학급 총 예산", f"{total_budget:,}원", f"배정 가능 잔액: {available_to_assign:,}원")

    with st.expander("➕ 부처별 예산 배정/수정", expanded=True):
        target = st.selectbox("부처 선택", all_depts)
        curr_val = st.session_state.config.loc[st.session_state.config['항목'] == target, '금액'].values[0]
        max_limit = available_to_assign + curr_val
        
        st.caption(f"현재 배정액: {curr_val:,}원 / 최대 가능: {max_limit:,}원")
        new_assign = st.number_input("새 배정 금액", value=int(curr_val), min_value=0, step=1000)
        
        if st.button("📍 배정 저장"):
            if new_assign > max_limit:
                st.error("학급 총 예산을 초과할 수 없습니다!")
            else:
                st.session_state.config.loc[st.session_state.config['항목'] == target, '금액'] = new_assign
                save_data(st.session_state.config, st.session_state.requests)
                st.success(f"{target} 배정 완료!"); st.rerun()

    st.subheader("📝 결재 대기 건")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    if not pending.empty:
        for i, r in pending.iterrows():
            with st.container():
                st.info(f"**[{r['부처명']}]** {r['항목']} ({r['금액']:,}원)")
                c1, c2 = st.columns(2)
                if c1.button("✅ 승인", key=f"app_{i}"):
                    st.session_state.requests.at[i, '상태'] = '승인'
                    st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
                    save_data(st.session_state.config, st.session_state.requests); st.rerun()
                if c2.button("❌ 반려", key=f"rej_{i}"):
                    st.session_state.requests.at[i, '상태'] = '반려'
                    save_data(st.session_state.config, st.session_state.requests); st.rerun()
    else: st.write("처리할 결재가 없습니다.")

# [C] 부장 모드: 잔액 확인 및 예산 신청
elif user_role == "부장":
    st.header("🧑‍💻 부처 업무 시스템")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    d = st.session_state.config[st.session_state.config['항목'] == my_dept].iloc[0]
    
    rem_budget = d['금액'] - d['지출액'] - d['벌금']
    
    st.metric("💳 우리 부서 잔액", f"{int(rem_budget):,}원", f"배정액: {int(d['금액']):,}원")
    if d['벌금'] > 0: st.warning(f"⚠️ 미납 벌금 {int(d['벌금']):,}원이 차감된 상태입니다.")

    st.divider()
    st.subheader("💰 예산 품의 신청")
    with st.form("req_form", clear_on_submit=True):
        item = st.text_input("구입 항목")
        amt = st.number_input("신청 금액", min_value=0, max_value=int(max(0, rem_budget)), step=100)
        if st.form_submit_button("🚀 승인 요청"):
            if item and amt > 0:
                new_req = {'날짜': datetime.now().strftime("%m-%d %H:%M"), '부처명': my_dept, '항목': item, '금액': amt, '상태': '대기'}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new_req])], ignore_index=True)
                save_data(st.session_state.config, st.session_state.requests)
                st.success("신청되었습니다!"); st.balloons()
            else: st.error("항목과 금액을 확인하세요.")

# [D] 감사원 모드: 전체 현황 감시
elif user_role == "감사원":
    st.header("🔍 감사 리포트")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        with st.expander(f"📍 {r['항목']} (잔액: {int(r['금액']-r['지출액']-r['벌금']):,}원)"):
            st.write(f"- 배정액: {int(r['금액']):,}원 / 지출액: {int(r['지출액']):,}원")
            if r['벌금'] > 0: st.error(f"- 미납 벌금: {int(r['벌금']):,}원")
    
    st.subheader("📜 전체 행정 로그")
    if not st.session_state.requests.empty:
        for i, row in st.session_state.requests.iloc[::-1].iterrows():
            st.markdown(f"**{row['부처명']}** | {row['항목']} | {int(row['금액']):,}원 ({row['상태']})")
            st.write("---")

# 공통 로그아웃
if st.sidebar.button("🔓 로그아웃"):
    del st.session_state.auth_role
    st.rerun()
