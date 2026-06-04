import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px

# --- 1. 환경 설정 ---
st.set_page_config(page_title="고령 운전자 정책 분석 대시보드", layout="wide")

# --- 2. DB 연결 ---
DB_FILE = 'drive.db' # 파일명이 drive.db인 경우

def run_query(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- 3. 사이드바 ---
st.sidebar.title("📊 분석 목차")
menu = st.sidebar.radio("보고서 섹션", ["서론: 문제 정의", "연령별 사고율 분석", "지역별 면허반납 분석", "대중교통과 반납율 관계", "결론 및 정책 제안"])

if not os.path.exists(DB_FILE):
    st.error(f"🚨 '{DB_FILE}' 파일을 확인해주세요.")
else:
    # --- [섹션 1: 서론] ---
    if menu == "서론: 문제 정의":
        st.title("👵 고령 운전자 사고 위험과 면허 반납 정책의 실효성")
        st.info("왼쪽 메뉴를 통해 상세 분석 내용을 확인하세요.")

    # --- [섹션 2: 연령별 사고율] ---
    elif menu == "연령별 사고율 분석":
        st.title("📈 연령대별 사고 위험도 분석")
        age_order = ['19세 이하', '20-29세', '30-39세', '40-49세', '50-59세', '60-64세', '65세 이상']
        
        query1 = "SELECT a.age_group, (CAST(a.accident_count AS FLOAT) / b.license_count) * 100 as accident_rate FROM 가해운전자 a JOIN 면허소지자 b ON a.age_group = b.age_group"
        df1 = run_query(query1)
        df1['age_group'] = pd.Categorical(df1['age_group'], categories=age_order, ordered=True)
        df1 = df1.sort_values('age_group')
        
        fig1 = px.bar(df1, x='age_group', y='accident_rate', color_discrete_sequence=['crimson'])
        st.plotly_chart(fig1, use_container_width=True)

        st.header("2) 고령 vs 비고령 상대 위험도 (65세 이상 기준)")
        query2 = "SELECT a.age_group, a.accident_count, b.license_count FROM 가해운전자 a JOIN 면허소지자 b ON a.age_group = b.age_group"
        df2 = run_query(query2)
        df2['group_type'] = df2['age_group'].apply(lambda x: '고령운전자' if x == '65세 이상' else '비고령운전자')
        df_grouped = df2.groupby('group_type')[['accident_count', 'license_count']].sum().reset_index()
        df_grouped['rate'] = (df_grouped['accident_count'] / df_grouped['license_count']) * 100
        
        try:
            risk = df_grouped.loc[df_grouped['group_type']=='고령운전자', 'rate'].values[0] / df_grouped.loc[df_grouped['group_type']=='비고령운전자', 'rate'].values[0]
            st.metric("고령층 상대 위험도", f"{risk:.2f} 배")
        except: st.error("계산 오류")

    # --- [섹션 3: 지역별 면허반납 분석] ---
    elif menu == "지역별 면허반납 분석":
        st.title("📍 지역별 면허 반납 정책 현황")
        query3 = "SELECT a.region, (CAST(a.return_count AS FLOAT) / b.elderly_population) * 100 as return_rate FROM 면허반납 a JOIN 인구비 b ON a.region = b.region"
        df3 = run_query(query3)
        
        name_mapping = {'서울':'서울특별시', '부산':'부산광역시', '대구':'대구광역시', '인천':'인천광역시', '광주':'광주광역시', '대전':'대전광역시', '울산':'울산광역시', '세종':'세종특별자치시', '경기':'경기도', '강원':'강원도', '충북':'충청북도', '충남':'충청남도', '전북':'전라북도', '전남':'전라남도', '경북':'경상북도', '경남':'경상남도', '제주':'제주도'}
        df3['region_full'] = df3['region'].map(name_mapping)
        
        geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo.json"
        fig = px.choropleth(df3, geojson=geojson_url, locations='region_full', featureidkey="properties.name", color='return_rate', color_continuous_scale="Blues")
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- [섹션 4: 대중교통과 반납율 관계] ---
    elif menu == "대중교통과 반납율 관계":
        st.title("🚌 대중교통 인프라 vs 면허 반납율")
        query = "SELECT a.region, a.senior, b.total_population, b.elderly_population, c.return_count FROM 대중교통 a JOIN 인구비 b ON a.region = b.region JOIN 면허반납 c ON a.region = c.region"
        df = run_query(query)
        df['transport_index'] = df['senior'] / df['total_population']
        df['return_rate'] = (df['return_count'] / df)