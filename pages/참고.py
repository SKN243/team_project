import streamlit as st
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. 페이지 설정
st.set_page_config(
    page_title="전기차 등록 현황 대시보드",
    page_icon="⚡",
    layout="wide"
)

# 한글 폰트 설정 (윈도우 기준)
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드 함수
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
        # [수정된 쿼리] tbl_register와 tbl_region을 조인하여 지역명을 가져옵니다.
        query = """
        SELECT 
            r.year, 
            reg.regionNm AS region, 
            r.registrations 
        FROM tbl_register r
        JOIN tbl_region reg ON r.zcode = reg.zcode
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"DB 에러: {e}")
        return None
    finally:
        conn.close()

# 3. 사이드바 필터
with st.sidebar:
    st.header("📊 데이터 필터")
    st.write("확인하고 싶은 지역을 선택하세요.")

# 4. 메인 로직
try:
    df = load_data()

    if df is not None and not df.empty:
        # 지역 리스트 추출 (서울, 부산 등)
        region_list = sorted(df['region'].unique())
        selected_region = st.selectbox("지역 선택", region_list)
        
        # 선택된 지역 데이터 필터링 및 연도순 정렬
        filtered_df = df[df['region'] == selected_region].sort_values('year')

        st.title(f"⚡ {selected_region} 전기차 등록 추이 분석")
        st.markdown("---")

        if not filtered_df.empty:
            # 지표 계산
            last_row = filtered_df.iloc[-1]   
            first_row = filtered_df.iloc[0]   
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("최근 등록 대수", f"{int(last_row['registrations']):,}대")
            with col2:
                st.metric("데이터 집계 기간", f"{int(first_row['year'])} ~ {int(last_row['year'])}")

            st.markdown("---")

            # 5. 그래프 그리기 (Matplotlib)
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 선 그래프 및 영역 채우기
            ax.plot(filtered_df['year'], filtered_df['registrations'], 
                    color='#10B981', marker='o', markersize=8, linewidth=3, zorder=3)
            ax.fill_between(filtered_df['year'], filtered_df['registrations'], 
                            color='#10B981', alpha=0.1)

            # 그래프 내부 숫자 표시 (Annotation)
            for i, row in filtered_df.iterrows():
                ax.annotate(
                    text=f"{int(row['registrations']):,}", 
                    xy=(row['year'], row['registrations']), 
                    xytext=(0, 10), 
                    textcoords='offset points', 
                    ha='center', va='bottom',
                    fontsize=11, fontweight='bold', color='#065F46',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#10B981", alpha=0.9)
                )

            # 디자인 설정
            ax.set_xlabel("연도", fontsize=10)
            ax.set_ylabel("등록 대수 (대)", fontsize=10)
            ax.set_xticks(filtered_df['year'])
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            ax.grid(True, linestyle='--', alpha=0.3)
            
            # 테두리 제거
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            st.pyplot(fig)

            # 6. 상세 데이터 표
            with st.expander("📄 상세 데이터 표 보기"):
                st.dataframe(filtered_df.style.format({"year": "{:.0f}", "registrations": "{:,}대"}), use_container_width=True)
        
        else:
            st.info("해당 지역의 데이터가 없습니다.")
    else:
        st.error("데이터 로드 실패: 테이블에 데이터가 있는지 확인하세요.")

except Exception as e:
    st.error(f"오류 발생: {e}")