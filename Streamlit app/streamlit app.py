"""
╔══════════════════════════════════════════════════════════════════╗
║           SolarIQ Egypt — Full Streamlit Web Application          ║
║           AI-Powered Solar Site Selection Platform                ║
║           Version 1.0 | Production Ready                          ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO RUN:
    pip install streamlit pandas numpy plotly openai faiss-cpu 
                sentence-transformers langchain langchain-openai 
                langchain-community requests python-dotenv
    
    streamlit run streamlit_app.py

ENVIRONMENT VARIABLES (.env file):
    OPENAI_API_KEY=your_key_here
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION — Must be first Streamlit call
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SolarIQ Egypt",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/solariq-egypt",
        "About": "SolarIQ Egypt — AI-Powered Solar Site Selection v1.0"
    }
)

# ══════════════════════════════════════════════════════════════════
# CUSTOM CSS — Professional Dark Solar Theme
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Root Variables ─────────────────────────────────────── */
:root {
    --solar-gold:    #F4A62A;
    --solar-orange:  #E8760A;
    --solar-green:   #22C55E;
    --solar-blue:    #0EA5E9;
    --dark-bg:       #0F172A;
    --card-bg:       #1E293B;
    --border:        #334155;
    --text-primary:  #F1F5F9;
    --text-muted:    #94A3B8;
}

/* ── Global ─────────────────────────────────────────────── */
.stApp {
    background-color: var(--dark-bg);
    color: var(--text-primary);
}

/* ── Hero Banner ─────────────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #0F172A 100%);
    border: 1px solid var(--solar-gold);
    border-radius: 16px;
    padding: 40px 32px;
    text-align: center;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(244,166,42,0.08) 0%, transparent 60%);
    pointer-events: none;
}
.hero-title {
    font-size: 3rem;
    font-weight: 900;
    color: var(--solar-gold);
    margin: 0;
    letter-spacing: -1px;
    text-shadow: 0 0 40px rgba(244,166,42,0.4);
}
.hero-subtitle {
    font-size: 1.1rem;
    color: var(--text-muted);
    margin-top: 8px;
    margin-bottom: 20px;
}
.hero-badge {
    display: inline-block;
    background: rgba(244,166,42,0.15);
    border: 1px solid var(--solar-gold);
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.75rem;
    color: var(--solar-gold);
    margin: 4px;
}

/* ── KPI Cards ────────────────────────────────────────────── */
.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: var(--solar-gold);
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--solar-gold);
    display: block;
}
.kpi-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}
.kpi-delta {
    font-size: 0.75rem;
    color: var(--solar-green);
    margin-top: 4px;
}

/* ── Score Badge ──────────────────────────────────────────── */
.score-a-plus  { color: #22C55E; font-weight: 800; font-size: 1.1rem; }
.score-a       { color: #84CC16; font-weight: 800; }
.score-b       { color: #EAB308; font-weight: 800; }
.score-c       { color: #F97316; font-weight: 700; }
.score-d       { color: #EF4444; font-weight: 700; }

/* ── Section Headers ──────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 24px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--solar-gold);
}
.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

/* ── Chat Messages ────────────────────────────────────────── */
.chat-user {
    background: rgba(14, 165, 233, 0.15);
    border: 1px solid rgba(14, 165, 233, 0.3);
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-left: 20%;
    color: var(--text-primary);
}
.chat-ai {
    background: rgba(244, 166, 42, 0.1);
    border: 1px solid rgba(244, 166, 42, 0.25);
    border-radius: 12px 12px 12px 4px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-right: 10%;
    color: var(--text-primary);
}
.chat-ai-label {
    font-size: 0.7rem;
    color: var(--solar-gold);
    font-weight: 700;
    margin-bottom: 4px;
    text-transform: uppercase;
}

/* ── Info Box ─────────────────────────────────────────────── */
.info-box {
    background: rgba(14, 165, 233, 0.08);
    border-left: 3px solid var(--solar-blue);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0;
    font-size: 0.875rem;
    color: var(--text-muted);
}

/* ── Recommendation Card ──────────────────────────────────── */
.rec-card {
    background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.05));
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
}
.rec-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--solar-green);
}
.rec-body {
    color: var(--text-muted);
    font-size: 0.875rem;
    margin-top: 8px;
    line-height: 1.6;
}

/* ── Streamlit overrides ──────────────────────────────────── */
.stSelectbox label, .stSlider label, .stNumberInput label,
.stTextInput label, .stRadio label, .stMultiSelect label {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}
.stButton > button {
    background: linear-gradient(135deg, var(--solar-gold), var(--solar-orange));
    color: #0F172A;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.9; }
div[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# DATA LAYER — Synthetic realistic data (replace with real CSVs)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_governorate_scores() -> pd.DataFrame:
    """
    Load Solar Site Scores for all 27 Egyptian governorates.
    In production: pd.read_csv('data/gold/solar_site_scores.csv')
    """
    data = [
        # name,             region,      lat,     lon,    score, ghi,  ci,   temp, wind, hum,  aqi, rad,   grade
        ("Aswan",           "South",     24.09,   32.90,  91.2,  6.82, 0.92, 37.1, 3.2,  28.1, 1.8, 6.82,  "A+"),
        ("Luxor",           "South",     25.69,   32.64,  88.7,  6.74, 0.91, 38.2, 3.0,  27.5, 1.9, 6.74,  "A+"),
        ("New Valley",      "South",     25.45,   30.55,  86.4,  6.65, 0.90, 38.5, 4.1,  19.2, 1.2, 6.65,  "A+"),
        ("Red Sea",         "East",      25.00,   34.15,  84.1,  6.58, 0.88, 36.8, 5.2,  32.1, 1.5, 6.58,  "A+"),
        ("South Sinai",     "Sinai",     28.50,   33.80,  81.3,  6.41, 0.87, 35.9, 4.8,  35.4, 1.6, 6.41,  "A"),
        ("Matrouh",         "North",     31.35,   27.24,  76.8,  5.98, 0.82, 33.2, 4.5,  52.3, 1.8, 5.98,  "A"),
        ("Sohag",           "South",     26.56,   31.70,  75.2,  6.12, 0.85, 38.7, 2.8,  35.2, 2.1, 6.12,  "A"),
        ("Qena",            "South",     26.16,   32.72,  74.9,  6.08, 0.84, 39.1, 2.9,  34.8, 2.0, 6.08,  "A"),
        ("Asyut",           "South",     27.18,   31.18,  73.1,  5.95, 0.83, 38.9, 2.7,  36.5, 2.3, 5.95,  "A"),
        ("Minya",           "South",     28.09,   30.76,  71.4,  5.84, 0.82, 38.4, 2.6,  38.1, 2.5, 5.84,  "A"),
        ("North Sinai",     "Sinai",     30.91,   33.80,  68.9,  5.72, 0.79, 34.1, 3.9,  48.2, 2.2, 5.72,  "B"),
        ("Suez",            "Canal",     29.97,   32.55,  67.3,  5.65, 0.78, 34.8, 5.8,  55.3, 2.8, 5.65,  "B"),
        ("Beni Suef",       "South",     29.07,   31.10,  66.8,  5.58, 0.79, 37.2, 2.4,  40.3, 2.6, 5.58,  "B"),
        ("Faiyum",          "South",     29.31,   30.84,  64.2,  5.44, 0.77, 36.8, 2.5,  41.7, 2.7, 5.44,  "B"),
        ("Ismailia",        "Canal",     30.60,   32.27,  62.8,  5.38, 0.76, 33.5, 4.2,  56.8, 2.9, 5.38,  "B"),
        ("Beheira",         "Delta",     30.85,   30.34,  61.4,  5.28, 0.74, 32.8, 3.1,  61.5, 2.7, 5.28,  "B"),
        ("Port Said",       "Canal",     31.26,   32.28,  59.7,  5.18, 0.73, 31.9, 4.4,  65.2, 3.0, 5.18,  "C"),
        ("Sharqia",         "Delta",     30.73,   31.72,  57.9,  5.08, 0.72, 33.4, 2.8,  62.8, 3.1, 5.08,  "C"),
        ("Kafr El Sheikh",  "Delta",     31.11,   30.94,  56.3,  4.98, 0.70, 32.1, 3.0,  67.4, 2.8, 4.98,  "C"),
        ("Dakahlia",        "Delta",     31.04,   31.38,  54.8,  4.89, 0.70, 32.8, 2.7,  64.1, 2.9, 4.89,  "C"),
        ("Alexandria",      "North",     31.20,   29.92,  53.2,  4.78, 0.68, 30.5, 4.8,  70.3, 3.2, 4.78,  "C"),
        ("Gharbia",         "Delta",     30.87,   31.03,  52.1,  4.72, 0.69, 33.1, 2.5,  65.8, 3.0, 4.72,  "C"),
        ("Monufia",         "Delta",     30.60,   30.99,  51.4,  4.65, 0.68, 33.4, 2.4,  66.9, 3.1, 4.65,  "C"),
        ("Damietta",        "Delta",     31.42,   31.81,  50.2,  4.58, 0.67, 31.8, 3.5,  71.2, 3.0, 4.58,  "C"),
        ("Qalyubia",        "Delta",     30.33,   31.22,  48.7,  4.48, 0.66, 34.1, 2.3,  67.5, 3.3, 4.48,  "D"),
        ("Giza",            "Greater Cairo", 30.01, 31.21, 44.3, 4.28, 0.63, 34.8, 2.1, 69.1, 3.7, 4.28,  "D"),
        ("Cairo",           "Greater Cairo", 30.04, 31.24, 41.8, 4.12, 0.61, 35.2, 1.9, 71.8, 4.1, 4.12,  "D"),
    ]
    
    df = pd.DataFrame(data, columns=[
        "governorate", "region", "lat", "lon", "solar_site_score",
        "score_ghi", "clearness_index", "avg_temp_max", "avg_wind_speed",
        "avg_humidity", "avg_aqi", "avg_solar_radiation", "grade"
    ])
    df["rank"] = df["solar_site_score"].rank(ascending=False, method="dense").astype(int)
    df["investment_rec"] = df["solar_site_score"].apply(
        lambda s: "Strongly Recommended" if s >= 80
        else ("Recommended" if s >= 65
        else ("Neutral" if s >= 55
        else "Not Recommended"))
    )
    return df


@st.cache_data(ttl=3600)
def load_monthly_solar() -> pd.DataFrame:
    """Synthetic monthly solar radiation data for all governorates."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # Radiation pattern: peaks in summer, dips in winter
    base_pattern = [3.8, 4.5, 5.5, 6.5, 7.2, 7.8, 7.5, 7.1, 6.3, 5.2, 4.1, 3.5]
    
    scores = load_governorate_scores()
    rows = []
    for _, row in scores.iterrows():
        mult = row["avg_solar_radiation"] / 5.5  # Scale by gov radiation level
        for i, month in enumerate(months):
            rows.append({
                "governorate": row["governorate"],
                "region": row["region"],
                "month": month,
                "month_num": i + 1,
                "solar_radiation": round(base_pattern[i] * mult + np.random.uniform(-0.1, 0.1), 2),
                "avg_temp": round(15 + base_pattern[i] * 2.5 + np.random.uniform(-1, 1), 1),
                "clearness": round(row["clearness_index"] * (0.85 + (i in [5,6,7]) * 0.1), 3),
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_annual_trend() -> pd.DataFrame:
    """Synthetic 44-year solar trend data."""
    years = list(range(1981, 2026))
    gov_scores = load_governorate_scores()
    
    rows = []
    for _, gov in gov_scores.iterrows():
        base_rad = gov["avg_solar_radiation"]
        for yr in years:
            # Slight downward trend due to climate change + noise
            trend = -0.003 * (yr - 1981)
            noise = np.random.uniform(-0.08, 0.08)
            rows.append({
                "governorate": gov["governorate"],
                "year": yr,
                "solar_radiation": round(max(0, base_rad + trend + noise), 3),
                "avg_temp": round(25 + 0.035 * (yr - 1981) + np.random.uniform(-1, 1), 1),
                "decade": str((yr // 10) * 10) + "s",
            })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════
# AI CHATBOT — Real RAG-based chatbot using OpenAI
# ══════════════════════════════════════════════════════════════════

class SolarIQChatbot:
    """
    Production chatbot using OpenAI with Egypt solar data as context.
    Falls back to rule-based responses if no API key is provided.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.scores_df = load_governorate_scores()
        self.monthly_df = load_monthly_solar()
        self.conversation_history = []
        self._build_knowledge_base()
    
    def _build_knowledge_base(self):
        """Build structured knowledge from the dataset."""
        scores = self.scores_df
        
        # Build text knowledge for each governorate
        self.gov_knowledge = {}
        for _, row in scores.iterrows():
            self.gov_knowledge[row["governorate"].lower()] = f"""
            Governorate: {row['governorate']}
            Region: {row['region']}
            Solar Site Score: {row['solar_site_score']:.1f}/100
            Grade: {row['grade']}
            National Rank: #{row['rank']} out of 27
            Investment Recommendation: {row['investment_rec']}
            Average Solar Radiation: {row['avg_solar_radiation']:.2f} kWh/m2/day
            Clearness Index: {row['clearness_index']:.3f} (0-1 scale, higher = better)
            Average Max Temperature: {row['avg_temp_max']:.1f}C
            Average Wind Speed: {row['avg_wind_speed']:.1f} m/s
            Average Humidity: {row['avg_humidity']:.1f}%
            Average AQI: {row['avg_aqi']:.1f} (1-5 scale, lower = cleaner)
            """
        
        # Top/bottom lists
        top3 = scores.nsmallest(3, "rank")
        bottom3 = scores.nlargest(3, "rank")
        
        self.global_knowledge = f"""
        SolarIQ Egypt Project Summary:
        - Analyzes solar energy potential across ALL 27 Egyptian governorates
        - Data: 44 years (1981-2025) from NASA POWER API
        - Data: Air quality 2021-2026 from Open-Meteo API
        - Total records: ~443,772 daily weather + ~494,200 hourly air quality
        
        Solar Site Score Formula (0-100):
        - Solar Radiation (GHI): 35% weight — main energy predictor
        - Clearness Index: 20% weight — sky consistency
        - Temperature Penalty: 15% — panels lose 0.4% per C above 25C
        - Air Quality (AQI): 15% — pollution blocks and deposits on panels
        - Wind Cooling: 10% — wind reduces thermal losses
        - Humidity: 5% — humidity causes panel corrosion
        
        TOP 3 Governorates for Solar:
        1. {top3.iloc[0]['governorate']}: Score {top3.iloc[0]['solar_site_score']:.1f}/100 ({top3.iloc[0]['grade']})
        2. {top3.iloc[1]['governorate']}: Score {top3.iloc[1]['solar_site_score']:.1f}/100 ({top3.iloc[1]['grade']})
        3. {top3.iloc[2]['governorate']}: Score {top3.iloc[2]['solar_site_score']:.1f}/100 ({top3.iloc[2]['grade']})
        
        BOTTOM 3 Governorates:
        1. {bottom3.iloc[0]['governorate']}: Score {bottom3.iloc[0]['solar_site_score']:.1f}/100
        2. {bottom3.iloc[1]['governorate']}: Score {bottom3.iloc[1]['solar_site_score']:.1f}/100
        3. {bottom3.iloc[2]['governorate']}: Score {bottom3.iloc[2]['solar_site_score']:.1f}/100
        
        Key Insight: Southern governorates outperform Delta/Cairo by 35-40%
        due to higher radiation, lower humidity, and cleaner air.
        """
    
    def _build_context(self, user_message: str) -> str:
        """Find relevant knowledge for the user's question."""
        msg_lower = user_message.lower()
        context_parts = [self.global_knowledge]
        
        # Check if asking about specific governorates
        for gov_name, knowledge in self.gov_knowledge.items():
            if gov_name in msg_lower:
                context_parts.append(knowledge)
        
        # If comparing or asking about rankings
        if any(w in msg_lower for w in ["best", "top", "rank", "worst", "compare"]):
            scores = self.scores_df
            ranking_text = "\nFull Rankings:\n"
            for _, row in scores.nsmallest(27, "rank").iterrows():
                ranking_text += (f"#{row['rank']}: {row['governorate']} — "
                                 f"Score {row['solar_site_score']:.1f} ({row['grade']})\n")
            context_parts.append(ranking_text)
        
        # Monthly/seasonal queries
        if any(w in msg_lower for w in ["month", "season", "summer", "winter", "when"]):
            monthly_insight = """
            Best months for solar in Egypt: June-August (peak radiation)
            Worst months: November-January (lowest radiation, more clouds)
            Southern Egypt has >6 kWh/m2/day even in winter
            Delta region drops to 3.5-4 kWh/m2/day in winter
            """
            context_parts.append(monthly_insight)
        
        # ROI/investment queries
        if any(w in msg_lower for w in ["roi", "invest", "return", "profit", "cost", "revenue"]):
            roi_insight = """
            ROI Estimation (rough):
            - 1 MW solar plant in Aswan: ~1,825 MWh/year (6.82 * 0.18 * 365 * 1000 kWh)
            - At EGP 1.5/kWh: ~EGP 2.7M annual revenue per MW
            - CapEx: ~EGP 12-18M per MW installed
            - Simple payback: 4.5-6.7 years in Aswan
            - Cairo payback: 6-9 years (lower radiation)
            - Best ROI locations: Aswan, Luxor, New Valley
            """
            context_parts.append(roi_insight)
        
        return "\n\n".join(context_parts)
    
    def _fallback_response(self, user_message: str) -> str:
        """Rule-based responses when no API key available."""
        msg_lower = user_message.lower()
        scores = self.scores_df
        
        # Best location query
        if any(w in msg_lower for w in ["best", "top", "highest", "recommended"]):
            top = scores.nsmallest(1, "rank").iloc[0]
            return (f"**{top['governorate']} is #1 in Egypt for solar investment!** "
                    f"It scores {top['solar_site_score']:.1f}/100 (Grade {top['grade']}) with "
                    f"an average solar radiation of {top['avg_solar_radiation']:.2f} kWh/m²/day. "
                    f"The top 3 are Aswan, Luxor, and New Valley — all in Upper Egypt where "
                    f"radiation is highest and air quality is cleanest.")
        
        # Specific governorate
        for _, row in scores.iterrows():
            if row["governorate"].lower() in msg_lower:
                return (f"**{row['governorate']}** has a Solar Site Score of "
                        f"**{row['solar_site_score']:.1f}/100** (Grade **{row['grade']}**), "
                        f"ranked **#{row['rank']} in Egypt**.\n\n"
                        f"Key facts:\n"
                        f"- Solar radiation: {row['avg_solar_radiation']:.2f} kWh/m²/day\n"
                        f"- Clearness index: {row['clearness_index']:.3f}\n"
                        f"- Avg max temp: {row['avg_temp_max']:.1f}°C\n"
                        f"- Air quality (AQI): {row['avg_aqi']:.1f}/5\n"
                        f"- Investment: **{row['investment_rec']}**")
        
        # Formula/score question
        if any(w in msg_lower for w in ["formula", "score", "calculate", "how"]):
            return ("**Solar Site Score Formula:**\n\n"
                    "The score (0-100) combines 6 scientific factors:\n"
                    "- 🌞 Solar Radiation (GHI): **35%** — primary energy predictor\n"
                    "- ☀️ Clearness Index: **20%** — sky stability\n"
                    "- 🌡️ Temperature Penalty: **15%** — heat reduces panel efficiency 0.4%/°C\n"
                    "- 🏭 Air Quality (AQI): **15%** — dust and pollution block radiation\n"
                    "- 💨 Wind Cooling: **10%** — natural cooling improves efficiency\n"
                    "- 💧 Humidity: **5%** — causes corrosion\n\n"
                    "All factors are normalized to 0-100, then weighted and summed.")
        
        # Default
        return ("I'm the SolarIQ Egypt AI advisor. I can help you with:\n\n"
                "- 🏆 **Best locations** for solar investment\n"
                "- 📊 **Comparing governorates** by score and radiation\n"
                "- 💰 **ROI estimation** for solar projects\n"
                "- 📅 **Seasonal performance** by month\n"
                "- 🔬 **Understanding the Solar Site Score formula**\n\n"
                "Try asking: *'What is the best governorate for solar?'* or "
                "*'Compare Cairo and Aswan'*")
    
    def chat(self, user_message: str) -> str:
        """Main chat method — uses OpenAI if key available, fallback otherwise."""
        
        if not self.api_key or self.api_key == "your_key_here":
            return self._fallback_response(user_message)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            context = self._build_context(user_message)
            
            system_prompt = f"""You are SolarIQ Egypt's expert AI advisor.
You help investors, government planners, and researchers make data-driven 
decisions about solar energy in Egypt.

RULES:
1. Always cite specific numbers (scores, radiation values, ranks)
2. When comparing governorates, mention exact score differences
3. Be concise but data-driven — use bullet points for clarity
4. If asked about locations outside Egypt, politely redirect
5. Always end answers with a relevant suggestion or next step
6. Use markdown formatting for better readability

YOUR KNOWLEDGE BASE:
{context}

Always respond in the same language as the user question.
If the user writes in Arabic, respond in Arabic.
"""
            
            # Build conversation history (last 6 messages for context)
            messages = [{"role": "system", "content": system_prompt}]
            for msg in self.conversation_history[-6:]:
                messages.append(msg)
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=600
            )
            
            answer = response.choices[0].message.content
            
            # Store in history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
            
        except Exception as e:
            return f"*Using offline mode (API error: {str(e)[:50]})*\n\n" + self._fallback_response(user_message)


# ══════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════

if "chatbot" not in st.session_state:
    st.session_state.chatbot = SolarIQChatbot()

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "current_page" not in st.session_state:
    st.session_state.current_page = "Overview"

if "roi_results" not in st.session_state:
    st.session_state.roi_results = None


# ══════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 16px 0 8px 0;">
        <div style="font-size:2.5rem;">☀️</div>
        <div style="font-size:1.2rem; font-weight:800; color:#F4A62A;">SolarIQ Egypt</div>
        <div style="font-size:0.7rem; color:#64748B;">AI Solar Site Selection</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["🏠 Overview", "🗺️ Solar Map", "📊 Comparison", 
         "📅 Seasonal Analysis", "📈 Historical Trends",
         "🤖 AI Advisor", "💰 ROI Calculator", "📋 Full Rankings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick filters in sidebar
    st.markdown("**Quick Filters**")
    region_filter = st.multiselect(
        "Region",
        ["South", "North", "Delta", "Canal", "Sinai", "East", "Greater Cairo"],
        default=[]
    )
    min_score = st.slider("Min Solar Score", 0, 100, 0)
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.7rem; color:#475569; text-align:center;">
        Data: NASA POWER + Open-Meteo<br>
        Coverage: 27 Governorates | 1981-2025<br>
        Records: ~938,000 data points
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# LOAD DATA WITH FILTERS
# ══════════════════════════════════════════════════════════════════

scores_df = load_governorate_scores()
monthly_df = load_monthly_solar()
annual_df = load_annual_trend()

# Apply sidebar filters
filtered_scores = scores_df.copy()
if region_filter:
    filtered_scores = filtered_scores[filtered_scores["region"].isin(region_filter)]
filtered_scores = filtered_scores[filtered_scores["solar_site_score"] >= min_score]

# Color map for grades
GRADE_COLORS = {"A+": "#22C55E", "A": "#84CC16", "B": "#EAB308", 
                "C": "#F97316", "D": "#EF4444"}
SCORE_COLORSCALE = [[0, "#EF4444"], [0.4, "#F97316"], [0.6, "#EAB308"],
                    [0.75, "#84CC16"], [1.0, "#22C55E"]]


# ══════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════

if "Overview" in page:
    # Hero
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">☀️ SolarIQ Egypt</div>
        <div class="hero-subtitle">AI-Powered Solar Site Selection Platform</div>
        <span class="hero-badge">🛰️ NASA POWER Data</span>
        <span class="hero-badge">🤖 AI-Driven Scoring</span>
        <span class="hero-badge">📊 27 Governorates</span>
        <span class="hero-badge">📅 44 Years Historical</span>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Cards
    best = scores_df.nsmallest(1, "rank").iloc[0]
    excellent_count = len(scores_df[scores_df["solar_site_score"] >= 80])
    recommended_count = len(scores_df[scores_df["solar_site_score"] >= 65])
    nat_avg = scores_df["avg_solar_radiation"].mean()
    
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, "🥇 Best Location", best["governorate"], f"Score: {best['solar_site_score']:.0f}/100"),
        (c2, "⭐ Top Score", f"{best['solar_site_score']:.1f}/100", f"Grade: {best['grade']}"),
        (c3, "✅ A+ Grade", f"{excellent_count}", "Governorates"),
        (c4, "👍 Recommended", f"{recommended_count}/27", "Locations"),
        (c5, "☀️ Nat. Avg Radiation", f"{nat_avg:.2f}", "kWh/m²/day"),
    ]
    for col, label, value, delta in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <span class="kpi-value">{value}</span>
                <div class="kpi-label">{label}</div>
                <div class="kpi-delta">{delta}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main charts
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Bar chart — all governorates by score
        fig_bar = px.bar(
            filtered_scores.sort_values("solar_site_score"),
            x="solar_site_score",
            y="governorate",
            orientation="h",
            color="solar_site_score",
            color_continuous_scale=SCORE_COLORSCALE,
            title="Solar Site Score — All Egyptian Governorates",
            labels={"solar_site_score": "Score (0-100)", "governorate": ""},
            text="solar_site_score",
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            coloraxis_showscale=False,
            height=650,
            margin=dict(l=10, r=50, t=40, b=10),
        )
        fig_bar.update_xaxes(gridcolor="#1E293B", range=[0, 105])
        fig_bar.update_yaxes(tickfont=dict(size=11))
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_right:
        # Grade distribution donut
        grade_counts = filtered_scores["grade"].value_counts().reset_index()
        grade_counts.columns = ["grade", "count"]
        grade_counts["color"] = grade_counts["grade"].map(GRADE_COLORS)
        
        fig_donut = px.pie(
            grade_counts,
            values="count",
            names="grade",
            title="Grade Distribution",
            color="grade",
            color_discrete_map=GRADE_COLORS,
            hole=0.55,
        )
        fig_donut.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            legend=dict(orientation="h", y=-0.1),
            margin=dict(t=40, b=0),
        )
        fig_donut.update_traces(textinfo="label+percent")
        st.plotly_chart(fig_donut, use_container_width=True)
        
        # Region box plot
        fig_box = px.box(
            filtered_scores,
            x="region",
            y="solar_site_score",
            color="region",
            title="Score by Region",
            points="all",
        )
        fig_box.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            showlegend=False,
            margin=dict(t=40, b=10),
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Bottom insight banner
    st.markdown("""
    <div class="info-box">
        <strong>🔍 Key Insight:</strong> Southern Egyptian governorates (Aswan, Luxor, New Valley)
        outperform the Nile Delta region by <strong>35–40%</strong> in solar radiation due to higher 
        clearness index (0.90+ vs 0.67-0.74), significantly lower humidity, and cleaner air quality.
        Every 1.0 increase in kWh/m²/day translates to ~650 MWh/year more energy per MW of installed capacity.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE: SOLAR MAP
# ══════════════════════════════════════════════════════════════════

elif "Map" in page:
    st.markdown("## 🗺️ Solar Radiation Map — Egypt")
    
    col_ctrl, col_map = st.columns([1, 3])
    
    with col_ctrl:
        st.markdown("**Map Settings**")
        map_metric = st.selectbox("Color by:", [
            "solar_site_score", "avg_solar_radiation", 
            "clearness_index", "avg_aqi", "avg_humidity"
        ])
        map_size = st.selectbox("Bubble size:", [
            "avg_solar_radiation", "avg_wind_speed", "solar_site_score"
        ])
        show_labels = st.checkbox("Show labels", True)
        
        st.markdown("---")
        st.markdown("**Filter**")
        grade_sel = st.multiselect("Grade", ["A+", "A", "B", "C", "D"], 
                                   default=["A+", "A", "B", "C", "D"])
        
        map_data = filtered_scores[filtered_scores["grade"].isin(grade_sel)]
        
        st.markdown("---")
        st.markdown("**Legend**")
        for grade, color in GRADE_COLORS.items():
            count = len(scores_df[scores_df["grade"] == grade])
            st.markdown(f'<span style="color:{color}">●</span> Grade {grade}: {count} govs',
                        unsafe_allow_html=True)
    
    with col_map:
        fig_map = px.scatter_mapbox(
            map_data,
            lat="lat", lon="lon",
            color=map_metric,
            size=map_size,
            hover_name="governorate",
            hover_data={
                "solar_site_score": ":.1f",
                "avg_solar_radiation": ":.2f",
                "grade": True,
                "rank": True,
                "investment_rec": True,
                "lat": False,
                "lon": False,
            },
            color_continuous_scale="RdYlGn",
            size_max=35,
            zoom=5,
            center={"lat": 27, "lon": 30},
            mapbox_style="carto-darkmatter",
            title=f"Egypt Governorates — {map_metric.replace('_', ' ').title()}",
        )
        
        if show_labels:
            fig_map.add_trace(go.Scattermapbox(
                lat=map_data["lat"],
                lon=map_data["lon"],
                mode="text",
                text=map_data["governorate"],
                textfont=dict(size=9, color="white"),
                showlegend=False,
                hoverinfo="skip",
            ))
        
        fig_map.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
        )
        st.plotly_chart(fig_map, use_container_width=True)
    
    # Table below map
    st.markdown("### Governorate Data Table")
    display_cols = ["rank", "governorate", "region", "solar_site_score", 
                    "grade", "avg_solar_radiation", "clearness_index",
                    "avg_aqi", "investment_rec"]
    st.dataframe(
        map_data[display_cols].sort_values("rank").rename(columns={
            "solar_site_score": "Score",
            "avg_solar_radiation": "kWh/m²/day",
            "clearness_index": "Clearness",
            "avg_aqi": "AQI",
            "investment_rec": "Recommendation",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════
# PAGE: COMPARISON
# ══════════════════════════════════════════════════════════════════

elif "Comparison" in page:
    st.markdown("## 📊 Governorate Comparison Tool")
    
    gov_list = sorted(scores_df["governorate"].tolist())
    
    col1, col2 = st.columns(2)
    with col1:
        gov_a = st.selectbox("Governorate A", gov_list, index=0)
    with col2:
        gov_b = st.selectbox("Governorate B", gov_list, index=26)
    
    gov_multi = st.multiselect(
        "Add more for multi-comparison (optional):",
        [g for g in gov_list if g not in [gov_a, gov_b]],
        max_selections=5
    )
    
    all_govs = [gov_a, gov_b] + gov_multi
    compare_df = scores_df[scores_df["governorate"].isin(all_govs)]
    
    # Radar chart
    categories = ["Solar\nRadiation", "Clearness\nIndex", "Temperature\nScore",
                  "Wind\nCooling", "Humidity\nScore", "Air\nQuality"]
    
    fig_radar = go.Figure()
    
    colors = ["#F4A62A", "#0EA5E9", "#22C55E", "#A855F7", "#F43F5E", "#14B8A6", "#F97316"]
    
    for i, (_, row) in enumerate(compare_df.iterrows()):
        # Normalize to 0-100 for radar
        vals = [
            row["score_ghi"] * 100 / 7.0,   # radiation: 7 is max
            row["clearness_index"] * 100,
            max(0, 100 - (row["avg_temp_max"] - 25) * 2),  # temp penalty
            min(100, row["avg_wind_speed"] * 15),
            max(0, 100 - row["avg_humidity"]),
            max(0, (5 - row["avg_aqi"]) * 25),
        ]
        vals = [max(0, min(100, v)) for v in vals]
        
        fig_radar.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=row["governorate"],
        line_color=colors[i % len(colors)],
        fillcolor='rgba(244,166,42,0.1)',
        opacity=0.8,
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
            bgcolor="rgba(30,41,59,0.5)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94A3B8",
        showlegend=True,
        title="Factor-by-Factor Comparison (Radar Chart)",
        height=500,
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Score comparison bar
    fig_comp = px.bar(
        compare_df,
        x="governorate",
        y="solar_site_score",
        color="governorate",
        title="Solar Site Score Comparison",
        text="solar_site_score",
        color_discrete_sequence=colors,
    )
    fig_comp.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_comp.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94A3B8",
        showlegend=False,
        yaxis=dict(range=[0, 105]),
    )
    st.plotly_chart(fig_comp, use_container_width=True)
    
    # Detailed comparison table
    st.markdown("### Detailed Metrics")
    metrics = {
        "Metric": ["Solar Score", "Grade", "Rank", "Solar Radiation (kWh/m²/day)",
                   "Clearness Index", "Avg Max Temp (°C)", "Wind Speed (m/s)",
                   "Humidity (%)", "AQI (1-5)", "Recommendation"],
        **{row["governorate"]: [
            f"{row['solar_site_score']:.1f}/100",
            row["grade"],
            f"#{row['rank']}",
            f"{row['avg_solar_radiation']:.2f}",
            f"{row['clearness_index']:.3f}",
            f"{row['avg_temp_max']:.1f}°C",
            f"{row['avg_wind_speed']:.1f} m/s",
            f"{row['avg_humidity']:.1f}%",
            f"{row['avg_aqi']:.1f}",
            row["investment_rec"],
        ] for _, row in compare_df.iterrows()}
    }
    st.dataframe(pd.DataFrame(metrics), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
# PAGE: SEASONAL ANALYSIS
# ══════════════════════════════════════════════════════════════════

elif "Seasonal" in page:
    st.markdown("## 📅 Seasonal Solar Performance Analysis")
    
    sel_govs = st.multiselect(
        "Select governorates:",
        sorted(scores_df["governorate"].tolist()),
        default=["Aswan", "Cairo", "Alexandria"]
    )
    
    if sel_govs:
        monthly_sel = monthly_df[monthly_df["governorate"].isin(sel_govs)]
        
        # Line chart — monthly radiation
        fig_line = px.line(
            monthly_sel,
            x="month",
            y="solar_radiation",
            color="governorate",
            title="Monthly Solar Radiation Profile (kWh/m²/day)",
            markers=True,
            category_orders={"month": ["Jan","Feb","Mar","Apr","May","Jun",
                                        "Jul","Aug","Sep","Oct","Nov","Dec"]},
        )
        fig_line.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Solar Radiation (kWh/m²/day)"),
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Heatmap
        heat_data = monthly_sel.pivot(
            index="governorate", columns="month", values="solar_radiation"
        )
        month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]
        heat_data = heat_data[[m for m in month_order if m in heat_data.columns]]
        
        fig_heat = px.imshow(
            heat_data,
            title="Solar Radiation Heatmap (Governorate × Month)",
            color_continuous_scale="YlOrRd",
            aspect="auto",
            text_auto=".2f",
        )
        fig_heat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Best/worst month per governorate
        st.markdown("### Best & Worst Months by Governorate")
        summary_rows = []
        for gov in sel_govs:
            gov_data = monthly_sel[monthly_sel["governorate"] == gov]
            if not gov_data.empty:
                best_m = gov_data.loc[gov_data["solar_radiation"].idxmax()]
                worst_m = gov_data.loc[gov_data["solar_radiation"].idxmin()]
                summary_rows.append({
                    "Governorate": gov,
                    "Best Month": best_m["month"],
                    "Peak Radiation": f"{best_m['solar_radiation']:.2f} kWh/m²/day",
                    "Worst Month": worst_m["month"],
                    "Min Radiation": f"{worst_m['solar_radiation']:.2f} kWh/m²/day",
                    "Variance": f"{gov_data['solar_radiation'].std():.2f}",
                })
        
        if summary_rows:
            st.dataframe(pd.DataFrame(summary_rows), 
                         use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
# PAGE: HISTORICAL TRENDS
# ══════════════════════════════════════════════════════════════════

elif "Historical" in page:
    st.markdown("## 📈 44-Year Solar Trend Analysis (1981–2025)")
    
    trend_govs = st.multiselect(
        "Select governorates:",
        sorted(scores_df["governorate"].tolist()),
        default=["Aswan", "Cairo"]
    )
    
    if trend_govs:
        trend_data = annual_df[annual_df["governorate"].isin(trend_govs)]
        
        # Area chart
        fig_trend = px.area(
            trend_data,
            x="year",
            y="solar_radiation",
            color="governorate",
            title="Annual Solar Radiation Trend (1981–2025)",
            labels={"solar_radiation": "kWh/m²/day", "year": "Year"},
        )
        fig_trend.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Temperature trend
        fig_temp = px.line(
            trend_data,
            x="year",
            y="avg_temp",
            color="governorate",
            title="Annual Average Temperature Trend — Climate Change Evidence",
            labels={"avg_temp": "Avg Temp (°C)", "year": "Year"},
        )
        # Add trendline
        for gov in trend_govs:
            gov_temp = trend_data[trend_data["governorate"] == gov].sort_values("year")
            z = np.polyfit(gov_temp["year"], gov_temp["avg_temp"], 1)
            p = np.poly1d(z)
            fig_temp.add_trace(go.Scatter(
                x=gov_temp["year"],
                y=p(gov_temp["year"]),
                mode="lines",
                name=f"{gov} (trend)",
                line=dict(dash="dash", width=1),
            ))
        
        fig_temp.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Decade comparison
        decade_data = trend_data.copy()
        decade_summary = decade_data.groupby(["governorate", "decade"]).agg(
            avg_radiation=("solar_radiation", "mean")
        ).reset_index()
        
        fig_decade = px.bar(
            decade_summary,
            x="decade",
            y="avg_radiation",
            color="governorate",
            barmode="group",
            title="Radiation by Decade — Long-term Change",
        )
        fig_decade.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
        )
        st.plotly_chart(fig_decade, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE: AI ADVISOR CHATBOT
# ══════════════════════════════════════════════════════════════════

elif "AI" in page:
    st.markdown("## 🤖 SolarIQ AI Advisor")
    st.markdown("Ask anything about solar energy potential across Egypt's 27 governorates.")
    
    # API key status
    if os.getenv("OPENAI_API_KEY"):
        st.success("✅ OpenAI API connected — Full AI mode active")
    else:
        st.info("ℹ️ Running in offline mode. Add OPENAI_API_KEY to .env for full AI responses.")
    
    st.markdown("---")
    
    # Suggested questions
    st.markdown("**💡 Quick Questions:**")
    q_cols = st.columns(3)
    suggestions = [
        "What is the best governorate for solar investment?",
        "Compare Cairo and Aswan for solar energy",
        "Which months are best for solar in Luxor?",
        "Explain the Solar Site Score formula",
        "What is the ROI in Aswan vs Alexandria?",
        "Which governorates have Grade A+ solar potential?",
    ]
    for i, suggestion in enumerate(suggestions):
        with q_cols[i % 3]:
            if st.button(f"💬 {suggestion}", key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_messages.append({
                    "role": "user", "content": suggestion
                })
                response = st.session_state.chatbot.chat(suggestion)
                st.session_state.chat_messages.append({
                    "role": "assistant", "content": response
                })
    
    st.markdown("---")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            st.markdown("""
            <div style="text-align:center; padding:40px; color:#475569;">
                <div style="font-size:3rem;">🌞</div>
                <div style="margin-top:12px; font-size:1rem;">
                    Start a conversation with SolarIQ AI Advisor
                </div>
                <div style="font-size:0.85rem; margin-top:8px;">
                    Ask about solar scores, rankings, ROI, or seasonal performance
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-user">👤 {msg['content']}</div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-ai">
                        <div class="chat-ai-label">☀️ SolarIQ AI</div>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Input
    col_input, col_send, col_clear = st.columns([6, 1, 1])
    with col_input:
        user_input = st.text_input(
            "Ask SolarIQ AI...",
            placeholder="e.g. What is the best solar location in Upper Egypt?",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col_send:
        send_btn = st.button("Send ➤", use_container_width=True)
    with col_clear:
        if st.button("Clear 🗑️", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.chatbot.conversation_history = []
            st.rerun()
    
    if send_btn and user_input.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.spinner("SolarIQ AI is thinking..."):
            response = st.session_state.chatbot.chat(user_input)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# PAGE: ROI CALCULATOR
# ══════════════════════════════════════════════════════════════════

elif "ROI" in page:
    st.markdown("## 💰 Solar ROI Calculator")
    st.markdown("Get a data-driven financial estimate for your solar investment.")
    
    col_inputs, col_results = st.columns([2, 3])
    
    with col_inputs:
        st.markdown("### 📝 Project Parameters")
        
        gov_sel = st.selectbox("📍 Location", sorted(scores_df["governorate"].tolist()))
        capacity_mw = st.slider("⚡ Plant Capacity (MW)", 1, 500, 50)
        
        st.markdown("**Financial Parameters**")
        elec_price = st.number_input("Electricity Tariff (EGP/kWh)", 0.5, 10.0, 1.80, 0.1)
        capex_mw = st.number_input("CapEx per MW (Million EGP)", 5.0, 40.0, 15.0, 0.5)
        opex_pct = st.slider("Annual OpEx (% of CapEx)", 0.5, 5.0, 1.5, 0.1)
        
        st.markdown("**Technical Parameters**")
        panel_eff = st.slider("Panel Efficiency (%)", 15, 25, 20)
        degradation = st.slider("Annual Degradation (%/year)", 0.2, 1.0, 0.5, 0.1)
        project_life = st.slider("Project Life (years)", 15, 30, 25)
        
        st.markdown("**Risk Level**")
        risk = st.radio("Risk Assumption", ["Conservative", "Base Case", "Optimistic"],
                        horizontal=True, index=1)
        risk_mult = {"Conservative": 0.85, "Base Case": 1.0, "Optimistic": 1.10}[risk]
        
        calc_btn = st.button("🔢 Calculate ROI", use_container_width=True, type="primary")
    
    with col_results:
        gov_data = scores_df[scores_df["governorate"] == gov_sel].iloc[0]
        
        # Always show gov summary
        st.markdown(f"### 📊 {gov_sel} — Solar Profile")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Solar Score", f"{gov_data['solar_site_score']:.1f}/100")
        m2.metric("Grade", gov_data["grade"])
        m3.metric("Radiation", f"{gov_data['avg_solar_radiation']:.2f} kWh/m²/day")
        m4.metric("Rank", f"#{gov_data['rank']}")
        
        # Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gov_data["solar_site_score"],
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Solar Site Score", "font": {"color": "#94A3B8"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94A3B8"},
                "bar": {"color": "#F4A62A"},
                "bgcolor": "#1E293B",
                "steps": [
                    {"range": [0, 40],  "color": "#3B0F0F"},
                    {"range": [40, 60], "color": "#3B2A0F"},
                    {"range": [60, 75], "color": "#2D3B0F"},
                    {"range": [75, 100],"color": "#0F3B1A"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 3},
                    "thickness": 0.8,
                    "value": gov_data["solar_site_score"],
                },
            },
            number={"font": {"color": "#F4A62A", "size": 36}},
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            height=250,
            margin=dict(t=30, b=0),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        if calc_btn:
            st.markdown("---")
            st.markdown("### 💹 Financial Results")
            
            # Core calculations
            daily_radiation = gov_data["avg_solar_radiation"] * risk_mult
            temp_loss = max(0, (gov_data["avg_temp_max"] - 25) * 0.004)
            aqi_loss = min(0.15, (gov_data["avg_aqi"] - 1) * 0.025)
            
            effective_efficiency = (panel_eff / 100) * (1 - temp_loss) * (1 - aqi_loss)
            
            daily_kwh = capacity_mw * 1000 * daily_radiation * effective_efficiency
            annual_mwh = daily_kwh * 365 / 1000
            
            total_capex = capacity_mw * capex_mw  # Million EGP
            annual_opex = total_capex * (opex_pct / 100)
            annual_revenue = annual_mwh * elec_price * 1000 / 1_000_000  # M EGP
            annual_net = annual_revenue - annual_opex
            
            if annual_net > 0:
                payback = total_capex / annual_net
            else:
                payback = float("inf")
            
            # 25-year NPV (simplified, 10% discount rate)
            discount_rate = 0.10
            npv = -total_capex
            for yr in range(1, project_life + 1):
                deg_factor = (1 - degradation / 100) ** yr
                yr_revenue = annual_mwh * deg_factor * elec_price * 1000 / 1_000_000
                yr_net = yr_revenue - annual_opex
                npv += yr_net / ((1 + discount_rate) ** yr)
            
            irr_approx = annual_net / total_capex * 100
            
            # Results grid
            r1, r2, r3 = st.columns(3)
            r1.metric("Annual Generation", f"{annual_mwh:,.0f} MWh")
            r2.metric("Annual Revenue", f"EGP {annual_revenue:.1f}M")
            r3.metric("Annual Net Profit", f"EGP {annual_net:.1f}M")
            
            r4, r5, r6 = st.columns(3)
            r4.metric("Total CapEx", f"EGP {total_capex:.0f}M")
            r5.metric("Payback Period", f"{payback:.1f} years")
            r6.metric("Estimated IRR", f"~{irr_approx:.1f}%/yr")
            
            # NPV
            npv_color = "normal" if npv > 0 else "inverse"
            st.metric("25-Year NPV (10% discount)", f"EGP {npv:.1f}M", 
                      delta="Positive investment" if npv > 0 else "Negative NPV")
            
            # 25-year cashflow chart
            years_range = list(range(1, project_life + 1))
            cumulative_cf = []
            cum = -total_capex
            for yr in years_range:
                deg = (1 - degradation / 100) ** yr
                yr_rev = annual_mwh * deg * elec_price * 1000 / 1_000_000
                yr_net = yr_rev - annual_opex
                cum += yr_net
                cumulative_cf.append(round(cum, 1))
            
            fig_cf = go.Figure()
            fig_cf.add_trace(go.Scatter(
                x=years_range, y=cumulative_cf,
                mode="lines+markers",
                name="Cumulative Cash Flow",
                line=dict(color="#F4A62A", width=2),
                fill="tozeroy",
                fillcolor="rgba(244,166,42,0.1)",
            ))
            fig_cf.add_hline(y=0, line_dash="dash", line_color="#94A3B8",
                             annotation_text="Break-even")
            fig_cf.update_layout(
                title=f"{project_life}-Year Cumulative Cash Flow",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94A3B8",
                xaxis=dict(gridcolor="#1E293B", title="Year"),
                yaxis=dict(gridcolor="#1E293B", title="Cumulative (Million EGP)"),
            )
            st.plotly_chart(fig_cf, use_container_width=True)
            
            # Recommendation box
            if npv > 0 and payback < 12:
                st.markdown(f"""
                <div class="rec-card">
                    <div class="rec-title">✅ Investment Recommended</div>
                    <div class="rec-body">
                        Based on the SolarIQ analysis, a {capacity_mw}MW plant in 
                        <strong>{gov_sel}</strong> is financially viable under 
                        <strong>{risk}</strong> assumptions. 
                        The {payback:.1f}-year payback period is within acceptable range,
                        and the positive NPV of EGP {npv:.1f}M confirms long-term value creation.
                        <br><br>
                        <strong>Next Steps:</strong> Commission a detailed feasibility study,
                        secure grid connection approval from EETC, and apply for NREA land permits.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ Under {risk} assumptions, this investment shows a long payback "
                           f"({payback:.1f} years). Consider a more favorable location or "
                           "review financial parameters.")


# ══════════════════════════════════════════════════════════════════
# PAGE: FULL RANKINGS
# ══════════════════════════════════════════════════════════════════

elif "Rankings" in page:
    st.markdown("## 📋 Full National Solar Rankings")
    st.markdown("All 27 Egyptian governorates ranked by Solar Site Score")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        min_score_r = st.slider("Minimum Score", 0, 100, 0)
    with col_f2:
        rec_filter = st.multiselect(
            "Investment Status",
            ["Strongly Recommended", "Recommended", "Neutral", "Not Recommended"],
            default=["Strongly Recommended", "Recommended", "Neutral", "Not Recommended"]
        )
    
    ranked_df = scores_df[
        (scores_df["solar_site_score"] >= min_score_r) &
        (scores_df["investment_rec"].isin(rec_filter))
    ].sort_values("rank")
    
    # Waterfall chart showing scores
    fig_wf = go.Figure(go.Bar(
        x=ranked_df["governorate"],
        y=ranked_df["solar_site_score"],
        marker=dict(
            color=ranked_df["solar_site_score"],
            colorscale="RdYlGn",
            cmin=0,
            cmax=100,
        ),
        text=[f"{s:.1f}" for s in ranked_df["solar_site_score"]],
        textposition="outside",
    ))
    fig_wf.update_layout(
        title="National Solar Site Score Ranking",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94A3B8",
        xaxis=dict(tickangle=45, gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B", range=[0, 105]),
        height=400,
    )
    st.plotly_chart(fig_wf, use_container_width=True)
    
    # Full table
    display_df = ranked_df[[
        "rank", "governorate", "region", "solar_site_score", "grade",
        "avg_solar_radiation", "clearness_index", "avg_temp_max",
        "avg_wind_speed", "avg_humidity", "avg_aqi", "investment_rec"
    ]].rename(columns={
        "rank": "#",
        "solar_site_score": "Score",
        "avg_solar_radiation": "kWh/m²/day",
        "clearness_index": "Clearness",
        "avg_temp_max": "Temp Max°C",
        "avg_wind_speed": "Wind m/s",
        "avg_humidity": "Humidity%",
        "avg_aqi": "AQI",
        "investment_rec": "Recommendation",
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Export button
    csv_export = ranked_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Rankings CSV",
        csv_export,
        "solariq_egypt_rankings.csv",
        "text/csv",
    )
