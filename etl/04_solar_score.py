"""
SolarIQ Egypt — Gold Layer: Solar Site Scoring (Full Robust Version)
FIXED: Column name mismatch and KeyError handling.
Weights based on peer-reviewed solar site selection research.
"""

import pandas as pd
import numpy as np
import logging
import os

# ── Setup ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def calculate_solar_site_score(
    weather_path: str = 'data/silver/weather_clean.csv',
    air_path: str     = 'data/silver/air_quality_clean.csv',
    output_path: str  = 'data/gold/solar_site_scores.csv'
) -> pd.DataFrame:

    # ── 1. Load Data ─────────────────────────────────────
    logger.info("Loading silver datasets...")
    if not os.path.exists(weather_path) or not os.path.exists(air_path):
        logger.error("Missing silver files! Please run cleaning scripts first.")
        raise FileNotFoundError("Missing silver files!")

    weather = pd.read_csv(weather_path)
    air     = pd.read_csv(air_path)

    # تنظيف أسماء الأعمدة (إزالة المسافات وتحويلها لصغير لضمان المطابقة)
    weather.columns = [c.strip().lower() for c in weather.columns]
    air.columns = [c.strip().lower() for c in air.columns]

    # ── 2. Aggregate Weather ────────────────────────────
    logger.info("Aggregating weather metrics...")
    
    # التأكد من وجود عمود peak_sun_hours أو حسابه من الإشعاع
    if 'peak_sun_hours' not in weather.columns:
        if 'allsky_sfc_sw_dwn' in weather.columns:
            weather['peak_sun_hours'] = weather['allsky_sfc_sw_dwn']
        else:
            logger.error("Critical column 'allsky_sfc_sw_dwn' missing in weather data!")

    w_agg = weather.groupby('governorate').agg(
        avg_solar_radiation=('allsky_sfc_sw_dwn', 'mean'),
        avg_peak_sun_hours=('peak_sun_hours', 'mean'),
        # معالجة اختلاف أسماء الأعمدة (clearness vs clearness_index)
        avg_clearness=('clearness_index', 'mean') if 'clearness_index' in weather.columns else ('clearness', 'mean'),
        avg_temp_max=('t2m_max', 'mean'),
        avg_temp_range=('temp_range', 'mean') if 'temp_range' in weather.columns else ('t2m_max', 'std'),
        avg_cloud_impact=('cloud_impact', 'mean') if 'cloud_impact' in weather.columns else ('clearness', 'std'),
        avg_wind_speed=('ws2m', 'mean'),
        avg_humidity=('rh2m', 'mean'),
        # معالجة اختلاف أسماء الأعمدة (temp_pen vs temp_penalty_pct)
        avg_temp_penalty=('temp_penalty_pct', 'mean') if 'temp_penalty_pct' in weather.columns else ('temp_pen', 'mean'),
        hot_days_per_year=('is_hot_day', 'mean')
    ).reset_index()

    # ── 3. Aggregate Air Quality ───────────────────────
    logger.info("Aggregating air quality metrics...")
    
    # التوافق مع ملف air_quality_clean.csv الجديد
    aq_agg = air.groupby('governorate').agg(
        avg_aqi=('aqi_level', 'mean') if 'aqi_level' in air.columns else ('aqi', 'mean'),
        avg_pm25=('pm2_5', 'mean'),
        avg_pm10=('pm10', 'mean'),
        avg_no2=('nitrogen_dioxide', 'mean') if 'nitrogen_dioxide' in air.columns else ('no2', 'mean'),
        avg_so2=('sulphur_dioxide', 'mean') if 'sulphur_dioxide' in air.columns else ('so2', 'mean')
    ).reset_index()

    # ── 4. Merge ─────────────────────────────────────────
    df = w_agg.merge(aq_agg, on='governorate', how='left')
    logger.info(f"Merged dataset contains {len(df)} governorates.")

    # ── 5. Normalization Logic ──────────────────────────
    def normalize(series, higher_is_better=True):
        mn, mx = series.min(), series.max()
        if mn == mx or pd.isna(mn): return pd.Series(50, index=series.index)
        norm = (series - mn) / (mx - mn) * 100
        return norm if higher_is_better else 100 - norm

    # ── 6. Scientific Scoring ────────────────────────────
    # تحويل القيم لدرجات من 0 لـ 100
    df['score_ghi']       = normalize(df['avg_solar_radiation'], True)
    df['score_clearness'] = normalize(df['avg_clearness'], True)
    df['score_temp']      = normalize(df['avg_temp_max'], False)
    df['score_wind']      = normalize(df['avg_wind_speed'], True)
    df['score_humidity']  = normalize(df['avg_humidity'], False)
    df['score_air']       = normalize(df['avg_aqi'].fillna(df['avg_aqi'].median()), False)

    # أوزان العوامل (Weights)
    WEIGHTS = {
        'score_ghi': 0.35,       # Solar Radiation
        'score_clearness': 0.20, # Atmospheric Clarity
        'score_temp': 0.15,      # Heat Penalty
        'score_air': 0.15,       # Air Quality/Dust
        'score_wind': 0.10,      # Wind Cooling
        'score_humidity': 0.05,  # Humidity/Corrosion
    }

    df['solar_site_score'] = sum(df[col] * weight for col, weight in WEIGHTS.items()).round(2)

    # ── 7. Ranking & Recommendations ─────────────────────
    df['rank'] = df['solar_site_score'].rank(ascending=False, method='dense').astype(int)

    def get_recommendation(score):
        if score >= 75: return 'Strongly Recommended'
        if score >= 60: return 'Recommended'
        if score >= 50: return 'Neutral'
        return 'Not Recommended'

    def get_grade(score):
        if score >= 80: return 'A+'
        if score >= 70: return 'A'
        if score >= 60: return 'B'
        if score >= 50: return 'C'
        return 'D'

    df['investment_reco'] = df['solar_site_score'].apply(get_recommendation)
    df['grade'] = df['solar_site_score'].apply(get_grade)

    # ── 8. Save Final Gold Table ─────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"SUCCESS: Gold layer saved to {output_path}")

    # Print Summary for Verification
    print("\n" + "="*50)
    print("TOP GOVERNORATES FOR SOLAR INVESTMENT")
    print("="*50)
    print(df.sort_values('rank').head(5)[['rank', 'governorate', 'solar_site_score', 'grade']])
    
    return df

if __name__ == '__main__':
    calculate_solar_site_score()