"""
토너 리뷰 인사이트 도출 분석 모듈
10가지 핵심 인사이트를 월별 트렌드와 결합하여 분석
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class TinerInsightAnalysis:
    def __init__(self, csv_path):
        """데이터 로드 및 초기화"""
        try:
            self.df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            self.df = pd.read_csv(csv_path, encoding='cp949')
        self.product_list = []
        self._prepare_data()

    def get_products(self):
        """제품 목록 반환"""
        if '브랜드명' in self.df.columns:
            self.product_list = self.df['브랜드명'].unique().tolist()
            return self.product_list
        return []

    def get_product_data(self, product_name):
        """제품별 데이터 반환"""
        if '브랜드명' in self.df.columns:
            return self.df[self.df['브랜드명'] == product_name].copy()
        return self.df.copy()

    def _prepare_data(self):
        """데이터 전처리"""
        # 날짜 변환
        if '리뷰등록일' in self.df.columns:
            self.df['리뷰등록일'] = pd.to_datetime(self.df['리뷰등록일'], errors='coerce')
            self.df['YEAR_MONTH'] = self.df['리뷰등록일'].dt.to_period('M')
            self.df['MONTH'] = self.df['리뷰등록일'].dt.month

        # 감정 정규화
        if 'OVERALL_SENTIMENT' in self.df.columns:
            self.df['OVERALL_SENTIMENT'] = self.df['OVERALL_SENTIMENT'].fillna('NEUTRAL').str.upper()
        if 'ABSORPTION_SENTIMENT' in self.df.columns:
            self.df['ABSORPTION_SENTIMENT'] = self.df['ABSORPTION_SENTIMENT'].fillna('NEUTRAL').str.upper()
        if 'FINISH_SENTIMENT' in self.df.columns:
            self.df['FINISH_SENTIMENT'] = self.df['FINISH_SENTIMENT'].fillna('NEUTRAL').str.upper()
        if 'MOISTURE_SENTIMENT' in self.df.columns:
            self.df['MOISTURE_SENTIMENT'] = self.df['MOISTURE_SENTIMENT'].fillna('NEUTRAL').str.upper()
        if 'SCENT_SENTIMENT' in self.df.columns:
            self.df['SCENT_SENTIMENT'] = self.df['SCENT_SENTIMENT'].fillna('NEUTRAL').str.upper()

        # 피부 타입 정규화
        if 'SKIN_TYPE_FINAL' in self.df.columns:
            self.df['SKIN_TYPE_FINAL'] = self.df['SKIN_TYPE_FINAL'].fillna('미분류')

        # 구매 유형 정규화
        if 'PURCHASE_TYPE' in self.df.columns:
            self.df['PURCHASE_TYPE'] = self.df['PURCHASE_TYPE'].fillna('미분류')

    # ===== IDEA 1: 흡수력과 재구매의 관계 =====
    def idea1_absorption_repurchase(self):
        """흡수력은 재구매의 핵심이며, 여름에 더 중요해진다"""
        # 재구매 + 흡수 긍정인 리뷰 필터링
        filtered = self.df[
            (self.df['ABSORPTION_SENTIMENT'] == 'POSITIVE') &
            (self.df['PURCHASE_TYPE'].str.contains('재구매', na=False))
        ].copy()

        # 월별 비율 계산
        monthly_repurchase = self.df[
            self.df['PURCHASE_TYPE'].str.contains('재구매', na=False)
        ].groupby('MONTH').size()

        monthly_absorption_positive = filtered.groupby('MONTH').size()

        result = pd.DataFrame({
            '총 재구매 리뷰': monthly_repurchase,
            '흡수 긍정 비율': (monthly_absorption_positive / monthly_repurchase * 100).round(2)
        }).fillna(0)

        return result

    # ===== IDEA 2: 점성 제형과 계절의 관계 =====
    def idea2_texture_seasonality(self):
        """점성 제형은 가을·겨울에만 긍정으로 인식된다"""
        # 점성/쫀쫀 제형 필터링
        filtered = self.df[
            self.df['TEXTURE_VALUE'].isin(['점성', '쫀쫀'])
        ].copy()

        # 월별 긍정 비율
        monthly_sentiment = filtered.groupby('MONTH').agg({
            'OVERALL_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100
        }).round(2)
        monthly_sentiment.columns = ['긍정 비율']

        return monthly_sentiment

    # ===== IDEA 3: 보습 만족과 여름철 불만 =====
    def idea3_moisture_summer_dissatisfaction(self):
        """보습 만족은 줄어도 불만은 여름에 증가한다"""
        # 보습 부정 + 전체 부정
        filtered = self.df[
            (self.df['MOISTURE_SENTIMENT'] == 'NEGATIVE') |
            (self.df['OVERALL_SENTIMENT'] == 'NEGATIVE')
        ].copy()

        monthly_count = filtered.groupby('MONTH').size()
        monthly_ratio = (monthly_count / self.df.groupby('MONTH').size() * 100).round(2)

        result = pd.DataFrame({
            '보습/전체 부정 리뷰': monthly_count,
            '비율': monthly_ratio
        }).fillna(0)

        return result

    # ===== IDEA 4: 산뜻함 선호와 보습 불만의 동시 발생 =====
    def idea4_freshness_moisture_conflict(self):
        """산뜻함 선호 증가와 보습 불만이 동시에 발생한다"""
        # 산뜻 + 보습 부정 필터링
        filtered = self.df[
            (self.df['FINISH_SENTIMENT'] == 'POSITIVE') &
            (self.df['MOISTURE_SENTIMENT'] == 'NEGATIVE')
        ].copy()

        monthly_count = filtered.groupby('MONTH').size()

        # 각각의 월별 비율도 계산
        finish_positive = self.df[self.df['FINISH_SENTIMENT'] == 'POSITIVE'].groupby('MONTH').size()
        moisture_negative = self.df[self.df['MOISTURE_SENTIMENT'] == 'NEGATIVE'].groupby('MONTH').size()

        result = pd.DataFrame({
            '산뜻+보습불만 동시': monthly_count,
            '산뜻긍정': finish_positive,
            '보습부정': moisture_negative
        }).fillna(0)

        return result

    # ===== IDEA 5: 향의 계절 무관성과 특정 월 이슈 =====
    def idea5_scent_seasonality(self):
        """향은 계절 무관, 특정 월에만 이슈로 터진다"""
        # 향 부정 필터링
        filtered = self.df[self.df['SCENT_SENTIMENT'] == 'NEGATIVE'].copy()

        monthly_count = filtered.groupby('MONTH').size()
        monthly_ratio = (monthly_count / self.df.groupby('MONTH').size() * 100).round(2)

        result = pd.DataFrame({
            '향부정': monthly_count,
            '비율': monthly_ratio
        }).fillna(0)

        return result

    # ===== IDEA 6: 무난함과 신규 유입의 관계 =====
    def idea6_neutral_new_purchase(self):
        """무난한 평가는 신규 유입기에서 증가한다"""
        # 무난 + 첫구매 필터링
        filtered = self.df[
            (self.df['ONE_LINE_SUMMARY'].str.contains('무난', na=False)) &
            (self.df['PURCHASE_TYPE'].str.contains('첫구매|신규', na=False, regex=True))
        ].copy()

        monthly_count = filtered.groupby('MONTH').size()

        # 신규 구매 총량 대비
        new_purchase = self.df[
            self.df['PURCHASE_TYPE'].str.contains('첫구매|신규', na=False, regex=True)
        ].groupby('MONTH').size()

        result = pd.DataFrame({
            '무난+신규': monthly_count,
            '신규총': new_purchase,
            '신규대비비율': (monthly_count / new_purchase * 100).round(2)
        }).fillna(0)

        return result

    # ===== IDEA 7: 지성 피부와 여름 마무리감 민감성 =====
    def idea7_oily_skin_finish_sensitivity(self):
        """지성 피부는 여름에 마무리에 민감해진다"""
        # 지성 피부 + 마무리 부정
        filtered = self.df[
            (self.df['SKIN_TYPE_FINAL'].str.contains('지성', na=False)) &
            (self.df['FINISH_SENTIMENT'] == 'NEGATIVE')
        ].copy()

        monthly_count = filtered.groupby('MONTH').size()

        # 지성 피부 총량 대비
        oily_skin = self.df[
            self.df['SKIN_TYPE_FINAL'].str.contains('지성', na=False)
        ].groupby('MONTH').size()

        result = pd.DataFrame({
            '지성+마무리부정': monthly_count,
            '지성총': oily_skin,
            '비율': (monthly_count / oily_skin * 100).round(2)
        }).fillna(0)

        return result

    # ===== IDEA 8: 자극 이슈의 월별 Spike 탐지 =====
    def idea8_irritation_spike(self):
        """자극 이슈는 특정 월에 집중적으로 발생한다"""
        # 자극 있음 필터링
        filtered = self.df[
            self.df['IRRITATION_VALUE'] != '없음'
        ].copy()

        monthly_count = filtered.groupby('MONTH').size()
        monthly_ratio = (monthly_count / self.df.groupby('MONTH').size() * 100).round(2)

        result = pd.DataFrame({
            '자극이슈': monthly_count,
            '비율': monthly_ratio
        }).fillna(0)

        return result

    # ===== IDEA 9: 가성비 평가와 불만 완충 =====
    def idea9_value_for_money_buffering(self):
        """가성비 평가는 불만을 완충한다"""
        # 가성비 언급 필터링
        filtered = self.df[
            self.df['ONE_LINE_SUMMARY'].str.contains('가성비', na=False)
        ].copy()

        # 가성비 언급 시 감정 분포
        sentiment_dist = filtered.groupby('MONTH')['OVERALL_SENTIMENT'].apply(
            lambda x: {
                'POSITIVE': (x == 'POSITIVE').sum(),
                'NEUTRAL': (x == 'NEUTRAL').sum(),
                'NEGATIVE': (x == 'NEGATIVE').sum()
            }
        )

        # 전체 감정 분포와 비교
        overall_dist = self.df.groupby('MONTH')['OVERALL_SENTIMENT'].apply(
            lambda x: {
                'POSITIVE': (x == 'POSITIVE').sum(),
                'NEUTRAL': (x == 'NEUTRAL').sum(),
                'NEGATIVE': (x == 'NEGATIVE').sum()
            }
        )

        result = pd.DataFrame({
            '가성비 긍정': [sentiment_dist[m]['POSITIVE'] if m in sentiment_dist.index else 0 for m in range(1, 13)],
            '가성비 부정': [sentiment_dist[m]['NEGATIVE'] if m in sentiment_dist.index else 0 for m in range(1, 13)],
            '전체 긍정': [overall_dist[m]['POSITIVE'] if m in overall_dist.index else 0 for m in range(1, 13)],
            '전체 부정': [overall_dist[m]['NEGATIVE'] if m in overall_dist.index else 0 for m in range(1, 13)]
        }, index=range(1, 13))

        return result

    # ===== IDEA 10: 재구매 리뷰의 계절 영향 적음 =====
    def idea10_repurchase_seasonal_resilience(self):
        """재구매 리뷰는 계절 영향이 작다"""
        # 재구매 리뷰
        repurchase = self.df[
            self.df['PURCHASE_TYPE'].str.contains('재구매', na=False)
        ].copy()

        # 재구매 속성별 변화의 표준편차
        repurchase_monthly = repurchase.groupby('MONTH').agg({
            'ABSORPTION_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
            'FINISH_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
            'MOISTURE_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
            'OVERALL_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100
        }).round(2)

        # 전체 리뷰
        overall_monthly = self.df.groupby('MONTH').agg({
            'ABSORPTION_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
            'FINISH_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
            'MOISTURE_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
            'OVERALL_SENTIMENT': lambda x: (x == 'POSITIVE').sum() / len(x) * 100
        }).round(2)

        # 표준편차 비교
        result = pd.DataFrame({
            '재구매_흡수_std': [repurchase_monthly['ABSORPTION_SENTIMENT'].std()],
            '전체_흡수_std': [overall_monthly['ABSORPTION_SENTIMENT'].std()],
            '재구매_마무리_std': [repurchase_monthly['FINISH_SENTIMENT'].std()],
            '전체_마무리_std': [overall_monthly['FINISH_SENTIMENT'].std()],
            '재구매_보습_std': [repurchase_monthly['MOISTURE_SENTIMENT'].std()],
            '전체_보습_std': [overall_monthly['MOISTURE_SENTIMENT'].std()],
            '재구매_전체_std': [repurchase_monthly['OVERALL_SENTIMENT'].std()],
            '전체_전체_std': [overall_monthly['OVERALL_SENTIMENT'].std()]
        }).round(2)

        return result, repurchase_monthly, overall_monthly

    # ===== 월별 × 속성 × 감성 지표 테이블 =====
    def get_monthly_attribute_sentiment_table(self):
        """월별 속성별 감성 지표"""
        attributes = [
            ('ABSORPTION_SENTIMENT', '흡수'),
            ('FINISH_SENTIMENT', '마무리'),
            ('MOISTURE_SENTIMENT', '보습'),
            ('TEXTURE_SENTIMENT', '제형'),
            ('SCENT_SENTIMENT', '향'),
            ('IRRITATION_SENTIMENT', '자극'),
            ('SOOTHING_SENTIMENT', '진정')
        ]

        results = {}
        for col, name in attributes:
            monthly = self.df.groupby('MONTH')[col].apply(
                lambda x: {
                    'POSITIVE': (x == 'POSITIVE').sum(),
                    'NEUTRAL': (x == 'NEUTRAL').sum(),
                    'NEGATIVE': (x == 'NEGATIVE').sum(),
                    'Total': len(x)
                }
            )

            positive_rate = []
            for m in range(1, 13):
                if m in monthly.index:
                    rate = monthly[m]['POSITIVE'] / monthly[m]['Total'] * 100 if monthly[m]['Total'] > 0 else 0
                    positive_rate.append(round(rate, 2))
                else:
                    positive_rate.append(0)

            results[name] = positive_rate

        return pd.DataFrame(results, index=range(1, 13))

    # ===== 종합 요약 =====
    def get_summary(self):
        """전체 분석 요약"""
        try:
            if '리뷰등록일' in self.df.columns:
                date_range = f"{self.df['리뷰등록일'].min().date()} ~ {self.df['리뷰등록일'].max().date()}"
            else:
                date_range = "데이터 확인 중"
        except:
            date_range = "데이터 확인 중"

        total = len(self.df)
        positive_count = (self.df['OVERALL_SENTIMENT'] == 'POSITIVE').sum() if 'OVERALL_SENTIMENT' in self.df.columns else 0
        negative_count = (self.df['OVERALL_SENTIMENT'] == 'NEGATIVE').sum() if 'OVERALL_SENTIMENT' in self.df.columns else 0
        neutral_count = (self.df['OVERALL_SENTIMENT'] == 'NEUTRAL').sum() if 'OVERALL_SENTIMENT' in self.df.columns else 0

        return {
            'total_reviews': total,
            'date_range': date_range,
            'positive_ratio': f"{positive_count / total * 100:.2f}%" if total > 0 else "0%",
            'negative_ratio': f"{negative_count / total * 100:.2f}%" if total > 0 else "0%",
            'neutral_ratio': f"{neutral_count / total * 100:.2f}%" if total > 0 else "0%"
        }


if __name__ == '__main__':
    # 분석 실행
    analysis = TinerInsightAnalysis('data/올영리뷰_토너.csv')

    print("=== 토너 리뷰 인사이트 분석 ===\n")
    print("IDEA 1: 흡수력과 재구매의 관계")
    print(analysis.idea1_absorption_repurchase())
    print("\nIDEA 2: 점성 제형과 계절의 관계")
    print(analysis.idea2_texture_seasonality())
