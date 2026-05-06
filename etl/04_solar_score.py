"""
Solar Site Score = weighted composite of 6 scientific factors.
Weights based on peer-reviewed solar site selection research.
"""

import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


def calculate_solar_site_score(
    weather_path: str = 'data/silver/weather_clean.csv',
    air_path: str     = 'data/silver/air_quality_clean.csv',
    output_path: str  = 'data/gold/solar_site_scores.csv'
) -> pd.DataFrame:

    # ── Load ─────────────────────────────────────────────
    logger.info("Loading cleaned datasets...")

    if not os.path.exists(weather_path) or not os.path.exists(air_path):
        logger.error("Missing silver files! Run cleaning scripts first.")
        raise FileNotFoundError("Missing silver files! Run cleaning scripts first.")

    weather = pd.read_csv(weather_path, parse_dates=['date'])
    air     = pd.read_csv(air_path)

    # ── Fix datetime column name issue (important fix) ───
    if 'datetime' in air.columns:
        air['datetime'] = pd.to_datetime(air['datetime'])
    elif 'date' in air.columns:
        air['datetime'] = pd.to_datetime(air['date'])

    # ── Validate required columns early ───────────────────
    required_weather_cols = [
        'ALLSKY_SFC_SW_DWN', 'clearness_index',
        'T2M_MAX', 'WS2M', 'RH2M'
    ]

    missing = [col for col in required_weather_cols if col not in weather.columns]
    if missing:
        raise ValueError(f"Missing columns in weather dataset: {missing}")

    # ── Aggregate weather ────────────────────────────────
    logger.info("Aggregating weather metrics by governorate...")

    w_agg = weather.groupby('governorate').agg(
        avg_clearness_index=('clearness_index', 'mean'),
        avg_peak_sun_hours=('peak_sun_hours', 'mean'),
        avg_solar_radiation=('ALLSKY_SFC_SW_DWN', 'mean'),

        avg_temp_penalty=('temp_penalty_pct', 'mean'),

        avg_temp_max=('T2M_MAX', 'mean'),
        avg_temp_range=('temp_range', 'mean'),

        avg_cloud_impact=('cloud_impact', 'mean'),
        avg_wind_speed=('WS2M', 'mean'),
        avg_humidity=('RH2M', 'mean'),
        
        hot_days_per_year=('is_hot_day', 'mean'),
        years_of_data=('year', 'nunique')
    ).reset_index()


    # ── Aggregate air quality ────────────────────────────
    logger.info("Aggregating air quality metrics by governorate...")

    aq_agg = air.groupby('governorate').agg(
        avg_aqi=('aqi', 'mean'),
        avg_pm25=('pm2_5', 'mean'),
        avg_pm10=('pm10', 'mean'),
    ).reset_index()

    # ── Merge ────────────────────────────────────────────
    df = w_agg.merge(aq_agg, on='governorate', how='left')
    logger.info(f"Merged dataset: {len(df)} governorates")

    # ── FIXED normalization function ──────────────────────
    def normalize(series, higher_is_better=True):
        mn, mx = series.min(), series.max()

        if pd.isna(mn) or pd.isna(mx) or mx == mn:
            return pd.Series(50, index=series.index)

        norm = (series - mn) / (mx - mn) * 100

        if not higher_is_better:
            norm = 100 - norm

        return norm.clip(0, 100)

    # ── Scores ────────────────────────────────────────────
    df['score_ghi']       = normalize(df['avg_solar_radiation'], True)
    df['score_clearness'] = normalize(df['avg_clearness_index'], True)
    df['score_temp']      = normalize(df['avg_temp_max'], False)
    df['score_wind']      = normalize(df['avg_wind_speed'], True)
    df['score_humidity']   = normalize(df['avg_humidity'], False)

    df['score_air'] = normalize(
        df['avg_aqi'].fillna(df['avg_aqi'].median()),
        False
    )

    # ── Weights ──────────────────────────────────────────
    WEIGHTS = {
        'score_ghi': 0.35,
        'score_clearness': 0.20,
        'score_temp': 0.15,
        'score_air': 0.15,
        'score_wind': 0.10,
        'score_humidity': 0.05,
    }

    df['solar_site_score'] = sum(
        df[col] * weight for col, weight in WEIGHTS.items()
    ).round(2)

    # ── Rank ─────────────────────────────────────────────
    df['rank'] = df['solar_site_score'].rank(
        ascending=False, method='dense'
    ).astype(int)

    # ── Recommendation ───────────────────────────────────
    def recommendation(score):
        if score >= 75:
            return 'Strongly Recommended'
        elif score >= 60:
            return 'Recommended'
        elif score >= 50:
            return 'Neutral'
        else:
            return 'Not Recommended'

    df['investment_recommendation'] = df['solar_site_score'].apply(recommendation)

    # FIX: grade column was missing
    def grade(score):
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

    df['grade'] = df['solar_site_score'].apply(grade)

    # ── Save ─────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    logger.info(f"Saved to {output_path}")

    # ── Top 10 ───────────────────────────────────────────
    print("\n" + "="*60)
    print("SOLAR SITE SCORE RANKING — TOP 10")
    print("="*60)

    top_10 = df.sort_values('rank').head(10)[
        ['rank', 'governorate', 'solar_site_score', 'grade']
    ]

    print(top_10.to_string(index=False))

    return df


if __name__ == '__main__':
    calculate_solar_site_score()