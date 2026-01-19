import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px

# 1. DB 연결
def get_connection():
    return pymysql.connect(
        host='127.0.0.1',
        user='ohgiraffers',
        password='ohgiraffers', 
        db='evdb',
        charset='utf8mb4',
    )

st.set_page_config(layout="wide")
st.title("📊 국내 전기차 연도별 누적 등록 현황")

try:
    # 2. 데이터 가져오기
    conn = get_connection()
    query = "SELECT * FROM tbl_register"
    df = pd.read_sql(query, conn)
    conn.close()

    if not df.empty:
        # 3. 데이터 전처리
        df_clean = df.copy() # 원본을 해치치 않기 위한 복사본 생성
        
        # 연도, 합계를 제외한 지역 컬럼 추출
        exclude_cols = ['year', 'total', 'zcode', '합계', 'ID'] # 제외할 컬럼 모음
        region_cols = [col for col in df_clean.columns if col not in exclude_cols] # 지역 컬럼에 제외목록을 제거
        
        # 지역 컬럼들을 숫자로 변환 (오류 데이터는 0 처리)
        df_clean[region_cols] = df_clean[region_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # 연도별로 그룹화하여 합산 (막대 그래프 층층이 쌓여서 해결위한 코드)
        df_yearly = df_clean.groupby('year')[region_cols].sum().reset_index()
        
        # 행 전체 합산
        df_yearly['전국총합'] = df_yearly[region_cols].sum(axis=1)
        
        # 정렬
        df_yearly = df_yearly.sort_values('year')

        # 4. 막대 그래프 생성
        fig = px.bar(
            df_yearly, 
            x='year', 
            y='전국총합',
            title="연도별 전국 전기차 등록대수 (누적)",
            color='전국총합',
            color_continuous_scale='Greens' # 그래프 색상 
        )

        # 5. 그래프 위에 수치 표시 설정
        fig.update_traces(
            # 정수로 변환시킨 뒤 콤마와 '대' 추가
            text=df_yearly['전국총합'].astype(int).apply(lambda x: f'{x:,}대'),
            textposition='outside', # 막대 바깥에 수치 표기
            textfont_size=12,
            cliponaxis=False        # 그래프 영역 밖으로 나가도 글자 안 잘리게
        )

        # 6. 그래프 레이아웃 설정
        fig.update_layout(
            xaxis_title="기준 연도",
            yaxis_title="총 등록대수 (대)",
            xaxis=dict(type='category'), # 연도를 숫자가 아닌 카테고리로 인식
            yaxis=dict(tickformat=',d'), # y축 단위 콤마
            height=600,
            margin=dict(t=100),          # 상단 여백 확보 (수치 표시용)
            uniformtext_minsize=8, 
            uniformtext_mode='hide'
        )
        
        # 그래프 출력
        st.plotly_chart(fig, use_container_width=True)
        
        # 세부 상세표 표기
        with st.expander("원본 데이터 보기"):
            st.dataframe(df_yearly[['year', '전국총합']].style.format({"전국총합": "{:,}"}))

    else:
        st.warning("데이터베이스에 불러올 데이터가 없습니다.")

except Exception as e:
    st.error("데이터 처리 중 오류가 발생했습니다.")
    st.exception(e)