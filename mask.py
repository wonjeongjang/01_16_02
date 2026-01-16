import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="10월 수산물 무역 리포트", layout="wide")

# [중요] GitHub에 올린 실제 파일명과 똑같이 수정하세요.
FILE_NAME = '해양수산부_HSK품목별수출입현황_20251031.csv' 

# --- 2. 데이터 불러오기 함수 (강력한 인코딩 방어형) ---
@st.cache_data
def load_data():
    # 시도해볼 인코딩 목록
    encodings = ['cp949', 'utf-8', 'euc-kr']
    
    for enc in encodings:
        try:
            # errors='ignore' 옵션으로 깨진 글자가 있어도 에러 없이 읽어옵니다.
            df = pd.read_csv(FILE_NAME, encoding=enc, errors='ignore')
            
            # 필요한 컬럼이 있는지 확인 후 데이터 처리
            if '당월수출입중량(킬로그램)' in df.columns:
                # 중량이 0인 데이터는 단가 계산 오류 방지를 위해 제거
                df = df[df['당월수출입중량(킬로그램)'] > 0].copy()
                # 단가 계산 ($ / kg)
                df['단가'] = df['당월수출입미화금액(달러)'] / df['당월수출입중량(킬로그램)']
                return df
        except Exception:
            continue
            
    # 모든 시도가 실패할 경우 빈 데이터프레임 반환
    return pd.DataFrame()

# --- 3. 실행 및 화면 구성 ---
try:
    df = load_data()

    if df.empty:
        st.error(f"파일 '{FILE_NAME}'을 읽을 수 없거나 데이터가 비어 있습니다.")
        st.info("파일 이름이 GitHub에 있는 것과 동일한지, 그리고 파일 인코딩을 확인해주세요.")
    else:
        st.title("📊 10월 수산물 수출입 요약 리포트")

        # --- 상단 요약 지표 ---
        exp_df = df[df['수출입구분명'] == '수출']
        imp_df = df[df['수출입구분명'] == '수입']
        
        total_exp = exp_df['당월수출입미화금액(달러)'].sum()
        total_imp = imp_df['당월수출입미화금액(달러)'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("10월 총 수출액", f"${total_exp:,.0f}")
        c2.metric("10월 총 수입액", f"${total_imp:,.0f}")
        c3.metric("무역 수지", f"${total_exp - total_imp:,.0f}")

        st.divider()

        # --- 4. 시각화 섹션 ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🏆 10월 수출 금액 TOP 10")
            # 상위 10개 품목 추출
            top10_export = exp_df.nlargest(10, '당월수출입미화금액(달러)')
            fig_bar = px.bar(
                top10_export, 
                x='당월수출입미화금액(달러)', 
                y='수산물수출입품목명', 
                orientation='h',
                color='당월수출입미화금액(달러)',
                color_continuous_scale='Viridis',
                labels={'당월수출입미화금액(달러)': '수출액($)'}
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            st.subheader("💰 품목별 평균 단가 분석 (Top 10)")
            # 단가가 높은 순으로 상위 10개 추출
            top10_price = df.nlargest(10, '단가')
            fig_scatter = px.scatter(
                top10_price, 
                x='당월수출입중량(킬로그램)', 
                y='당월수출입미화금액(달러)',
                size='단가', 
                color='수산물수출입품목명',
                hover_name='수산물수출입품목명',
                size_max=50,
                title="중량 대비 금액 (원의 크기 = 단가)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # --- 5. 상세 정보 검색 ---
        st.divider()
        st.subheader("🔍 품목별 상세 정보 검색")
        
        # 가나다 순으로 정렬된 품목 리스트
        all_items = sorted(df['수산물수출입품목명'].unique())
        target_item = st.selectbox("품목을 선택하세요", all_items)
        item_data = df[df['수산물수출입품목명'] == target_item].copy()
        
        # 표 출력을 위해 단가 포맷팅
        item_data['단가_표기'] = item_data['단가'].map('${:,.2f}'.format)
        st.table(item_data[['수출입구분명', '당월수출입중량(킬로그램)', '당월수출입미화금액(달러)', '단가_표기']])

except Exception as e:
    st.error(f"알 수 없는 오류가 발생했습니다: {e}")
