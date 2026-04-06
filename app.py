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
        # '지출액'은 부처 예산 사용량, '벌금'은 납부할 금액, '복지금'은 봉사부 전용 감면 재원
        config_df = pd.DataFrame({
            '항목': ['학급총액', '복지금재원'] + depts,
            '금액': [0.0] * (len(depts) + 2),
            '지출액': [0.0] * (len(depts) + 2),
            '벌금': [0.0] * (len(depts) + 2)
        })
    # 구 버전 데이터에 '복지금재원' 행이 없는 경우 강제 추가
    if '복지금재원' not in config_df['항목'].values:
        new_row = pd.DataFrame({'항목':['복지금재원'], '금액':[0.0], '지출액':[0.0], '벌금':[0.0]})
        config_df = pd.concat([config_df, new_row], ignore_index=True)
        
    req_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태', '비고'])
    return config_df, req_df

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# 2. UI 스타일 설정
st.set_page_config(page_title="학급 정부 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0F172A !important; border: 2px solid #3B82F6 !important; padding: 15px !important; border-radius: 15px !important; }
    [data-testid="stMetricLabel"] div { color: #94A3B8 !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] div { color: #FDE047 !important; font-size: 1.8rem !important; font-weight: 900 !important; }
    .stButton>button { background-color: #2563EB !important; color: white !important; border-radius: 10px; height: 3.2em; font-weight: bold; width: 100%; }
    .welfare-card { border: 2px solid #10B981; padding: 15px; border-radius: 10px; background-color: #064E3B; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# 3. 로그인
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
all_depts = st.session_state.config[~st.session_state.config['항목'].isin(['학급총액', '복지금재원'])]['항목'].tolist()

# 4. 행정 로직

# [A] 교사 모드
if user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    new_total = st.number_input("학급 총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 총액 확정"):
        st.session_state.config.at[idx, '금액'] = float(new_total)
        save_data(st.session_state.config, st.session_state.requests)
        st.success("저장 완료!"); st.balloons()

# [B] 총무 모드: 복지금 별도 편성 로직 추가
elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    cfg = st.session_state.config
    total_budget = cfg[cfg['항목'] == '학급총액']['금액'].values[0]
    welfare_fund = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
    assigned_sum = cfg[~cfg['항목'].isin(['학급총액', '복지금재원'])]['금액'].sum()
    
    # 가용 잔액 계산 (복지금도 예산의 일부로 취급)
    available = total_budget - assigned_sum - welfare_fund
    
    st.metric("💰 학급 총 예산", f"{int(total_budget):,}원", f"배정 가능 잔액: {int(available):,}원")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"현재 복지금 재원: {int(welfare_fund):,}원")
    with col2:
        # 복지금 편성 UI
        new_welfare = st.number_input("복지금 추가/수정", value=int(welfare_fund), step=500)
        if st.button("🗳️ 복지금 확정"):
            if assigned_sum + new_welfare > total_budget:
                st.error("예산 범위를 초과하여 복지금을 설정할 수 없습니다.")
            else:
                cfg.loc[cfg['항목'] == '복지금재원', '금액'] = float(new_welfare)
                save_data(cfg, st.session_state.requests)
                st.success("복지금 편성 완료!"); st.balloons(); st.rerun()

    st.divider()
    with st.expander("➕ 부처별 예산 배정"):
        target = st.selectbox("부처 선택", all_depts)
        curr_dept_val = cfg.loc[cfg['항목'] == target, '금액'].values[0]
        max_dept_limit = available + curr_dept_val
        new_assign = st.number_input(f"{target} 배정액", value=int(curr_dept_val), min_value=0, step=1000)
        if st.button("📍 예산 배정 저장"):
            if new_assign > max_dept_limit: st.error("잔액 부족!")
            else:
                cfg.loc[cfg['항목'] == target, '금액'] = float(new_assign)
                save_data(cfg, st.session_state.requests)
                st.success("배정 성공!"); st.rerun()

    # 결재 승인 로직 (생략 - 기존 유지)
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        st.warning(f"**[{r['부처명']}]** {r['항목']} ({int(r['금액']):,}원)")
        if st.button("✅ 승인", key=f"app_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            cfg.loc[cfg['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(cfg, st.session_state.requests); st.balloons(); st.rerun()

# [C] 부장 모드: 복지금 한도 내 감면 구속
elif user_role == "부장":
    st.header("🧑‍💻 부처 업무")
    my_dept = st.selectbox("내 부처 선택", all_depts)
    cfg = st.session_state.config
    d = cfg[cfg['항목'] == my_dept].iloc[0]
    
    st.metric("💳 가용 잔액", f"{int(d['금액'] - d['지출액'] - d['벌금']):,}원", f"벌금액: {int(d['벌금']):,}원")

    if my_dept in DEPT_PASSWORDS:
        st.divider()
        if f'auth_{my_dept}' not in st.session_state: st.session_state[f'auth_{my_dept}'] = False
        
        if not st.session_state[f'auth_{my_dept}']:
            sec_pw = st.text_input("🔐 2차 보안 비밀번호", type="password")
            if st.button("🔑 특수 행정 로그인"):
                if sec_pw == DEPT_PASSWORDS[my_dept]:
                    st.session_state[f'auth_{my_dept}'] = True; st.rerun()
                else: st.error("인증 실패")
        else:
            st.success(f"🔓 {my_dept} 권한 활성화됨")
            target_dept = st.selectbox("대상 부처 선택", all_depts)
            
            if my_dept == "봉사부":
                # 복지금 재원 확인
                welfare_fund = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
                st.markdown(f'<div class="welfare-card">✨ 현재 가용 복지금: <b>{int(welfare_fund):,}원</b></div>', unsafe_allow_html=True)
                
                reduction = st.number_input("감면할 벌금액 (복지금에서 차감)", min_value=0, step=500)
                if st.button("✨ 복지금으로 감면 수행"):
                    if reduction > welfare_fund:
                        st.error("🚨 거부: 보유한 복지금 재원을 초과하여 감면할 수 없습니다.")
                    elif reduction > cfg.loc[cfg['항목'] == target_dept, '벌금'].values[0]:
                        st.error("🚨 거부: 대상 부처의 벌금보다 더 많이 감면할 수 없습니다.")
                    else:
                        # 1. 대상 부처 벌금 차감
                        cfg.loc[cfg['항목'] == target_dept, '벌금'] -= float(reduction)
                        # 2. 복지금 재원 소모
                        cfg.loc[cfg['항목'] == '복지금재원', '금액'] -= float(reduction)
                        save_data(cfg, st.session_state.requests)
                        st.success(f"🎉 성공: 복지금을 사용하여 {target_dept}의 벌금을 {reduction:,}원 감면했습니다.")
                        st.balloons()
            
            elif my_dept in ["인성예절부", "선교부"]:
                fine_amt = st.number_input("벌금 조정액 (+부과, -사면)", step=500)
                if st.button("⚖️ 행정 처리 확정"):
                    cfg.loc[cfg['항목'] == target_dept, '벌금'] += float(fine_amt)
                    save_data(cfg, st.session_state.requests)
                    st.success("데이터 업데이트 완료!"); st.balloons()
            
            if st.button("🔓 권한 해제"): st.session_state[f'auth_{my_dept}'] = False; st.rerun()

    st.divider()
    with st.form("req_form"):
        item = st.text_input("품목")
        amt = st.number_input("신청 금액", min_value=0, max_value=int(max(0, d['금액'] - d['지출액'] - d['벌금'])), step=100)
        if st.form_submit_button("🚀 예산 신청"):
            if item and amt > 0:
                new = {'날짜': datetime.now().strftime("%m-%d %H:%M"), '부처명': my_dept, '항목': item, '금액': float(amt), '상태': '대기'}
                st.session_state.requests = pd.concat([st.session_state.requests, pd.DataFrame([new])], ignore_index=True)
                save_data(cfg, st.session_state.requests); st.success("신청 완료!"); st.balloons()

# [D] 감사원 모드
elif user_role == "감사원":
    st.header("🔍 감사 리포트")
    welfare_val = st.session_state.config[st.session_state.config['항목'] == '복지금재원']['금액'].values[0]
    st.info(f"현재 남은 복지금 총액: {int(welfare_val):,}원")
    for _, r in st.session_state.config[~st.session_state.config['항목'].isin(['학급총액', '복지금재원'])].iterrows():
        st.write(f"- {r['항목']}: 배정 {int(r['금액']):,} / 지출 {int(r['지출액']):,} / 벌금 {int(r['벌금']):,}")

# 공통 로그아웃
if st.sidebar.button("🔓 로그아웃"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
