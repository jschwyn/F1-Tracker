"""
app.py
──────
Streamlit front-end for the F1 Lap Tracker.
Run with:  streamlit run app.py
"""

import streamlit as st
import laptracker as lt

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="F1 Lap Tracker", page_icon="🏎️", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

  html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; background-color: #0d0d0d; color: #e8e8e8; }
  .stApp { background-color: #0d0d0d; }
  h1, h2, h3 { font-family: 'Orbitron', monospace !important; letter-spacing: 0.05em; }

  .hero-title {
    font-family: 'Orbitron', monospace; font-size: 3rem; font-weight: 900;
    background: linear-gradient(90deg, #e10600 0%, #ff6b35 50%, #ffffff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: 0.1em; margin-bottom: 0; line-height: 1.1;
  }
  .hero-sub {
    font-family: 'Rajdhani', sans-serif; font-size: 1.1rem; color: #888;
    letter-spacing: 0.25em; text-transform: uppercase; margin-top: 4px; margin-bottom: 2rem;
  }

  .stButton > button {
    background: linear-gradient(135deg, #e10600, #b00400); color: white;
    font-family: 'Orbitron', monospace; font-weight: 700; font-size: 0.85rem;
    letter-spacing: 0.15em; border: none; border-radius: 3px; padding: 0.65rem 2rem;
    transition: all 0.2s ease; text-transform: uppercase; width: 100%;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #ff1a16, #e10600);
    box-shadow: 0 0 20px rgba(225,6,0,0.5); transform: translateY(-1px);
  }

  .stSelectbox label, .stTextInput label, .stNumberInput label {
    font-family: 'Orbitron', monospace !important; font-size: 0.7rem !important;
    letter-spacing: 0.15em !important; color: #e10600 !important; text-transform: uppercase;
  }
  .stSelectbox > div > div, .stTextInput > div > div > input {
    background-color: #1a1a1a !important; border: 1px solid #333 !important;
    border-radius: 3px !important; color: #e8e8e8 !important;
    font-family: 'Rajdhani', sans-serif !important; font-size: 1rem !important;
  }

  .metric-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #111 100%);
    border: 1px solid #2a2a2a; border-left: 3px solid #e10600;
    border-radius: 4px; padding: 1rem 1.25rem; margin-bottom: 0.5rem;
  }
  .metric-label { font-family: 'Orbitron', monospace; font-size: 0.65rem; letter-spacing: 0.2em; color: #666; text-transform: uppercase; margin-bottom: 4px; }
  .metric-value { font-family: 'Orbitron', monospace; font-size: 1.4rem; font-weight: 700; color: #e8e8e8; }
  .driver1-accent { border-left-color: #0600ef; }
  .driver2-accent { border-left-color: #dc0000; }

  .divider { border: none; border-top: 1px solid #2a2a2a; margin: 1.5rem 0; }
  .section-label { font-family: 'Orbitron', monospace; font-size: 0.7rem; letter-spacing: 0.3em; color: #e10600; text-transform: uppercase; margin-bottom: 0.75rem; }
  .info-banner {
    background: linear-gradient(90deg, #1a1a1a, #111); border: 1px solid #2a2a2a;
    border-top: 2px solid #e10600; border-radius: 4px; padding: 0.75rem 1.25rem;
    margin-bottom: 1.5rem; font-size: 0.95rem; color: #aaa;
  }
  .stDataFrame { font-family: 'Rajdhani', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ── Cache init ────────────────────────────────────────────────────────────────
lt.enable_cache()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">F1 LAP TRACKER</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Telemetry · Animation · Comparison</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Session Parameters</div>', unsafe_allow_html=True)

    year = st.number_input("Year", min_value=2018, max_value=2025, value=2024, step=1)
    race = st.text_input("Race", value="Monaco", placeholder="e.g. Monaco, Monza, Silverstone")

    session_map = {
        "Qualifying (Q)":       "Q",
        "Race (R)":             "R",
        "FP1 – Free Practice 1": "FP1",
        "FP2 – Free Practice 2": "FP2",
        "FP3 – Free Practice 3": "FP3",
        "Sprint (S)":           "S",
    }
    session_label = st.selectbox("Session", list(session_map.keys()))
    session_code  = session_map[session_label]

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Drivers</div>', unsafe_allow_html=True)

    driver1 = st.text_input("Driver 1", value="VER", placeholder="e.g. VER").strip().upper()
    driver2 = st.text_input("Driver 2", value="LEC", placeholder="e.g. LEC").strip().upper()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Animation Quality</div>', unsafe_allow_html=True)
    fps         = st.slider("FPS", min_value=10, max_value=30, value=15)
    sample_rate = st.slider("Telemetry Sample Rate (higher = faster)", min_value=1, max_value=10, value=3)

    run = st.button("🏁  GENERATE ANALYSIS")

# ── Landing state ─────────────────────────────────────────────────────────────
if not run:
    st.markdown("""
    <div class="info-banner">
      Configure your session in the sidebar, then hit <strong>GENERATE ANALYSIS</strong>
      to load telemetry, compare lap times, and render the track animation.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, icon, title, desc in [
        (col1, "Live Telemetry",  "Pulls positional data direct from the FastF1 API for any session from 2018 onward."),
        (col2, "Lap Comparison",  "Side-by-side table of every lap, with the fastest lap highlighted for each driver."),
        (col3, "Track Animation", "Animated GIF showing both cars moving around the circuit on their fastest laps."),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:1.8rem;margin-bottom:8px">{icon}</div>
              <div class="metric-label">{title}</div>
              <div style="font-size:0.9rem;color:#888;font-family:'Rajdhani',sans-serif">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ── Load session ──────────────────────────────────────────────────────────────
with st.spinner(f"Loading {year} {race} GP – {session_code}…"):
    try:
        session      = lt.load_session(year, race, session_code)
        circuit_info = lt.get_circuit_info(session)
    except Exception as e:
        st.error(f"❌ Could not load session: {e}")
        st.stop()

# ── Circuit info strip ────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
for col, label, value in [
    (c1, "Event",    circuit_info["EventName"]),
    (c2, "Location", circuit_info["Location"]),
    (c3, "Country",  circuit_info["Country"]),
    (c4, "Date",     circuit_info["Date"]),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="font-size:1rem">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Driver data ───────────────────────────────────────────────────────────────
with st.spinner("Fetching driver data…"):
    try:
        laps1, fastest1 = lt.get_driver_data(session, driver1)
        laps2, fastest2 = lt.get_driver_data(session, driver2)
    except ValueError as e:
        st.error(f"❌ {e}")
        st.stop()

# ── Fastest lap metrics ───────────────────────────────────────────────────────
m1, m2 = st.columns(2)
with m1:
    st.markdown(f"""
    <div class="metric-card driver1-accent">
      <div class="metric-label">🔵 {driver1} – Fastest Lap</div>
      <div class="metric-value">{fastest1['LapTime']}</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card driver2-accent">
      <div class="metric-label">🔴 {driver2} – Fastest Lap</div>
      <div class="metric-value">{fastest2['LapTime']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Lap times table ───────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Lap Times Comparison</div>', unsafe_allow_html=True)

lap_df = lt.build_lap_table(driver1, laps1, fastest1, driver2, laps2, fastest2)
st.dataframe(lap_df, use_container_width=True, hide_index=True, height=380)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Animation ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Track Animation – Fastest Lap</div>', unsafe_allow_html=True)

with st.spinner("Rendering animation… this may take a minute ⏳"):
    try:
        gif_bytes = lt.build_animation_gif(
            driver1, fastest1,
            driver2, fastest2,
            circuit_info,
            fps=fps,
            sample_rate=sample_rate,
        )

        st.image(gif_bytes,
                 caption=f"{driver1} vs {driver2} – Fastest Lap Animation",
                 use_container_width=True)

        st.download_button(
            label="Download GIF",
            data=gif_bytes,
            file_name=f"{year}_{race}_{driver1}_vs_{driver2}.gif",
            mime="image/gif",
        )

    except Exception as e:
        st.error(f"Animation error: {e}")
        st.exception(e)