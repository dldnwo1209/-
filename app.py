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
            '항목': ['학급총액', '복지금재원'] + depts,
            '금액': [0.0] * (len(depts) + 2),
            '지출액': [0.0] * (len(depts) + 2),
            '벌금': [0.0] * (len(depts) + 2)
        })
    # 복지금 데이터 행 강제 생성 확인
    if '복지금재원' not in config_df['항목'].values:
        new_row = pd.DataFrame({'항목':['복지금재원'], '금액':[0.0], '지출액':[0.0], '벌금':[0.0]})
        config_df = pd.concat([config_df, new_row], ignore_index=True)
    return config_df, req_df

def save_data(config_df, req_df):
    # 봉사부 금액은 복지금재원과 항상 동기화
    w_val = config_df.loc[config_df['항목'] == '복지금재원', '금액'].values[0]
    config_df.loc[config_df['항목'] == '봉사부', '금액'] = w_val
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# 2. UI 스타일 설정
st.set_page_config(page_title="학급 정부 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0F172A !important; border: 2px solid #3B82F6 !important; padding: 15px !important; border-radius: 15px !important; }
    .stButton>button { background-color: #2563EB !important; color: white !important; border-radius: 10px; height: 3.2em; font-weight: bold; }
    .welfare-highlight { border: 2px solid #10B981; padding: 15px; border-radius: 10px; background-color: #064E3B; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

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
all_depts = [d for d in st.session_state.config['항목'].tolist() if d not in ['학급총액', '복지금재원']]

# 4. 역할별 행정 로직

# [A] 교사 모드 (생략)
if user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    new_total = st.number_input("학급 총 예산 설정", value=int(st.session_state.config.at[idx, '금액']), step=1000)
    if st.button("💾 총액 확정"):
        st.session_state.config.at[idx, '금액'] = float(new_total)
        save_data(st.session_state.config, st.session_state.requests)
        st.success("저장 완료!"); st.balloons()

# [B] 총무 모드: 통합 배정 + 봉사부 특수 로직
elif user_role == "총무":
    st.header("👩‍💼 총무 행정 시스템")
    cfg = st.session_state.config
    total_budget = cfg[cfg['항목'] == '학급총액']['금액'].values[0]
    welfare_fund = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
    
    # 일반 부서(봉사부 제외) 배정액 합계
    normal_assigned = cfg[~cfg['항목'].isin(['학급총액', '복지금재원', '봉사부'])]['금액'].sum()
    available = total_budget - normal_assigned - welfare_fund
    
    st.metric("💰 학급 총 예산", f"{int(total_budget):,}원", f"배정 가능 잔액: {int(available):,}원")

    st.divider()
    st.subheader("➕ 부처별 예산 배정")
    target = st.selectbox("예산을 편성할 부처를 선택하세요", all_depts)
    
    # 💡 핵심 로직: 봉사부 선택 시 UI 변경
    if target == "봉사부":
        st.markdown('<div class="welfare-highlight">', unsafe_allow_html=True)
        st.success("✨ 봉사부는 '복지금' 항목으로 예산을 편성합니다.")
        st.info(f"현재 편성된 복지금: {int(welfare_fund):,}원")
        new_welfare = st.number_input("복지금(봉사부 예산) 책정액", value=int(welfare_fund), min_value=0, step=1000)
        
        if st.button("🗳️ 봉사부 복지금 확정"):
            if normal_assigned + new_welfare > total_budget:
                st.error("🚨 총 예산 한도를 초과할 수 없습니다!")
            else:
                cfg.loc[cfg['항목'] == '복지금재원', '금액'] = float(new_welfare)
                save_data(cfg, st.session_state.requests)
                st.success("봉사부 복지금 편성 완료!"); st.balloons(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # 일반 부서 배정 UI
        curr_dept_val = cfg.loc[cfg['항목'] == target, '금액'].values[0]
        max_limit = available + curr_dept_val
        st.write(f"ℹ️ {target}의 현재 배정액: {int(curr_dept_val):,}원")
        new_assign = st.number_input(f"{target} 새 배정액", value=int(curr_dept_val), min_value=0, step=1000)
        
        if st.button(f"📍 {target} 예산 저장"):
            if new_assign > max_limit: st.error("잔액 부족!")
            else:
                cfg.loc[cfg['항목'] == target, '금액'] = float(new_assign)
                save_data(cfg, st.session_state.requests)
                st.success(f"{target} 배정 성공!"); st.rerun()

    st.divider()
    # 결재 승인 로직 (기존 유지)
    st.subheader("📝 결재 대기 건")
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    if not pending.empty:
        for i, r in pending.iterrows():
            st.warning(f"**[{r['부처명']}]** {r['항목']} ({int(r['금액']):,}원)")
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인", key=f"app_{i}"):
                st.session_state.requests.at[i, '상태'] = '승인'
                cfg.loc[cfg['항목'] == r['부처명'], '지출액'] += r['금액']
                save_data(cfg, st.session_state.requests); st.balloons(); st.rerun()
            if c2.button("❌ 반려", key=f"rej_{i}"):
                st.session_state.requests.at[i, '상태'] = '반려'
                save_data(cfg, st.session_state.requests); st.rerun()

# [C] 부장 모드 (기존 복지금 감면 로직 유지)
elif user_role == "부장":
    st.header("🧑‍💻 부처 행정")
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
            target_dept = st.selectbox("대상 부처 선택", [d for d in cfg['항목'].tolist() if d not in ['학급총액', '복지금재원']])
            
            if my_dept == "봉사부":
                welfare_fund = cfg[cfg['항목'] == '복지금재원']['금액'].values[0]
                st.info(f"✨ 현재 가용 복지금: {int(welfare_fund):,}원")
                reduction = st.number_input("감면할 벌금액 (복지금에서 차감)", min_value=0, step=500)
                if st.button("✨ 복지금으로 감면 수행"):
                    target_fine = cfg.loc[cfg['항목'] == target_dept, '벌금'].values[0]
                    if reduction > welfare_fund: st.error("🚨 복지금 재원 부족!")
                    elif reduction > target_fine: st.error("🚨 벌금보다 많이 감면할 수 없습니다.")
                    else:
                        cfg.loc[cfg['항목'] == target_dept, '벌금'] -= float(reduction)
                        cfg.loc[cfg['항목'] == '복지금재원', '금액'] -= float(reduction)
                        save_data(cfg, st.session_state.requests)
                        st.success("🎉 감면 성공!"); st.balloons(); st.rerun()
            
            elif my_dept in ["인성예절부", "선교부"]:
                fine_amt = st.number_input("벌금 조정액 (+부과, -사면)", step=500)
                if st.button("⚖️ 행정 처리 확정"):
                    cfg.loc[cfg['항목'] == target_dept, '벌금'] += float(fine_amt)
                    save_data(cfg, st.session_state.requests)
                    st.success("업데이트 완료!"); st.balloons()
            
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

# [D] 감사원 모드 (생략)
elif user_role == "감사원":
    st.header("🔍 감사 리포트")
    welfare_val = st.session_state.config[st.session_state.config['항목'] == '복지금재원']['금액'].values[0]
    st.info(f"현재 남은 복지금 총액: {int(welfare_val):,}원")
    for _, r in st.session_state.config[~st.session_state.config['항목'].isin(['학급총액', '복지금재원'])].iterrows():
        st.write(f"- {r['항목']}: 배정 {int(r['금액']):,} / 지출 {int(r['지출액']):,} / 벌금 {int(r['벌금']):,}")

# 로그아웃
if st.sidebar.button("🔓 로그아웃"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
