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
        st.title("👵 운전대를 놓은 노인은 어디로 갈 수 있을까?")
        st.subheader("언론과 대중은 고령 운전자 사고라는 결과만 보고 **운전하지 말라** 고 한다.")
        st.markdown("""
        그렇다면 고령 운전자는 실제로 위험한가? 
        위험하다면, 왜 고령 운전자는 위험을 알면서 운전대를 놓지 못하는가? 
        노인 운전은 그들의 이동권에 직결되지 않는가? 
        이동권을 대체할 대중교통 인프라는 충분한가? 
        
        최근 고령 운전자 사고가 연일 보도되면서 사회적 불안감이 커지고 있습니다. 
        하지만 **'단순히 나이가 많아서 위험한가?'** 혹은 **'면허 반납이 유일한 해결책인가?'** 에 대한 질문에는 데이터로 답해야 합니다.
        
        **가설: 노인 운전은 그들의 이동권을 대체할 대중교통 인프라가 부족하기 때문이다.**
        
        **연구 목적: 본 프로젝트는 지역별 면허 반납율과 대중교통 이용 데이터의 상관관계를 분석하여 정책이 성공하기 위해 선행되어야 할 구조적 교통 환경을 도출하고자 한다.**
        """)
        st.write("")
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
        st.plotly_chart(fig1, use_container_width=True, key="age_accident_chart")
        
        st.markdown("**사용된 SQL 쿼리**")
        st.code(query1, language='sql')

        # 그래프와 SQL 아래에 전체 인사이트 배치
        st.markdown("**분석 인사이트**")
        st.info("""
        - 분석 결과, 연령대별 사고율은 1등 19세이하, 2등 65세 이상, 3등 60-64세로 19세 이하 집단을 제외하면 40-49세부터  연령이 증가할 수록 사고율이 상승하는 것으로 나타났다. 19세 이하의 집단의 사고율은 운전미숙과 초보운전 비율 등이 영향을 준 것으로 해석가능하다.
        """)

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

            st.markdown("**분석 인사이트**")
            st.info("""
            - 운전자 집단을 고령운전자(60세 이상)와 비고령운전자(60세 미만)로 구분하여 다음과 같이 나타냈다. (고령층 사고율/비고령층 사고율)로 상대 위험도를 산출할 수 있다. 분석결과 고령운전자의 사고율은 약 0.84, 비고령운전자의 사고율은 약 0.59로, 고령운전자의 사고율이 비고령운전자보다 약 1.42배 높게 나타난다.
            - 따라서 사회문제로 대두되는 고령운전자 운전 미숙이 단순 편견과 오해가 아니라 고령운전자의 인지능력 저하 및 신체 기능 저하로 발생할 수 있는 실제 통계임을 확인할 수 있다.
            """)
            
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

        # 2. 지역명 매핑 
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
            color_continuous_scale="Blues",
            title="시도별 고령 인구 대비 면허 반납율"
        )
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # 상위/하위 지역 정보 요약
        st.subheader("📊 지역별 반납율 상세 현황")
        
        # 데이터 정렬 (결측치 제외)
        sorted_df = df3.dropna(subset=['return_rate']).sort_values('return_rate', ascending=False)
        
        # 컬럼 분할 (상위/하위)
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("🏆 **상위 반납율 지역 (Top 3)**")
            st.table(sorted_df[['region', 'return_rate']].head(3).reset_index(drop=True).style.format({"return_rate": "{:.2f}%"}))
            
        with col2:
            st.write("⚠️ **하위 반납율 지역 (Bottom 3)**")
            st.table(sorted_df[['region', 'return_rate']].tail(3).reset_index(drop=True).style.format({"return_rate": "{:.2f}%"}))


        st.subheader("🔍 SQL 및 인사이트")
        st.code(query3, language='sql')
        st.write("""
        - 지도 시각화 해석: 고령 인구 대비 면허 반납 성과가 높을 수록 색이 진할수록 면허반납 정책 참여도가 각 지역에서 높다는 의미이다. 면허반납율은 최대 1.4%로 부산이 가장 높고, 뒤이어 서울과 대구가 있다. 반대로 하위 반납율 지역은 광주, 세종, 전남으로 최저 0.72%이다. 지역별로 반납율 편차가 크므로 통계의 요인을 찾아야 할 필요성이 있다.
        - 서울연구원에 따르면, 운전면허 자진반납률이 1%p 증가할 경우 고령운전자 교통사고는 평균 0.02%p 감소하는 것으로 확인됐다. 이를 토대로 정책 효과를 시뮬레이션하면, 전국 면허 반납율이 현재보다 1.0%p 높아지면, 연간 고령자 사고를 약 200건 예방할 수 있다.
        """)


        # 4. 정책 효과 시뮬레이션
        st.subheader("💡 정책 효과 시뮬레이션")
        st.write("서울시 사례(반납율 1%p↑ → 사고 200건↓)를 적용한 예상치입니다.")
        target = st.slider("목표 반납율 추가 달성치(%p)", 0.0, 5.0, 1.0)
        expected_reduction = target * 200
        st.success(f"전국 반납율이 현재보다 {target}%p 높아지면, 연간 고령자 사고를 약 {expected_reduction:,.0f}건 예방할 수 있습니다.")

        # --- [섹션 4: 대중교통과 반납율 관계] ---
    elif menu == "대중교통과 반납율 관계":
        st.title("🚌 대중교통 인프라 vs 면허 반납율")
        
        # 1. 데이터 가져오기 및 데이터프레임 생성 (df4를 df로 통일)
        query = """
        SELECT a.region, a.senior, b.total_population, b.elderly_population, c.return_count 
        FROM 대중교통 a 
        JOIN 인구비 b ON a.region = b.region 
        JOIN 면허반납 c ON a.region = c.region
        """
        df = run_query(query)
        df['transport_index'] = df['senior'] / df['total_population']
        df['return_rate'] = (df['return_count'] / df['elderly_population']) * 100
        
        # 2. 산점도 분석
        st.subheader("상관관계 분석")
        fig_scatter = px.scatter(df, x='transport_index', y='return_rate', text='region', 
                                 title="대중교통 이용 수준 vs 면허 반납율", trendline="ols")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.subheader("🔍 SQL 및 인사이트")
        query_text = """
        SELECT a.region, a.senior, b.total_population, b.elderly_population, c.return_count 
        FROM 대중교통 a JOIN 인구비 b ON a.region = b.region JOIN 면허반납 c ON a.region = c.region
        """
        st.code(query_text, language='sql')
        st.write("""
        - 그래프의 추세선이 우상향하고 있어, 대중교통이용 수준이 높을수록 면허반납률도 높아지는 경향을 보인다. 즉, 버스나 지하철 등 대중교통 접근성이 좋은 지역일수록 고령자가 운전을 포기하기 쉬운것으로 해석된다. 다만 대중교통 이용성이 낮은 지역의 반납률은 상관관계가 다소 부족한 것으로 보이는데, 이는 면허반납의 정책이 지자체별로 상이하고 지역별 교통안전 정책들이 영향을 끼친 것으로 분석했다. 반대로 대중교통 이용성이 높은 서울, 부산, 대구 등은 다른 지역들에 비해 상대적으로 높은 면허반납률을 보인다.
        """)

        st.divider()

        # 3. 지도 시각화 (공간적 분포 비교)
        st.subheader("공간적 분포 비교")
        name_mapping = {
            '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시', 
            '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시', 
            '울산': '울산광역시', '세종': '세종특별자치시', 
            '경기': '경기도', '경기도': '경기도', # 두 경우 모두 '경기도'로 매핑
            '강원': '강원도', '강원도': '강원도', 
            '충북': '충청북도', '충남': '충청남도', 
            '전북': '전라북도', '전라북도': '전라북도',
            '전남': '전라남도', '경북': '경상북도', 
            '경남': '경상남도', '제주': '제주도'
        }
        df['region_full'] = df['region'].map(name_mapping)
        
        col1, col2 = st.columns(2)
        geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo.json"
        
        with col1:
            st.write("#### 🚌 대중교통 이용 지표")
            fig1 = px.choropleth(df, geojson=geojson_url, locations='region_full', featureidkey="properties.name",
                                 color='transport_index', color_continuous_scale="Greens")
            fig1.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            st.write("#### 📍 면허 반납율")
            fig2 = px.choropleth(df, geojson=geojson_url, locations='region_full', featureidkey="properties.name",
                                 color='return_rate', color_continuous_scale="Blues")
            fig2.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig2, use_container_width=True)
            
        st.info("💡 두 지도의 색상 패턴이 일치할수록 대중교통과 면허 반납이 밀접한 관련이 있음을 시사합니다.")
        
        st.subheader("🔍 SQL 및 인사이트")
        query_text = """
        SELECT a.region, a.senior, b.total_population, b.elderly_population, c.return_count 
        FROM 대중교통 a JOIN 인구비 b ON a.region = b.region JOIN 면허반납 c ON a.region = c.region
        """
        st.code(query_text, language='sql')
        st.write("""
        - 위의 그래프의 각 요인들을 지역별로 보여주기 위하여 대한민국 지도에 색으로 그 정도를 표현하였다.
        - 대중교통 이용 지표(Greens): 해당 지역의 고령자 인구 대비 대중교통 접근성 및 이용 수준을 나타낸다. 색이 진할수록 인프라가 우수하다는 의미이다. 
        - 면허 반납율(Blues): 고령 인구 대비 면허 반납 성과를 나타낸다. 색이 진할수록 정책 참여도가 높다는 의미이다. 
        - 색상의 진하기 정도 차이로 각 지역의 대중교통 이용성과 면허반납 간 관계를 알아볼 수 있다. 색상패턴이 일치할 수록 대중교통과 면허 반납이 밀접한 관련이 있음을 시사한다. 
        """)

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