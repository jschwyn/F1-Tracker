import os
import gc
import warnings

import fastf1
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import streamlit as st

warnings.filterwarnings('ignore')

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')


# ============================================================================
# Data loading (cached so re-runs on widget changes don't re-download)
# ============================================================================
@st.cache_resource(show_spinner=False)
def load_session(year, race, session_code):
    """Load a fastf1 session. Cached per (year, race, session)."""
    session = fastf1.get_session(year, race, session_code)
    session.load()
    return session


def build_lap_table(session, driver_1, driver_2, d1_fastest, d2_fastest):
    """Build the lap-by-lap comparison DataFrame for the two drivers."""
    driver1_laps = session.laps.pick_driver(driver_1)
    driver2_laps = session.laps.pick_driver(driver_2)

    lap_data = []
    for i, lap in enumerate(driver1_laps.iterlaps(), 1):
        lap_data.append({
            'Lap': i,
            f'{driver_1} Time': lap[1]['LapTime'],
            f'{driver_1} Fastest': '★' if lap[1]['LapTime'] == d1_fastest['LapTime'] else ''
        })

    for i, lap in enumerate(driver2_laps.iterlaps(), 1):
        if i <= len(lap_data):
            lap_data[i - 1][f'{driver_2} Time'] = lap[1]['LapTime']
            lap_data[i - 1][f'{driver_2} Fastest'] = '★' if lap[1]['LapTime'] == d2_fastest['LapTime'] else ''
        else:
            lap_data.append({
                'Lap': i,
                f'{driver_1} Time': None,
                f'{driver_1} Fastest': '',
                f'{driver_2} Time': lap[1]['LapTime'],
                f'{driver_2} Fastest': '★' if lap[1]['LapTime'] == d2_fastest['LapTime'] else ''
            })

    return pd.DataFrame(lap_data)


def get_position(time_val, time_array, x_array, y_array):
    """Interpolate (x, y) position at a given time."""
    if time_val > time_array[-1]:
        return x_array[-1], y_array[-1]
    idx = np.searchsorted(time_array, time_val)
    if idx == 0:
        return x_array[0], y_array[0]
    if idx >= len(time_array):
        return x_array[-1], y_array[-1]
    t1, t2 = time_array[idx - 1], time_array[idx]
    alpha = (time_val - t1) / (t2 - t1) if t2 != t1 else 0
    x = x_array[idx - 1] + alpha * (x_array[idx] - x_array[idx - 1])
    y = y_array[idx - 1] + alpha * (y_array[idx] - y_array[idx - 1])
    return x, y


def build_animation(circuit_info, driver_1, driver_2, d1_fastest, d2_fastest,
                    output_filename, sample_rate=3, fps=15):
    """Render the fastest-lap comparison animation to a GIF and return its path."""
    driver1_tel = d1_fastest.get_telemetry().iloc[::sample_rate].reset_index(drop=True)
    driver2_tel = d2_fastest.get_telemetry().iloc[::sample_rate].reset_index(drop=True)

    driver1_x = driver1_tel['X'].values
    driver1_y = driver1_tel['Y'].values
    driver2_x = driver2_tel['X'].values
    driver2_y = driver2_tel['Y'].values

    driver1_time = driver1_tel['Time'].dt.total_seconds().values
    driver2_time = driver2_tel['Time'].dt.total_seconds().values
    driver1_time = driver1_time - driver1_time[0]
    driver2_time = driver2_time - driver2_time[0]

    gc.collect()

    fig, ax = plt.subplots(figsize=(10, 8), dpi=60)
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#2a2a2a')

    track_sample = 5
    ax.plot(driver1_x[::track_sample], driver1_y[::track_sample],
            color='white', alpha=0.3, linewidth=1.5,
            linestyle='--', label='Track Layout')

    driver1_point, = ax.plot([], [], 'o', color='#0600ef', markersize=12,
                             label=f'{driver_1}', markeredgecolor='white', markeredgewidth=1.5)
    driver2_point, = ax.plot([], [], 'o', color='#dc0000', markersize=12,
                             label=f'{driver_2}', markeredgecolor='white', markeredgewidth=1.5)
    driver1_trail, = ax.plot([], [], color='#0600ef', alpha=0.5, linewidth=1.5)
    driver2_trail, = ax.plot([], [], color='#dc0000', alpha=0.5, linewidth=1.5)

    time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                        fontsize=11, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                        color='white', fontfamily='monospace')

    title_text = (f"{circuit_info['EventName']} - {circuit_info['Location']}\n"
                  f"{driver_1} vs {driver_2} - Fastest Lap Comparison")
    ax.set_title(title_text, fontsize=14, color='white', pad=15, fontweight='bold')

    ax.set_xlabel('X Position (m)', fontsize=10, color='white')
    ax.set_ylabel('Y Position (m)', fontsize=10, color='white')
    ax.tick_params(colors='white', labelsize=9)
    ax.legend(loc='upper right', fontsize=9, facecolor='black',
              edgecolor='white', labelcolor='white')
    ax.grid(True, alpha=0.2, color='white')
    ax.set_aspect('equal')

    max_time = max(driver1_time[-1], driver2_time[-1])
    total_frames = int(max_time * fps)

    def animate(frame):
        current_time = frame / fps
        x1, y1 = get_position(current_time, driver1_time, driver1_x, driver1_y)
        x2, y2 = get_position(current_time, driver2_time, driver2_x, driver2_y)
        driver1_point.set_data([x1], [y1])
        driver2_point.set_data([x2], [y2])

        trail_length = 30
        start_frame = max(0, frame - trail_length)
        trail1_x, trail1_y, trail2_x, trail2_y = [], [], [], []
        for f in range(start_frame, frame + 1, 2):
            t = f / fps
            tx1, ty1 = get_position(t, driver1_time, driver1_x, driver1_y)
            tx2, ty2 = get_position(t, driver2_time, driver2_x, driver2_y)
            trail1_x.append(tx1)
            trail1_y.append(ty1)
            trail2_x.append(tx2)
            trail2_y.append(ty2)
        driver1_trail.set_data(trail1_x, trail1_y)
        driver2_trail.set_data(trail2_x, trail2_y)

        time_text.set_text(f'Time: {current_time:.2f}s\n'
                           f'{driver_1}: {d1_fastest["LapTime"]}\n'
                           f'{driver_2}: {d2_fastest["LapTime"]}')
        return driver1_point, driver2_point, driver1_trail, driver2_trail, time_text

    anim = FuncAnimation(fig, animate, frames=total_frames,
                         interval=1000 / fps, blit=True, repeat=True)
    writer = PillowWriter(fps=fps, bitrate=1800)
    anim.save(output_filename, writer=writer, dpi=60)

    plt.close('all')
    gc.collect()
    return output_filename, max_time, total_frames


# ============================================================================
# Streamlit UI
# ============================================================================
st.set_page_config(page_title="F1 Lap Tracker", page_icon="🏎️", layout="centered")
st.title("F1 Fastest-Lap Tracker")
st.caption("Compare two drivers' fastest laps with a side-by-side track animation.")

with st.sidebar:
    st.header("Session")
    year = st.number_input("Year", min_value=1950, max_value=2026, value=2024, step=1)
    race = st.text_input("Race name", value="Monaco",
                         help="e.g. Monaco, Sao Paulo, Bahrain")
    session_code = st.selectbox(
        "Session",
        options=["R", "Q", "SQ", "S", "FP1", "FP2", "FP3"],
        index=1,
        help="R=Race, Q=Qualifying, SQ=Sprint Quali, S=Sprint, FP=Practice",
    )

    st.header("Drivers")
    driver_1 = st.text_input("Driver 1 code", value="VER",
                             help="3-letter code, e.g. VER").strip().upper()
    driver_2 = st.text_input("Driver 2 code", value="LEC",
                             help="3-letter code, e.g. LEC").strip().upper()

    generate = st.button("Generate comparison", type="primary", use_container_width=True)

if not generate:
    st.info("Set the session and drivers in the sidebar, then click **Generate comparison**.")
    st.stop()

if not race.strip():
    st.error("Please enter a race name.")
    st.stop()
if not driver_1 or not driver_2:
    st.error("Please enter both driver codes.")
    st.stop()

# --- Load session ---
try:
    with st.spinner(f"Loading {year} {race} GP - {session_code} session..."):
        session = load_session(int(year), race.strip(), session_code)
except Exception as e:
    st.error(f"Could not load session: {e}")
    st.stop()

circuit_info = session.event

st.subheader("Circuit Information")
c1, c2 = st.columns(2)
c1.metric("Event", str(circuit_info['EventName']))
c1.metric("Location", str(circuit_info['Location']))
c2.metric("Country", str(circuit_info['Country']))
c2.metric("Date", str(circuit_info['EventDate']))
st.caption(str(circuit_info['OfficialEventName']))

# --- Fastest laps ---
try:
    d1_fastest = session.laps.pick_driver(driver_1).pick_fastest()
    d2_fastest = session.laps.pick_driver(driver_2).pick_fastest()
    if d1_fastest is None or d2_fastest is None or pd.isna(d1_fastest['LapTime']) or pd.isna(d2_fastest['LapTime']):
        raise ValueError("No valid fastest lap found for one of the drivers.")
except Exception as e:
    st.error(f"Could not find fastest laps for {driver_1} / {driver_2}: {e}")
    st.stop()

# --- Lap table ---
st.subheader(f"Lap Times Comparison — {driver_1} vs {driver_2}")
st.caption("★ indicates the fastest lap used in the animation.")
lap_times_df = build_lap_table(session, driver_1, driver_2, d1_fastest, d2_fastest)
st.dataframe(lap_times_df, use_container_width=True, hide_index=True)

m1, m2 = st.columns(2)
m1.metric(f"{driver_1} Fastest Lap", str(d1_fastest['LapTime']))
m2.metric(f"{driver_2} Fastest Lap", str(d2_fastest['LapTime']))

# --- Animation ---
st.subheader("Fastest Lap Animation")
output_filename = f"{year}_{race.strip()}_{driver_1}_vs_{driver_2}_lite.gif"
try:
    with st.spinner("Rendering animation (this can take a while)..."):
        path, duration, frames = build_animation(
            circuit_info, driver_1, driver_2, d1_fastest, d2_fastest, output_filename
        )
    st.image(path, caption=f"{driver_1} vs {driver_2} — {duration:.2f}s, {frames} frames")
    with open(path, "rb") as f:
        st.download_button("Download GIF", f, file_name=os.path.basename(path),
                           mime="image/gif", use_container_width=True)
except Exception as e:
    st.error(f"Could not build animation: {e}")
