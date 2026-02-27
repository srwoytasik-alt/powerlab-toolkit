import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from modules.mosfet import conduction_loss, switching_loss, total_loss
from modules.thermal import junction_temp_simple, junction_temp_detailed, safety_margin

st.set_page_config(page_title="MOSFET Power & Thermal Analyzer", layout="wide")

st.title("⚡ MOSFET Power & Thermal Analyzer")

# =========================
# Sidebar Inputs
# =========================

st.sidebar.header("Electrical Parameters")

Vds = st.sidebar.number_input("Vds (V)", value=400.0)
Id = st.sidebar.number_input("Drain Current Id (A)", value=10.0)
Rds = st.sidebar.number_input("Rds(on) (Ω)", value=0.05)

st.sidebar.header("Switching Parameters")

tr = st.sidebar.number_input("Rise Time (ns)", value=50.0) * 1e-9
tf = st.sidebar.number_input("Fall Time (ns)", value=50.0) * 1e-9
fsw = st.sidebar.number_input("Switching Frequency (Hz)", value=50000.0)

st.sidebar.header("Output Parameters")

Vout = st.sidebar.number_input("Output Voltage (V)", value=48.0)
Iout = st.sidebar.number_input("Output Current (A)", value=10.0)

st.sidebar.header("Thermal Model")

Ta = st.sidebar.number_input("Ambient Temperature (°C)", value=25.0)
Tj_max = st.sidebar.number_input("Maximum Junction Temp (°C)", value=150.0)

thermal_mode = st.sidebar.radio(
    "Thermal Model Type",
    ["Simple (RθJA)", "Detailed Stack"],
    index=1
)

if thermal_mode == "Simple (RθJA)":
    Rth_ja = st.sidebar.number_input("RθJA (°C/W)", value=4.0)
else:
    Rth_jc = st.sidebar.number_input("RθJC (°C/W)", value=1.5)
    Rth_cs = st.sidebar.number_input("RθCS (°C/W)", value=0.5)
    Rth_sa = st.sidebar.number_input("RθSA (°C/W)", value=3.0)

enable_sweeps = st.sidebar.checkbox("Enable Parameter Sweeps", value=True)

# =========================
# Core Calculations
# =========================

Pcond = conduction_loss(Id, Rds)
Psw = switching_loss(Vds, Id, tr, tf, fsw)
Ptotal = total_loss(Pcond, Psw)

if thermal_mode == "Simple (RθJA)":
    Tj = junction_temp_simple(Ta, Ptotal, Rth_ja)
    Rth_total_current = Rth_ja
else:
    Tj = junction_temp_detailed(Ta, Ptotal, Rth_jc, Rth_cs, Rth_sa)
    Rth_total_current = Rth_jc + Rth_cs + Rth_sa

margin = safety_margin(Tj, Tj_max)

# Efficiency
Pout = Vout * Iout
Pin = Pout + Ptotal
efficiency = Pout / Pin if Pin > 0 else 0.0
efficiency = max(0.0, min(efficiency, 1.0))

# =========================
# Metrics Display
# =========================

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Conduction Loss (W)", f"{Pcond:.2f}")
col2.metric("Switching Loss (W)", f"{Psw:.2f}")
col3.metric("Total Loss (W)", f"{Ptotal:.2f}")
col4.metric("Junction Temp (°C)", f"{Tj:.1f}")
col5.metric("Efficiency (%)", f"{efficiency * 100:.2f}")

# =========================
# Thermal Warning Logic
# =========================

if Tj > Tj_max:
    st.error("⚠ Junction temperature exceeds maximum limit!")
elif Tj > Tj_max - 25:
    st.warning("⚠ Junction temperature approaching limit.")
else:
    st.success("Thermal performance within safe range.")

# =========================
# Automatic Heatsink Sizing
# =========================

st.subheader("Required Thermal Resistance")

if Ptotal > 0:
    Rth_required_total = (Tj_max - Ta) / Ptotal
    st.write(f"Required Total Thermal Resistance (°C/W): {Rth_required_total:.2f}")

    if thermal_mode == "Detailed Stack":
        Rth_sa_required = Rth_required_total - Rth_jc - Rth_cs
        st.write(f"Required Heatsink RθSA (°C/W): {Rth_sa_required:.2f}")

        if Rth_sa_required < 0:
            st.success("Current heatsink exceeds required performance.")
        else:
            st.info("Select a heatsink with RθSA less than this value.")
else:
    st.write("No thermal resistance requirement (zero power dissipation).")

# =========================
# Power Breakdown Plot
# =========================

fig1, ax1 = plt.subplots()
ax1.bar(["Conduction", "Switching"], [Pcond, Psw])
ax1.set_ylabel("Power Loss (W)")
ax1.set_title("Power Loss Breakdown")
st.pyplot(fig1)

# =========================
# Parameter Sweeps
# =========================

if enable_sweeps:

    I_sweep = np.linspace(max(0.1, Id * 0.05), Id * 2, 100)

    # Junction Temp vs Current
    st.subheader("Junction Temperature vs Drain Current")

    Tj_sweep = []

    for I in I_sweep:
        Pcond_s = conduction_loss(I, Rds)
        Psw_s = switching_loss(Vds, I, tr, tf, fsw)
        Ptotal_s = total_loss(Pcond_s, Psw_s)

        if thermal_mode == "Simple (RθJA)":
            Tj_s = junction_temp_simple(Ta, Ptotal_s, Rth_ja)
        else:
            Tj_s = junction_temp_detailed(Ta, Ptotal_s, Rth_jc, Rth_cs, Rth_sa)

        Tj_sweep.append(Tj_s)

    fig2, ax2 = plt.subplots()
    ax2.plot(I_sweep, Tj_sweep)
    ax2.axhline(Tj_max)
    ax2.set_xlabel("Drain Current (A)")
    ax2.set_ylabel("Junction Temperature (°C)")
    ax2.set_title("Junction Temperature vs Current")
    st.pyplot(fig2)

# =========================
# Safety Margin
# =========================

st.subheader("Thermal Safety Margin")
st.write(f"Remaining Margin to {Tj_max:.0f}°C: {margin:.1f} °C")
