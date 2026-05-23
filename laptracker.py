import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import gc
import warnings
import os

warnings.filterwarnings('ignore')

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

YEAR_INPUT = input("Enter year (e.g. 2024): ").strip()
if not YEAR_INPUT:
    YEAR_INPUT = '2024'
YEAR = int(YEAR_INPUT)


RACE = input("Enter race name (e.g. Monaco): ").strip()
if not RACE:
    RACE = 'Monaco'

SESSION = input("Enter session code (e.g. Q, FP1, R): ").strip()
if not SESSION:
    SESSION = 'Q'

print(f"\nLoading {YEAR} {RACE} GP - {SESSION} session...")
session = fastf1.get_session(YEAR, RACE, SESSION)
session.load()

circuit_info = session.event

print(f"\n{'='*60}")
print(f"Circuit Information")
print(f"{'='*60}")
print(f"Event: {circuit_info['EventName']}")
print(f"Location: {circuit_info['Location']}")
print(f"Country: {circuit_info['Country']}")
print(f"Circuit: {circuit_info['OfficialEventName']}")
print(f"Date: {circuit_info['EventDate']}")
print(f"{'='*60}\n")

Driver_1 = input("Enter first driver code (e.g. VER): ").strip().upper()
if not Driver_1:
    Driver_1 = 'VER'

Driver_2 = input("Enter second driver code (e.g. LEC): ").strip().upper()
if not Driver_2:
    Driver_2 = 'LEC'

driver1_fastest = session.laps.pick_driver(Driver_1).pick_fastest()
driver2_fastest = session.laps.pick_driver(Driver_2).pick_fastest()

driver1_name = driver1_fastest['Driver']
driver2_name = driver2_fastest['Driver']

driver1_laps = session.laps.pick_driver(Driver_1)
driver2_laps = session.laps.pick_driver(Driver_2)

lap_data = []

for i, lap in enumerate(driver1_laps.iterlaps(), 1):
    lap_data.append({
        'Lap': i,
        f'{Driver_1} Time': lap[1]['LapTime'],
        f'{Driver_1} Fastest': '★' if lap[1]['LapTime'] == driver1_fastest['LapTime'] else ''
    })
for i, lap in enumerate(driver2_laps.iterlaps(), 1):
    if i <= len(lap_data):
        lap_data[i-1][f'{Driver_2} Time']= lap[1]['LapTime']
        lap_data[i-1][f'{Driver_2} Fastest']= '★' if lap[1]['LapTime'] == driver2_fastest['LapTime'] else ''
    else:
        lap_data.append({
            'Lap': i,
            f'{Driver_1} Time': None,
            f'{Driver_1} Fastest' : '',
            f'{Driver_2} Time': lap[1]['LapTime'],
            f'{Driver_2} Fastest': '★' if lap[1]['LapTime'] == driver2_fastest['LapTime'] else ''
        })
lap_times_df = pd.DataFrame(lap_data)
print("\n" + "="*80)
print(f"Lap Times Comparison - {Driver_1} vs {Driver_2}")
print("="*80)
print(f"★ indicates the fastest lap used in the animation")
print("-"*80)
print(lap_times_df.to_string(index=False))
print("="*80)
print(f"\n{Driver_1} Fastest Lap: {driver1_fastest['LapTime']}")
print(f"{Driver_2} Fastest Lap: {driver2_fastest['LapTime']}")
# ============================================================================
# STEP 4: Create Lap Times Table
# ============================================================================

# Get all laps for both drivers
driver1_laps = session.laps.pick_driver(Driver_1)
driver2_laps = session.laps.pick_driver(Driver_2)

# Create comparison table
lap_data = []

for i, lap in enumerate(driver1_laps.iterlaps(), 1):
    lap_data.append({
        'Lap': i,
        f'{Driver_1} Time': lap[1]['LapTime'],
        f'{Driver_1} Fastest': '★' if lap[1]['LapTime'] == driver1_fastest['LapTime'] else ''
    })

for i, lap in enumerate(driver2_laps.iterlaps(), 1):
    if i <= len(lap_data):
        lap_data[i-1][f'{Driver_2} Time'] = lap[1]['LapTime']
        lap_data[i-1][f'{Driver_2} Fastest'] = '★' if lap[1]['LapTime'] == driver2_fastest['LapTime'] else ''
    else:
        lap_data.append({
            'Lap': i,
            f'{Driver_1} Time': None,
            f'{Driver_1} Fastest': '',
            f'{Driver_2} Time': lap[1]['LapTime'],
            f'{Driver_2} Fastest': '★' if lap[1]['LapTime'] == driver2_fastest['LapTime'] else ''
        })

lap_times_df = pd.DataFrame(lap_data)

print("\n" + "="*80)
print(f"LAP TIMES COMPARISON - {Driver_1} vs {Driver_2}")
print("="*80)
print(f"★ indicates the fastest lap used in the animation")
print("-"*80)
print(lap_times_df.to_string(index=False))
print("="*80)

print(f"\n{Driver_1} Fastest Lap: {driver1_fastest['LapTime']}")
print(f"{Driver_2} Fastest Lap: {driver2_fastest['LapTime']}")


# ============================================================================
# STEP 5: Get Telemetry Data for Animation
# ============================================================================

# Get telemetry for fastest laps
driver1_tel = driver1_fastest.get_telemetry()
driver2_tel = driver2_fastest.get_telemetry()

# OPTIMIZATION: Sample every 3rd point to reduce memory
SAMPLE_RATE = 3
driver1_tel = driver1_tel.iloc[::SAMPLE_RATE].reset_index(drop=True)
driver2_tel = driver2_tel.iloc[::SAMPLE_RATE].reset_index(drop=True)

# Extract position data
driver1_x = driver1_tel['X'].values
driver1_y = driver1_tel['Y'].values
driver2_x = driver2_tel['X'].values
driver2_y = driver2_tel['Y'].values

# Calculate time arrays
driver1_time = driver1_tel['Time'].dt.total_seconds().values
driver2_time = driver2_tel['Time'].dt.total_seconds().values

# Normalize time to start from 0
driver1_time = driver1_time - driver1_time[0]
driver2_time = driver2_time - driver2_time[0]

print("\n✓ Telemetry data extracted successfully!")
print(f"  - {Driver_1}: {len(driver1_x)} data points (sampled)")
print(f"  - {Driver_2}: {len(driver2_x)} data points (sampled)")

# Clear unnecessary data
gc.collect()

print("\n" + "="*60)
print("CREATING ANIMATION (OPTIMIZED FOR LOW MEMORY)...")
print("="*60)

# OPTIMIZATION: Reduced figure size
fig, ax = plt.subplots(figsize=(10, 8), dpi=60)
fig.patch.set_facecolor('#1a1a1a')
ax.set_facecolor('#2a2a2a')

# OPTIMIZATION: Sample track background points (every 5th point)
track_sample = 5
ax.plot(driver1_x[::track_sample], driver1_y[::track_sample],
        color='white', alpha=0.3, linewidth=1.5,
        linestyle='--', label='Track Layout')

# Initialize moving elements
driver1_point, = ax.plot([], [], 'o', color='#0600ef', markersize=12,
                         label=f'{Driver_1}', markeredgecolor='white',
                         markeredgewidth=1.5)
driver2_point, = ax.plot([], [], 'o', color='#dc0000', markersize=12,
                         label=f'{Driver_2}', markeredgecolor='white',
                         markeredgewidth=1.5)

# OPTIMIZATION: Shorter trails
driver1_trail, = ax.plot([], [], color='#0600ef', alpha=0.5, linewidth=1.5)
driver2_trail, = ax.plot([], [], color='#dc0000', alpha=0.5, linewidth=1.5)

# Time display
time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                   fontsize=11, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                   color='white', fontfamily='monospace')

# Title with circuit info
title_text = (f"{circuit_info['EventName']} - {circuit_info['Location']}\n"
              f"{Driver_1} vs {Driver_2} - Fastest Lap Comparison")
ax.set_title(title_text, fontsize=14, color='white', pad=15, fontweight='bold')

# Styling
ax.set_xlabel('X Position (m)', fontsize=10, color='white')
ax.set_ylabel('Y Position (m)', fontsize=10, color='white')
ax.tick_params(colors='white', labelsize=9)
ax.legend(loc='upper right', fontsize=9, facecolor='black',
         edgecolor='white', labelcolor='white')
ax.grid(True, alpha=0.2, color='white')
ax.set_aspect('equal')

# OPTIMIZATION: Lower FPS and frame count
FPS = 15  # Reduced from 30
max_time = max(driver1_time[-1], driver2_time[-1])
total_frames = int(max_time * FPS)

print(f"Animation settings:")
print(f"  - FPS: {FPS} (lower = less memory)")
print(f"  - Total frames: {total_frames}")
print(f"  - Duration: {max_time:.2f} seconds")

def get_position(time_val, time_array, x_array, y_array):
    """Interpolate position at given time"""
    if time_val > time_array[-1]:
        return x_array[-1], y_array[-1]
    idx = np.searchsorted(time_array, time_val)
    if idx == 0:
        return x_array[0], y_array[0]
    if idx >= len(time_array):
        return x_array[-1], y_array[-1]

    # Linear interpolation
    t1, t2 = time_array[idx-1], time_array[idx]
    alpha = (time_val - t1) / (t2 - t1) if t2 != t1 else 0
    x = x_array[idx-1] + alpha * (x_array[idx] - x_array[idx-1])
    y = y_array[idx-1] + alpha * (y_array[idx] - y_array[idx-1])
    return x, y

def animate(frame):
    """Animation function (optimized)"""
    current_time = frame / FPS

    # Get positions
    x1, y1 = get_position(current_time, driver1_time, driver1_x, driver1_y)
    x2, y2 = get_position(current_time, driver2_time, driver2_x, driver2_y)

    # Update points
    driver1_point.set_data([x1], [y1])
    driver2_point.set_data([x2], [y2])

    # OPTIMIZATION: Shorter trail (30 points instead of 100)
    trail_length = 30
    start_frame = max(0, frame - trail_length)

    trail1_x, trail1_y = [], []
    trail2_x, trail2_y = [], []

    # OPTIMIZATION: Sample trail points (every 2nd)
    for f in range(start_frame, frame + 1, 2):
        t = f / FPS
        tx1, ty1 = get_position(t, driver1_time, driver1_x, driver1_y)
        tx2, ty2 = get_position(t, driver2_time, driver2_x, driver2_y)
        trail1_x.append(tx1)
        trail1_y.append(ty1)
        trail2_x.append(tx2)
        trail2_y.append(ty2)

    driver1_trail.set_data(trail1_x, trail1_y)
    driver2_trail.set_data(trail2_x, trail2_y)

    # Update time display
    time_text.set_text(f'Time: {current_time:.2f}s\n'
                      f'{Driver_1}: {driver1_fastest["LapTime"]}\n'
                      f'{Driver_2}: {driver2_fastest["LapTime"]}')

    # Progress indicator (every 50 frames)
    if frame % 50 == 0:
        progress = (frame / total_frames) * 100
        print(f"  Rendering: {progress:.1f}% complete", end='\r')

    return driver1_point, driver2_point, driver1_trail, driver2_trail, time_text

# Create animation
print("\nBuilding animation frames (this is faster with optimizations)...")
anim = FuncAnimation(fig, animate, frames=total_frames,
                    interval=1000/FPS, blit=True, repeat=True)
output_filename = f'{YEAR}_{RACE}_{Driver_1}_vs_{Driver_2}_lite.gif'
print(f"\n\nSaving animation to: {output_filename}")
print("⚡ Using optimized settings to save memory...")

# OPTIMIZATION: Lower DPI for smaller file
writer = PillowWriter(fps=FPS, bitrate=1800)
anim.save(output_filename, writer=writer, dpi=60)

print(f"\n{'='*60}")
print(f"✓ Animation saved successfully!")
print(f"{'='*60}")
print(f"File: {output_filename}")
print(f"Duration: {max_time:.2f} seconds")
print(f"Frames: {total_frames}")
print(f"FPS: {FPS}")
print(f"Quality: Optimized for Google Colab")
print(f"{'='*60}\n")

# Clear memory
plt.close('all')
gc.collect()

# Display the animation in the notebook
from IPython.display import Image, display
print("Displaying animation...")
display(Image(filename=output_filename))

print("\nANIMATION COMPLETE!")