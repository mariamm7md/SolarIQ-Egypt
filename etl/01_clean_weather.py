"""
SolarIQ Egypt — Weather Data Cleaning Script
WHY: Raw weather_data.csv has -999 error codes, integer dates,
     and missing time-based features needed for all dashboards.
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime

# ── Setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

RAW_PATH   = 'data/raw/weather_data.csv'
SILVER_PATH = 'data/silver/weather_clean.csv'

# ── Load ───────────────────────────────────────────────────────────
def load_raw(path: str) -> pd.DataFrame:
    logger.info(f"Loading raw weather data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    return df

# ── Audit ──────────────────────────────────────────────────────────
def audit_data(df: pd.DataFrame) -> None:
    """Print a full data quality report before cleaning."""
    logger.info("=" * 60)
    logger.info("DATA QUALITY AUDIT")
    logger.info("=" * 60)
    
    # Missing values
    logger.info("\nNull values per column:")
    nulls = df.isnull().sum()
    for col, count in nulls[nulls > 0].items():
        logger.info(f"  {col}: {count:,} nulls ({count/len(df)*100:.1f}%)")
    
    # -999 error codes in solar columns
    solar_cols = ['CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_SW_DWN']
    for col in solar_cols:
        if col in df.columns:
            count = (df[col] == -999).sum()
            logger.warning(f"  {col}: {count:,} values = -999 "
                           f"({count/len(df)*100:.1f}%)")
    
    # Date format check
    logger.info(f"\nDate column dtype: {df['date'].dtype}")
    logger.info(f"Date sample: {df['date'].head(3).tolist()}")
    logger.info(f"Date range: {df['date'].min()} → {df['date'].max()}")

# ── Clean ──────────────────────────────────────────────────────────
def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert integer dates (19810101) to proper datetime."""
    logger.info("Converting integer dates to datetime...")
    df['date'] = pd.to_datetime(
        df['date'].astype(str), format='%Y%m%d'
    )
    logger.info(f"Date range: {df['date'].min().date()} "
                f"→ {df['date'].max().date()}")
    return df

def replace_error_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Replace -999 NASA error codes with NaN."""
    logger.info("Replacing -999 error codes with NaN...")
    
    solar_cols = ['CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_SW_DWN']
    for col in solar_cols:
        if col in df.columns:
            before = (df[col] == -999).sum()
            df[col] = df[col].replace(-999, np.nan)
            logger.info(f"  {col}: replaced {before:,} values")
    
    return df

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add year, month, quarter, season — needed for every dashboard."""
    logger.info("Adding time-based features...")
    
    df['year']    = df['date'].dt.year
    df['month']   = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    
    # Season mapping for Egypt (meteorological)
    # WHY: Egypt's climate seasons differ from Europe
    season_map = {
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3:  'Spring', 4: 'Spring', 5: 'Spring',
        6:  'Summer', 7: 'Summer', 8: 'Summer',
        9:  'Autumn', 10: 'Autumn', 11: 'Autumn'
    }
    df['season'] = df['month'].map(season_map)
    
    # Decade for long-term trend analysis
    df['decade'] = (df['year'] // 10) * 10
    
    # Period for before/after comparison (Dashboard #29)
    df['period'] = df['year'].apply(
        lambda y: 'Pre-2000' if y < 2000 
        else ('2000-2010' if y < 2010 
        else ('2010-2020' if y < 2020 else '2020+'))
    )
    
    logger.info(f"Seasons distribution:\n{df['season'].value_counts()}")
    return df

def add_solar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived solar metrics needed for scoring."""
    logger.info("Calculating derived solar features...")
    
    # Clearness Index: ratio of actual to clear-sky radiation
    # WHY: Values close to 1 = clear sky = ideal solar location
    mask = (df['CLRSKY_SFC_SW_DWN'].notna() & 
            df['ALLSKY_SFC_SW_DWN'].notna() &
            (df['CLRSKY_SFC_SW_DWN'] > 0))
    
    df['clearness_index'] = np.nan
    df.loc[mask, 'clearness_index'] = (
        df.loc[mask, 'ALLSKY_SFC_SW_DWN'] / 
        df.loc[mask, 'CLRSKY_SFC_SW_DWN']
    ).clip(0, 1)  # Can't exceed 1.0
    
    # Peak Sun Hours (PSH) = daily kWh/m² (ALLSKY already in kWh/m²/day)
    df['peak_sun_hours'] = df['ALLSKY_SFC_SW_DWN']
    
    # Temperature Penalty for solar panels
    # WHY: Panels lose ~0.4% efficiency per °C above 25°C
    df['temp_penalty_pct'] = (
        (df['T2M_MAX'] - 25).clip(lower=0) * 0.4
    ).round(2)
    
    # Daily temperature range (thermal stress on panels)
    df['temp_range'] = (df['T2M_MAX'] - df['T2M_MIN']).round(2)
    
    # Cloud impact (difference between clear sky and actual)
    df['cloud_impact'] = (
        df['CLRSKY_SFC_SW_DWN'] - df['ALLSKY_SFC_SW_DWN']
    ).clip(lower=0)
    
    # Hot days flag (>40°C is critical for solar panels)
    df['is_hot_day'] = (df['T2M_MAX'] >= 40).astype(int)
    
    return df

def validate_cleaned(df: pd.DataFrame) -> None:
    """Final validation before saving."""
    logger.info("=" * 60)
    logger.info("POST-CLEANING VALIDATION")
    logger.info("=" * 60)
    
    # Check no more -999 values
    solar_cols = ['CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_SW_DWN']
    for col in solar_cols:
        if col in df.columns:
            bad = (df[col] == -999).sum()
            assert bad == 0, f"Still have {bad} error codes in {col}!"
            logger.info(f"  {col}: no -999 values remaining")
    
    # Check date is datetime
    assert pd.api.types.is_datetime64_any_dtype(df['date']), "Date not datetime!"
    logger.info(f"date column: {df['date'].dtype}")
    
    # Check required columns exist
    required = ['year', 'month', 'season', 'clearness_index']
    for col in required:
        assert col in df.columns, f"Missing column: {col}"
        logger.info(f" {col}: present")
    
    logger.info(f"\nFinal dataset: {len(df):,} rows × {len(df.columns)} cols")
    logger.info(f"Governorates: {df['governorate'].nunique()}")
    logger.info(f"Date range: {df['date'].min().date()} → "
                f"{df['date'].max().date()}")

# ── Main ───────────────────────────────────────────────────────────
def main():
    os.makedirs('data/silver', exist_ok=True)
    
    df = load_raw(RAW_PATH)
    audit_data(df)
    
    df = clean_dates(df)
    df = replace_error_codes(df)
    df = add_time_features(df)
    df = add_solar_features(df)
    
    validate_cleaned(df)
    
    # Save with UTF-8 BOM for Arabic compatibility in Power BI
    df.to_csv(SILVER_PATH, index=False, encoding='utf-8-sig')
    logger.info(f"\nSaved to {SILVER_PATH}")
    
    # Quick stats for review
    print("\n" + "="*60)
    print("SUMMARY STATISTICS — SOLAR RADIATION")
    print("="*60)
    print(df.groupby('governorate')['ALLSKY_SFC_SW_DWN'].agg(
        ['mean', 'min', 'max', 'count']
    ).round(2))

if __name__ == '__main__':
    main()