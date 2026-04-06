import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# 1. 환경 설정 및 데이터 엔진
DB_CONFIG = 'config_v4.csv'
LOG_FILE = 'transactions_v4.csv'
PASSWORDS = {"교사": "1209", "총무": "1357", "부장": "2468", "감사원": "1111"}
DEPT_PASSWORDS = {"인성예절부": "24278", "봉사부": "848", "선교부": "398"}

def load_data():
    depts = ['여당(회장)', '야당(회장)', '감찰부(서기)', '총무부', '인성예절부', '환경부', '체육부', '교육부', '발명부', '선교부', '봉사부']
    if os.path.exists(DB_CONFIG):
        config_df = pd.read_csv(DB_CONFIG)
    else:
        config_df = pd.DataFrame({
            '항목': ['학급총액', '복지금재원'] + depts,
            '금액': [0.0] * (len(depts) + 2),
            '지출액': [0.0] * (len(depts) + 2),
            '벌금': [0.0] * (len(depts) + 2)
        })
    if '복지금재원' not in config_df['항목'].values:
        new_row = pd.DataFrame({'항목':['복지금재원'], '금액':[0.0], '지출액':[0.0], '벌금':[0.0]})
        config_df = pd.concat([config_df, new_row], ignore_index=True)
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

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
st.set_page_config(page_title="학급 정부 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #1E293B !important; border-radius: 12px !important; border-left: 5px solid #3B82F6 !important; padding: 15px !important; }
    .welfare-card { border: 2px solid #10B981; padding: 15px; border-radius: 10px; background-color: #064E3B; margin-bottom: 20px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; transition: 0.2s; }
    .reset-box { border: 1px solid #EF4444; padding: 20px; border-radius: 10px; background-color: #450a0a; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 행정 시스템")

# 3. 로그인 시스템
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
all_depts = [d for d in cfg['항목'].tolist() if d not in ['학급총액', '복지금재원']]

# 4. 역할별 행정 로직

# [A] 교사 모드: 전체 예산 통제 및 월간 초기화
if user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    total_val = cfg[cfg['항목'] == '학급총액']['금액'].values[0]
    st.metric("💰 현재 설정된 학급 총액", f"{int(total_val):,}원")
    
    new_total = st.number_input("학급 총 예산 수정", value=int(total_val), step=1000)
    if st.button("💾 총액 확정"):
        cfg.loc[cfg['항목'] == '학급총액', '금액'] = float(new_total)
        save_data(cfg, st.session_state.requests)
        trigger_flash_effect("학급 총액 설정 완료")
        st.rerun()

    # ✨ 추가: 월간 초기화 기능
    st.markdown('<div class="reset-box">', unsafe_allow_html=True)
    st.subheader("🚨 월간 행정 데이터 초기화")
    st.write("새로운 달의 예산 편성을 위해 **지출액, 벌금, 신청 로그**를 모두 삭제합니다.")
    st.warning("이 작업은 되돌릴 수 없습니다. 모든 부서의 잔액이 배정액(금액) 상태로 복구됩니다.")
    
    if st.button("⚠️ 모든 부서 데이터 초기화 수행"):
        # 1. 지출액 및 벌금 0으로 초기화 (학급총액, 복지금재원 포함 전 항목)
        cfg['지출액'] = 0.0
        cfg['벌금'] = 0.0
        # 2. 지출 신청 이력 삭제
        st.session_state.requests = pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태'])
        # 3. 데이터 저장
        save_data(cfg, st.session_state.requests)
        trigger_flash_effect("새로운 달을 위해 모든 데이터가 초기화되었습니다!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# [B] 총무 모드: 배정 잔액 집중형 대시보드
elif user_role == "총무":
    st.header("👩‍💼 총무 행정 시스템")
    total_budget = cfg[cfg['항목'] == '학급총액']['금액'].values[0]
    wf_fund = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
    assigned_sum = cfg[cfg['항목'].isin(all_depts)]['금액'].sum()
    available = total_budget - assigned_sum - wf_fund
    
    st.metric("⚖️ 배정 가능 잔액 (복지금 제외)", f"{int(available):,}원", f"총 예산: {int(total_budget):,}원")
    st.divider()
    
    target = st.selectbox("예산 편성 부처 선택", all_depts)
    if target == "봉사부":
        st.markdown('<div class="welfare-card">', unsafe_allow_html=True)
        st.subheader("🍃 봉사부 운영비 및 복지금 배정")
        curr_op = cfg.loc[cfg['항목'] == '봉사부', '금액'].values[0]
        v1 = st.number_input("봉사부 운영비 (부서 활동용)", value=int(curr_op), step=1000)
        v2 = st.number_input("복지금 재원 (벌금 감면용 공금)", value=int(wf_fund), step=1000)
        if st.button("🗳️ 봉사부 이중 예산 확정"):
            cfg.loc[cfg['항목'] == '봉사부', '금액'] = float(v1)
            cfg.loc[cfg['항목'] == '복지금재원', '금액'] = float(v2)
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect("봉사부 예산 편성 완료")
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

    st.subheader("📝 결재 대기")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        if st.button(f"✅ {r['부처명']} {r['항목']} 승인", key=f"app_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            cfg.loc[cfg['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect("지출 승인 완료"); st.rerun()

# [C] 부장 모드: 잔액 + 봉사부 전용 복지금 대시보드
elif user_role == "부장":
    st.header("🧑‍💻 부처 업무")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    d = cfg[cfg['항목'] == my_dept].iloc[0]
    rem = d['금액'] - d['지출액'] - d['벌금']
    st.metric(f"💳 {my_dept} 가용 운영비", f"{int(rem):,}원", f"미납 벌금: {int(d['벌금']):,}원", delta_color="inverse")

    if my_dept in DEPT_PASSWORDS:
        st.divider()
        if not st.session_state.get(f'auth_{my_dept}'):
            sec_pw = st.text_input("🔐 2차 보안 비밀번호", type="password")
            if st.button("🔑 특수 행정 로그인"):
                if sec_pw == DEPT_PASSWORDS[my_dept]:
                    st.session_state[f'auth_{my_dept}'] = True; st.rerun()
        else:
            st.success(f"🔓 {my_dept} 특수 권한 활성화")
            if my_dept == "봉사부":
                st.markdown('<div class="welfare-card">', unsafe_allow_html=True)
                wf = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
                st.metric("✨ 현재 가용 복지금 (벌금 감면용)", f"{int(wf):,}원")
                target_dept = st.selectbox("감면 대상 부처", [d for d in all_depts if d != "봉사부"])
                red = st.number_input("감면할 벌금액", min_value=0, step=500)
                if st.button("✨ 복지금 감면 수행"):
                    t_fine = cfg.loc[cfg['항목'] == target_dept, '벌금'].values[0]
                    if red <= wf and red <= t_fine:
                        cfg.loc[cfg['항목'] == target_dept, '벌금'] -= float(red)
                        cfg.loc[cfg['항목'] == '복지금재원', '금액'] -= float(red)
                        save_data(cfg, st.session_state.requests)
                        trigger_flash_effect("복지 감면 성공"); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            elif my_dept in ["인성예절부", "선교부"]:
                target_dept = st.selectbox("벌금 조정 대상", all_depts)
                f_amt = st.number_input("벌금 조정 (+/-)", step=500)
                if st.button("⚖️ 행정 처리 확정"):
                    cfg.loc[cfg['항목'] == target_dept, '벌금'] += float(f_amt)
                    save_data(cfg, st.session_state.requests)
                    trigger_flash_effect("벌금 데이터 기록 완료"); st.rerun()
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
                st.toast("신청 완료", icon="📧"); time.sleep(0.4); st.rerun()

# [D] 감사원 모드: 전체 현황 및 로그 감사
elif user_role == "감사원":
    st.header("🔍 감사원 행정업무")
    st.subheader("📊 부처별 재무 현황")
    summary_df = cfg[cfg['항목'].isin(all_depts)].copy()
    summary_df['가용잔액'] = summary_df['금액'] - summary_df['지출액'] - summary_df['벌금']
    st.table(summary_df[['항목', '금액', '지출액', '벌금', '가용잔액']].style.format(precision=0))
    
    st.divider()
    st.subheader("📜 지출 및 신청 이력 (최근순)")
    if not st.session_state.requests.empty:
        log_display = st.session_state.requests.iloc[::-1]
        st.dataframe(log_display, use_container_width=True)
    else:
        st.write("기록된 지출 내역이 없습니다.")

# 공통 로그아웃
if st.sidebar.button("🔓 시스템 로그아웃"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    trigger_flash_effect("로그아웃 완료"); st.rerun()
