import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="마스크 수출입 통계 분석", layout="wide")

# GitHub에 올린 실제 CSV 파일명 (대소문자/공백 주의)
FILE_NAME = '관세청_마스크 수출입통계_20251231.csv'

# --- 2. 데이터 불러오기 및 전처리 ---
@st.cache_data
def load_data():
    try:
        # encoding_errors='ignore' 를 사용하여 깨진 글자 무시
        df = pd.read_csv(FILE_NAME, encoding='cp949', encoding_errors='ignore')
    except:
        df = pd.read_csv(FILE_NAME, encoding='utf-8', encoding_errors='ignore')
    
    # 1. 날짜 데이터 생성 (연도 + 월)
    # 월을 2자리(01, 02...)로 만들어서 날짜 형식으로 변환
    df['날짜'] = pd.to_datetime(df['연도'].astype(str) + '-' + df['월'].astype(str).str.zfill(2) + '-01')
    
    # 2. 데이터 재구조화 (옆으로 긴 데이터를 아래로 길게 변환)
    id_vars = ['연도', '월', '날짜']
    value_vars = [col for col in df.columns if col not in id_vars]
    
    df_melted = df.melt(id_vars=id_vars, value_vars=value_vars, 
                        var_name='구분_상세', value_name='금액')
    
    # 3. '수출입구분'과 '마스크종류' 분리
    # 컬럼명이 "수술용마스크...수출" 형식이므로 마지막 두 글자로 판단
    df_melted['수출입구분'] = df_melted['구분_상세'].apply(lambda x: '수출' if x.endswith('수출') else '수입')
    df_melted['마스크종류'] = df_melted['구분_상세'].apply(lambda x: x[:-2]) # "수출/수입" 글자 제거
    
    return df_melted

# --- 3. 메인 화면 구성 ---
try:
    df = load_data()

    st.title("📊 마스크 품목별 수출입 통계 (2021-2025)")
    st.info("단위: USD 1,000 (천 달러) | 출처: 관세청")

    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 데이터 필터")
    
    # 마스크 종류 필터
    all_masks = sorted(df['마스크종류'].unique())
    selected_masks = st.sidebar.multiselect("마스크 종류", all_masks, default=all_masks)
    
    # 수출입 구분 필터
    trade_type = st.sidebar.radio("거래 구분", ["전체", "수출", "수입"])

    # 데이터 필터링 적용
    filtered_df = df[df['마스크종류'].isin(selected_masks)]
    if trade_type != "전체":
        filtered_df = filtered_df[filtered_df['수출입구분'] == trade_type]

    # --- 상단 요약 지표 ---
    c1, c2, c3 = st.columns(3)
    exp_val = filtered_df[filtered_df['수출입구분'] == '수출']['금액'].sum()
    imp_val = filtered_df[filtered_df['수출입구분'] == '수입']['금액'].sum()
    
    c1.metric("총 수출액", f"${exp_val:,.0f}K")
    c2.metric("총 수입액", f"${imp_val:,.0f}K")
    c3.metric("무역 수지", f"${exp_val - imp_val:,.0f}K")

    st.divider()

    # --- 시각화 섹션 ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 월별 수출입 추이")
        # 선 그래프 (마스크 종류별로 색상, 수출입구분별로 점선/실선 구분)
        fig_line = px.line(filtered_df, x='날짜', y='금액', color='마스크종류', 
                           line_dash='수출입구분', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.subheader("🥧 품목별 비중 (선택 기간)")
        fig_pie = px.pie(filtered_df, values='금액', names='마스크종류', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 상세 데이터 테이블 ---
    with st.expander("📋 상세 데이터 확인"):
        st.dataframe(filtered_df.sort_values('날짜', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
    st.info("파일 이름이 '관세청_마스크 수출입통계_20251231.csv'인지 다시 확인해주세요.")