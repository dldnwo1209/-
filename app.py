import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# 1. 환경 설정 및 데이터 로드 (기존 동일)
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
    if '복지금재원' not in config_df['항목'].values:
        new_row = pd.DataFrame({'항목':['복지금재원'], '금액':[0.0], '지출액':[0.0], '벌금':[0.0]})
        config_df = pd.concat([config_df, new_row], ignore_index=True)
    return config_df, pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=['날짜', '부처명', '항목', '금액', '상태'])

def save_data(config_df, req_df):
    config_df.to_csv(DB_CONFIG, index=False)
    req_df.to_csv(LOG_FILE, index=False)

# 💡 2. 화면 점멸(Flash) 애니메이션 정의
def trigger_flash_effect():
    # CSS 애니메이션 주입 (배경색이 0.5초 동안 흰색/밝은 파랑으로 반짝임)
    flash_html = """
        <style>
        @keyframes flash {
            0% { background-color: transparent; }
            50% { background-color: rgba(255, 255, 255, 0.15); }
            100% { background-color: transparent; }
        }
        .stApp {
            animation: flash 0.5s ease-out;
        }
        </style>
    """
    st.markdown(flash_html, unsafe_allow_html=True)
    st.toast("✅ 처리 완료", icon="✔")
    time.sleep(0.1) # 애니메이션이 보일 짧은 시간 확보

if 'config' not in st.session_state:
    st.session_state.config, st.session_state.requests = load_data()

# 3. UI 기본 스타일
st.set_page_config(page_title="학급 정부 시스템", layout="centered")
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #1E293B !important; border-radius: 8px !important; border-left: 4px solid #3B82F6 !important; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 학급 정부 시스템")

# 4. 로그인 (이펙트 제외)
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

# 5. 행정 로직 (모든 버튼에 trigger_flash_effect 적용)

if user_role == "교사":
    st.header("👨‍🏫 교사 관리")
    idx = cfg.index[cfg['항목'] == '학급총액'][0]
    new_total = st.number_input("학급 총 예산 설정", value=int(cfg.at[idx, '금액']), step=1000)
    if st.button("💾 총액 확정"):
        cfg.at[idx, '금액'] = float(new_total)
        save_data(cfg, st.session_state.requests)
        trigger_flash_effect() # ✨ 화면 점멸
        st.rerun()

elif user_role == "총무":
    st.header("👩‍💼 총무 행정")
    target = st.selectbox("편성 부처 선택", all_depts)
    
    if target == "봉사부":
        new_op = st.number_input("봉사부 운영비", value=int(cfg.loc[cfg['항목'] == '봉사부', '금액'].values[0]))
        new_wf = st.number_input("감면용 복지금", value=int(cfg[cfg['항목'] == '복지금재원']['금액'].values[0]))
        if st.button("🗳️ 봉사부 예산 전액 확정"):
            cfg.loc[cfg['항목'] == '봉사부', '금액'] = float(new_op)
            cfg.loc[cfg['항목'] == '복지금재원', '금액'] = float(new_wf)
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect() # ✨ 화면 점멸
            st.rerun()
    else:
        new_val = st.number_input(f"{target} 배정액", value=int(cfg.loc[cfg['항목'] == target, '금액'].values[0]))
        if st.button(f"📍 {target} 예산 저장"):
            cfg.loc[cfg['항목'] == target, '금액'] = float(new_val)
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect() # ✨ 화면 점멸
            st.rerun()

    # 결재 승인
    pending = st.session_state.requests[st.session_state.requests['상태'] == '대기']
    for i, r in pending.iterrows():
        if st.button(f"✅ {r['부처명']} 승인", key=f"app_{i}"):
            st.session_state.requests.at[i, '상태'] = '승인'
            cfg.loc[cfg['항목'] == r['부처명'], '지출액'] += r['금액']
            save_data(cfg, st.session_state.requests)
            trigger_flash_effect() # ✨ 화면 점멸
            st.rerun()

elif user_role == "부장":
    my_dept = st.selectbox("내 부처 선택", all_depts)
    # ... (가용 잔액 표시 등 기존 로직 생략)

    if my_dept in DEPT_PASSWORDS:
        if st.session_state.get(f'auth_{my_dept}'):
            # 특수 행정 버튼들
            if st.button("✨ 복지금 감면 수행") or st.button("⚖️ 행정 처리 확정"):
                # (중략: 데이터 처리 로직)
                trigger_flash_effect() # ✨ 화면 점멸
                st.rerun()
            
            if st.button("🔓 권한 해제"):
                st.session_state[f'auth_{my_dept}'] = False
                trigger_flash_effect() # ✨ 화면 점멸
                st.rerun()

    # 예산 신청 폼 (Form은 버튼 클릭 시 자동 반영되므로 Toast 위주)
    with st.form("req_form"):
        if st.form_submit_button("🚀 예산 신청"):
            # (중략: 데이터 추가 로직)
            save_data(cfg, st.session_state.requests)
            st.toast("🚀 신청 완료", icon="📧")
            time.sleep(0.4)
            st.rerun()

# 로그아웃
if st.sidebar.button("🔓 로그아웃"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    trigger_flash_effect() # ✨ 화면 점멸
    st.rerun()
