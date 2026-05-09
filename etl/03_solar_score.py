"""
╔══════════════════════════════════════════════════════════════════╗
║   SolarIQ Egypt — Gold Layer: Solar Site Score (FINAL v3)       ║
║   Input : data/silver/weather_clean.csv                         ║
║           data/silver/air_quality_clean.csv                     ║
║   Output: data/gold/solar_site_scores.csv                       ║
╚══════════════════════════════════════════════════════════════════╝

WHY GROUP BY GOVERNORATE (NOT DATE) — FULL EXPLANATION:
═══════════════════════════════════════════════════════════════════

QUESTION: "ليه عملت GROUP BY على governorate بس وملعملتش على date؟"

ANSWER:
The Solar Site Score is a SITE-LEVEL metric, not a daily metric.
Its business question is: "Which governorate is the BEST location
for a solar investment?" — not "What was Cairo's score on Jan 5?"

To answer that, we need to summarize 40+ years of data into ONE
score per governorate. That requires aggregating across ALL dates.

Think of it like a credit score:
- Your credit score = a single number summarizing years of history
- You don't have a different credit score for every day
- Similarly, each governorate gets ONE Solar Site Score

HOWEVER — you are RIGHT to think about date-level grouping.
Here is where each grain is used:

┌─────────────────────────────────────────────────────────────────┐
│ GRAIN              │ USED FOR                │ FILE             │
├─────────────────────────────────────────────────────────────────┤
│ Daily (as-is)      │ Fact tables, time-series│ weather_clean    │
│                    │ dashboards, trend charts│ air_quality_clean│
├─────────────────────────────────────────────────────────────────┤
│ Monthly avg        │ Seasonality dashboards  │ monthly_agg      │
│ (gov + month)      │ (#3, #7, #11, #16)      │ (optional)       │
├─────────────────────────────────────────────────────────────────┤
│ Yearly avg         │ Climate trend (#4, #9)  │ yearly_agg       │
│ (gov + year)       │ Before/After analysis   │ (optional)       │
├─────────────────────────────────────────────────────────────────┤
│ All-time avg       │ Solar Site SCORE (#24)  │ solar_site_scores│
│ (gov only)         │ Investment ranking (#2) │ ← THIS FILE      │
└─────────────────────────────────────────────────────────────────┘

FOR YOUR STAR SCHEMA (Fact + Dimension Tables):
═══════════════════════════════════════════════
The Silver files stay at DAILY grain as Fact tables.
The Gold file is your summary/score table.

Recommended star schema:

  DimDate ──────────────────┐
  DimGovernorate ───────────┼──► FactWeather (daily grain)
  DimSeason ────────────────┘         │
                                      │ (join on governorate)
  DimGovernorate ───────────────────► FactAirQuality (daily grain)
                                      │
                                      │ (aggregate from both facts)
                                      ▼
                               GoldSolarSiteScore (one row per gov)

In Power BI:
- Use FactWeather for all weather dashboards (#1–#17)
- Use FactAirQuality for pollution dashboards (#18–#22)
- JOIN them via DimGovernorate for combined dashboards (#23–#26)
- Use GoldSolarSiteScore for the ranking/investment dashboards (#24)
"""

import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_solar_site_score(
    weather_path: str = 'data/silver/weather_clean.csv',
    air_path: str     = 'data/silver/air_quality_clean.csv',
    output_path: str  = 'data/gold/solar_site_scores.csv'
) -> pd.DataFrame:

    # ── 1. Load Silver Files ─────────────────────────────────────
    logger.info("Loading silver datasets...")
    if not os.path.exists(weather_path):
        raise FileNotFoundError(f"Missing: {weather_path}")
    if not os.path.exists(air_path):
        raise FileNotFoundError(f"Missing: {air_path}")

    weather = pd.read_csv(weather_path, parse_dates=['date'])
    air     = pd.read_csv(air_path,     parse_dates=['date'])

    # Normalize column names
    weather.columns = [c.strip() for c in weather.columns]
    air.columns     = [c.strip() for c in air.columns]

    logger.info(f"Weather: {len(weather):,} rows | Air: {len(air):,} rows")

    # ── 2. Aggregate Weather → One Row per Governorate ───────────
    #
    # WHY: The Solar Site Score represents the LONG-TERM AVERAGE
    # potential of each governorate. We aggregate across all years
    # (1981–2025) to get stable, representative metrics that are
    # not skewed by any single good or bad year.
    #
    logger.info("Aggregating weather to governorate level...")

    # Detect clearness column name (may vary between runs)
    clearness_col = (
        'clearness_index' if 'clearness_index' in weather.columns
        else 'clearness' if 'clearness' in weather.columns
        else None
    )
    temp_penalty_col = (
        'temp_penalty_pct' if 'temp_penalty_pct' in weather.columns
        else 'temp_pen' if 'temp_pen' in weather.columns
        else None
    )

    agg_dict = {
        'avg_solar_radiation': ('ALLSKY_SFC_SW_DWN', 'mean'),
        'avg_peak_sun_hours':  ('ALLSKY_SFC_SW_DWN', 'mean'),  # same column
        'avg_temp_max':        ('T2M_MAX', 'mean'),
        'avg_wind_speed':      ('WS2M', 'mean'),
        'avg_humidity':        ('RH2M', 'mean'),
        'hot_days_pct':        ('is_hot_day', 'mean'),
    }

    if clearness_col:
        agg_dict['avg_clearness'] = (clearness_col, 'mean')
    if temp_penalty_col:
        agg_dict['avg_temp_penalty'] = (temp_penalty_col, 'mean')

    w_agg = weather.groupby('governorate').agg(**agg_dict).reset_index()
    logger.info(f"  Weather aggregated: {len(w_agg)} governorates")

    # ── 3. Aggregate Air Quality → One Row per Governorate ───────
    logger.info("Aggregating air quality to governorate level...")

    # Normalize governorate column name
    gov_col_air = 'Governorate' if 'Governorate' in air.columns else 'governorate'

    aq_agg = air.groupby(gov_col_air).agg(
        avg_aqi    =('AQI_Level', 'mean'),
        avg_pm25   =('PM2_5', 'mean'),
        avg_pm10   =('PM10', 'mean'),
        dust_storm_days=('is_dust_storm', 'sum') if 'is_dust_storm' in air.columns
                       else ('AQI_Level', 'count'),
        avg_pollution_penalty=('pollution_solar_penalty_pct', 'mean')
                              if 'pollution_solar_penalty_pct' in air.columns
                              else ('PM2_5', 'mean'),
    ).reset_index()
    aq_agg = aq_agg.rename(columns={gov_col_air: 'governorate'})
    logger.info(f"  Air quality aggregated: {len(aq_agg)} governorates")

    # ── 4. Merge on Governorate ───────────────────────────────────
    #
    # WHY LEFT JOIN: Weather covers all 27 governorates.
    # Air quality may cover fewer. We keep all 27 weather governorates
    # and fill missing AQI with median (conservative assumption).
    #
    df = w_agg.merge(aq_agg, on='governorate', how='left')
    logger.info(f"  Merged: {len(df)} governorates")

    # Fill missing AQI with median (for governorates without air data)
    if df['avg_aqi'].isnull().any():
        median_aqi = df['avg_aqi'].median()
        missing = df['avg_aqi'].isnull().sum()
        df['avg_aqi'] = df['avg_aqi'].fillna(median_aqi)
        logger.warning(
            f"  {missing} governorates missing AQI → filled with median ({median_aqi:.2f})"
        )

    # ── 5. Normalization (0–100 scale) ───────────────────────────
    #
    # WHY: Each metric has different units (kWh/m², °C, μg/m³, etc.).
    # We must normalize to a common 0–100 scale before applying weights.
    # Min-max normalization: (x - min) / (max - min) × 100
    #
    def normalize(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
        mn, mx = series.min(), series.max()
        if mn == mx or pd.isna(mn):
            return pd.Series(50.0, index=series.index)  # No variation → neutral
        norm = (series - mn) / (mx - mn) * 100
        return norm if higher_is_better else 100 - norm

    df['score_ghi']       = normalize(df['avg_solar_radiation'],   True)
    df['score_clearness'] = normalize(
        df.get('avg_clearness', pd.Series([50.0]*len(df))), True
    )
    df['score_temp']      = normalize(df['avg_temp_max'],           False)  # Lower = better
    df['score_wind']      = normalize(df['avg_wind_speed'],         True)   # Higher = better (cooling)
    df['score_humidity']  = normalize(df['avg_humidity'],           False)  # Lower = better
    df['score_air']       = normalize(df['avg_aqi'],                False)  # Lower = better

    # ── 6. Weighted Solar Site Score ─────────────────────────────
    #
    # Weights based on peer-reviewed solar site selection literature:
    # - GHI is by far the most important factor (35%)
    # - Clearness Index shows sky stability (20%)
    # - Temperature penalty reduces real-world output (15%)
    # - Air quality/dust degrades panels and blocks irradiance (15%)
    # - Wind cooling partially offsets heat penalty (10%)
    # - Humidity causes corrosion and soiling (5%)
    #
    WEIGHTS = {
        'score_ghi':       0.35,
        'score_clearness': 0.20,
        'score_temp':      0.15,
        'score_air':       0.15,
        'score_wind':      0.10,
        'score_humidity':  0.05,
    }

    df['solar_site_score'] = sum(
        df[col] * weight for col, weight in WEIGHTS.items()
    ).round(2)

    # ── 7. Ranking & Labels ───────────────────────────────────────
    df['rank'] = df['solar_site_score'].rank(
        ascending=False, method='dense'
    ).astype(int)

    def get_grade(score):
        if score >= 80: return 'A+'
        if score >= 70: return 'A'
        if score >= 60: return 'B'
        if score >= 50: return 'C'
        return 'D'

    def get_recommendation(score):
        if score >= 75: return 'Strongly Recommended'
        if score >= 60: return 'Recommended'
        if score >= 50: return 'Neutral'
        return 'Not Recommended'

    df['grade']           = df['solar_site_score'].apply(get_grade)
    df['investment_reco'] = df['solar_site_score'].apply(get_recommendation)

    # ── 8. Save ───────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"✔ Gold layer saved to: {output_path}")

    # ── 9. Print Results ──────────────────────────────────────────
    print("\n" + "═" * 60)
    print("SOLAR SITE SCORE — ALL 27 GOVERNORATES")
    print("═" * 60)
    cols = ['rank', 'governorate', 'solar_site_score', 'grade',
            'investment_reco', 'avg_solar_radiation', 'avg_clearness']
    cols = [c for c in cols if c in df.columns]
    print(df.sort_values('rank')[cols].to_string(index=False))

    return df


if __name__ == '__main__':
    calculate_solar_site_score()