import streamlit as st


def apply_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }

        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            background-color: #F4F6F9 !important;
            color: #1F2937 !important;
        }

        header[data-testid="stHeader"] {
            background-color: #0B3D6E !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #0B3D6E !important;
        }

        section[data-testid="stSidebar"] * {
            color: #F4F6F9 !important;
        }

        p, span, label, div {
            color: #1F2937;
        }

        h1, h2, h3 {
            color: #0B3D6E !important;
            font-weight: 700;
        }

        /* Tricolor strip - official touch, right under the header */
        .tricolor-strip {
            height: 4px;
            width: 100%;
            background: linear-gradient(90deg, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #138808 66%);
            margin-bottom: 20px;
            border-radius: 2px;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #D8DEE6;
            border-radius: 8px;
            padding: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }

        div[data-testid="stMetric"] label {
            color: #6B7280 !important;
        }

        div[data-testid="stMetricValue"] {
            color: #0B3D6E !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            color: #6B7280 !important;
            font-weight: 500;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #0E7490 !important;
            border-bottom: 3px solid #0E7490 !important;
        }

        /* Dataframe/table container */
        [data-testid="stDataFrame"] {
            border: 1px solid #D8DEE6;
            border-radius: 8px;
        }

        /* Buttons */
        .stButton > button {
            background-color: #0E7490;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
        }

        .stButton > button:hover {
            background-color: #0B3D6E;
            color: white;
        }

        
                /* ===== SIDEBAR — Professional Redesign ===== */
        section[data-testid="stSidebar"] {
            background-color: #0B3D6E !important;
            border-right: 1px solid #082C52;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.5rem;
        }

        /* Sidebar nav container */
        [data-testid="stSidebarNav"] {
            padding: 0 12px;
        }

        /* Sidebar nav links - bada, readable font */
        [data-testid="stSidebarNav"] a {
            font-size: 18px !important;
            font-weight: 500 !important;
            color: #D6E4F0 !important;
            padding: 12px 16px !important;
            margin-bottom: 4px !important;
            border-radius: 8px !important;
            display: block !important;
            transition: background-color 0.2s ease;
        }

        [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebarNav"] a p {
            font-size: 18px !important;
            color: #D6E4F0 !important;
        }

        /* Hover effect */
        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
        }

        /* Currently active page - highlighted */
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: #FFFFFF !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNav"] a[aria-current="page"] p {
            color: #0B3D6E !important;
            font-weight: 700 !important;
        }

        /* Overall spacing tight karo - top padding kam karo */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }

        /* Title thoda chota karo taaki jyada jagah na le */
        h1 {
            font-size: 47px !important;
            margin-bottom: 0.2rem !important;
        }

        h3 {
            font-size: 18px !important;
            margin-top: 0.8rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Metric cards ka padding kam karo */
        div[data-testid="stMetric"] {
            padding: 10px !important;
        }
                /* Dataframe - light theme se match karo */
        [data-testid="stDataFrame"] {
            background-color: #FFFFFF !important;
        }

        [data-testid="stDataFrame"] * {
            color: #1F2937 !important;
        }

        [data-testid="stDataFrame"] [role="columnheader"] {
            background-color: #F1F5F9 !important;
            color: #0B3D6E !important;
            font-weight: 600 !important;
        }

        [data-testid="stDataFrame"] div[role="row"]:nth-child(even) {
            background-color: #F9FAFB !important;
        }
                /* Selectbox - clearly ek dropdown jaisa dikhna chahiye */
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 2px solid #0E7490 !important;
            border-radius: 6px !important;
            min-height: 44px !important;
        }

        div[data-baseweb="select"] span {
            color: #1F2937 !important;
            font-size: 16px !important;
        }

        /* Label upar wala ("Select a station") bhi thoda bold */
        .stSelectbox label {
            font-weight: 600 !important;
            font-size: 15px !important;
            color: #0B3D6E !important;
        }    
        </style>
    """, unsafe_allow_html=True)


def tricolor_strip():
    st.markdown('<div class="tricolor-strip"></div>', unsafe_allow_html=True)


RISK_COLORS = {
    "Normal": "#16A34A",
    "Watch": "#CA8A04",
    "Warning": "#EA580C",
    "Danger": "#DC2626",
    "Unknown": "#6B7280"
}
def data_attribution():
    st.caption(
        "Data: Central Water Commission (water level) and Narmada Control Authority (rainfall), "
        "via the National Water Data Portal, NWIC, Ministry of Jal Shakti, Govt. of India. "
        "Values shown are processed by this project and are not official figures."
    )