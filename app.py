import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ======================================================
# Page config
# ======================================================
st.set_page_config(page_title="Current Rose Tool", layout="wide")
st.title("🌊 Current Rose with Directional Extreme Bars & Annual Maxima")

# ======================================================
# Sidebar – Time Settings
# ======================================================
st.sidebar.header("⏱ Time Settings")

start_time_str = st.sidebar.text_input(
    "Start Time (dd-mm-yyyy hh:mm)",
    value="01-01-2025 00:00"
)

col1, col2, col3, col4 = st.sidebar.columns(4)
use_day = col1.checkbox("Day")
use_hour = col2.checkbox("Hour", value=True)
use_min = col3.checkbox("Minute")
use_sec = col4.checkbox("Second")

interval = timedelta(
    days=1 if use_day else 0,
    hours=1 if use_hour else 0,
    minutes=1 if use_min else 0,
    seconds=1 if use_sec else 0
)

# ======================================================
# Inputs
# ======================================================
st.subheader("📥 Paste Current Speed Data")
raw_current = st.text_area(
    "Format: speed[TAB]direction(deg)",
    height=200,
    placeholder="2.44\t301.35\n2.61\t303.69\n2.59\t291.55"
)

st.subheader("📥 Paste Extreme Data (Directional Design Current)")
raw_extreme = st.text_area(
    "Format: DIR[TAB]speed",
    height=150,
    placeholder="N\t3.93\nNE\t4.81\nE\t6.43\nSE\t5.00\nS\t5.59\nSW\t6.07\nW\t7.52\nNW\t6.50"
)

# ======================================================
# Helpers
# ======================================================
dir_map = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SW": 225,
    "W": 270,
    "NW": 315,
}

def parse_current_data(raw_text):
    rows = []
    for line in raw_text.strip().splitlines():
        parts = line.replace(",", ".").split()
        if len(parts) != 2:
            continue
        speed = float(parts[0])
        deg = float(parts[1]) % 360
        rows.append((speed, deg))
    return pd.DataFrame(rows, columns=["speed", "deg"])

def parse_extreme_data(raw_text):
    rows = []
    for line in raw_text.strip().splitlines():
        parts = line.replace(",", ".").split()
        if len(parts) != 2:
            continue
        direction = parts[0].upper()
        speed = float(parts[1])
        if direction in dir_map:
            rows.append((dir_map[direction], speed, direction))
    return pd.DataFrame(rows, columns=["deg", "speed", "dir"])

def bin_direction(deg, bins=8):
    # Map degrees to nearest compass sector (N, NE, E, ...)
    sector_size = 360 / bins
    idx = int(np.round(deg / sector_size)) % bins
    compass = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return compass[idx]

# ======================================================
# Plot
# ======================================================
if st.button("🚀 Generate Current Rose"):
    try:
        df_current = parse_current_data(raw_current)
        df_extreme = parse_extreme_data(raw_extreme)

        # Time axis
        start_time = datetime.strptime(start_time_str, "%d-%m-%Y %H:%M")
        df_current["time"] = [start_time + i * interval for i in range(len(df_current))]

        # Assign compass sector for annual maxima
        df_current["year"] = df_current["time"].dt.year
        df_current["sector"] = df_current["deg"].apply(bin_direction)

        # Annual maxima per sector
        df_annual_max = (
            df_current.groupby(["year", "sector"])["speed"]
            .max()
            .reset_index()
        )

        # Convert to radians
        theta = np.deg2rad(df_current["deg"].values)
        r = df_current["speed"].values

        theta_bar = np.deg2rad(df_extreme["deg"].values)
        r_bar = df_extreme["speed"].values

        # Annual maxima to radians
        theta_max = np.deg2rad(
            df_annual_max["sector"].map(dir_map).values
        )
        r_max = df_annual_max["speed"].values

        bar_width = np.deg2rad(22.5)

        # Plot
        fig = plt.figure(figsize=(9, 9))
        ax = plt.subplot(111, polar=True)

        # Current scatter
        ax.scatter(theta, r, s=12, alpha=0.5, label="Current Data")

        # Extreme bars (outline only)
        ax.bar(
            theta_bar,
            r_bar,
            width=bar_width,
            bottom=0.0,
            fill=False,              # no fill color
            edgecolor="red",         # red outline
            linewidth=2,
            label="Extreme (Design Current)"
        )

        # Annual maxima dots
        ax.scatter(
            theta_max,
            r_max,
            s=40,
            color="orange",
            edgecolors="black",
            zorder=5,
            label="Annual Maxima"
        )

        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=3)

        st.pyplot(fig)

        # Tables
        st.subheader("📊 Parsed Current Data")
        st.dataframe(df_current)

        st.subheader("📊 Annual Maximum per Direction per Year")
        st.dataframe(df_annual_max)

        st.subheader("📊 Extreme Data")
        st.dataframe(df_extreme)

    except Exception as e:
        st.error(f"❌ Error: {e}")
