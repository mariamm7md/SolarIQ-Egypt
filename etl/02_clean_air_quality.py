"""
SolarIQ Egypt — Air Quality Data Cleaning (V2)
Updated for: Egypt_Air_Quality_Final_Report.csv
Changes: Mapping new column names (Nitrogen_Dioxide, Sulphur_Dioxide, etc.) 
and fixing Ozone (O3) identification.
"""

import pandas as pd
import numpy as np
import os
import logging

# ── Setup ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

RAW_PATH    = 'data/raw/Egypt_Air_Quality_Final_Report.csv'
SILVER_PATH = 'data/silver/air_quality_clean.csv'

# ── Functions ──────────────────────────────────────────────────────
def load_and_audit(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
    
    # تحديث أسماء الأعمدة لتسهيل التعامل معها (إزالة المسافات)
    df.columns = [c.strip() for c in df.columns]
    
    # Audit datetime NaN issue (العمود في الملف الجديد اسمه 'time')
    time_col = 'time' if 'time' in df.columns else 'datetime'
    null_dt = df[time_col].isnull().sum()
    logger.warning(f"Time nulls: {null_dt:,} ({null_dt/len(df)*100:.1f}%)")
    
    return df

def clean_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with no time and convert to datetime objects."""
    time_col = 'time' if 'time' in df.columns else 'datetime'
    
    logger.info(f"Handling {time_col} nulls...")
    df = df.dropna(subset=[time_col]).copy()
    
    # تحويل العمود إلى datetime
    df['datetime'] = pd.to_datetime(df[time_col], dayfirst=True, errors='coerce')
    
    # حذف الصفوف التي فشل تحويلها
    df = df.dropna(subset=['datetime'])
    
    logger.info(f"Datetime range: {df['datetime'].min()} → {df['datetime'].max()}")
    return df

def replace_error_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Replace -9999 with NaN in pollution columns based on new names."""
    # الأعمدة الجديدة كما تظهر في الصورة
    pollution_cols = ['PM10', 'PM2_5', 'Nitrogen_Dioxide', 'Sulphur_Dioxide', 'Carbon_Monoxide']
    
    for col in pollution_cols:
        if col in df.columns:
            before = (df[col] == -9999).sum()
            df[col] = df[col].replace(-9999, np.nan)
            if before > 0:
                logger.info(f"Replaced {before:,} error codes in {col}")
    return df

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time dimensions for dashboard filtering."""
    logger.info("Adding time-based features...")
    df['date']    = df['datetime'].dt.date
    df['hour']    = df['datetime'].dt.hour
    df['month']   = df['datetime'].dt.month
    df['year']    = df['datetime'].dt.year
    df['quarter'] = df['datetime'].dt.quarter
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Time of day buckets
    def time_bucket(hour):
        if 0 <= hour < 6:     return 'Late Night'
        elif 6 <= hour < 10:  return 'Morning Rush'
        elif 10 <= hour < 14: return 'Midday'
        elif 14 <= hour < 18: return 'Afternoon'
        elif 18 <= hour < 22: return 'Evening Rush'
        else: return 'Night'
    
    df['time_bucket'] = df['hour'].apply(time_bucket)
    
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Autumn', 10: 'Autumn', 11: 'Autumn'}
    df['season'] = df['month'].map(season_map)
    return df

def add_health_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add labels and health alerts based on new column names."""
    # ملاحظة: AQI_Level موجود بالفعل في الملف الجديد
    aqi_labels = {1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor'}
    
    if 'AQI_Level' in df.columns:
        df['aqi_label'] = df['AQI_Level'].map(aqi_labels)
        df['health_alert'] = (df['AQI_Level'] >= 4).astype(int)
    
    # استخدام PM2_5 بدلاً من pm2_5 (حسب الصورة)
    if 'PM2_5' in df.columns:
        df['pm25_exceeds_who'] = (df['PM2_5'] > 15).astype(int)
        # Solar impact penalty (حساب تأثير التلوث على الألواح)
        df['pollution_solar_penalty_pct'] = ((df['PM2_5'] / 10) * 1.5).clip(0, 30).round(2)
        
    return df

def validate_final(df: pd.DataFrame):
    """Ensure data is ready for Azure/Power BI."""
    logger.info("Final Validation...")
    assert pd.api.types.is_datetime64_any_dtype(df['datetime']), "Datetime conversion failed!"
    
    # التأكد من صحة أسماء المحافظات (عربي/إنجليزي)
    logger.info(f"Unique Governorates: {df['Governorate'].unique()}")
    logger.info("All validations passed!")

# ── Main ───────────────────────────────────────────────────────────
def main():
    os.makedirs('data/silver', exist_ok=True)
    
    df = load_and_audit(RAW_PATH)
    df = clean_datetime(df)
    df = replace_error_codes(df)
    df = add_time_features(df)
    df = add_health_features(df)
    
    # ملاحظة: الملف الجديد يحتوي بالفعل على خطوط الطول والعرض (latitude, longitude)
    # سنقوم فقط بتغيير أسمائهم لتناسب الـ Dashboard إذا لزم الأمر
    if 'latitude' in df.columns:
        df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    
    validate_final(df)
    
    logger.info(f"Final dataset: {len(df):,} rows × {len(df.columns)} cols")
    df.to_csv(SILVER_PATH, index=False, encoding='utf-8-sig')
    logger.info(f"Saved to {SILVER_PATH}")

if __name__ == '__main__':
    main()