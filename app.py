"""
토너 리뷰 인사이트 도출 대시보드
Streamlit으로 작성된 인터랙티브 대시보드 (제품별 분석)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from analysis import TinerInsightAnalysis
import warnings

warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="토너 리뷰 인사이트 도출 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 캐싱을 통한 데이터 로드
@st.cache_resource
def load_analysis():
    import os
    csv_path = os.path.join(os.path.dirname(__file__), 'data', '올영리뷰_토너.csv')
    return TinerInsightAnalysis(csv_path)

# 분석 객체 로드
analysis = load_analysis()

# 사이드바 네비게이션
st.sidebar.title("📊 토너 리뷰 인사이트 대시보드")

# 제품 선택
products = analysis.get_products()
selected_product = st.sidebar.selectbox("📦 제품 선택", products if products else ["전체"])

# 선택된 제품의 데이터 추출
if selected_product != "전체" and selected_product in products:
    product_df = analysis.get_product_data(selected_product)
    product_analysis = analysis.get_product_data(selected_product)
else:
    product_df = analysis.df
    product_analysis = analysis.df

# 분석 객체 업데이트 (제품별 분석을 위해 임시 df 교체)
original_df = analysis.df
analysis.df = product_df

page = st.sidebar.radio(
    "메뉴",
    ["📈 대시보드 개요", "🔍 10가지 인사이트", "📋 월별 속성 분석", "📑 상세 데이터"]
)

# ===== PAGE 1: 대시보드 개요 =====
if page == "📈 대시보드 개요":
    st.title("📈 토너 리뷰 인사이트 대시보드")
    st.markdown(f"### 📦 제품: {selected_product}")
    st.markdown("---")

    # 요약 통계
    summary = analysis.get_summary()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📝 총 리뷰 수", f"{summary['total_reviews']:,}")

    with col2:
        st.metric("😊 긍정", summary['positive_ratio'])

    with col3:
        st.metric("😐 중립", summary['neutral_ratio'])

    with col4:
        st.metric("😞 부정", summary['negative_ratio'])

    with col5:
        st.metric("📅 분석 기간", summary['date_range'] if 'date_range' in summary else "데이터 확인 중")

    st.markdown("---")

    # 월별 감정 분포
    if 'MONTH' in analysis.df.columns and 'OVERALL_SENTIMENT' in analysis.df.columns:
        monthly_sentiment = analysis.df.groupby('MONTH')['OVERALL_SENTIMENT'].value_counts().unstack(fill_value=0)

        fig_sentiment = go.Figure()
        for col in monthly_sentiment.columns:
            fig_sentiment.add_trace(go.Bar(
                x=monthly_sentiment.index,
                y=monthly_sentiment[col],
                name=col,
                marker_color={'POSITIVE': '#2ECC71', 'NEUTRAL': '#F39C12', 'NEGATIVE': '#E74C3C'}.get(col, '#95A5A6')
            ))

        fig_sentiment.update_layout(
            title="월별 감정 분포",
            xaxis_title="월",
            yaxis_title="리뷰 수",
            barmode='stack',
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig_sentiment, use_container_width=True)

        # 월별 긍정 비율 추이
        positive_ratio = analysis.df.groupby('MONTH')['OVERALL_SENTIMENT'].apply(
            lambda x: (x == 'POSITIVE').sum() / len(x) * 100
        )

        fig_ratio = go.Figure()
        fig_ratio.add_trace(go.Scatter(
            x=positive_ratio.index,
            y=positive_ratio.values,
            mode='lines+markers',
            name='긍정 비율',
            line=dict(color='#2ECC71', width=3),
            marker=dict(size=10)
        ))

        fig_ratio.update_layout(
            title="월별 긍정 리뷰 비율 추이",
            xaxis_title="월",
            yaxis_title="긍정 비율 (%)",
            height=400,
            hovermode='x'
        )

        st.plotly_chart(fig_ratio, use_container_width=True)

# ===== PAGE 2: 10가지 인사이트 =====
elif page == "🔍 10가지 인사이트":
    st.title("🔍 10가지 핵심 인사이트")
    st.markdown(f"### 📦 제품: {selected_product}")
    st.markdown("---")

    # 인사이트 선택
    insight_list = [
        "IDEA 1: 흡수력과 재구매의 관계",
        "IDEA 2: 점성 제형과 계절의 관계",
        "IDEA 3: 보습 만족과 여름철 불만",
        "IDEA 4: 산뜻함 선호와 보습 불만의 동시 발생",
        "IDEA 5: 향의 계절 무관성과 특정 월 이슈",
        "IDEA 6: 무난함과 신규 유입의 관계",
        "IDEA 7: 지성 피부와 여름 마무리감 민감성",
        "IDEA 8: 자극 이슈의 월별 Spike",
        "IDEA 9: 가성비 평가와 불만 완충",
        "IDEA 10: 재구매 리뷰의 계절 영향 적음"
    ]

    selected_idea = st.selectbox("분석할 인사이트 선택", insight_list)

    st.markdown("---")

    # IDEA 1
    if "IDEA 1" in selected_idea:
        st.subheader("💡 IDEA 1: 흡수력은 재구매의 핵심이며, 여름에 더 중요해진다")
        st.markdown("""
        **분석 목표**: 재구매 고객이 흡수력을 얼마나 중요하게 평가하는지, 특히 여름철(6-8월)에 더 중요해지는지 검증

        **가설**: 재구매 리뷰 중 흡수 긍정 비율이 여름에 더 높을 것
        """)

        if 'MONTH' in analysis.df.columns and 'ABSORPTION_SENTIMENT' in analysis.df.columns and 'PURCHASE_TYPE' in analysis.df.columns:
            result = analysis.idea1_absorption_repurchase()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result.index,
                y=result['흡수 긍정 비율'],
                name='흡수 긍정 비율',
                marker_color='#3498DB'
            ))
            fig.update_layout(
                title="월별 재구매 리뷰의 흡수 긍정 비율",
                xaxis_title="월",
                yaxis_title="비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # 인사이트 요약
            try:
                summer_ratio = result.loc[result.index.isin([6, 7, 8]), '흡수 긍정 비율'].mean()
                other_ratio = result.loc[~result.index.isin([6, 7, 8]), '흡수 긍정 비율'].mean()

                st.success(f"""
                **핵심 발견**:
                - 여름(6-8월) 평균: {summer_ratio:.2f}%
                - 비여름 평균: {other_ratio:.2f}%
                - 차이: {summer_ratio - other_ratio:+.2f}%
                """)
            except:
                st.info("데이터가 부족하여 통계를 계산할 수 없습니다.")
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 2
    elif "IDEA 2" in selected_idea:
        st.subheader("💡 IDEA 2: 점성 제형은 가을·겨울에만 긍정으로 인식된다")
        st.markdown("""
        **분석 목표**: 점성/쫀쫀한 제형이 계절에 따라 다르게 인식되는지 검증

        **가설**: 점성 제형의 긍정 평가가 가을(9월)부터 증가할 것
        """)

        if 'MONTH' in analysis.df.columns and 'TEXTURE_VALUE' in analysis.df.columns and 'OVERALL_SENTIMENT' in analysis.df.columns:
            result = analysis.idea2_texture_seasonality()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=result.index,
                y=result['긍정 비율'],
                mode='lines+markers',
                name='긍정 비율',
                line=dict(color='#E67E22', width=3),
                marker=dict(size=10)
            ))
            fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
            fig.update_layout(
                title="점성 제형의 월별 긍정 비율",
                xaxis_title="월",
                yaxis_title="긍정 비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 3
    elif "IDEA 3" in selected_idea:
        st.subheader("💡 IDEA 3: 보습 만족은 줄어도 불만은 여름에 증가한다")
        st.markdown("""
        **분석 목표**: 여름철에 보습 관련 불만이 증가하는지 검증

        **가설**: 보습 부정 또는 전체 부정 리뷰가 여름(6-8월)에 증가할 것
        """)

        if 'MONTH' in analysis.df.columns and 'MOISTURE_SENTIMENT' in analysis.df.columns and 'OVERALL_SENTIMENT' in analysis.df.columns:
            result = analysis.idea3_moisture_summer_dissatisfaction()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result.index,
                y=result['비율'],
                name='불만 비율',
                marker_color='#E74C3C'
            ))
            fig.update_layout(
                title="월별 보습/전체 부정 리뷰 비율",
                xaxis_title="월",
                yaxis_title="비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 4
    elif "IDEA 4" in selected_idea:
        st.subheader("💡 IDEA 4: 산뜻함 선호와 보습 불만이 동시에 발생한다")
        st.markdown("""
        **분석 목표**: 산뜻함을 원하면서 동시에 보습 불만을 표현하는 리뷰가 함께 증가하는지 검증

        **가설**: 산뜻+보습불만 리뷰와 각각의 발생이 같은 월에 증가할 것
        """)

        if 'MONTH' in analysis.df.columns and 'FINISH_SENTIMENT' in analysis.df.columns and 'MOISTURE_SENTIMENT' in analysis.df.columns:
            result = analysis.idea4_freshness_moisture_conflict()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result.index,
                y=result['산뜻+보습불만 동시'],
                name='산뜻+보습불만 동시',
                marker_color='#9B59B6'
            ))
            fig.add_trace(go.Scatter(
                x=result.index,
                y=result['산뜻긍정'],
                name='산뜻긍정',
                mode='lines+markers',
                yaxis='y2'
            ))
            fig.update_layout(
                title="산뜻함과 보습 불만의 관계",
                xaxis_title="월",
                yaxis_title="동시 발생 수",
                yaxis2=dict(title="산뜻긍정 수", overlaying='y', side='right'),
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 5
    elif "IDEA 5" in selected_idea:
        st.subheader("💡 IDEA 5: 향은 계절 무관, 특정 월에만 이슈로 터진다")
        st.markdown("""
        **분석 목표**: 향에 대한 불만이 특정 월에 집중적으로 발생하는지 검증

        **가설**: 향 부정 리뷰가 계절과 무관하게 특정 월에만 spike를 보일 것
        """)

        if 'MONTH' in analysis.df.columns and 'SCENT_SENTIMENT' in analysis.df.columns:
            result = analysis.idea5_scent_seasonality()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result.index,
                y=result['비율'],
                name='향 부정 비율',
                marker_color='#1ABC9C'
            ))
            fig.update_layout(
                title="월별 향 부정 리뷰 비율",
                xaxis_title="월",
                yaxis_title="비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 6
    elif "IDEA 6" in selected_idea:
        st.subheader("💡 IDEA 6: 무난한 평가는 신규 유입기에서 증가한다")
        st.markdown("""
        **분석 목표**: 신규 구매 고객이 "무난하다"는 표현을 더 많이 사용하는지 검증

        **가설**: 신규 구매 리뷰 중 "무난"이 포함된 비율이 일정 시기에 증가할 것
        """)

        if 'MONTH' in analysis.df.columns and 'ONE_LINE_SUMMARY' in analysis.df.columns and 'PURCHASE_TYPE' in analysis.df.columns:
            result = analysis.idea6_neutral_new_purchase()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result.index,
                y=result['신규대비비율'],
                name='신규 대비 무난 비율',
                marker_color='#F39C12'
            ))
            fig.update_layout(
                title="월별 신규 구매 리뷰의 '무난' 표현 비율",
                xaxis_title="월",
                yaxis_title="비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 7
    elif "IDEA 7" in selected_idea:
        st.subheader("💡 IDEA 7: 지성 피부는 여름에 마무리에 민감해진다")
        st.markdown("""
        **분석 목표**: 지성 피부 고객이 마무리감에 대해 여름에 더 민감해지는지 검증

        **가설**: 지성 피부 + 마무리 부정 리뷰의 비율이 여름(6-8월)에 증가할 것
        """)

        if 'MONTH' in analysis.df.columns and 'SKIN_TYPE_FINAL' in analysis.df.columns and 'FINISH_SENTIMENT' in analysis.df.columns:
            result = analysis.idea7_oily_skin_finish_sensitivity()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=result.index,
                y=result['비율'],
                mode='lines+markers',
                name='지성+마무리부정 비율',
                line=dict(color='#E74C3C', width=3),
                marker=dict(size=10)
            ))
            fig.update_layout(
                title="지성 피부의 월별 마무리감 불만 비율",
                xaxis_title="월",
                yaxis_title="비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 8
    elif "IDEA 8" in selected_idea:
        st.subheader("💡 IDEA 8: 자극 이슈는 특정 월에 집중적으로 발생한다")
        st.markdown("""
        **분석 목표**: 자극 관련 문제가 특정 월에 집중적으로 보고되는지 검증

        **가설**: 자극 문제 리뷰가 계절과 무관하게 특정 월에만 증가할 것
        """)

        if 'MONTH' in analysis.df.columns and 'IRRITATION_VALUE' in analysis.df.columns:
            result = analysis.idea8_irritation_spike()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result.index,
                y=result['비율'],
                name='자극 이슈 비율',
                marker_color='#E74C3C'
            ))
            fig.update_layout(
                title="월별 자극 이슈 리뷰 비율",
                xaxis_title="월",
                yaxis_title="비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 9
    elif "IDEA 9" in selected_idea:
        st.subheader("💡 IDEA 9: 가성비 평가는 불만을 완충한다")
        st.markdown("""
        **분석 목표**: 가성비를 언급한 리뷰가 전체 평가에 더 긍정적인지 검증

        **가설**: 가성비 언급 리뷰의 긍정 비율이 전체 긍정 비율보다 높을 것
        """)

        if 'MONTH' in analysis.df.columns and 'ONE_LINE_SUMMARY' in analysis.df.columns and 'OVERALL_SENTIMENT' in analysis.df.columns:
            result = analysis.idea9_value_for_money_buffering()
            st.dataframe(result, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=result.index,
                y=(result['가성비 긍정'] / (result['가성비 긍정'] + result['가성비 부정'] + 1) * 100),
                mode='lines+markers',
                name='가성비 언급 긍정 비율',
                line=dict(color='#2ECC71', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=result.index,
                y=(result['전체 긍정'] / (result['전체 긍정'] + result['전체 부정'] + 1) * 100),
                mode='lines+markers',
                name='전체 긍정 비율',
                line=dict(color='#95A5A6', width=2, dash='dash')
            ))
            fig.update_layout(
                title="가성비 언급 여부에 따른 긍정 비율 비교",
                xaxis_title="월",
                yaxis_title="긍정 비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

    # IDEA 10
    elif "IDEA 10" in selected_idea:
        st.subheader("💡 IDEA 10: 재구매 리뷰는 계절 영향이 작다")
        st.markdown("""
        **분석 목표**: 재구매 고객의 평가가 신규 고객보다 계절 변화에 덜 민감한지 검증

        **가설**: 재구매 리뷰의 월별 속성 평가 변화 표준편차가 전체 리뷰보다 작을 것
        """)

        if 'MONTH' in analysis.df.columns and 'PURCHASE_TYPE' in analysis.df.columns:
            result, repurchase_monthly, overall_monthly = analysis.idea10_repurchase_seasonal_resilience()

            col1, col2 = st.columns(2)

            with col1:
                st.write("**표준편차 비교**")
                st.dataframe(result, use_container_width=True)

            with col2:
                st.write("**속성별 월간 긍정 비율 비교**")
                comparison_data = pd.DataFrame({
                    '재구매': repurchase_monthly['OVERALL_SENTIMENT'],
                    '전체': overall_monthly['OVERALL_SENTIMENT']
                })
                st.dataframe(comparison_data, use_container_width=True)

            # 시각화
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=repurchase_monthly.index,
                y=repurchase_monthly['OVERALL_SENTIMENT'],
                mode='lines+markers',
                name='재구매 긍정 비율',
                line=dict(color='#2ECC71', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=overall_monthly.index,
                y=overall_monthly['OVERALL_SENTIMENT'],
                mode='lines+markers',
                name='전체 긍정 비율',
                line=dict(color='#95A5A6', width=2, dash='dash')
            ))
            fig.update_layout(
                title="재구매 vs 전체 리뷰의 월별 긍정 비율 안정성",
                xaxis_title="월",
                yaxis_title="긍정 비율 (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            st.info("""
            **해석**:
            - 재구매 리뷰의 표준편차가 더 작다면 → 계절 영향이 적다
            - 재구매 리뷰의 표준편차가 더 크다면 → 계절 영향이 크다
            """)
        else:
            st.warning("필요한 컬럼 데이터가 부족합니다.")

# ===== PAGE 3: 월별 속성 분석 =====
elif page == "📋 월별 속성 분석":
    st.title("📋 월별 속성별 감성 분석")
    st.markdown(f"### 📦 제품: {selected_product}")
    st.markdown("---")

    # 월별 속성 감성 테이블
    monthly_attribute = analysis.get_monthly_attribute_sentiment_table()

    st.subheader("월별 속성별 긍정 비율 (%)")
    st.dataframe(monthly_attribute, use_container_width=True)

    st.markdown("---")

    if len(monthly_attribute) > 0 and len(monthly_attribute.columns) > 0:
        # 히트맵 시각화
        fig = px.imshow(
            monthly_attribute.T,
            labels=dict(x="월", y="속성", color="긍정 비율 (%)"),
            x=monthly_attribute.index,
            y=monthly_attribute.columns,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            height=400
        )
        fig.update_layout(title="월별 × 속성별 긍정 비율 히트맵")
        st.plotly_chart(fig, use_container_width=True)

        # 속성별 월간 추이
        st.markdown("---")
        st.subheader("속성별 월간 긍정 비율 추이")

        attributes = monthly_attribute.columns.tolist()
        selected_attributes = st.multiselect(
            "분석할 속성을 선택하세요",
            attributes,
            default=attributes[:3] if len(attributes) > 0 else []
        )

        if selected_attributes:
            fig_attribute = go.Figure()
            for attr in selected_attributes:
                fig_attribute.add_trace(go.Scatter(
                    x=monthly_attribute.index,
                    y=monthly_attribute[attr],
                    mode='lines+markers',
                    name=attr,
                    marker=dict(size=8)
                ))

            fig_attribute.update_layout(
                title="속성별 월간 긍정 비율 추이",
                xaxis_title="월",
                yaxis_title="긍정 비율 (%)",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig_attribute, use_container_width=True)
    else:
        st.info("월별 데이터가 부족합니다.")

# ===== PAGE 4: 상세 데이터 =====
elif page == "📑 상세 데이터":
    st.title("📑 상세 데이터")
    st.markdown(f"### 📦 제품: {selected_product}")
    st.markdown("---")

    # 데이터 필터링
    col1, col2, col3 = st.columns(3)

    months_available = sorted(analysis.df['MONTH'].dropna().unique().astype(int)) if 'MONTH' in analysis.df.columns else list(range(1, 13))

    with col1:
        selected_month = st.multiselect(
            "월 선택",
            months_available,
            default=months_available
        )

    sentiment_options = analysis.df['OVERALL_SENTIMENT'].dropna().unique().tolist() if 'OVERALL_SENTIMENT' in analysis.df.columns else []
    with col2:
        selected_sentiment = st.multiselect(
            "감정 선택",
            sentiment_options,
            default=sentiment_options
        )

    skin_options = analysis.df['SKIN_TYPE_FINAL'].dropna().unique().tolist()[:10] if 'SKIN_TYPE_FINAL' in analysis.df.columns else []
    with col3:
        selected_skin = st.multiselect(
            "피부 타입 선택",
            skin_options,
            default=skin_options[:3] if len(skin_options) > 0 else []
        )

    # 필터링된 데이터
    filtered_df = analysis.df.copy()

    if 'MONTH' in filtered_df.columns and selected_month:
        filtered_df = filtered_df[filtered_df['MONTH'].isin(selected_month)]
    if 'OVERALL_SENTIMENT' in filtered_df.columns and selected_sentiment:
        filtered_df = filtered_df[filtered_df['OVERALL_SENTIMENT'].isin(selected_sentiment)]
    if 'SKIN_TYPE_FINAL' in filtered_df.columns and selected_skin:
        filtered_df = filtered_df[filtered_df['SKIN_TYPE_FINAL'].isin(selected_skin)]

    # 필터 결과
    st.info(f"📊 필터링 결과: {len(filtered_df):,}개의 리뷰")

    # 주요 컬럼만 선택해서 표시
    display_columns = [
        '리뷰등록일', 'ONE_LINE_SUMMARY', 'OVERALL_SENTIMENT',
        'ABSORPTION_SENTIMENT', 'FINISH_SENTIMENT', 'MOISTURE_SENTIMENT',
        'SCENT_SENTIMENT', 'PURCHASE_TYPE', 'SKIN_TYPE_FINAL'
    ]

    # 존재하는 컬럼만 선택
    existing_columns = [col for col in display_columns if col in filtered_df.columns]

    if len(existing_columns) > 0:
        st.dataframe(
            filtered_df[existing_columns].sort_values('리뷰등록일', ascending=False) if '리뷰등록일' in existing_columns else filtered_df[existing_columns],
            use_container_width=True,
            height=400
        )

        # 다운로드 버튼
        csv = filtered_df[existing_columns].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 필터링된 데이터 다운로드 (CSV)",
            data=csv,
            file_name=f"filtered_toner_reviews_{selected_product}.csv",
            mime="text/csv"
        )

        # 통계
        st.markdown("---")
        st.subheader("필터링된 데이터 통계")

        col1, col2, col3, col4 = st.columns(4)

        if 'OVERALL_SENTIMENT' in filtered_df.columns:
            with col1:
                st.metric("긍정", (filtered_df['OVERALL_SENTIMENT'] == 'POSITIVE').sum())

            with col2:
                st.metric("중립", (filtered_df['OVERALL_SENTIMENT'] == 'NEUTRAL').sum())

            with col3:
                st.metric("부정", (filtered_df['OVERALL_SENTIMENT'] == 'NEGATIVE').sum())

            with col4:
                positive_ratio = (filtered_df['OVERALL_SENTIMENT'] == 'POSITIVE').sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
                st.metric("긍정 비율", f"{positive_ratio:.1f}%")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <small>💡 토너 리뷰 인사이트 도출 대시보드</small><br>
    <small>데이터 기반 제품별 인사이트 분석</small>
</div>
""", unsafe_allow_html=True)
