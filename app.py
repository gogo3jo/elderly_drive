import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px

# --- 1. 환경 설정 ---
st.set_page_config(page_title="고령 운전자 정책 분석 대시보드", layout="wide")

# --- 2. DB 연결 및 에러 처리 ---
DB_FILE = 'drive.db'

def get_connection():
    if not os.path.exists(DB_FILE):
        return None
    return sqlite3.connect(DB_FILE)

def run_query(query):
    conn = get_connection()
    if conn is None:
        return None
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- 3. 사이드바 구성 ---
st.sidebar.title("📊 분석 목차")
menu = st.sidebar.radio(
    "보고서 섹션",
    ["서론: 문제 정의", "연령별 사고율 분석", "지역별 면허반납 분석", "대중교통과 반납율 관계", "결론 및 정책 제안"]
)

# DB 파일 존재 여부 체크
if not os.path.exists(DB_FILE):
    st.error(f"🚨 '{DB_FILE}' 파일이 같은 폴더에 없습니다. 데이터베이스 파일을 확인해주세요.")
else:
    # --- [섹션 1: 서론] ---
    if menu == "서론: 문제 정의":
        st.title("👵 고령 운전자 사고 위험과 면허 반납 정책의 실효성")
        st.subheader("사회적 인식과 데이터의 괴리")
        st.markdown("""
        최근 고령 운전자 사고가 연일 보도되면서 사회적 불안감이 커지고 있습니다. 
        하지만 **'단순히 나이가 많아서 위험한가?'** 혹은 **'면허 반납이 유일한 해결책인가?'**에 대한 질문에는 데이터로 답해야 합니다.
        
        본 대시보드는 다음의 흐름을 따릅니다:
        1. **위험 진단**: 연령대별 실제 사고율 비교
        2. **정책 점검**: 지자체별 면허 반납 정책의 성과
        3. **대안 모색**: 대중교통 인프라가 반납에 미치는 영향
        """)
        st.info("💡 왼쪽 메뉴를 클릭하여 상세 분석 내용을 확인하세요.")

    # --- [섹션 2: 연령별 사고율 분석] ---
    elif menu == "연령별 사고율 분석":
        st.title("📈 연령대별 사고 위험도 분석")
        
        # 1. 연령대별 사고율
        st.header("1) 연령대별 사고율 비교")
        query1 = """
        SELECT a.age_group, 
               (CAST(a.accident_count AS FLOAT) / b.license_count) * 100 as accident_rate
        FROM 가해운전자 a
        JOIN 면허소지자 b ON a.age_group = b.age_group
        ORDER BY accident_rate DESC
        """
        df1 = run_query(query1)
        
        fig1 = px.bar(df1, x='age_group', y='accident_rate', color='accident_rate',
                     title="면허 소지자 100명당 사고 건수", labels={'accident_rate':'사고율(%)'},
                     color_continuous_scale='Reds')
        st.plotly_chart(fig1, use_container_width=True)
        
        with st.expander("🔍 SQL 및 인사이트"):
            st.code(query1, language='sql')
            st.write("- **인사이트**: 단순 사고 건수가 아닌 면허 소지자 대비 비율을 보았을 때, 특정 연령대(고령층)의 사고 확률이 상대적으로 높은지 한눈에 파악할 수 있습니다.")

        # 2. 상대 위험도
        st.header("2) 고령 vs 비고령 상대 위험도")
        query2 = """
        SELECT 
            CASE WHEN age_group IN ('65세-69세', '70세-74세', '75세-79세', '80세-84세', '85세이상') THEN '고령운전자'
            ELSE '비고령운전자' END as group_type,
            SUM(accident_count) as total_acc,
            SUM(license_count) as total_lic
        FROM (SELECT a.age_group, a.accident_count, b.license_count 
              FROM 가해운전자 a JOIN 면허소지자 b ON a.age_group = b.age_group)
        GROUP BY group_type
        """
        df2 = run_query(query2)
        df2['rate'] = (df2['total_acc'] / df2['total_lic']) * 100
        
        elderly_rate = df2.loc[df2['group_type']=='고령운전자', 'rate'].values[0]
        normal_rate = df2.loc[df2['group_type']=='비고령운전자', 'rate'].values[0]
        relative_risk = elderly_rate / normal_rate

        fig2 = px.pie(df2, values='rate', names='group_type', title="집단별 평균 사고율 비중", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
        
        st.metric("고령층 상대 위험도", f"{relative_risk:.2f} 배", help="비고령층 사고율 대비 고령층의 사고율")
        
        with st.expander("🔍 SQL 및 인사이트"):
            st.code(query2, language='sql')
            st.write(f"- **인사이트**: 고령 운전자의 사고 위험도가 비고령자보다 약 **{relative_risk:.2f}배** 높게 나타납니다. 이는 집중 관리가 필요함을 시사합니다.")

    # --- [섹션 3: 지역별 면허반납 분석] ---
    elif menu == "지역별 면허반납 분석":
        st.title("📍 지역별 면허 반납 정책 현황")
        
        query3 = """
        SELECT a.region, 
               (CAST(a.return_count AS FLOAT) / b.elderly_population) * 100 as return_rate
        FROM 면허반납 a
        JOIN 인구비 b ON a.region = b.region
        ORDER BY return_rate DESC
        """
        df3 = run_query(query3)
        
        fig3 = px.bar(df3, x='region', y='return_rate', color='return_rate',
                     title="지역별 고령 인구 대비 면허 반납율(%)", color_continuous_scale='GnBu')
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("💡 정책 효과 시뮬레이션")
        st.write("서울시 사례(반납율 1%p↑ → 사고 200건↓)를 적용한 예상치입니다.")
        target = st.slider("목표 반납율 추가 달성치(%p)", 0.0, 5.0, 1.0)
        expected_reduction = target * 200
        st.success(f"전국 반납율이 현재보다 {target}%p 높아지면, 연간 고령자 사고를 약 {expected_reduction:,.0f}건 예방할 수 있습니다.")

        with st.expander("🔍 SQL 및 인사이트"):
            st.code(query3, language='sql')
            st.write("- **인사이트**: 지역별로 반납율 편차가 큽니다. 반납율이 높은 지역의 벤치마킹이 필요하며, 낮은 지역은 그 원인을 분석해야 합니다.")

    # --- [섹션 4: 대중교통과 반납율 관계] ---
    elif menu == "대중교통과 반납율 관계":
        st.title("🚌 대중교통 인프라가 반납율에 미치는 영향")
        
        query4 = """
        SELECT a.region,
               (CAST(a.senior AS FLOAT) / b.total_population) as transport_index,
               (CAST(c.return_count AS FLOAT) / b.elderly_population) * 100 as return_rate
        FROM 대중교통 a
        JOIN 인구비 b ON a.region = b.region
        JOIN 면허반납 c ON a.region = c.region
        """
        df4 = run_query(query4)
        
        fig4 = px.scatter(df4, x='transport_index', y='return_rate', text='region',
                         title="대중교통 이용 수준 vs 면허 반납율 상관관계",
                         trendline="ols", labels={'transport_index':'대중교통 이용지표', 'return_rate':'면허 반납율(%)'})
        st.plotly_chart(fig4, use_container_width=True)
        
        corr = df4['transport_index'].corr(df4['return_rate'])
        st.info(f"분석 결과: 대중교통 지표와 면허 반납율 간의 상관계수는 **{corr:.2f}**입니다.")

        with st.expander("🔍 SQL 및 인사이트"):
            st.code(query4, language='sql')
            st.write("- **인사이트**: 상관관계가 높게 나타난다면, **'운전대를 놓아도 이동할 수 있는 환경'**이 조성되어야 면허 반납 정책이 성공할 수 있음을 입증합니다.")

    # --- [섹션 5: 결론 및 정책 제안] ---
    elif menu == "결론 및 정책 제안":
        st.title("🏁 분석 결론 및 정책 제안")
        
        st.markdown("""
        ### 1. 데이터 분석 요약
        *   **고령자 사고 위험성**: 비고령자 대비 사고율이 높은 것은 사실이나, 연령대별로 위험도가 다름.
        *   **반납 정책의 실효성**: 반납율이 높을수록 사고 감소 효과가 뚜렷함(서울시 사례 기반).
        *   **결정적 요인**: 대중교통 이용이 편리한 지역일수록 고령 운전자의 면허 반납이 활발함.

        ### 2. 정책 제안
        *   **[인프라 강화]** 농어촌 등 대중교통 취약 지역은 면허 반납 시 '수요응답형 택시(마을택시)' 쿠폰 지원 확대.
        *   **[타겟팅 홍보]** 상대적 사고 위험도가 급격히 높아지는 75세 이상 구간에 대한 집중 반납 캠페인 실시.
        *   **[인센티브 다양화]** 단순 일회성 현금 지원보다는 지속적인 '교통 복지 포인트' 형태로 전환하여 이동권 보장.
        """)
        st.balloons()