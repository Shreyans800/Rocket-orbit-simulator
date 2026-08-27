import math, base64
from io import BytesIO
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title="Rocket Launch Simulator", layout="wide", initial_sidebar_state="expanded")

G0, R_EARTH, MU_EARTH, R_AIR, GAMMA = 9.80665, 6_371_000.0, 3.986004418e14, 287.05, 1.4


def atmosphere(h):
    h = max(0.0, h)
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
    return P / (R_AIR * T), P, T, math.sqrt(GAMMA * R_AIR * T)


@st.cache_data(show_spinner=False)
def create_rocket_images():
    imgs, size = {}, 160
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)

    d.polygon([(80, 12), (48, 58), (48, 108), (112, 108), (112, 58)], fill=(235, 238, 242, 255))

    d.ellipse((60, 42, 100, 82), fill=(35, 95, 150, 255), outline=(210, 225, 240, 255), width=3)

    d.polygon([(48, 82), (20, 120), (48, 108)], fill=(200, 45, 45, 255))

    d.polygon([(112, 82), (140, 120), (112, 108)], fill=(200, 45, 45, 255))
    
    d.rectangle((52, 100, 108, 116), fill=(210, 214, 220, 255))

    d.polygon([(60, 114), (80, 154), (100, 114)], fill=(255, 145, 35, 255))
    
    d.polygon([(69, 114), (80, 145), (91, 114)], fill=(255, 220, 80, 255))

    for a in range(0, 360, 5):
        r = base.rotate(a - 90, resample=Image.Resampling.BICUBIC, expand=True)
        b = BytesIO()
        r.save(b, format="PNG")
        imgs[a] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    return imgs



def simulate(dry, fuel0, isp, burn, cd, area, angle, sim_time, dt, target, p_exit, a_exit):

    mass, fuel = dry + fuel0, fuel0

    h, vx, vy, x = 0.0, 0.0, 0.0, 0.0
    
    rows, ve = [], isp * G0

    mdot = fuel0 / burn
    
    angle_rad = math.radians(angle)

    tx_dir, ty_dir = math.cos(angle_rad), math.sin(angle_rad)


    impulse = 0.0

    for step in range(int(sim_time / dt) + 1):
        t = step * dt
        rho, pressure, temp, sound = atmosphere(h)

        if fuel > 0 and t < burn:
            thrust = max(0.0, mdot * ve + (p_exit - pressure) * a_exit)
            fuel -= min(mdot * dt, fuel)
            mass = dry + fuel

        else:
            thrust, mass = 0.0, dry


        g = G0 * (R_EARTH / (R_EARTH + h)) ** 2
        v = math.hypot(vx, vy)
        q = 0.5 * rho * v ** 2
        drag = q * cd * area

        if v > 0:
            dx, dy = -drag * vx / v, -drag * vy / v
        else:
            dx = dy = 0.0

        thrust_x, thrust_y = thrust * tx_dir, thrust * ty_dir
        ax = (thrust_x + dx) / mass
        ay = (thrust_y + dy - mass * g) / mass
        acc = math.hypot(ax, ay)

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        h += vy * dt
        

        if h < 0:
            h, vy = 0.0, 0.0

        v = math.hypot(vx, vy)
        mach = v / sound if sound > 0 else 0.0

        v_orbit = math.sqrt(MU_EARTH / (R_EARTH + h))
        impulse += thrust * dt


        rows.append({
            "time": t, "altitude": h, "velocity": v,

            "velocity_x": vx, "velocity_y": vy,

            "acceleration": acc, "acceleration_x": ax,

            "acceleration_y": ay, "mass": mass, "fuel": max(fuel, 0),

            "thrust": thrust, "thrust_x": thrust_x, "thrust_y": thrust_y,

            "drag": drag, "drag_x": dx, "drag_y": dy, "gravity": g,
           
            "density": rho, "pressure": pressure, "temperature": temp,

            "mach": mach, "dynamic_pressure": q,

            "orbital_velocity": v_orbit, "x": x, "y": h
        })

        if h <= 0 and t > 5 and vy < 0 or h >= target:
            break

    df = pd.DataFrame(rows)

    max_h, max_v = df.altitude.max(), df.velocity.max()

    max_acc, max_q = df.acceleration.max(), df.dynamic_pressure.max()
    
    final_v, final_h = df.velocity.iloc[-1], df.altitude.iloc[-1]

    v_orbit = math.sqrt(MU_EARTH / (R_EARTH + target))

    ratio = final_v / v_orbit if v_orbit else 0

    return df, max_h, max_v, max_acc, max_q, final_v, final_h, v_orbit, ratio, mdot, burn, impulse



st.title("Rocket Launch Simulator")



st.markdown("Simulate a rocket launch while accounting for **thrust, fuel consumption, gravity, atmospheric drag and changing mass**.")

st.sidebar.header("Rocket Parameters")

dry = st.sidebar.number_input("Dry Mass (kg)", 1000.0, 1_000_000.0, 20_000.0, 5000.0)


fuel0 = st.sidebar.number_input("Fuel Mass (kg)", 1000.0, 1_000_000.0, 50_000.0, 5000.0)

isp = st.sidebar.number_input("Specific Impulse (s)", 100.0, 800.0, 300.0, 20.0)

burn = st.sidebar.number_input("Burn Time (s)", 50.0, 1000.0, 150.0, 20.0)

st.sidebar.header("Engine / Nozzle")


p_exit = st.sidebar.number_input("Nozzle Exit Pressure (Pa)", 0.0, 1_000_000.0, 50_000.0, 5000.0)


a_exit = st.sidebar.number_input("Nozzle Exit Area (m²)", 0.001, 100.0, 1.0, 0.1)

st.sidebar.header("Aerodynamics")


cd = st.sidebar.number_input("Drag Coefficient", 0.05, 2.0, 0.35, 0.05)

area = st.sidebar.number_input("Reference Area (m²)", 0.1, 1000.0, 10.0, 1.0)


st.sidebar.header("Launch")

angle = st.sidebar.slider("Launch Angle (From Ground in degrees)", 0.0, 90.0, 90.0, 1.0)

st.sidebar.caption("0° = horizontal | 90° = vertical")


target = st.sidebar.number_input("Target Altitude (km)", 10.0, 4000.0, 200.0, 50.0) * 1000

sim_time = st.sidebar.number_input("Maximum Simulation Time (s)", 30.0, 5000.0, 600.0, 30.0)

dt = st.sidebar.select_slider("Simulation Time Step (s)", [0.1, 0.25, 0.5, 1.0, 2.0], value=2.0)


if st.button("Launch Simulation", type="primary"):
    with st.spinner("Simulating launch..."):
        result = simulate(dry, fuel0, isp, burn, cd, area, angle, sim_time, dt, target, p_exit, a_exit)

    df, max_h, max_v, max_acc, max_q, final_v, final_h, v_orbit, ratio, mdot, stage_burn, impulse = result
    imgs = create_rocket_images()

    st.success("Simulation complete!")

    c1, c2, c3, c4 = st.columns(4)


    c1.metric("Maximum Altitude", f"{max_h / 1000:.2f} km")

    c2.metric("Maximum Velocity", f"{max_v / 1000:.2f} km/s")

    
    c3.metric("Maximum Acceleration", f"{max_acc / G0:.2f} g")


    
    c4.metric("Peak Dynamic Pressure", f"{max_q / 1000:.1f} kPa")

    st.subheader("Orbital Insertion Analysis")

    c1, c2, c3 = st.columns(3)
    
    c1.metric("Final Altitude", f"{final_h / 1000:.2f} km")
    
    c2.metric("Final Velocity", f"{final_v / 1000:.2f} km/s")

    c3.metric("Required Circular Velocity", f"{v_orbit / 1000:.2f} km/s")

    if final_h >= target * 0.95 and ratio >= 0.95:
        st.success("The simulated vehicle reached approximately orbital velocity at the target altitude.")


    elif final_h >= target * 0.95:
        st.warning("Target altitude reached, but velocity is insufficient for a circular orbit.")

    else:
        st.error("The rocket did not reach the target altitude.")

    st.subheader("Animated Rocket Flight")

    x_km = df.x.to_numpy() / 1000

    y_km = df.altitude.to_numpy() / 1000

    times = df.time.to_numpy()

    max_x = max(1.0, float(np.max(np.abs(x_km))))
    max_y = max(1.0, float(np.max(y_km)))

    if angle == 90:
        x_min, x_max = -max_x * 0.45, max_x * 0.45
    else:
        x_min, x_max = min(-max_x * 0.08, -1.0), max(max_x * 1.15, 10.0)

    y_min, y_max = 0.0, max(max_y * 1.15, 10.0)
    n_frames = min(len(df), 180)
    frame_ids = np.linspace(0, len(df) - 1, n_frames, dtype=int)

    sx = max((x_max - x_min) * 0.15, 0.5)
    sy = max((y_max - y_min) * 0.15, 0.5)

    def rocket_angle_for_index(i):
        vx = float(df["velocity_x"].iloc[i])

        vy = float(df["velocity_y"].iloc[i])

        speed = math.hypot(vx, vy)

        if speed < 1e-9:
            vx = math.cos(angle_rad)
            vy = math.sin(angle_rad)

        heading = math.degrees(math.atan2(vy, vx))
        if heading < 0:
            heading += 360

        return round(heading / 5) * 5 % 360

    angle_rad = math.radians(angle)

    initial_heading = angle if angle <= 90 else 90
    initial_heading = round(initial_heading / 5) * 5 % 360

    initial_img = dict(
        source=imgs[initial_heading], x=x_km[0], y=y_km[0],
        xref="x", yref="y", sizex=sx, sizey=sy,
        xanchor="center", yanchor="middle", sizing="contain",
        layer="above", opacity=1
    )

    frames = []

    for n, i in enumerate(frame_ids):
        heading = rocket_angle_for_index(i)
        frame_img = dict(
            source=imgs[heading], x=x_km[i], y=y_km[i],
            xref="x", yref="y", sizex=sx, sizey=sy,
            xanchor="center", yanchor="middle", sizing="contain",
            layer="above", opacity=1
        )

        frames.append(go.Frame(
            name=str(n),
            data=[go.Scatter(
                x=x_km[:i + 1], y=y_km[:i + 1],
                mode="lines", line=dict(width=4), name="Rocket Path"
            )],
            traces=[1],
            layout=go.Layout(images=[frame_img])
        ))

    trajectory = go.Figure(
        data=[
            go.Scatter(
                x=x_km, y=y_km, mode="lines",
                line=dict(width=2, dash="dot"),
                opacity=0.45, name="Planned Trajectory"
            ),
            go.Scatter(
                x=[x_km[0]], y=[y_km[0]], mode="lines",
                line=dict(width=4), name="Rocket Path"
            )
        ],
        frames=frames
    )

    trajectory.update_layout(
        height=680,

        paper_bgcolor="rgb(2, 7, 18)",

        plot_bgcolor="rgb(5, 15, 32)",

        font=dict(color="white"),

        xaxis=dict(
            title="Horizontal Distance (km)", range=[x_min, x_max],

            zeroline=True, zerolinecolor="rgba(255,255,255,0.30)",

            gridcolor="rgba(255,255,255,0.10)",
            showline=True, linecolor="rgba(255,255,255,0.35)"
        ),
        yaxis=dict(
            title="Altitude (km)", range=[y_min, y_max],

            zeroline=True, zerolinecolor="rgba(255,255,255,0.30)",
            gridcolor="rgba(255,255,255,0.10)",
            showline=True, linecolor="rgba(255,255,255,0.35)"

        ),
        images=[initial_img],
        hovermode="closest",

        updatemenus=[dict(
            type="buttons", direction="left", x=0, y=1.08, showactive=False,
            buttons=[

                dict(
                    label="Play", method="animate",
                    args=[None, dict(

                        frame=dict(duration=70, redraw=True),
                        transition=dict(duration=0),

                        fromcurrent=False, mode="immediate"
                    )]
                ),
                dict(
                    label="Pause", method="animate",

                    args=[[None], dict(
                        frame=dict(duration=0, redraw=False),
                        transition=dict(duration=0),

                        mode="immediate"
                    )]
                )
            ]
        )],

        sliders=[dict(
            active=0, x=0, y=-0.10, len=1,
            currentvalue=dict(prefix="Simulation Time: "),
       
            steps=[
                dict(

                    label=f"{times[i]:.1f}s", method="animate",
                    args=[[str(n)], dict(

                        frame=dict(duration=0, redraw=True),
                        transition=dict(duration=0),
       
                        mode="immediate"
                    )]
                )
                for n, i in enumerate(frame_ids)

            ]
        )],
        margin=dict(l=70, r=30, t=100, b=110)
    )


    st.plotly_chart(trajectory, use_container_width=True, key="rocket_flight_animation")


    st.subheader("Flight Trajectory")
    fig = go.Figure(go.Scatter(x=df.x / 1000, y=df.altitude / 1000, mode="lines", name="Rocket"))

    fig.update_layout(xaxis_title="Horizontal Distance (km)", yaxis_title="Altitude (km)", height=500)

    st.plotly_chart(fig, use_container_width=True)


    st.subheader("Altitude vs Time")

    fig = go.Figure(go.Scatter(x=df.time, y=df.altitude / 1000, mode="lines", name="Altitude"))

    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Altitude (km)", height=450)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Velocity vs Time")
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.time, y=df.velocity / 1000, mode="lines", name="Velocity"))

    fig.add_trace(go.Scatter(x=df.time, y=df.velocity_x / 1000, mode="lines", name="Horizontal Velocity"))

    fig.add_trace(go.Scatter(x=df.time, y=df.velocity_y / 1000, mode="lines", name="Vertical Velocity"))

    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Velocity (km/s)", height=450)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Acceleration")
    fig = go.Figure(go.Scatter(x=df.time, y=df.acceleration / G0, mode="lines", name="Total Acceleration"))

    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Acceleration (g)", height=450)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Mass and Fuel")
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.time, y=df.mass, mode="lines", name="Total Mass"))

    fig.add_trace(go.Scatter(x=df.time, y=df.fuel, mode="lines", name="Fuel Remaining"))

    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Mass (kg)", height=450)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Thrust vs Aerodynamic Drag")
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.time, y=df.thrust / 1000, mode="lines", name="Thrust"))

    fig.add_trace(go.Scatter(x=df.time, y=df.drag / 1000, mode="lines", name="Drag"))

    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Force (kN)", height=450)
    st.plotly_chart(fig, use_container_width=True)


    st.subheader("Mach Number")
    fig = go.Figure(go.Scatter(x=df.time, y=df.mach, mode="lines", name="Mach"))

    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Mach", height=400)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Engine Performance")

    e1, e2, e3 = st.columns(3)

    e1.metric("Mass Flow Rate", f"{mdot:.2f} kg/s")

    e2.metric("Estimated Fuel Burn", f"{stage_burn:.1f} s")

    e3.metric("Total Impulse", f"{impulse / 1e9:.2f} GN·s")

    st.divider()
    st.header("How the Simulation Works")

    st.markdown(
        """
        This simulator calculates the rocket's trajectory by repeatedly
        applying the laws of physics over small time intervals.
        """
    )

    with st.expander("1. Engine Thrust"):

        st.markdown("### Rocket Engine Thrust")

        st.latex(r"T=\dot{m}V_e+(p_e-p_a)A_e")

        st.markdown("- **T** = total engine thrust\n- **ṁ** = propellant mass flow rate\n- **Vₑ** = exhaust velocity\n- **pₑ** = nozzle exit pressure\n- **pₐ** = atmospheric pressure\n- **Aₑ** = nozzle exit area")

        st.latex(r"V_e=I_{sp}g_0")

        st.latex(r"T=\dot{m}I_{sp}g_0+(p_e-p_a)A_e")

    with st.expander("2. Gravity"):

        st.markdown("### Gravity Changes with Altitude")

        st.latex(r"g(h)=g_0\left(\frac{R_E}{R_E+h}\right)^2")

    with st.expander("3. Atmospheric Density"):

        st.markdown("### Earth's Atmosphere")

        st.markdown("The simulator calculates temperature, pressure, air density and speed of sound.")

        st.latex(r"\rho=\frac{P}{RT}")

    with st.expander("4. Atmospheric Drag"):

        st.markdown("### Aerodynamic Drag")

        st.latex(r"D=\frac{1}{2}\rho v^2C_DA")

        st.latex(r"D_x=-D\frac{v_x}{v}")

        st.latex(r"D_y=-D\frac{v_y}{v}")

    with st.expander("5. Launch Angle and Force Components"):
        st.markdown("0° = horizontal, 45° = 45° above horizontal, 90° = vertical.")

        st.latex(r"T_x=T\cos(\theta)")

        st.latex(r"T_y=T\sin(\theta)")

    with st.expander("6. Net Force"):

        st.latex(r"F_x=T_x+D_x")

        st.latex(r"F_y=T_y+D_y-mg")

    with st.expander("7. Acceleration"):

        st.latex(r"a_x=\frac{F_x}{m}")

        st.latex(r"a_y=\frac{F_y}{m}")

        st.latex(r"a=\sqrt{a_x^2+a_y^2}")

    with st.expander("8. Velocity Update"):
        st.latex(r"v_{x,new}=v_{x,old}+a_x\Delta t")

        st.latex(r"v_{y,new}=v_{y,old}+a_y\Delta t")

        st.latex(r"v=\sqrt{v_x^2+v_y^2}")

    with st.expander("9. Position / Altitude Update"):

        st.latex(r"x_{new}=x_{old}+v_x\Delta t")

        st.latex(r"h_{new}=h_{old}+v_y\Delta t")

    with st.expander("10. Orbital Velocity"):
        st.latex(r"v_{orb}=\sqrt{\frac{\mu}{R_E+h}}")

        st.markdown("This is the ideal circular orbital speed at the current altitude.")

    with st.expander("Complete Simulation Loop"):
        st.markdown(
            """
            1. Determine altitude.
            2. Calculate atmospheric conditions.
            3. Calculate gravity.
            4. Calculate exhaust velocity and mass flow.
            5. Calculate thrust.
            6. Calculate velocity and drag.
            7. Resolve thrust and drag.
            8. Calculate net force and acceleration.
            9. Update velocity and position.
            10. Calculate Mach number, dynamic pressure and orbital velocity.
            11. Store results and repeat.
            """
        )
        st.latex(
            r"\text{Thrust + Drag + Gravity}"

            r"\rightarrow\text{Acceleration}"

            r"\rightarrow\text{Velocity}"

            r"\rightarrow\text{Position}"
        )

else:
    st.info("Configure the rocket parameters in the sidebar and click **Launch Simulation**.")
