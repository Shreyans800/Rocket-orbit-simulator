# 🚀 Rocket Orbit Simulator

An interactive rocket launch and orbital insertion simulator built with Python and Streamlit.

## 🚀 Features

- Rocket launch simulation
- Engine thrust calculation
- Specific impulse and mass flow rate
- Fuel consumption and changing rocket mass
- Atmospheric density, pressure and temperature
- Atmospheric drag
- Gravity variation with altitude
- Flight trajectory visualization
- Animated rocket trajectory
- Altitude vs. time
- Velocity vs. time
- Acceleration vs. time
- Mass and fuel tracking
- Thrust vs. aerodynamic drag
- Mach number analysis
- Orbital velocity comparison
- Orbital insertion analysis
- Simulation data table
- CSV export

## 🛰️ Orbital Analysis

The simulator compares the rocket's final velocity with the circular orbital velocity required at the selected target altitude.

It reports whether the vehicle:

- Reached the target altitude and approximately orbital velocity
- Reached the target altitude but has insufficient velocity
- Failed to reach the target altitude

## 🌍 Physics Model

The simulation accounts for:

- Thrust
- Specific impulse
- Propellant mass flow
- Changing vehicle mass
- Atmospheric drag
- Atmospheric density
- Gravity variation with altitude
- Numerical integration
- Orbital velocity

### Thrust

The simulator uses the full rocket thrust equation:

$$
T = \dot{m}V_e + (p_e-p_a)A_e
$$

where:

- $T$ = total thrust
- $\dot{m}$ = propellant mass flow rate
- $V_e$ = exhaust velocity
- $p_e$ = nozzle exit pressure
- $p_a$ = atmospheric pressure
- $A_e$ = nozzle exit area

Exhaust velocity is calculated from specific impulse:

$$
V_e = I_{sp}g_0
$$

### Aerodynamic Drag

$$
D = \frac{1}{2}\rho v^2 C_D A
$$

Drag is calculated opposite to the rocket's velocity vector.

### Gravity

$$
g(h) = g_0\left(\frac{R_E}{R_E+h}\right)^2
$$

### Net Force

The simulator resolves forces into horizontal and vertical components:

$$
F_x = T_x + D_x
$$

$$
F_y = T_y + D_y - mg
$$

### Acceleration

$$
a_x = \frac{F_x}{m}
$$

$$
a_y = \frac{F_y}{m}
$$

The total acceleration is:

$$
a = \sqrt{a_x^2+a_y^2}
$$

### Orbital Velocity

The required circular orbital velocity is calculated using:

$$
v_{orb} = \sqrt{\frac{\mu}{R_E+h}}
$$

## 🚀 Launch Angle

The launch angle is measured from the ground:

- **0°** = horizontal
- **45°** = 45° above horizontal
- **90°** = vertical

## 📊 Visualization

The simulator provides interactive Plotly visualizations for:

- Rocket flight trajectory
- Animated rocket motion
- Altitude
- Velocity
- Acceleration
- Mass and fuel
- Thrust and drag
- Mach number

The trajectory visualization shows the planned flight path as a dotted line while the completed portion of the flight becomes a solid line.

## 💻 Technologies

- Python
- Streamlit
- NumPy
- Pandas
- Plotly

## 📁 Project Structure

```text
Rocket-orbit-simulator/
├── .streamlit/
│   └── config.toml
├── .gitignore
├── P1orbit.py
├── README.md
├── requirements.txt
└── streamlit_app.py
