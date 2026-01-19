import pymysql
import pandas as pd
import streamlit as st
import pydeck as pdk
from db import get_connection

# --------------------------
# 1. DB 연결 및 데이터 로드
# --------------------------
def get_connection():
    return pymysql.connect(
        host='localhost',
        user='ohgiraffers',
        password='ohgiraffers',
        db='evdb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@st.cache_data
def load_db_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 지역 데이터
            cursor.execute("SELECT zcode, regionNm FROM tbl_region")
            df_region = pd.DataFrame(cursor.fetchall())
            
            # 2. 지역 상세 데이터
            cursor.execute("SELECT zscode, regionDetailNm, zcode FROM tbl_region_detail")
            df_region_detail = pd.DataFrame(cursor.fetchall())
            
            # 3. 충전소 데이터
            cursor.execute("SELECT statid, statNm, addr, lat, lng, parkingFree, zscode FROM tbl_station")
            df_station = pd.DataFrame(cursor.fetchall())
            
            # [수정] 데이터 타입 정제 및 결측치 제거
            if not df_station.empty:
                # 숫자형으로 변환 (오류 데이터는 NaN 처리)
                df_station['lat'] = pd.to_numeric(df_station['lat'], errors='coerce')
                df_station['lng'] = pd.to_numeric(df_station['lng'], errors='coerce')
                # 좌표가 없는 행은 지도 표시가 불가능하므로 삭제
                df_station = df_station.dropna(subset=['lat', 'lng'])
            
        return df_region, df_region_detail, df_station
    finally:
        conn.close()

# 데이터 로딩
df_region, df_region_detail, df_station = load_db_data()

# --------------------------
# 2. 사이드바 지역 필터링 UI
# --------------------------
st.sidebar.header("지역 필터링")

regionNms = ['전체'] + sorted(df_region['regionNm'].unique().tolist())
selected_regionNm = st.sidebar.selectbox("시/도를 선택하세요", regionNms)

if selected_regionNm == '전체':
    selected_zcode = None
    selected_regionDetailNm = '전체'
    st.sidebar.selectbox("구/군을 선택하세요", ['전체'], disabled=True)
else:
    selected_zcode = df_region[df_region['regionNm'] == selected_regionNm]['zcode'].values[0]
    filtered_detail = df_region_detail[df_region_detail['zcode'] == selected_zcode]
    regionDetailNms = ['전체'] + sorted(filtered_detail['regionDetailNm'].unique().tolist())
    selected_regionDetailNm = st.sidebar.selectbox("구/군을 선택하세요", regionDetailNms)

# --------------------------
# 3. 데이터 필터링 로직
# --------------------------
if selected_regionNm == '전체':
    filtered_df = df_station.copy()
else:
    if selected_regionDetailNm == '전체':
        target_zscodes = df_region_detail[df_region_detail['zcode'] == selected_zcode]['zscode'].tolist()
        filtered_df = df_station[df_station['zscode'].isin(target_zscodes)].copy()
    else:
        # zscode 추출 시 인덱스 에러 방지
        detail_row = df_region_detail[
            (df_region_detail['zcode'] == selected_zcode) & 
            (df_region_detail['regionDetailNm'] == selected_regionDetailNm)
        ]
        if not detail_row.empty:
            selected_zscode_val = detail_row['zscode'].values[0]
            filtered_df = df_station[df_station['zscode'] == selected_zscode_val].copy()
        else:
            filtered_df = pd.DataFrame()

if not filtered_df.empty:
    filtered_df['parkingFree_txt'] = filtered_df['parkingFree'].map({'Y': '가능', 'N': '불가능'}).fillna('정보없음')

# --------------------------
# 4. 지도 및 통계 표시
# --------------------------
st.title("전국 전기차 충전소 지도")
st.write(f"필터링 결과: **{selected_regionNm} {selected_regionDetailNm}**")
st.write(f"충전소 개수: {len(filtered_df)}개")

# [수정] pydeck 레이어 설정
layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position='[lng, lat]',
    get_radius=200 if selected_regionNm != '전체' else 1000,
    get_fill_color=[65, 105, 225, 150],
    pickable=True
)

# [수정] 지도 뷰 설정 (NaN 값이 없는지 확인)
if not filtered_df.empty:
    center_lat = float(filtered_df['lat'].mean())
    center_lng = float(filtered_df['lng'].mean())
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lng,
        zoom=7 if selected_regionNm == '전체' else (11 if selected_regionDetailNm == '전체' else 13),
        pitch=0,
        bearing=0
    )
else:
    view_state = pdk.ViewState(latitude=36.5, longitude=127.5, zoom=6)

# [수정] 지도 렌더링 (map_style 변경)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style=None,  # 'road' 대신 기본 스타일 사용 (가장 안전함)
    tooltip={
        "html": "<b>충전소명:</b> {statNm}<br/><b>주소:</b> {addr}<br/><b>주차무료여부:</b> {parkingFree_txt}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }
))