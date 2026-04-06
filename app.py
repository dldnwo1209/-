# --- [감사원 모드] 수정 부분 ---
elif user_role == "감사원":
    st.header("🔍 학급 공수처 감찰 시스템")
    
    # 1. 요약 메트릭 (전체 현황)
    total_idx = st.session_state.config.index[st.session_state.config['항목'] == '학급총액'][0]
    total_val = st.session_state.config.at[total_idx, '금액']
    total_spent = st.session_state.config[st.session_state.config['항목'] != '학급총액']['지출액'].sum()
    total_fine = st.session_state.config[st.session_state.config['항목'] != '학급총액']['벌금'].sum()

    c1, c2 = st.columns(2)
    c1.metric("전체 지출액", f"{int(total_spent):,}원")
    c2.metric("전체 미납 벌금", f"{int(total_fine):,}원", delta_color="inverse")
    
    st.divider()

    # 2. 부처별 상세 현황 (카드형)
    st.subheader("📋 부처별 세부 현황")
    report_data = st.session_state.config[st.session_state.config['항목'] != '학급총액']
    
    for _, r in report_data.iterrows():
        with st.expander(f"📍 {r['항목']} ({int(r['지출액']):,}원 사용)"):
            st.write(f"**배정 예산:** {int(r['금액']):,}원")
            st.write(f"**현재 잔액:** {int(r['금액'] - r['지출액'] - r['벌금']):,}원")
            if r['벌금'] > 0:
                st.error(f"**미납 벌금:** {int(r['벌금']):,}원")
            
            # 해당 부처의 최근 기록만 필터링해서 보여주기
            dept_logs = st.session_state.requests[st.session_state.requests['부처명'] == r['항목']].iloc[::-1]
            if not dept_logs.empty:
                st.caption("최근 신청 내역")
                for _, log in dept_logs.head(3).iterrows():
                    st.text(f"- {log['날짜']} {log['항목']} ({log['상태']})")
            else:
                st.caption("신청 내역 없음")

    st.divider()

    # 3. 전체 거래 로그 (최신순)
    st.subheader("📜 전체 행정 로그")
    if not st.session_state.requests.empty:
        # 모바일에서는 표보다 텍스트 리스트가 훨씬 읽기 좋습니다.
        for i, row in st.session_state.requests.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"**{row['날짜']} | {row['부처명']}**")
                st.write(f"항목: {row['항목']} / 금액: {int(row['금액']):,}원")
                status_color = "🟢" if row['상태'] == "승인" else "🔴" if row['상태'] == "반려" else "🟡"
                st.write(f"상태: {status_color} {row['상태']}")
                st.write("---")
    else:
        st.info("기록된 로그가 없습니다.")
