import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 환경 설정 및 데이터 로드
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
            '금액': [0.0] * (len(depts) + 1),
            '지출액': [0.0] * (len(depts) + 1),
            '벌금': [0.0] * (len(depts) + 1)
        })
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '비고'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# 2. 모바일 UI 스타일 고정
st.set_page_config(page_title="학급 보안 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0F172A !important; border: 2px solid #3B82F6 !important; padding: 15px !important; border-radius: 15px !important; }
    [data-testid="stMetricLabel"] div { color: #94A3B8 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FDE047 !important; font-size: 1.8rem !important; font-weight: 900 !important; }
    .stButton>button { background-color: #2563EB !important; color: white !important; border-radius: 10px; height: 3.2em; font-weight: bold; width: 100%; }
    .special-box { border: 2px solid #FDE047; padding: 15px; border-radius: 10px; background-color: #1E293B; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# 3. 메인 로그인
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("1차 비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else: st.error("비밀번호 오류")
    st.stop()

user_role = st.session_state.auth_role
all_depts = st.session_state.config[st.session_state.config['항목'] != '학급총액']['항목'].tolist()

# 4. 행정 로직

# [A] 교사 모드 (동일)
if user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    new_total = st.number_input("학급 총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 총액 확정 저장"):
        st.session_state.config.at[idx, '금액'] = float(new_total)
        save_data(st.session_state.config, st.session_state.requests)
        st.success("총액 저장 완료!"); st.balloons()

# [B] 총무 모드 (동일)
elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_budget = st.session_state.config.at[total_idx, '금액']
    assigned_sum = st.session_state.config[st.session_state.config['항목'] != '학급총액']['금액'].sum()
    st.metric("💰 학급 총 예산", f"{int(total_budget):,}원", f"배정 가능: {int(total_budget - assigned_sum):,}원")
    
    with st.expander("➕ 부처별 예산 배정", expanded=True):
        target = st.selectbox("부처 선택", all_depts)
        curr_val = st.session_state.config.loc[st.session_state.config['항목'] == target, '금액'].values[0]
        new_val = st.number_input("배정 금액", value=int(curr_val), min_value=0, step=1000)
        if st.button("📍 배정 확정"):
            if assigned_sum - curr_val + new_val > total_budget:
                st.error("총 예산 초과!")
            else:
                st.session_state.config.loc[st.session_state.config['항목'] == target, '금액'] = float(new_val)
                save_data(st.session_state.config, st.session_state.requests)
                st.success("배정 성공!"); st.balloons(); st.rerun()

    st.subheader("📝 결재 대기")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        st.info(f"**[{r['부처명']}]** {r['항목']} ({int(r['금액']):,}원)")
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인", key=f"app_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            st.session_state.config.loc[st.session_state.config['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(st.session_state.config, st.session_state.requests); st.balloons(); st.rerun()
        if c2.button("❌ 반려", key=f"rej_{i}"):
            st.session_state.requests.at[i, '상태'] = '반려'
            save_data(st.session_state.config, st.session_state.requests); st.rerun()

# [C] 부장 모드 (특수 권한 업데이트)
elif user_role == "부장":
    st.header("🧑‍💻 부처 행정")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    d_idx = st.session_state.config.index[st.session_state.config['항목'] == my_dept][0]
    d = st.session_state.config.iloc[d_idx]
    
    rem = d['금액'] - d['지출액'] - d['벌금']
    st.metric("💳 가용 잔액", f"{int(rem):,}원", f"배정액: {int(d['금액']):,}원")
    if d['벌금'] > 0: st.error(f"⚠️ 벌금 미납액: {int(d['벌금']):,}원")

    # 💡 2차 보안 및 특수 행정 업무
    if my_dept in DEPT_PASSWORDS:
        st.write("---")
        st.subheader(f"🔐 {my_dept} 전용 업무")
        
        # 2차 비밀번호 입력 시에도 버튼을 눌러야 활성화
        if f'dept_auth_{my_dept}' not in st.session_state:
            st.session_state[f'dept_auth_{my_dept}'] = False
            
        if not st.session_state[f'dept_auth_{my_dept}']:
            sec_pw = st.text_input("2차 보안 비밀번호", type="password")
            if st.button("🔑 특수 권한 인증"):
                if sec_pw == DEPT_PASSWORDS[my_dept]:
                    st.session_state[f'dept_auth_{my_dept}'] = True
                    st.rerun()
                else: st.error("비밀번호 불일치")
        else:
            with st.container():
                st.markdown('<div class="special-box">', unsafe_allow_html=True)
                st.success(f"✅ {my_dept} 행정 시스템 접속됨")
                target_dept = st.selectbox("대상 부처 선택", all_depts)
                
                # 부처별 특성화 로직
                if my_dept == "봉사부":
                    st.info("💡 봉사부는 벌금을 감면(탕감)만 할 수 있습니다.")
                    reduction_amt = st.number_input("감면할 벌금액 입력 (양수 입력 시 자동 차감)", min_value=0, step=500)
                    if st.button("✨ 벌금 감면 확정"):
                        # 입력받은 값을 그대로 빼기 연산
                        st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '벌금'] -= float(reduction_amt)
                        save_data(st.session_state.config, st.session_state.requests)
                        st.success(f"🎉 {target_dept}의 벌금이 {reduction_amt:,}원 감면되었습니다!"); st.balloons()
                
                elif my_dept in ["인성예절부", "선교부"]:
                    st.info("💡 부과(+) 또는 사면(-) 금액을 입력하세요.")
                    fine_change = st.number_input("조정액 입력 (+부과, -사면)", step=500)
                    if st.button("⚖️ 벌금 데이터 업데이트"):
                        st.session_state.config.loc[st.session_state.config['항목'] == target_dept, '벌금'] += float(fine_change)
                        save_data(st.session_state.config, st.session_state.requests)
                        st.warning(f"⚖️ {target_dept}의 행정 처리가 완료되었습니다."); st.balloons()
                
                if st.button("🔓 권한 해제"):
                    st.session_state[f'dept_auth_{my_dept}'] = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("💰 예산 품의 신청")
    with st.form("req_form", clear_on_submit=True):
        item = st.text_input("품목")
        amt = st.number_input("금액", min_value=0, max_value=int(max(0, rem)), step=100)
        if st.form_submit_button("🚀 신청하기"):
            if item and amt > 0:
                new = {'날짜': datetime.now().strftime("%m-%d %H:%M"), '부처명': my_dept, '항목': item, '금액': float(amt), '상태': '대기'}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
                save_data(st.session_state.config, st.session_state.requests)
                st.success("신청되었습니다!"); st.balloons()

# [D] 감사원 모드 (동일)
elif user_role == "감사원":
    st.header("🔍 감사 리포트")
    for _, r in st.session_state.config[st.session_state.config['항목'] != '학급총액'].iterrows():
        with st.expander(f"📍 {r['항목']} 현황"):
            st.write(f"배정: {int(r['금액']):,}원 / 지출: {int(r['지출액']):,}원 / 벌금: {int(r['벌금']):,}원")
    st.subheader("📜 전체 로그")
    for i, row in st.session_state.requests.iloc[::-1].iterrows():
        st.text(f"[{row['상태']}] {row['부처명']}: {row['항목']} ({int(row['금액']):,}원)")

# 공통 로그아웃
if st.sidebar.button("🔓 로그아웃"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
