import math 
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
# Comments
st.set_page_config(
    page_title="Rocket Launch Simulator",
    page_icon="🚀",
    layout="wide"
)

# Constants

G0 = 9.80665
R_EARTH = 6_371_000.0
MU_EARTH = 3.986004418e14
R_AIR = 287.05
GAMMA = 1.4

# Atmosphere

def atmosphere(altitude):
    """
    Simplified standard atmosphere.
    Returns density, pressure, temperature and speed of sound.
    """
    h= max(0.0, altitude)
    if h < 11_000:
        T = 288.15 - 0.0065 * h
        P = 101325 * (T / 288.15) ** 5.25588

    elif h < 20_000:
        T = 216.65
        P = 22632.06 * math.exp(-G0 * (h - 11_000) / (R_AIR * T))

    elif h < 32_000:
        T = 216.65 + 0.001 * (h - 20_000)
        P = 5474.89 * (T / 216.65) ** (-G0 / (0.001 * R_AIR))

    elif h < 47_000:
        T = 228.65 + 0.0028 * (h - 32_000)
        P = 868.02 * (T / 228.65) ** (-G0 / (0.0028 * R_AIR))

    else:
         T = 270.65
         P = 110.0 * math.exp(-(h - 47_000) / 7000)

    rho = P / (R_AIR * T)
    sound = math.sqrt(GAMMA * R_AIR * T)

    return rho, P, T, sound

# Simulation