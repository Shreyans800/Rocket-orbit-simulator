# 🚀 Rocket Orbit Simulator

An interactive rocket launch and orbital insertion simulator built with Python and Streamlit.

TRY IT!

https://rocketorbitsimulator.streamlit.app/

##  Features

- Rocket launch simulation
  Parameters:
- Engine thrust calculation
- Specific impulse and mass flow rate
- Fuel consumption and changing rocket mass
- Atmospheric density, pressure and temperature
- Atmospheric drag
  Also Included:
- Graphs (mathematical aspect!)
- A guide as to how the simulation works

  
The simulation accounts for:   (Yes, you can edit these!)

- Thrust
- Specific impulse
- Propellant mass flow
- Changing vehicle mass
- Atmospheric drag
- Atmospheric density
- Gravity variation with altitude
- Orbital velocity

## What does it do?

The simulator gives a 2D demo of what the trajectory of the rocket would look like.
Please note that it is NOT accurate, and whilst I tried to include some variables, providing with an actual path is not possible

The trajectory visualization shows the planned flight path as a dotted line, while the completed portion of the flight is represented by a solid line.

## Python Libraries I used 

- Python
- Streamlit
- NumPy
- Pandas
- Plotly

This was quite a journey. Firstly, I studied the major variables(except drag) and found that it was similar to projectile motion, which eventually became the basis for the simulation. The only difficulty was using Plotly and Base64 and IO for the simulation, and also integrating it with Streamlit frame-by-frame motions. (Yes, a continuous  pre-built video-like projection would not work, so I had to make it move >16 FPS). The drag insertion in the calculations was solved by YouTube videos (Thanks, Google!) and pretty much that's it. Do enjoy adjusting different variables to see the results change!

  
##  Project Structure

```text
Rocket-orbit-simulator/
├── .streamlit/
│   └── config.toml
├── .gitignore
├── P1orbit.py
├── README.md
├── requirements.txt
└── streamlit_app.py
