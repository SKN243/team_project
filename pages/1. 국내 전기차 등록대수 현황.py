import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
from db import get_connection

# 1. DB 연결
def get_connection():
    return pymysql.connect(
        host='127.0.0.1',
        user='ohgiraffers',
        password='ohgiraffers', 
        db='evdb',
        charset='utf8mb4', # 한글 안깨지기 위함
    )

st.title("📊 국내 전기차 등록대수 현황")

try:
    # 2. DB 가져오기
    conn = get_connection()
    query = "SELECT * FROM tbl_register"
    df = pd.read_sql(query, conn)
    conn.close()

    if not df.empty:

        # 4. 전국총합 계산
        df_trend = df.copy() # 원본을 건드리지 않게 복사본 생성
        if 'total' in df_trend.columns: # Total은 뜨게하기 싫으니 제거 (그래프 이상해짐)
            df_trend = df_trend.drop(columns=['total'])
            
        df_trend['전국총합'] = df_trend.drop('year', axis=1).sum(axis=1) # year는 합X
        
        df_trend = df_trend[['year', '전국총합']].sort_values('year') # 연도와 전국총합만 두고, 연도로 정렬

        # 5. 막대 그래프 작성
        fig_trend = px.bar(
            df_trend, 
            x='year', 
            y='전국총합',
            title="국내 전기차 연도별 누적 등록 추세 (2010 ~ 2025년)",
            text=df_trend['전국총합'].apply(lambda x: f'{int(x):,}대'), # 그래프 위에 '대' 형식으로 표시
            color='전국총합',
            color_continuous_scale='Greens' # 그래프 색상 설정
        )

        # 6. 그래프 레이아웃 설정
        fig_trend.update_layout(
            xaxis_title="연도",
            yaxis_title="총 등록대수 (대)",
            xaxis=dict(type='category', tickangle=0), # 연도를 카테고리로 설정하고 가로로 출력
            yaxis=dict(tickformat=',d'), # Y축 숫자에 ,000 추가
            height=500 # 그래프 높이
        )
        
        fig_trend.update_traces(textposition='outside') # 그래프 밖에 숫자 표기

        st.plotly_chart(fig_trend, use_container_width=True) # 그래프 출력

        st.info("💡 전기차 등록대수가 매년 증가하고 있는 추세를 확인할 수 있습니다.") # 하단 설명 추가

    else:
        st.warning("데이터베이스에 데이터가 없습니다.")

except Exception as e:
    st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")