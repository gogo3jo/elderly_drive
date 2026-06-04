import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px

# --- 1. 환경 설정 ---
st.set_page_config(page_title="고령 운전자 정책 분석 대시보드", layout="wide")

# --- 2. DB 연결 및 에러 처리 ---
# 파일명이 'elderly_right.db'라고 가정했습니다. 다르면 수정하세요.
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
        하지만 **'단순히 나이가 많아서 위험한가?'** 혹은 **'면허 반납이 유일한 해결책인가?'** 에 대한 질문에는 데이터로 답해야 합니다.
        """)
        st.info("💡 왼쪽 메뉴를 클릭하여 상세 분석 내용을 확인하세요.")

    # --- [섹션 2: 연령별 사고율 분석] ---
    elif menu == "연령별 사고율 분석":
        st.title("📈 연령대별 사고 위험도 분석")
        
        # 정렬 순서 정의
        age_order = ['19세 이하', '20-29세', '30-39세', '40-49세', '50-59세', '60-64세', '65세 이상']
        
        st.header("1) 연령대별 사고율 비교")
        query1 = """
        SELECT a.age_group, (CAST(a.accident_count AS FLOAT) / b.license_count) * 100 as accident_rate
        FROM 가해운전자 a
        JOIN 면허소지자 b ON a.age_group = b.age_group
        """
        df1 = run_query(query1)
        df1['age_group'] = pd.Categorical(df1['age_group'], categories=age_order, ordered=True)
        df1 = df1.sort_values('age_group')
        
        df1['group'] = df1['age_group'].apply(lambda x: '고령층(60세 이상)' if x in ['60-64세', '65세 이상'] else '기타 연령')
        fig1 = px.bar(df1, x='age_group', y='accident_rate', color='group', 
                      color_discrete_map={'고령층(60세 이상)': 'crimson', '기타 연령': 'lightgray'})
        st.plotly_chart(fig1, use_container_width=True)
        
        st.divider()
        st.subheader("🔍 SQL 및 인사이트")
        st.code(query1, language='sql')
        st.write("- **인사이트**: 19세 이하 운전자의 사고율이 가장 높습니다. 정책 대상인 고령층(60세 이상)의 사고율 추세에 주목해야 합니다.")

        # 2) 고령 vs 비고령 상대 위험도 (65세 이상만 고령운전자)
        st.header("2) 고령 vs 비고령 상대 위험도")
        
        # 1. 데이터 가져오기
        query2 = """
        SELECT a.age_group, a.accident_count, b.license_count
        FROM 가해운전자 a 
        JOIN 면허소지자 b ON a.age_group = b.age_group
        """
        df2 = run_query(query2)
        
        # 2. 파이썬에서 그룹핑 (65세 이상만 고령운전자)
        df2['group_type'] = df2['age_group'].apply(
            lambda x: '고령운전자' if x == '65세 이상' else '비고령운전자'
        )
        
        # 3. 그룹별 합계 계산
        df_grouped = df2.groupby('group_type')[['accident_count', 'license_count']].sum().reset_index()
        df_grouped['rate'] = (df_grouped['accident_count'] / df_grouped['license_count']) * 100
        
        # 4. 상대 위험도 계산 (데이터가 모두 존재하는지 확인)
        try:
            # group_type에 '고령운전자'와 '비고령운전자'가 모두 있는지 확인 후 계산
            elderly = df_grouped.loc[df_grouped['group_type']=='고령운전자', 'rate'].values[0]
            normal = df_grouped.loc[df_grouped['group_type']=='비고령운전자', 'rate'].values[0]
            relative_risk = elderly / normal
            
            # 5. 결과 시각화
            fig2 = px.bar(df_grouped, x='group_type', y='rate', color='group_type',
                          color_discrete_map={'고령운전자': 'crimson', '비고령운전자': 'lightgray'})
            st.plotly_chart(fig2, use_container_width=True)
            
            # 6. 결과 표시
            st.metric("고령층 상대 위험도", f"{relative_risk:.2f} 배")
            st.code(query2, language='sql')
            
        except Exception as e:
            st.error("데이터 계산 오류: 그룹핑된 데이터가 충분하지 않습니다.")
            st.write("상세 정보:", e)


    # --- [섹션 3: 지역별 면허반납 분석] ---

    elif menu == "지역별 면허반납 분석":
        st.title("📍 지역별 면허 반납 정책 현황")
        
        # 1. 데이터 가져오기
        query3 = """
        SELECT a.region, (CAST(a.return_count AS FLOAT) / b.elderly_population) * 100 as return_rate
        FROM 면허반납 a JOIN 인구비 b ON a.region = b.region
        """
        df3 = run_query(query3)

        # 2. 지역명 매핑 (지도 라이브러리와 DB 이름 맞추기)
        # 중요: DB에 있는 region 이름이 여기 키(Key) 값과 같아야 합니다.
                # GeoJSON 파일 내부에 저장된 이름에 맞게 수정
        name_mapping = {
            '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시', 
            '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시', 
            '울산': '울산광역시', '세종': '세종특별자치시', 
            '경기': '경기도', '경기도': '경기도',
            '강원': '강원도', '강원도': '강원도', 
            '충북': '충청북도', '충남': '충청남도', 
            '전북': '전라북도', '전라북도': '전라북도',
            '전남': '전라남도', '경북': '경상북도', 
            '경남': '경상남도', '제주': '제주도'
        }
        df3['region_full'] = df3['region'].map(name_mapping)

        # 3. 지도 시각화
        # 대한민국 시도 경계 GeoJSON 데이터 (온라인 공개 URL)
        geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo.json"
        
        fig = px.choropleth(
            df3,
            geojson=geojson_url,
            locations='region_full',
            featureidkey="properties.name",
            color='return_rate',
            color_continuous_scale="Reds",
            title="시도별 고령 인구 대비 면허 반납율"
        )
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # 나머지 기존 시뮬레이션 코드...
        st.subheader("💡 정책 효과 시뮬레이션")
        # ... (기존 슬라이더 및 success 코드 그대로 유지)

        # 매핑 안 된 지역 확인
        missing = df3[df3['region_full'].isna()]
        st.write("매핑 실패한 지역:", missing)


    # --- [섹션 4: 대중교통과 반납율 관계] ---
    elif menu == "대중교통과 반납율 관계":
        st.title("🚌 대중교통 인프라가 반납율에 미치는 영향")
        query4 = """
        SELECT a.region, (CAST(a.senior AS FLOAT) / b.total_population) as transport_index,
               (CAST(c.return_count AS FLOAT) / b.elderly_population) * 100 as return_rate
        FROM 대중교통 a JOIN 인구비 b ON a.region = b.region
        JOIN 면허반납 c ON a.region = c.region
        """
        df4 = run_query(query4)
        fig4 = px.scatter(df4, x='transport_index', y='return_rate', text='region', trendline="ols")
        st.plotly_chart(fig4, use_container_width=True)

    # --- [섹션 5: 결론 및 정책 제안] ---
    elif menu == "결론 및 정책 제안":
        st.title("🏁 분석 결론 및 정책 제안")
        st.markdown("""
        ### 1. 데이터 분석 요약
        * 고령자 사고 위험성은 실제로 높으며, 대중교통 인프라가 반납율을 결정합니다.
        ### 2. 정책 제안
        * 수요응답형 택시 지원, 이동권 보장 중심의 정책이 필요합니다.
        """)
        st.balloons()