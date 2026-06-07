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
    ["문제 정의", "연령별 사고율 분석", "지역별 면허반납 분석", "대중교통과 반납율 관계", "결론 및 정책 제언"]
)

# DB 파일 존재 여부 체크
if not os.path.exists(DB_FILE):
    st.error(f"🚨 '{DB_FILE}' 파일이 같은 폴더에 없습니다. 데이터베이스 파일을 확인해주세요.")
else:
    # --- [섹션 1: 문제 정의] ---
    if menu == "문제 정의":
        st.title("👵 운전대를 놓은 노인은 어디로 갈 수 있을까?")
        st.subheader("언론과 대중은 고령 운전자 사고라는 결과만 보고 '운전하지 말라'고 한다.")
        
        # 1. DB에서 설문조사 데이터 불러오기
        # 주의: init_db.py에서 쓴 DB 파일명과 일치해야 합니다!
        st.subheader("📊 청년들이 바라보는 노인 안전사고의 중요도")
        df_survey = run_query("SELECT * FROM 설문조사 ORDER BY 총점 DESC")
        
        # 2. 시각화 (막대그래프)
        fig_survey = px.bar(df_survey, x='사고유형', y='총점', 
                            color='점수비중', color_continuous_scale='Viridis',
                            title="안전사고 유형별 중요도 점수")
        st.plotly_chart(fig_survey, use_container_width=True)
        
        # 3. 데이터 해석 텍스트
        st.markdown("""
        노인이 겪을 수 있는 안전사고와 관련하여 우리사회가 시급히 대응해야 하는 사항 중 노인의 교통사고를 1순위 혹은 2순위로 선택한 청년들의 설문조사 응답을 참고하여 1순위(2점), 2순위(1점)를 부여한 가중치 분석 결과, 교통사고는 전체 응답 점수의 16.9%를 차지하여 세 번째로 높은 중요도를 보였다.
        
        이처럼 고령화 사회인 대한민국에서, 노인 교통사고 문제는 심각한 사회적 문제로 인지되고 있다.
        """)

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
        st.markdown("""
        운전면허소지자 연령비와 가해운전자 연령비를 비교해 실제 노인 가해운전자 비중이 높은지 검증하고자 한다.
        """)

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
        - 분석 결과, 연령대별 사고율은 1등 19세 이하, 2등 65세 이상, 3등 60-64세로 19세 이하 집단을 제외하면 40-49세부터 연령이 증가할수록 사고율이 상승하는 것으로 나타났다. 19세 이하의 집단의 사고율은 운전미숙과 초보운전 비율 등이 영향을 준 것으로 해석 가능하다.
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
        
        # 4. 상대 위험도 계산 
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
            - 운전자 집단을 고령운전자(65세 이상)와 비고령운전자(65세 미만)로 구분하여 다음과 같이 나타냈다. (고령층 사고율/비고령층 사고율)로 상대 위험도를 산출할 수 있다. 분석결과 고령운전자의 사고율은 약 0.84, 비고령운전자의 사고율은 약 0.59로, 고령운전자의 사고율이 비고령운전자보다 약 1.42배 높게 나타난다.
            - 따라서 사회문제로 대두되는 고령운전자 운전 미숙이 단순 편견과 오해가 아니라 실제 통계임을 확인할 수 있다.
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
        - 고령 인구 대비 면허 반납 성과가 높을 수록 색이 진할수록 면허반납 정책 참여도가 각 지역에서 높다는 의미이다. 면허반납율은 최대 1.4%로 부산이 가장 높고, 뒤이어 서울과 대구가 있다. 반대로 하위 반납율 지역은 광주, 세종, 전남으로 최저 0.72%이다. 지역별로 반납율 편차가 크므로 통계의 요인을 찾아야 할 필요성이 있다.

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
        st.markdown("""
        면허 반납 정책이 일회성 현금 지급 등의 단기 보상만으로 효과를 거두는지, 아니면 반납 후의 삶을 지원하는 이동권 보장이 핵심인지 검증하기 위함이다. 또한 앞에서 다룬 지역별 면허 반납율의 통계 데이터를 바탕으로 이 요인이 사고율에 끼치는 영향이 전국적으로 동일한지 확인하고자 한다.
        """)
        
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
        - 대중교통 인프라의 공급 및 접근성을 나타내는 '이용 데이터'와 정책의 실효성을 보여주는 '면허 반납 데이터'를 지역 단위(Region)로 통합 분석하여 지역별 이동 환경이 면허 자진 반납 참여율에 미치는 실질적인 인과관계를 통계적으로 검증하고자 한다.
        - 그래프의 추세선이 우상향하고 있어, 대중교통이용 수준이 높을수록 면허반납률도 높아지는 경향을 보인다. 즉, 버스나 지하철 등 대중교통 접근성이 좋은 지역일수록 고령자가 운전을 포기하기 쉬운것으로 해석된다. 다만 대중교통 이용성이 낮은 지역의 반납률은 상관관계가 다소 부족한 것으로 보이는데, 이는 면허반납의 정책이 지자체별로 상이하고 지역별 교통안전 정책들이 영향을 끼친 것으로 분석했다. 반대로 대중교통 이용성이 높은 서울, 부산, 대구 등은 다른 지역들에 비해 상대적으로 높은 면허반납률을 보인다.
        - 일회성 지원보다 면허를 자진 반납한 고령운전자들의 이동권에 대한 대책이 더욱더 필요함을 알 수 있다. 
        """)

        st.divider()

        # 3. 지도 시각화 (공간적 분포 비교)
        st.subheader("공간적 분포 비교")
        st.markdown("""
        위의 그래프의 각 요인들을 지역별로 보여주기 위하여 대한민국 지도에 색으로 그 정도를 표현하였다.
        """)
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
            
        st.info("💡 두 지도의 색상 패턴이 일치할수록 대중교통과 면허 반납이 밀접한 관련이 있음을 시사한다.")
        
        st.subheader("🔍 SQL 및 인사이트")
        query_text = """
        SELECT a.region, a.senior, b.total_population, b.elderly_population, c.return_count 
        FROM 대중교통 a JOIN 인구비 b ON a.region = b.region JOIN 면허반납 c ON a.region = c.region
        """
        st.code(query_text, language='sql')
        st.write("""
        - 위의 그래프의 각 요인들을 지역별로 보여주기 위하여 대한민국 지도에 색으로 그 정도를 표현했다.
        - 대중교통 이용 지표(Greens): 해당 지역의 고령자 인구 대비 대중교통 접근성 및 이용 수준을 나타낸다. 색이 진할수록 인프라가 우수하다는 의미이다. 
        - 면허 반납율(Blues): 고령 인구 대비 면허 반납 성과를 나타낸다. 색이 진할수록 정책 참여도가 높다는 의미이다. 
        - 색상의 진하기 정도 차이로 각 지역의 대중교통 이용성과 면허반납 간 관계를 알아볼 수 있다. 색상패턴이 일치할 수록 대중교통과 면허 반납이 밀접한 관련이 있음을 시사한다. 
        """)

    # --- [섹션 5: 결론 및 정책 제언] ---
    elif menu == "결론 및 정책 제언":
        st.title("🏁 결론 및 정책 제언")
        st.write("")
        st.markdown("""

        ### 1. 데이터 분석을 통한 결론 
        본 프로젝트는 고령 운전자 사고 위험을 단순히 '고령화로 인한 인지능력 저하'라는 개인적 요인으로만 설명할 수 없으며, 이동권과 교통환경이 복합적으로 작용하는 사회적 문제임을 통계적으로 확인하였다.  
        
        분석 결과 고령 운전자의 사고 위험도(상대 위험도 1.42배)는 실제 비고령 운전자보다 높으나 면허 반납율의 지역적 편차는 대중교통 이용 지표와 밀접한 양의 상관관계를 보인다. 
        
        즉 고령 운전자가 운전대를 놓지 못하는 것은 단순한 고집이 아니라 **대중교통 인프라가 갖춰지지 않은 지역에서 면허 반납이 곧 이동권의 단절을 의미하기 때문이라는 결론을 내린다.** 따라서 면허 반납 정책의 성공 여부는 단순한 금전적 보상이 아니라, 얼마나 촘촘한 대체 이동 수단을 제공하느냐에 달려 있다. 


    
        ### 2. 정책 제언
        **(1) 구조적 인프라 강화**
        이동의 단절이 아닌 수단 교체가 될 수 있도록 하는 시스템을 만들어야 한다.
        
        **(2) 인센티브의 다각화**
        일회성 현금 지원, 교통카드 지급보다는 지속적 이동권 보장을 위한 다양한 형태의 인센티브를 제공하여 반납 이후에도 자유로운 노인의 이동을 보장해야 한다. 

        **(3) 사고 예방 정책**
        고령운전자 사고를 방지하기 위한 차량 보조 기구 지원 등의 정책을 도입하여 노인의 권리를 보장함과 동시에 사고를 예방하여야 한다. 
        
        &nbsp;&nbsp;&nbsp;&nbsp;**(a) 첨단 운전자 보조장치(ADAS) 지원** : 자동긴급제동장치, 차선이탈경고장치, 페달 오조작 방지장치, 사각지대 경고장치 등. 도로교통공사 인식조사 결과, 고령/비고령운전자 모두 비상제동장치가 고령운전자에게 특히 도움을 줄 수 있을 것이라고 인식하고 있다. 
        
        &nbsp;&nbsp;&nbsp;&nbsp;**(b) 도로환경 개선** : 고령자의 시력과 반응속도에 맞추어 도로 자체를 개선해야 한다. 큰 글씨 표시판, 야간 반사 표지 확대, 좌회전 신호 연장, 교차로 조명 강화 등이 있다. 특히 농촌 지역에서는 도로환경 개선 필요성이 강조되고 있다. 



        ### 3. 연구 한계 및 후속 연구 방향 
        본 프로젝트는 지자체별 통계 기반의 거시적 분석으로, 개인의 실제 이동 경로, 심리적 요인, 해당 지역의 상세 대중교통 배차 간격 등을 세밀하게 반영하지 못했다는 한계가 있다. 따라서 향후에는 개인별 이동 데이터 혹은 실시간 대중교통 접근성을 활용한 미시적 분석으로 반납 후 삶의 질까지 고려한 이동권 보장 최적 모델을 연구할 필요가 있다.  



        ### 4. 활용 데이터 
        노인인권에 대한 인식 및 실태조사, 2017:청장년 (한국사회과학자료원 KOSSDA) 
        경찰청_운전면허소지자 연령별 현황 (2020년 12월 말 기준, 공공데이터포털) 
        연령대별 가해운전자 교통사고 통계 (2020년 기준, 한국도로교통공단 교통사고분석시스템) 
        2024년 시도별 대중교통 이용인원 
        2024년 시도별 고령운전자 면허 자진반납 현황 
        2024년 시도별 고령인구비율 
        한국도로교통공사 보도자료, “고령운전자도 ‘운전능력 평가 강화’ 원한다” - 공단 인식조사 결과, 2025년 5월 15일.  
        고령 운전자 운전면허 관리 강화에 대한 농촌의 의견, 한국농촌경제연구원, 김용렬 외 2인, 2029년 6월. 
        """)
        st.balloons()