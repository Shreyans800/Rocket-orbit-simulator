import math
import base64
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(
    page_title="Rocket Launch Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

G0 = 9.80665
R_EARTH = 6_371_000.0
MU_EARTH = 3.986004418e14
R_AIR = 287.05
GAMMA = 1.4


def atmosphere(altitude):
    h = max(0.0, altitude)

    if h < 11_000:
        T = 288.15 - 0.0065 * h
        P = 101325 * (T / 288.15) ** 5.25588

    elif h < 20_000:
        T = 216.65
        P = 22632.06 * math.exp(
            -G0 * (h - 11_000) / (R_AIR * T)
        )

    elif h < 32_000:
        T = 216.65 + 0.001 * (h - 20_000)
        P = 5474.89 * (
            T / 216.65
        ) ** (-G0 / (0.001 * R_AIR))

    elif h < 47_000:
        T = 228.65 + 0.0028 * (h - 32_000)
        P = 868.02 * (
            T / 228.65
        ) ** (-G0 / (0.0028 * R_AIR))

    else:
        T = 270.65
        P = 110.0 * math.exp(
            -(h - 47_000) / 7000
        )

    rho = P / (R_AIR * T)

    sound = math.sqrt(
        GAMMA * R_AIR * T
    )

    return rho, P, T, sound


@st.cache_data(show_spinner=False)
def create_rocket_images():
    images = {}

    size = 160

    base = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(base)

    draw.polygon(
        [
            (80, 12),
            (48, 58),
            (48, 108),
            (112, 108),
            (112, 58)
        ],
        fill=(235, 238, 242, 255)
    )

    draw.ellipse(
        (60, 42, 100, 82),
        fill=(35, 95, 150, 255),
        outline=(210, 225, 240, 255),
        width=3
    )

    draw.polygon(
        [
            (48, 82),
            (20, 120),
            (48, 108)
        ],
        fill=(200, 45, 45, 255)
    )

    draw.polygon(
        [
            (112, 82),
            (140, 120),
            (112, 108)
        ],
        fill=(200, 45, 45, 255)
    )

    draw.rectangle(
        (52, 100, 108, 116),
        fill=(210, 214, 220, 255)
    )

    draw.polygon(
        [
            (60, 114),
            (80, 154),
            (100, 114)
        ],
        fill=(255, 145, 35, 255)
    )

    draw.polygon(
        [
            (69, 114),
            (80, 145),
            (91, 114)
        ],
        fill=(255, 220, 80, 255)
    )

    for angle in range(0, 360, 5):
        rotation = angle - 90

        rotated = base.rotate(
            rotation,
            resample=Image.Resampling.BICUBIC,
            expand=True
        )

        buffer = BytesIO()

        rotated.save(
            buffer,
            format="PNG"
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode()

        images[angle] = (
            "data:image/png;base64,"
            + encoded
        )

    return images


def simulate(
    dry_mass,
    fuel_mass,
    isp,
    burn_time,
    cd,
    area,
    launch_angle,
    simulation_time,
    dt,
    target_altitude,
    exit_pressure,
    nozzle_exit_area
):
    mass = dry_mass + fuel_mass
    fuel = fuel_mass

    altitude = 0.0

    velocity_x = 0.0
    velocity_y = 0.0

    x = 0.0
    y = 0.0

    rows = []

    exhaust_velocity = isp * G0

    mdot = fuel_mass / burn_time

    angle_rad = math.radians(
        launch_angle
    )

    thrust_direction_x = math.cos(
        angle_rad
    )

    thrust_direction_y = math.sin(
        angle_rad
    )

    total_impulse = 0.0

    for step in range(
        int(simulation_time / dt) + 1
    ):
        t = step * dt

        rho, pressure, temperature, sound_speed = atmosphere(
            altitude
        )

        if fuel > 0 and t < burn_time:

            current_thrust = (
                mdot * exhaust_velocity
                + (
                    exit_pressure
                    - pressure
                ) * nozzle_exit_area
            )

            current_thrust = max(
                0.0,
                current_thrust
            )

            consumed = min(
                mdot * dt,
                fuel
            )

            fuel -= consumed

            mass = dry_mass + fuel

        else:
            current_thrust = 0.0
            mass = dry_mass

        gravity = G0 * (
            R_EARTH /
            (R_EARTH + altitude)
        ) ** 2

        velocity = math.sqrt(
            velocity_x ** 2 +
            velocity_y ** 2
        )

        dynamic_pressure = (
            0.5 *
            rho *
            velocity ** 2
        )

        drag = (
            dynamic_pressure *
            cd *
            area
        )

        if velocity > 0:

            drag_x = (
                -drag *
                velocity_x /
                velocity
            )

            drag_y = (
                -drag *
                velocity_y /
                velocity
            )

        else:

            drag_x = 0.0
            drag_y = 0.0

        thrust_x = (
            current_thrust *
            thrust_direction_x
        )

        thrust_y = (
            current_thrust *
            thrust_direction_y
        )

        net_force_x = (
            thrust_x +
            drag_x
        )

        net_force_y = (
            thrust_y +
            drag_y -
            mass * gravity
        )

        acceleration_x = (
            net_force_x /
            mass
        )

        acceleration_y = (
            net_force_y /
            mass
        )

        acceleration = math.sqrt(
            acceleration_x ** 2 +
            acceleration_y ** 2
        )

        velocity_x += (
            acceleration_x *
            dt
        )

        velocity_y += (
            acceleration_y *
            dt
        )

        x += velocity_x * dt

        altitude += velocity_y * dt

        if altitude < 0:

            altitude = 0.0
            velocity_y = 0.0

        y = altitude

        velocity = math.sqrt(
            velocity_x ** 2 +
            velocity_y ** 2
        )

        mach = (
            velocity /
            sound_speed
            if sound_speed > 0
            else 0.0
        )

        orbital_velocity = math.sqrt(
            MU_EARTH /
            (R_EARTH + altitude)
        )

        total_impulse += (
            current_thrust * dt
        )

        rows.append({
            "time": t,
            "altitude": altitude,
            "velocity": velocity,
            "velocity_x": velocity_x,
            "velocity_y": velocity_y,
            "acceleration": acceleration,
            "acceleration_x": acceleration_x,
            "acceleration_y": acceleration_y,
            "mass": mass,
            "fuel": max(fuel, 0),
            "thrust": current_thrust,
            "thrust_x": thrust_x,
            "thrust_y": thrust_y,
            "drag": drag,
            "drag_x": drag_x,
            "drag_y": drag_y,
            "gravity": gravity,
            "density": rho,
            "pressure": pressure,
            "temperature": temperature,
            "mach": mach,
            "dynamic_pressure": dynamic_pressure,
            "orbital_velocity": orbital_velocity,
            "x": x,
            "y": y
        })

        if (
            altitude <= 0
            and t > 5
            and velocity_y < 0
        ):
            break

        if altitude >= target_altitude:
            break

    df = pd.DataFrame(rows)

    max_altitude = (
        df["altitude"].max()
    )

    max_velocity = (
        df["velocity"].max()
    )

    max_acceleration = (
        df["acceleration"].max()
    )

    max_dynamic_pressure = (
        df["dynamic_pressure"].max()
    )

    final_velocity = (
        df["velocity"].iloc[-1]
    )

    final_altitude = (
        df["altitude"].iloc[-1]
    )

    required_orbital_velocity = math.sqrt(
        MU_EARTH /
        (R_EARTH + target_altitude)
    )

    orbital_ratio = (
        final_velocity /
        required_orbital_velocity
        if required_orbital_velocity > 0
        else 0
    )

    return (
        df,
        max_altitude,
        max_velocity,
        max_acceleration,
        max_dynamic_pressure,
        final_velocity,
        final_altitude,
        required_orbital_velocity,
        orbital_ratio,
        mdot,
        burn_time,
        total_impulse
    )


st.title(
    "🚀 Rocket Launch Simulator"
)

st.markdown(
    """
    Simulate a rocket launch while accounting for **thrust,
    fuel consumption, gravity, atmospheric drag and changing mass**.
    """
)

st.sidebar.header(
    "🚀 Rocket Parameters"
)

dry_mass = st.sidebar.number_input(
    "Dry Mass (kg)",
    min_value=1000.0,
    max_value=1_000_000.0,
    value=20_000.0,
    step=5000.0
)

fuel_mass = st.sidebar.number_input(
    "Fuel Mass (kg)",
    min_value=1000.0,
    max_value=1_000_000.0,
    value=50_000.0,
    step=5000.0
)

isp = st.sidebar.number_input(
    "Specific Impulse (s)",
    min_value=100.0,
    max_value=800.0,
    value=300.0,
    step=20.0
)

burn_time = st.sidebar.number_input(
    "Burn Time (s)",
    min_value=50.0,
    max_value=1000.0,
    value=150.0,
    step=20.0
)

st.sidebar.header(
    "🔥 Engine / Nozzle"
)

exit_pressure = st.sidebar.number_input(
    "Nozzle Exit Pressure (Pa)",
    min_value=0.0,
    max_value=1_000_000.0,
    value=50_000.0,
    step=5_000.0
)

nozzle_exit_area = st.sidebar.number_input(
    "Nozzle Exit Area (m²)",
    min_value=0.001,
    max_value=100.0,
    value=1.0,
    step=0.1
)

st.sidebar.header(
    "🌍 Aerodynamics"
)

cd = st.sidebar.number_input(
    "Drag Coefficient",
    min_value=0.05,
    max_value=2.0,
    value=0.35,
    step=0.05
)

area = st.sidebar.number_input(
    "Reference Area (m²)",
    min_value=0.1,
    max_value=1000.0,
    value=10.0,
    step=1.0
)

st.sidebar.header(
    "🧭 Launch"
)

launch_angle = st.sidebar.slider(
    "Launch Angle (From Ground in degrees)",
    min_value=0.0,
    max_value=90.0,
    value=90.0,
    step=1.0
)

st.sidebar.caption(
    "0° = horizontal | 90° = vertical"
)

target_altitude = st.sidebar.number_input(
    "Target Altitude (km)",
    min_value=10.0,
    max_value=4000.0,
    value=200.0,
    step=50.0
) * 1000

simulation_time = st.sidebar.number_input(
    "Maximum Simulation Time (s)",
    min_value=30.0,
    max_value=5000.0,
    value=600.0,
    step=30.0
)

dt = st.sidebar.select_slider(
    "Simulation Time Step (s)",
    options=[
        0.1,
        0.25,
        0.5,
        1.0,
        2.0
    ],
    value=2.0
)

if st.button(
    "🚀 Launch Simulation",
    type="primary"
):

    with st.spinner(
        "Simulating launch..."
    ):

        results = simulate(
            dry_mass=dry_mass,
            fuel_mass=fuel_mass,
            isp=isp,
            burn_time=burn_time,
            cd=cd,
            area=area,
            launch_angle=launch_angle,
            simulation_time=simulation_time,
            dt=dt,
            target_altitude=target_altitude,
            exit_pressure=exit_pressure,
            nozzle_exit_area=nozzle_exit_area
        )

    (
        df,
        max_altitude,
        max_velocity,
        max_acceleration,
        max_dynamic_pressure,
        final_velocity,
        final_altitude,
        required_orbital_velocity,
        orbital_ratio,
        mdot,
        stage_burn_time,
        total_impulse
    ) = results

    rocket_images = create_rocket_images()

    st.success(
        "Simulation complete!"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Maximum Altitude",
        f"{max_altitude / 1000:.2f} km"
    )

    col2.metric(
        "Maximum Velocity",
        f"{max_velocity / 1000:.2f} km/s"
    )

    col3.metric(
        "Maximum Acceleration",
        f"{max_acceleration / G0:.2f} g"
    )

    col4.metric(
        "Peak Dynamic Pressure",
        f"{max_dynamic_pressure / 1000:.1f} kPa"
    )

    st.subheader(
        "🛰️ Orbital Insertion Analysis"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Final Altitude",
        f"{final_altitude / 1000:.2f} km"
    )

    c2.metric(
        "Final Velocity",
        f"{final_velocity / 1000:.2f} km/s"
    )

    c3.metric(
        "Required Circular Velocity",
        f"{required_orbital_velocity / 1000:.2f} km/s"
    )

    if (
        final_altitude >= target_altitude * 0.95
        and orbital_ratio >= 0.95
    ):

        st.success(
            "🛰️ The simulated vehicle reached "
            "approximately orbital velocity at "
            "the target altitude."
        )

    elif (
        final_altitude >= target_altitude * 0.95
    ):

        st.warning(
            "⚠️ Target altitude reached, but "
            "velocity is insufficient for a "
            "circular orbit."
        )

    else:

        st.error(
            "❌ The rocket did not reach "
            "the target altitude."
        )

    st.subheader(
        "🚀 Animated Rocket Flight"
    )

    x_km = (
        df["x"].to_numpy()
        / 1000.0
    )

    y_km = (
        df["altitude"].to_numpy()
        / 1000.0
    )

    time_data = (
        df["time"].to_numpy()
    )

    max_x = max(
        1.0,
        float(
            np.max(
                np.abs(x_km)
            )
        )
    )

    max_y = max(
        1.0,
        float(
            np.max(y_km)
        )
    )

    if launch_angle == 90:

        x_min = -max_x * 0.45
        x_max = max_x * 0.45

    else:

        x_min = min(
            -max_x * 0.08,
            -1.0
        )

        x_max = max(
            max_x * 1.15,
            10.0
        )

    y_min = 0.0

    y_max = max(
        max_y * 1.15,
        10.0
    )

    num_frames = min(
        len(df),
        180
    )

    frame_indices = np.linspace(
        0,
        len(df) - 1,
        num_frames,
        dtype=int
    )

    rocket_sizex = max(
        (x_max - x_min) * 0.08,
        0.5
    )

    rocket_sizey = max(
        (y_max - y_min) * 0.08,
        0.5
    )

    def rocket_angle_for_index(index):
        vx = float(
            df["velocity_x"].iloc[index]
        )

        vy = float(
            df["velocity_y"].iloc[index]
        )

        speed = math.sqrt(
            vx * vx +
            vy * vy
        )

        if speed < 1e-9:

            vx = math.cos(
                angle_rad
            )

            vy = math.sin(
                angle_rad
            )

        heading = math.degrees(
            math.atan2(
                vy,
                vx
            )
        )

        if heading < 0:
            heading += 360

        heading = (
            round(heading / 5) * 5
        ) % 360

        return heading

    angle_rad = math.radians(
        launch_angle
    )

    initial_heading = (
        launch_angle
        if launch_angle <= 90
        else 90
    )

    initial_heading = (
        round(
            initial_heading / 5
        ) * 5
    ) % 360

    initial_image = rocket_images[
        initial_heading
    ]

    initial_image_object = dict(
        source=initial_image,
        x=x_km[0],
        y=y_km[0],
        xref="x",
        yref="y",
        sizex=rocket_sizex,
        sizey=rocket_sizey,
        xanchor="center",
        yanchor="middle",
        sizing="contain",
        layer="above",
        opacity=1
    )

    frames = []

    for frame_number, i in enumerate(
        frame_indices
    ):

        current_path_x = (
            x_km[:i + 1]
        )

        current_path_y = (
            y_km[:i + 1]
        )

        heading = (
            rocket_angle_for_index(i)
        )

        rocket_image = (
            rocket_images[heading]
        )

        frame_image = dict(
            source=rocket_image,
            x=x_km[i],
            y=y_km[i],
            xref="x",
            yref="y",
            sizex=rocket_sizex,
            sizey=rocket_sizey,
            xanchor="center",
            yanchor="middle",
            sizing="contain",
            layer="above",
            opacity=1
        )

        frames.append(
            go.Frame(
                name=str(
                    frame_number
                ),
                data=[
                    go.Scatter(
                        x=current_path_x,
                        y=current_path_y,
                        mode="lines",
                        line=dict(
                            width=4
                        ),
                        name="Rocket Path"
                    )
                ],
                traces=[1],
                layout=go.Layout(
                    images=[frame_image]
                )
            )
        )

    trajectory = go.Figure(
        data=[
            go.Scatter(
                x=x_km,
                y=y_km,
                mode="lines",
                line=dict(
                    width=2,
                    dash="dot"
                ),
                opacity=0.45,
                name="Planned Trajectory"
            ),
            go.Scatter(
                x=[x_km[0]],
                y=[y_km[0]],
                mode="lines",
                line=dict(
                    width=4
                ),
                name="Rocket Path"
            )
        ],
        frames=frames
    )

    trajectory.update_layout(
        height=680,
        paper_bgcolor="rgb(2, 7, 18)",
        plot_bgcolor="rgb(5, 15, 32)",
        font=dict(
            color="white"
        ),
        xaxis=dict(
            title="Horizontal Distance (km)",
            range=[
                x_min,
                x_max
            ],
            zeroline=True,
            zerolinecolor=(
                "rgba(255,255,255,0.30)"
            ),
            gridcolor=(
                "rgba(255,255,255,0.10)"
            ),
            showline=True,
            linecolor=(
                "rgba(255,255,255,0.35)"
            )
        ),
        yaxis=dict(
            title="Altitude (km)",
            range=[
                y_min,
                y_max
            ],
            zeroline=True,
            zerolinecolor=(
                "rgba(255,255,255,0.30)"
            ),
            gridcolor=(
                "rgba(255,255,255,0.10)"
            ),
            showline=True,
            linecolor=(
                "rgba(255,255,255,0.35)"
            )
        ),
        images=[
            initial_image_object
        ],
        hovermode="closest",
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0,
                y=1.08,
                showactive=False,
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(
                                    duration=70,
                                    redraw=True
                                ),
                                transition=dict(
                                    duration=0
                                ),
                                fromcurrent=False,
                                mode="immediate"
                            )
                        ]
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(
                                    duration=0,
                                    redraw=False
                                ),
                                transition=dict(
                                    duration=0
                                ),
                                mode="immediate"
                            )
                        ]
                    )
                ]
            )
        ],
        sliders=[
            dict(
                active=0,
                x=0,
                y=-0.10,
                len=1,
                currentvalue=dict(
                    prefix="Simulation Time: "
                ),
                steps=[
                    dict(
                        label=(
                            f"{time_data[i]:.1f}s"
                        ),
                        method="animate",
                        args=[
                            [str(frame_number)],
                            dict(
                                frame=dict(
                                    duration=0,
                                    redraw=True
                                ),
                                transition=dict(
                                    duration=0
                                ),
                                mode="immediate"
                            )
                        ]
                    )
                    for frame_number, i
                    in enumerate(
                        frame_indices
                    )
                ]
            )
        ],
        margin=dict(
            l=70,
            r=30,
            t=100,
            b=110
        )
    )

    st.plotly_chart(
        trajectory,
        use_container_width=True,
        key="rocket_flight_animation"
    )

    st.subheader(
        "🌍 Flight Trajectory"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["x"] / 1000,
            y=df["altitude"] / 1000,
            mode="lines",
            name="Rocket"
        )
    )

    fig.update_layout(
        xaxis_title="Horizontal Distance (km)",
        yaxis_title="Altitude (km)",
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader(
        "📈 Altitude vs Time"
    )

    fig_altitude = go.Figure()

    fig_altitude.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["altitude"] / 1000,
            mode="lines",
            name="Altitude"
        )
    )

    fig_altitude.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Altitude (km)",
        height=450
    )

    st.plotly_chart(
        fig_altitude,
        use_container_width=True
    )

    st.subheader(
        "🚀 Velocity vs Time"
    )

    fig_velocity = go.Figure()

    fig_velocity.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["velocity"] / 1000,
            mode="lines",
            name="Velocity"
        )
    )

    fig_velocity.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["velocity_x"] / 1000,
            mode="lines",
            name="Horizontal Velocity"
        )
    )

    fig_velocity.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["velocity_y"] / 1000,
            mode="lines",
            name="Vertical Velocity"
        )
    )

    fig_velocity.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Velocity (km/s)",
        height=450
    )

    st.plotly_chart(
        fig_velocity,
        use_container_width=True
    )

    st.subheader(
        "⚡ Acceleration"
    )

    fig_acceleration = go.Figure()

    fig_acceleration.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["acceleration"] / G0,
            mode="lines",
            name="Total Acceleration"
        )
    )

    fig_acceleration.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Acceleration (g)",
        height=450
    )

    st.plotly_chart(
        fig_acceleration,
        use_container_width=True
    )

    st.subheader(
        "⛽ Mass and Fuel"
    )

    fig_mass = go.Figure()

    fig_mass.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["mass"],
            mode="lines",
            name="Total Mass"
        )
    )

    fig_mass.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["fuel"],
            mode="lines",
            name="Fuel Remaining"
        )
    )

    fig_mass.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Mass (kg)",
        height=450
    )

    st.plotly_chart(
        fig_mass,
        use_container_width=True
    )

    st.subheader(
        "🔥 Thrust vs Aerodynamic Drag"
    )

    fig_forces = go.Figure()

    fig_forces.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["thrust"] / 1000,
            mode="lines",
            name="Thrust"
        )
    )

    fig_forces.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["drag"] / 1000,
            mode="lines",
            name="Drag"
        )
    )

    fig_forces.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Force (kN)",
        height=450
    )

    st.plotly_chart(
        fig_forces,
        use_container_width=True
    )

    st.subheader(
        "💨 Mach Number"
    )

    fig_mach = go.Figure()

    fig_mach.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["mach"],
            mode="lines",
            name="Mach"
        )
    )

    fig_mach.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Mach",
        height=400
    )

    st.plotly_chart(
        fig_mach,
        use_container_width=True
    )

    st.subheader(
        "⚙️ Engine Performance"
    )

    e1, e2, e3 = st.columns(3)

    e1.metric(
        "Mass Flow Rate",
        f"{mdot:.2f} kg/s"
    )

    e2.metric(
        "Estimated Fuel Burn",
        f"{stage_burn_time:.1f} s"
    )

    e3.metric(
        "Total Impulse",
        f"{total_impulse / 1e9:.2f} GN·s"
    )

    st.divider()

    st.header(
        "📚 How the Simulation Works"
    )

    st.markdown(
        """
        This simulator calculates the rocket's trajectory by
        repeatedly applying the laws of physics over small time
        intervals.

        At every time step, the simulator calculates the forces
        acting on the rocket, finds the resulting acceleration,
        and then updates the rocket's velocity and position.
        """
    )

    with st.expander("1️⃣ Engine Thrust"):

        st.markdown(
            "### Rocket Engine Thrust"
        )

        st.latex(
            r"T=\dot{m}V_e+(p_e-p_a)A_e"
        )

        st.markdown(
            """
            The simulator uses the general rocket thrust equation.

            Where:

            - **T** = total engine thrust
            - **ṁ** = propellant mass flow rate
            - **Vₑ** = exhaust velocity
            - **pₑ** = nozzle exit pressure
            - **pₐ** = atmospheric pressure
            - **Aₑ** = nozzle exit area
            """
        )

        st.latex(
            r"V_e=I_{sp}g_0"
        )

        st.latex(
            r"T=\dot{m}I_{sp}g_0+(p_e-p_a)A_e"
        )

    with st.expander("2️⃣ Gravity"):

        st.markdown(
            "### Gravity Changes with Altitude"
        )

        st.latex(
            r"g(h)=g_0\left(\frac{R_E}{R_E+h}\right)^2"
        )

    with st.expander("3️⃣ Atmospheric Density"):

        st.markdown(
            "### Earth's Atmosphere"
        )

        st.markdown(
            """
            Atmospheric density decreases with altitude.

            The simulator calculates:

            - Temperature
            - Pressure
            - Air density
            - Speed of sound
            """
        )

        st.latex(
            r"\rho=\frac{P}{RT}"
        )

    with st.expander("4️⃣ Atmospheric Drag"):

        st.markdown(
            "### Aerodynamic Drag"
        )

        st.latex(
            r"D=\frac{1}{2}\rho v^2C_DA"
        )

        st.latex(
            r"D_x=-D\frac{v_x}{v}"
        )

        st.latex(
            r"D_y=-D\frac{v_y}{v}"
        )

    with st.expander(
        "5️⃣ Launch Angle and Force Components"
    ):

        st.markdown(
            """
            The launch angle is measured relative to the ground.

            - **0°** = horizontal launch
            - **45°** = 45° above horizontal
            - **90°** = vertical launch
            """
        )

        st.latex(
            r"T_x=T\cos(\theta)"
        )

        st.latex(
            r"T_y=T\sin(\theta)"
        )

    with st.expander("6️⃣ Net Force"):

        st.latex(
            r"F_x=T_x+D_x"
        )

        st.latex(
            r"F_y=T_y+D_y-mg"
        )

    with st.expander("7️⃣ Acceleration"):

        st.latex(
            r"a_x=\frac{F_x}{m}"
        )

        st.latex(
            r"a_y=\frac{F_y}{m}"
        )

        st.latex(
            r"a=\sqrt{a_x^2+a_y^2}"
        )

    with st.expander("8️⃣ Velocity Update"):

        st.latex(
            r"v_{x,new}=v_{x,old}+a_x\Delta t"
        )

        st.latex(
            r"v_{y,new}=v_{y,old}+a_y\Delta t"
        )

        st.latex(
            r"v=\sqrt{v_x^2+v_y^2}"
        )

    with st.expander(
        "9️⃣ Position / Altitude Update"
    ):

        st.latex(
            r"x_{new}=x_{old}+v_x\Delta t"
        )

        st.latex(
            r"h_{new}=h_{old}+v_y\Delta t"
        )

    with st.expander("🔟 Orbital Velocity"):

        st.latex(
            r"v_{orb}=\sqrt{\frac{\mu}{R_E+h}}"
        )

        st.markdown(
            """
            This is the ideal circular orbital speed at the
            current altitude.

            The simulator compares the rocket's total velocity
            with this value.
            """
        )

    with st.expander(
        "🔄 Complete Simulation Loop"
    ):

        st.markdown(
            """
            At every simulation time step:

            **1.** Determine altitude.

            **2.** Calculate atmospheric temperature,
            pressure and density.

            **3.** Calculate gravity.

            **4.** Calculate exhaust velocity.

            **5.** Calculate mass flow rate.

            **6.** Calculate thrust using momentum and pressure thrust.

            **7.** Calculate the rocket velocity vector.

            **8.** Calculate aerodynamic drag.

            **9.** Resolve thrust into horizontal and vertical components.

            **10.** Resolve drag into horizontal and vertical components.

            **11.** Calculate net forces.

            **12.** Calculate acceleration.

            **13.** Update velocity.

            **14.** Update position and altitude.

            **15.** Calculate Mach number and dynamic pressure.

            **16.** Calculate orbital velocity.

            **17.** Store the results.

            **18.** Repeat until the simulation ends.
            """
        )

        st.markdown(
            "### 🚀 In short"
        )

        st.latex(
            r"\text{Thrust + Drag + Gravity}"
            r"\rightarrow"
            r"\text{Acceleration}"
            r"\rightarrow"
            r"\text{Velocity}"
            r"\rightarrow"
            r"\text{Position}"
        )

        st.success(
            "Repeating this process over many small time steps "
            "produces the rocket's simulated trajectory."
        )

else:

    st.info(
        "Configure the rocket parameters in the sidebar "
        "and click **Launch Simulation**."
    )
