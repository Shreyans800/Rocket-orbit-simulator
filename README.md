\# 🚀 Rocket Orbit Simulator



An interactive rocket launch and orbital insertion simulator built with Python and Streamlit.



\## 🚀 Features



\- Rocket launch simulation

\- Engine thrust calculation

\- Specific impulse and mass flow rate

\- Fuel consumption and changing rocket mass

\- Atmospheric density, pressure and temperature

\- Atmospheric drag

\- Gravity variation with altitude

\- Flight trajectory visualization

\- Altitude vs. time

\- Velocity vs. time

\- Acceleration vs. time

\- Mass and fuel tracking

\- Thrust vs. aerodynamic drag

\- Mach number analysis

\- Orbital velocity comparison

\- Orbital insertion analysis

\- Simulation data table

\- CSV export



\## 🛰️ Orbital Analysis



The simulator compares the rocket's final velocity with the circular orbital velocity required at the selected target altitude.



It reports whether the vehicle:



\- Reached the target altitude and approximately orbital velocity

\- Reached the target altitude but has insufficient velocity

\- Failed to reach the target altitude



\## 🌍 Physics Model



The simulation accounts for:



\- Thrust

\- Specific impulse

\- Propellant mass flow

\- Changing vehicle mass

\- Atmospheric drag

\- Atmospheric density

\- Gravity variation with altitude

\- Numerical integration

\- Orbital velocity



\### Thrust



`T = mdot × Isp × g0`



\### Aerodynamic Drag



`D = 0.5 × rho × v² × Cd × A`



\### Gravity



`g(h) = g0 × (RE / (RE + h))²`



\### Net Force



`Fnet = T - D - m × g`



\### Acceleration



`a = Fnet / m`



\## 💻 Technologies



\- Python

\- Streamlit

\- NumPy

\- Pandas

\- Plotly



\## 📁 Project Structure



```text

Rocket-orbit-simulator/

├── .streamlit/

│   └── config.toml

├── .gitignore

├── P1orbit.py

├── README.md

├── requirements.txt

└── streamlit\_app.py

