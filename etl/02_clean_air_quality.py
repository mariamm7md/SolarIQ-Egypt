"""
SolarIQ Egypt — Air Quality Data Cleaning
FIXED: Added dayfirst=True for Egyptian date formats and robust datetime validation.
"""

import pandas as pd
import numpy as np
import os
import logging

# ── Setup ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

RAW_PATH    = 'data/raw/egypt_air_quality_clean.csv'
SILVER_PATH = 'data/silver/air_quality_clean.csv'

# ── Functions ──────────────────────────────────────────────────────
def load_and_audit(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
    
    # Audit datetime NaN issue
    null_dt = df['datetime'].isnull().sum()
    logger.warning(f"datetime nulls: {null_dt:,} "
                   f"({null_dt/len(df)*100:.1f}%) ← THE BIG PROBLEM")
    
    # Audit -9999 error codes
    error_cols = ['pm10', 'no2', 'o3']
    for col in error_cols:
        if col in df.columns:
            count = (df[col] == -9999).sum()
            logger.warning(f"{col} has {count:,} values = -9999")
    
    return df

def clean_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with no datetime and convert to datetime objects."""
    logger.info("Handling datetime nulls...")
    before = len(df)
    df = df.dropna(subset=['datetime']).copy() # Use copy to avoid SettingWithCopyWarning
    after = len(df)
    logger.info(f"Dropped {before - after:,} rows (no datetime). Kept: {after:,}")
    
    # FIXED: Added dayfirst=True to handle formats like 13/01/2021 correctly
    df['datetime'] = pd.to_datetime(df['datetime'], dayfirst=True, errors='coerce')
    
    # Drop rows that failed conversion (if any)
    df = df.dropna(subset=['datetime'])
    
    logger.info(f"Datetime range: {df['datetime'].min()} → {df['datetime'].max()}")
    return df

def replace_error_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Replace -9999 with NaN in pollution columns."""
    error_cols = ['pm10', 'no2', 'o3']
    for col in error_cols:
        if col in df.columns:
            before = (df[col] == -9999).sum()
            df[col] = df[col].replace(-9999, np.nan)
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
        if 0 <= hour < 6:    return 'Late Night'
        elif 6 <= hour < 10: return 'Morning Rush'
        elif 10 <= hour < 14: return 'Midday'
        elif 14 <= hour < 18: return 'Afternoon'
        elif 18 <= hour < 22: return 'Evening Rush'
        else: return 'Night'
    
    df['time_bucket'] = df['hour'].apply(time_bucket)
    
    season_map = {
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3:  'Spring', 4: 'Spring', 5: 'Spring',
        6:  'Summer', 7: 'Summer', 8: 'Summer',
        9:  'Autumn', 10: 'Autumn', 11: 'Autumn'
    }
    df['season'] = df['month'].map(season_map)
    return df

def add_health_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add WHO health classification columns."""
    aqi_labels = {1: 'Good', 2: 'Fair', 3: 'Moderate',
                  4: 'Poor', 5: 'Very Poor'}
    df['aqi_label'] = df['aqi'].map(aqi_labels)
    df['health_alert'] = (df['aqi'] >= 4).astype(int)
    df['pm25_exceeds_who'] = (df['pm2_5'] > 15).astype(int)
    
    # Solar impact penalty
    df['pollution_solar_penalty_pct'] = ((df['pm2_5'] / 10) * 1.5).clip(0, 30).round(2)
    return df

def add_governorate_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Map cities to coordinates for Power BI maps."""
    coords = {
        'Cairo':      (30.0444, 31.2357),
        'Giza':       (30.0131, 31.2089),
        'Alexandria': (31.2001, 29.9187),
        'Qalyubia':   (30.3292, 31.2168),
        'Luxor':      (25.6872, 32.6396),
        'Aswan':      (24.0889, 32.8998),
        'Suez':       (29.9668, 32.5498),
        'Ismailia':   (30.5965, 32.2715),
        'PortSaid':   (31.2565, 32.2841),
        'Dakahlia':   (31.0355, 31.3832),
        'Sharqia':    (30.7333, 31.7167),
    }
    df['lat'] = df['governorate'].map(lambda g: coords.get(g, (np.nan, np.nan))[0])
    df['lon'] = df['governorate'].map(lambda g: coords.get(g, (np.nan, np.nan))[1])
    return df

def validate_final(df: pd.DataFrame):
    """Ensure data is ready for Azure/Power BI."""
    logger.info("Final Validation...")
    # Flexible datetime check
    assert pd.api.types.is_datetime64_any_dtype(df['datetime']), "Datetime conversion failed!"
    # Ensure no -9999 left
    for col in ['pm10', 'no2', 'o3']:
        assert (df[col] == -9999).sum() == 0, f"Error codes still in {col}"
    logger.info("All validations passed!")

# ── Main ───────────────────────────────────────────────────────────
def main():
    os.makedirs('data/silver', exist_ok=True)
    
    df = load_and_audit(RAW_PATH)
    df = clean_datetime(df)
    df = replace_error_codes(df)
    df = add_time_features(df)
    df = add_health_features(df)
    df = add_governorate_coordinates(df)
    
    validate_final(df)
    
    logger.info(f"Final dataset: {len(df):,} rows × {len(df.columns)} cols")
    df.to_csv(SILVER_PATH, index=False, encoding='utf-8-sig')
    logger.info(f"Saved to {SILVER_PATH}")

if __name__ == '__main__':
    main()