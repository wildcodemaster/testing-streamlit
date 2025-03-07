import streamlit as st
import time
import random

# Constants
GRID_ROWS, GRID_COLS = 10, 10
STARTING_CASH = 500
DAY_HOURS = 24
MINUTE_DURATION = 0.25  # seconds per in-game hour

# Crop Definitions
CROP_TYPES = {
    "Parsnip": {"growth_time": 4, "sell_price": 20, "yield": 1, "allowed_seasons": ["Spring"]},
    "Strawberry": {"growth_time": 6, "sell_price": 35, "yield": 1, "allowed_seasons": ["Spring"]},
}

# Game State
if 'money' not in st.session_state:
    st.session_state.money = STARTING_CASH
if 'day' not in st.session_state:
    st.session_state.day = 1
if 'season' not in st.session_state:
    st.session_state.season = "Spring"
if 'grid' not in st.session_state:
    st.session_state.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

# Functions
def advance_day():
    st.session_state.day += 1
    st.success(f"Day advanced to {st.session_state.day}")
    time.sleep(1)

def plant_crop(row, col, crop_name):
    if st.session_state.grid[row][col] is None:
        st.session_state.grid[row][col] = {'crop': crop_name, 'growth': 0}
        st.success(f"Planted {crop_name} at ({row}, {col})")
    else:
        st.warning("Tile is already occupied!")

def harvest_crop(row, col):
    if st.session_state.grid[row][col]:
        crop_name = st.session_state.grid[row][col]['crop']
        st.session_state.money += CROP_TYPES[crop_name]['sell_price']
        st.session_state.grid[row][col] = None
        st.success(f"Harvested {crop_name} for ${CROP_TYPES[crop_name]['sell_price']}")
    else:
        st.warning("No crop to harvest!")

# UI
title_col, money_col = st.columns([3, 1])
with title_col:
    st.title("Farming Game")
with money_col:
    st.metric("Money", f"${st.session_state.money}")

st.button("Advance Day", on_click=advance_day)

st.subheader("Farm Grid")
for row in range(GRID_ROWS):
    cols = st.columns(GRID_COLS)
    for col in range(GRID_COLS):
        crop = st.session_state.grid[row][col]
        if crop:
            cols[col].button(f"{crop['crop']}\nHarvest", key=f"harvest_{row}_{col}", on_click=harvest_crop, args=(row, col))
        else:
            cols[col].button("Plant", key=f"plant_{row}_{col}", on_click=plant_crop, args=(row, col, "Parsnip"))
