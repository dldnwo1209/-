import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# 1. 환경 설정 및 데이터 로드 (봉사부 이중 구조 반영)
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
            '항목': ['학급총액', '복지금재원'] + depts,
            '금액': [0.0] * (len(depts) + 2),
            '지출액': [0.0] * (len(depts) + 2),
            '벌금': [0.0] * (len(depts) + 2)
        })
    # 복지금 재원 항목 누락 방지
    if '복지금재원' not in config_df['항목'].values:
        new_row = pd.DataFrame({'항목':['복지금재원'], '금액':[0.0], '지출액':[0.0], '벌금':[0.0]})
        config_df = pd.concat([config_df, new_row], ignore_index=True)
    
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

# 💡 화면 점멸(Flash) 이펙트 함수 (단정하고 직관적인 피드백)
def trigger_flash_effect(msg="처리가 완료되었습니다."):
    st.markdown("""
        <style>
        @keyframes flash { 0% { background-color: transparent; } 50% { background-color: rgba(255, 255, 255, 0.2); } 100% { background-color: transparent; } }
        .stApp { animation: flash 0.4s ease-out; }
        </style>
    """, unsafe_allow_html=True)
    st.toast(msg, icon="✅")
    time.sleep(0.1)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# 2. UI 스타일 설정
st.set_page_config(page_title="학급 정부 시스템", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #1E293B !important; border-radius: 10px !important; border-left: 5px solid #3B82F6 !important; }
    .welfare-card { border: 2px solid #10B981; padding: 15px; border-radius: 10px; background-color: #064E3B; margin: 10px 0; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; transition: 0.2s; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 실시간 행정 시스템")

# 📊 3. 상단 통합 현황판 (모든 모드 공통)
with st.expander("📊 실시간 예산 및 벌금 대시보드", expanded=True):
    cfg = st.session_state.config
    total_val = cfg[cfg['항목'] == '학급총액']['금액'].values[0]
    wf_val = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
    
    col_t1, col_t2 = st.columns(2)
    col_t1.metric("💰 학급 총 예산", f"{int(total_val):,}원")
    col_t2.metric("✨ 가용 복지금(벌금 감면용)", f"{int(wf_val):,}원")
    
    st.divider()
    all_depts = [d for d in cfg['항목'].tolist() if d not in ['학급총액', '복지금재원']]
    cols = st.columns(4)
    for i, d_name in enumerate(all_depts):
        row = cfg[cfg['항목'] == d_name].iloc[0]
        bal = row['금액'] - row['지출액'] - row['벌금']
        cols[i % 4].metric(d_name, f"{int(bal):,}원", f"벌금 {int(row['벌금']):,}원", delta_color="inverse")

# 4. 로그인 시스템
if 'auth_role' not in st.session_state:
    st.subheader("🔐 보안 로그인")
    role = st.selectbox("역할", ["선택하세요", "교사", "총무", "부장", "감사원"])
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if role != "선택하세요" and pw == PASSWORDS.get(role):
            st.session_state.auth_role = role
            st.rerun()
        else: st.error("비밀번호 오류")
    st.stop()

user_role = st.session_state.auth_role
cfg = st.session_state.config

# 5. 행정 로직

if user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    idx = cfg.index[cfg['항목'] == '학급총액'][0]
    new_total = st.number_input("학급 총 예산 설정", value=int(cfg.at[idx, '금액']), step=1000)
    if st.button("💾 총액 확정"):
        cfg.at[idx, '금액'] = float(new_total)
        save_data(cfg, st.session_state.requests)
        trigger_flash_effect("학급 예산 동기화 완료")
        st.rerun()

elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    target = st.selectbox("편성 부처 선택", all_depts)
    
    if target == "봉사부":
        st.markdown('<div class="welfare-card">', unsafe_allow_html=True)
        st.success("✨ 봉사부 이중 예산 편성")
        curr_op = cfg.loc[cfg['항목'] == '봉사부', '금액'].values[0]
        curr_wf = cfg.loc[cfg['항목'] == '복지금재원', '금액'].values[0]
        new_op = st.number_input("1. 봉사부 일반 운영비", value=int(curr_op), step=1000)
        new_wf = st.number_input("2. 감면용 복지금 재원", value=int(curr_wf), step=1000)
        if st.button("🗳️ 봉사부 예산 전액 확정"):
            cfg.loc[cfg['항목'] == '봉사부', '금액'] = float(new_op)
            cfg.loc[cfg['항목'] == '복지금재원', '금액'] = float(new_wf)
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect("봉사부 이중 예산 확정")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        curr_val = cfg.loc[cfg['항목'] == target, '금액'].values[0]
        new_val = st.number_input(f"{target} 배정액", value=int(curr_val), step=1000)
        if st.button(f"📍 {target} 예산 저장"):
            cfg.loc[cfg['항목'] == target, '금액'] = float(new_val)
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect(f"{target} 예산 업데이트")
            st.rerun()

    # 결재 승인
    st.subheader("📝 결재 대기 건")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        if st.button(f"✅ {r['부처명']} 승인", key=f"app_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            cfg.loc[cfg['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect("지출 최종 승인")
            st.rerun()

elif user_role == "부장":
    st.header("🧑‍💻 부처 업무")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    d = cfg[cfg['항목'] == my_dept].iloc[0]
    rem = d['금액'] - d['지출액'] - d['벌금']
    st.metric(f"💳 {my_dept} 가용 운영비 잔액", f"{int(rem):,}원", f"미납 벌금: {int(d['벌금']):,}원")

    if my_dept in DEPT_PASSWORDS:
        st.divider()
        if f'auth_{my_dept}' not in st.session_state: st.session_state[f'auth_{my_dept}'] = False
        if not st.session_state[f'auth_{my_dept}']:
            sec_pw = st.text_input("🔐 2차 비밀번호", type="password")
            if st.button("🔑 특수 행정 로그인"):
                if sec_pw == DEPT_PASSWORDS[my_dept]:
                    st.session_state[f'auth_{my_dept}'] = True; st.rerun()
        else:
            st.success(f"🔓 {my_dept} 특수 권한 활성화")
            target_dept = st.selectbox("대상 부처 선택", [d for d in cfg['항목'].tolist() if d not in ['학급총액', '복지금재원']])
            if my_dept == "봉사부":
                wf = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
                st.info(f"✨ 가용 복지금(감면 재원): {int(wf):,}원")
                red = st.number_input("감면액", min_value=0, step=500)
                if st.button("✨ 복지금 감면 수행"):
                    target_fine = cfg.loc[cfg['항목'] == target_dept, '벌금'].values[0]
                    if red <= wf and red <= target_fine:
                        cfg.loc[cfg['항목'] == target_dept, '벌금'] -= float(red)
                        cfg.loc[cfg['항목'] == '복지금재원', '금액'] -= float(red)
                        save_data(cfg, st.session_state.requests)
                        trigger_flash_effect("복지 혜택 적용 완료")
                        st.rerun()
            elif my_dept in ["인성예절부", "선교부"]:
                f_amt = st.number_input("벌금 조정 (+/-)", step=500)
                if st.button("⚖️ 행정 처리 확정"):
                    cfg.loc[cfg['항목'] == target_dept, '벌금'] += float(f_amt)
                    save_data(cfg, st.session_state.requests)
                    trigger_flash_effect("벌금 데이터 기록")
                    st.rerun()
            if st.button("🔓 권한 해제"):
                st.session_state[f'auth_{my_dept}'] = False
                trigger_flash_effect("세션 종료"); st.rerun()

    st.divider()
    with st.form("req_form"):
        st.subheader("💰 운영비 지출 신청")
        item = st.text_input("품목")
        amt = st.number_input("신청 금액", min_value=0, max_value=int(max(0, rem)), step=100)
        if st.form_submit_button("🚀 예산 신청"):
            if item and amt > 0:
                new = {'날짜': datetime.now().strftime("%m-%d %H:%M"), '부처명': my_dept, '항목': item, '금액': float(amt), '상태': '대기'}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
                save_data(cfg, st.session_state.requests)
                st.toast("🚀 신청서 전송", icon="📧")
                time.sleep(0.4); st.rerun()

if st.sidebar.button("🔓 로그아웃"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    trigger_flash_effect("시스템 종료"); st.rerun()
