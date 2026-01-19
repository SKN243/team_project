import streamlit as st
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

st.set_page_config(
    page_title="전기차 등록 현황 대시보드",
    page_icon="⚡",
    layout="wide"
)

plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

@st.cache_data
def load_data():
    conn = pymysql.connect(
        host="127.0.0.1",
        user="ohgiraffers",
        password="ohgiraffers",
        database="evdb",
        port=3306,
        charset="utf8mb4",
    )
    try:
        query = "SELECT year, region, registrations FROM tbl_region"
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

#UI

with st.sidebar:
    st.header("📊 데이터 필터")
    st.write("확인하고 싶은 지역을 선택하세요.")

try:
    df = load_data()

    if df is not None:
        region_list = sorted(df['region'].unique())
        selected_region = st.selectbox("지역 선택", region_list)
        
        filtered_df = df[df['region'] == selected_region].sort_values('year')

        st.title(f"⚡ {selected_region} 전기차 등록 추이 분석")
        st.markdown("---")

        if not filtered_df.empty:
            # [지표 설정] 복잡한 성장률은 빼고, 깔끔하게 2개만 보여줍니다.
            last_row = filtered_df.iloc[-1]   
            first_row = filtered_df.iloc[0]   
            
            #컬럼을 2개로 나눔
            col1, col2 = st.columns(2)
            with col1:
                st.metric("최근 등록 대수", f"{int(last_row['registrations']):,}대")
            with col2:
                st.metric("데이터 집계 기간", f"{int(first_row['year'])} ~ {int(last_row['year'])}")

            st.markdown("---")

            #그래프 그리기
            fig, ax = plt.subplots(figsize=(12, 7))
            
            #Area Chart 효과 (아래 색칠)
            ax.plot(filtered_df['year'], filtered_df['registrations'], 
                    color='#3B82F6', marker='o', markersize=8, linewidth=3, zorder=2)
            
            ax.fill_between(filtered_df['year'], filtered_df['registrations'], 
                            color='#3B82F6', alpha=0.1)

            #y축 여백 설정
            min_val = filtered_df['registrations'].min()
            max_val = filtered_df['registrations'].max()
            padding = (max_val - min_val) * 0.2 if max_val != min_val else 10
            ax.set_ylim(max(0, min_val - padding), max_val + padding)
            
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            ax.grid(True, linestyle='--', alpha=0.4, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            #이제 에러 없이 숫자가 점 위에 예쁘게 뜸
            for i, row in filtered_df.iterrows():
                ax.annotate(
                    text=f"{int(row['registrations']):,}", 
                    xy=(row['year'], row['registrations']), 
                    xytext=(0, 10),  #점 위로 10포인트 띄우기
                    textcoords='offset points', 
                    ha='center', 
                    va='bottom',
                    fontsize=12, 
                    fontweight='bold', 
                    color='#1E3A8A',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8)
                )

            ax.set_xlabel("연도", fontsize=12)
            ax.set_ylabel("등록 대수 (단위: 대)", fontsize=12)
            ax.set_xticks(filtered_df['year'])
            
            st.pyplot(fig)

            with st.expander("📄 상세 데이터 표 보기"):
                st.dataframe(filtered_df.style.format({"registrations": "{:,}대"}))
        
        else:
            st.info("해당 지역의 데이터가 없습니다.")
    else:
        st.error("데이터 로드 실패")

except Exception as e:
    st.error("오류 발생")
    st.write(f"내용: {e}")